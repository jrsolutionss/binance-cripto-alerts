# Technical Analysis utilities for Vercel serverless functions
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

class TechnicalAnalysis:
    """Simplified technical analysis calculations for serverless environment"""
    
    def __init__(self):
        self.ma_periods = [20, 50, 200]
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return pd.Series(dtype=float, index=prices.index)
        return prices.rolling(window=period, min_periods=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return pd.Series(dtype=float, index=prices.index)
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_all_ma(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Calculate all moving averages for a symbol"""
        if df.empty or 'close' not in df.columns:
            return {'symbol': symbol, 'error': 'No price data available'}
        
        close_prices = df['close']
        latest_price = float(close_prices.iloc[-1])
        
        # Calculate moving averages
        ma_data = {
            'symbol': symbol,
            'current_price': latest_price,
            'timestamp': datetime.now().isoformat(),
            'data_points': len(df),
            'moving_averages': {}
        }
        
        for period in self.ma_periods:
            sma = self.calculate_sma(close_prices, period)
            ema = self.calculate_ema(close_prices, period)
            
            ma_info = {
                'period': period,
                'sma_value': float(sma.iloc[-1]) if not sma.empty and not pd.isna(sma.iloc[-1]) else None,
                'ema_value': float(ema.iloc[-1]) if not ema.empty and not pd.isna(ema.iloc[-1]) else None,
                'sma_trend': self._get_trend(sma),
                'ema_trend': self._get_trend(ema),
                'price_vs_sma': None,
                'price_vs_ema': None
            }
            
            # Calculate price position relative to MAs
            if ma_info['sma_value']:
                ma_info['price_vs_sma'] = 'above' if latest_price > ma_info['sma_value'] else 'below'
                ma_info['sma_distance_pct'] = ((latest_price - ma_info['sma_value']) / ma_info['sma_value']) * 100
            
            if ma_info['ema_value']:
                ma_info['price_vs_ema'] = 'above' if latest_price > ma_info['ema_value'] else 'below'
                ma_info['ema_distance_pct'] = ((latest_price - ma_info['ema_value']) / ma_info['ema_value']) * 100
            
            ma_data['moving_averages'][f'ma_{period}'] = ma_info
        
        return ma_data
    
    def detect_crossovers(self, df: pd.DataFrame, symbol: str) -> List[Dict[str, Any]]:
        """Detect moving average crossovers"""
        if df.empty or len(df) < 200:  # Need enough data for 200-period MA
            return []
        
        close_prices = df['close']
        crossovers = []
        
        # Define crossover pairs to check
        crossover_pairs = [
            {'fast': 20, 'slow': 50, 'type': 'SMA'},
            {'fast': 50, 'slow': 200, 'type': 'SMA'},
            {'fast': 20, 'slow': 50, 'type': 'EMA'}
        ]
        
        for pair in crossover_pairs:
            fast_period = pair['fast']
            slow_period = pair['slow']
            ma_type = pair['type']
            
            if ma_type == 'SMA':
                fast_ma = self.calculate_sma(close_prices, fast_period)
                slow_ma = self.calculate_sma(close_prices, slow_period)
            else:  # EMA
                fast_ma = self.calculate_ema(close_prices, fast_period)
                slow_ma = self.calculate_ema(close_prices, slow_period)
            
            # Check for crossovers in the last few periods
            crossover = self._detect_crossover_pair(fast_ma, slow_ma, symbol, pair)
            if crossover:
                crossovers.append(crossover)
        
        return crossovers
    
    def _detect_crossover_pair(self, fast_ma: pd.Series, slow_ma: pd.Series, 
                              symbol: str, config: Dict) -> Optional[Dict[str, Any]]:
        """Detect crossover between two MA series"""
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return None
        
        # Get recent values
        fast_ma_clean = fast_ma.dropna()
        slow_ma_clean = slow_ma.dropna()
        
        if len(fast_ma_clean) < 2 or len(slow_ma_clean) < 2:
            return None
        
        current_fast = float(fast_ma_clean.iloc[-1])
        current_slow = float(slow_ma_clean.iloc[-1])
        prev_fast = float(fast_ma_clean.iloc[-2])
        prev_slow = float(slow_ma_clean.iloc[-2])
        
        crossover_type = None
        if prev_fast <= prev_slow and current_fast > current_slow:
            crossover_type = "GOLDEN_CROSS"  # Bullish
        elif prev_fast >= prev_slow and current_fast < current_slow:
            crossover_type = "DEATH_CROSS"   # Bearish
        
        if crossover_type:
            return {
                'symbol': symbol,
                'type': crossover_type,
                'timestamp': fast_ma_clean.index[-1].isoformat(),
                'ma_type': config['type'],
                'fast_period': config['fast'],
                'slow_period': config['slow'],
                'fast_ma_value': current_fast,
                'slow_ma_value': current_slow,
                'crossover_name': f"{config['type']}{config['fast']}/{config['slow']}",
                'signal_strength': abs(current_fast - current_slow) / current_slow * 100
            }
        
        return None
    
    def _get_trend(self, ma_series: pd.Series, periods: int = 5) -> str:
        """Determine trend direction of moving average"""
        if ma_series.empty or len(ma_series) < periods:
            return 'neutral'
        
        clean_ma = ma_series.dropna()
        if len(clean_ma) < periods:
            return 'neutral'
        
        recent_values = clean_ma.iloc[-periods:]
        if len(recent_values) < 2:
            return 'neutral'
        
        first_value = recent_values.iloc[0]
        last_value = recent_values.iloc[-1]
        
        change_pct = (last_value - first_value) / first_value * 100
        
        if change_pct > 1:
            return 'rising'
        elif change_pct < -1:
            return 'falling'
        else:
            return 'neutral'
    
    def get_market_summary(self, symbols_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate market summary from multiple symbols"""
        if not symbols_data:
            return {
                'total_symbols': 0,
                'timestamp': datetime.now().isoformat(),
                'error': 'No data available'
            }
        
        # Count crossovers and trends
        golden_crosses = 0
        death_crosses = 0
        above_ma20 = 0
        above_ma50 = 0
        above_ma200 = 0
        
        for data in symbols_data:
            if 'crossovers' in data:
                for crossover in data['crossovers']:
                    if crossover['type'] == 'GOLDEN_CROSS':
                        golden_crosses += 1
                    elif crossover['type'] == 'DEATH_CROSS':
                        death_crosses += 1
            
            if 'moving_averages' in data:
                ma_data = data['moving_averages']
                if 'ma_20' in ma_data and ma_data['ma_20'].get('price_vs_sma') == 'above':
                    above_ma20 += 1
                if 'ma_50' in ma_data and ma_data['ma_50'].get('price_vs_sma') == 'above':
                    above_ma50 += 1
                if 'ma_200' in ma_data and ma_data['ma_200'].get('price_vs_sma') == 'above':
                    above_ma200 += 1
        
        total_symbols = len(symbols_data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_symbols': total_symbols,
            'crossover_summary': {
                'golden_crosses': golden_crosses,
                'death_crosses': death_crosses,
                'total_crossovers': golden_crosses + death_crosses
            },
            'market_sentiment': {
                'above_ma20_pct': (above_ma20 / total_symbols * 100) if total_symbols > 0 else 0,
                'above_ma50_pct': (above_ma50 / total_symbols * 100) if total_symbols > 0 else 0,
                'above_ma200_pct': (above_ma200 / total_symbols * 100) if total_symbols > 0 else 0
            },
            'market_strength': self._calculate_market_strength(above_ma20, above_ma50, above_ma200, total_symbols)
        }
    
    def _calculate_market_strength(self, above_ma20: int, above_ma50: int, above_ma200: int, total: int) -> str:
        """Calculate overall market strength"""
        if total == 0:
            return 'neutral'
        
        # Weight different MAs
        score = (above_ma20 * 0.3 + above_ma50 * 0.4 + above_ma200 * 0.3) / total
        
        if score > 0.7:
            return 'very_bullish'
        elif score > 0.55:
            return 'bullish'
        elif score > 0.45:
            return 'neutral'
        elif score > 0.3:
            return 'bearish'
        else:
            return 'very_bearish'