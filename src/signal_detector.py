# Signal Detection for Moving Average Crossovers
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from config.settings import Settings
from src.utils import setup_logging, PerformanceTimer, calculate_signal_strength


class SignalDetector:
    """Detect trading signals from moving average crossovers"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.crossover_types = Settings.CROSSOVER_TYPES
    
    def detect_crossover(self, fast_ma: pd.Series, slow_ma: pd.Series, 
                        lookback_periods: int = 3) -> Optional[Dict[str, Any]]:
        """Detect crossover between two moving average series"""
        if len(fast_ma) < lookback_periods + 1 or len(slow_ma) < lookback_periods + 1:
            return None
        
        # Align the series
        aligned_fast = fast_ma.dropna()
        aligned_slow = slow_ma.dropna()
        
        if len(aligned_fast) < 2 or len(aligned_slow) < 2:
            return None
        
        # Get recent values for crossover detection
        current_fast = aligned_fast.iloc[-1]
        current_slow = aligned_slow.iloc[-1]
        prev_fast = aligned_fast.iloc[-2]
        prev_slow = aligned_slow.iloc[-2]
        
        # Check for crossover
        crossover_type = None
        
        if prev_fast <= prev_slow and current_fast > current_slow:
            crossover_type = "GOLDEN_CROSS"  # Bullish crossover
        elif prev_fast >= prev_slow and current_fast < current_slow:
            crossover_type = "DEATH_CROSS"   # Bearish crossover
        
        if crossover_type:
            signal_strength = calculate_signal_strength(current_fast, current_slow)
            
            return {
                'type': crossover_type,
                'timestamp': aligned_fast.index[-1],
                'fast_ma_value': float(current_fast),
                'slow_ma_value': float(current_slow),
                'strength': signal_strength['strength'],
                'percentage_diff': signal_strength['percentage_diff'],
                'direction': signal_strength['direction']
            }
        
        return None
    
    def analyze_symbol_crossovers(self, symbol: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze all configured crossovers for a single symbol"""
        crossovers = []
        
        if df.empty:
            return crossovers
        
        for crossover_config in self.crossover_types:
            fast_period = crossover_config['fast']
            slow_period = crossover_config['slow']
            ma_type = crossover_config['type']
            
            fast_col = f'{ma_type}_{fast_period}'
            slow_col = f'{ma_type}_{slow_period}'
            
            if fast_col not in df.columns or slow_col not in df.columns:
                continue
            
            crossover = self.detect_crossover(df[fast_col], df[slow_col])
            
            if crossover:
                crossover.update({
                    'symbol': symbol,
                    'fast_period': fast_period,
                    'slow_period': slow_period,
                    'ma_type': ma_type,
                    'crossover_name': f'{ma_type}_{fast_period}_{slow_period}',
                    'current_price': float(df['close'].iloc[-1])
                })
                crossovers.append(crossover)
        
        return crossovers
    
    def detect_all_crossovers(self, symbol_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Detect crossovers for all symbols"""
        all_crossovers = []
        total_symbols = len(symbol_data)
        
        self.logger.info(f"Detecting crossovers for {total_symbols} symbols")
        
        with PerformanceTimer(f"Crossover detection for {total_symbols} symbols") as timer:
            for i, (symbol, df) in enumerate(symbol_data.items(), 1):
                try:
                    symbol_crossovers = self.analyze_symbol_crossovers(symbol, df)
                    all_crossovers.extend(symbol_crossovers)
                    
                    if symbol_crossovers:
                        self.logger.debug(f"Found {len(symbol_crossovers)} crossovers for {symbol}")
                
                except Exception as e:
                    self.logger.error(f"Error detecting crossovers for {symbol}: {e}")
                    continue
        
        self.logger.info(f"Found {len(all_crossovers)} total crossovers in {timer.elapsed_seconds:.2f}s")
        return all_crossovers
    
    def classify_signal_importance(self, crossover: Dict[str, Any]) -> str:
        """Classify the importance of a crossover signal"""
        strength = crossover.get('strength', 'MINIMAL')
        ma_type = crossover.get('ma_type', 'SMA')
        fast_period = crossover.get('fast_period', 20)
        slow_period = crossover.get('slow_period', 50)
        percentage_diff = crossover.get('percentage_diff', 0)
        
        # Base importance on multiple factors
        importance_score = 0
        
        # MA periods importance (longer periods = more important)
        if slow_period >= 200:
            importance_score += 3
        elif slow_period >= 50:
            importance_score += 2
        else:
            importance_score += 1
        
        # Signal strength importance
        if strength == 'STRONG':
            importance_score += 3
        elif strength == 'MEDIUM':
            importance_score += 2
        elif strength == 'WEAK':
            importance_score += 1
        
        # EMA crossovers are generally considered more responsive
        if ma_type == 'EMA':
            importance_score += 1
        
        # Large percentage differences indicate stronger signals
        if percentage_diff > 5:
            importance_score += 2
        elif percentage_diff > 2:
            importance_score += 1
        
        # Classify based on total score
        if importance_score >= 7:
            return 'HIGH'
        elif importance_score >= 4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def filter_recent_crossovers(self, crossovers: List[Dict[str, Any]], 
                                hours_back: int = 24) -> List[Dict[str, Any]]:
        """Filter crossovers that occurred within the specified time window"""
        if not crossovers:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_crossovers = []
        
        for crossover in crossovers:
            crossover_time = crossover.get('timestamp')
            if isinstance(crossover_time, pd.Timestamp):
                crossover_time = crossover_time.to_pydatetime()
            elif isinstance(crossover_time, str):
                crossover_time = pd.to_datetime(crossover_time).to_pydatetime()
            
            if crossover_time and crossover_time >= cutoff_time:
                recent_crossovers.append(crossover)
        
        return recent_crossovers
    
    def get_signal_statistics(self, crossovers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about detected signals"""
        if not crossovers:
            return {
                'total_signals': 0,
                'golden_crosses': 0,
                'death_crosses': 0,
                'high_importance': 0,
                'medium_importance': 0,
                'low_importance': 0
            }
        
        stats = {
            'total_signals': len(crossovers),
            'golden_crosses': 0,
            'death_crosses': 0,
            'high_importance': 0,
            'medium_importance': 0,
            'low_importance': 0,
            'ma_type_breakdown': {},
            'period_breakdown': {},
            'avg_percentage_diff': 0
        }
        
        total_diff = 0
        
        for crossover in crossovers:
            # Count crossover types
            if crossover.get('type') == 'GOLDEN_CROSS':
                stats['golden_crosses'] += 1
            elif crossover.get('type') == 'DEATH_CROSS':
                stats['death_crosses'] += 1
            
            # Count importance levels
            importance = self.classify_signal_importance(crossover)
            if importance == 'HIGH':
                stats['high_importance'] += 1
            elif importance == 'MEDIUM':
                stats['medium_importance'] += 1
            else:
                stats['low_importance'] += 1
            
            # MA type breakdown
            ma_type = crossover.get('ma_type', 'Unknown')
            stats['ma_type_breakdown'][ma_type] = stats['ma_type_breakdown'].get(ma_type, 0) + 1
            
            # Period breakdown
            periods = f"{crossover.get('fast_period', 0)}/{crossover.get('slow_period', 0)}"
            stats['period_breakdown'][periods] = stats['period_breakdown'].get(periods, 0) + 1
            
            # Average percentage difference
            total_diff += crossover.get('percentage_diff', 0)
        
        stats['avg_percentage_diff'] = total_diff / len(crossovers) if crossovers else 0
        
        return stats
    
    def rank_signals_by_importance(self, crossovers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank signals by importance and return sorted list"""
        if not crossovers:
            return []
        
        # Add importance classification to each crossover
        for crossover in crossovers:
            crossover['importance'] = self.classify_signal_importance(crossover)
        
        # Sort by importance (HIGH > MEDIUM > LOW) and then by percentage_diff
        importance_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        
        sorted_crossovers = sorted(
            crossovers,
            key=lambda x: (
                importance_order.get(x.get('importance', 'LOW'), 1),
                x.get('percentage_diff', 0)
            ),
            reverse=True
        )
        
        return sorted_crossovers
    
    def detect_multiple_timeframe_confluence(self, symbol_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Detect confluence when multiple timeframes/MAs show similar signals"""
        confluence_signals = []
        
        # Group crossovers by symbol
        symbol_crossovers = {}
        for symbol, df in symbol_data.items():
            crossovers = self.analyze_symbol_crossovers(symbol, df)
            if crossovers:
                symbol_crossovers[symbol] = crossovers
        
        # Look for confluence (multiple signals for the same symbol)
        for symbol, crossovers in symbol_crossovers.items():
            if len(crossovers) >= 2:
                # Check if signals are in the same direction
                golden_crosses = [c for c in crossovers if c['type'] == 'GOLDEN_CROSS']
                death_crosses = [c for c in crossovers if c['type'] == 'DEATH_CROSS']
                
                if len(golden_crosses) >= 2:
                    confluence_signals.append({
                        'symbol': symbol,
                        'confluence_type': 'BULLISH',
                        'signal_count': len(golden_crosses),
                        'signals': golden_crosses,
                        'avg_strength': np.mean([c['percentage_diff'] for c in golden_crosses])
                    })
                
                if len(death_crosses) >= 2:
                    confluence_signals.append({
                        'symbol': symbol,
                        'confluence_type': 'BEARISH',
                        'signal_count': len(death_crosses),
                        'signals': death_crosses,
                        'avg_strength': np.mean([c['percentage_diff'] for c in death_crosses])
                    })
        
        return confluence_signals