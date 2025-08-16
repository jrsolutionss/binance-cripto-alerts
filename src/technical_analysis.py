# Technical Analysis calculations for moving averages
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from config.settings import Settings
from src.utils import setup_logging, PerformanceTimer


class TechnicalAnalysis:
    """Technical analysis calculations for cryptocurrency data"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.ma_periods = Settings.MA_PERIODS
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            self.logger.warning(f"Insufficient data for SMA {period}: {len(data)} < {period}")
            return pd.Series(index=data.index, dtype=float)
        
        return data.rolling(window=period, min_periods=period).mean()
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            self.logger.warning(f"Insufficient data for EMA {period}: {len(data)} < {period}")
            return pd.Series(index=data.index, dtype=float)
        
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_all_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all configured moving averages for a DataFrame"""
        if df.empty or 'close' not in df.columns:
            self.logger.error("Invalid DataFrame for moving average calculation")
            return df
        
        result_df = df.copy()
        close_prices = df['close']
        
        # Calculate SMAs
        for period in self.ma_periods:
            sma_col = f'SMA_{period}'
            ema_col = f'EMA_{period}'
            
            result_df[sma_col] = self.calculate_sma(close_prices, period)
            result_df[ema_col] = self.calculate_ema(close_prices, period)
        
        return result_df
    
    def calculate_moving_average_data(self, symbol_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Calculate moving averages for multiple symbols"""
        results = {}
        total_symbols = len(symbol_data)
        
        self.logger.info(f"Calculating moving averages for {total_symbols} symbols")
        
        with PerformanceTimer(f"MA calculations for {total_symbols} symbols") as timer:
            for i, (symbol, df) in enumerate(symbol_data.items(), 1):
                try:
                    ma_df = self.calculate_all_moving_averages(df)
                    results[symbol] = ma_df
                    
                    # Log progress for every 10 symbols
                    if i % 10 == 0 or i == total_symbols:
                        self.logger.info(f"Processed {i}/{total_symbols} symbols")
                
                except Exception as e:
                    self.logger.error(f"Error calculating MAs for {symbol}: {e}")
                    continue
        
        self.logger.info(f"Completed MA calculations in {timer.elapsed_seconds:.2f}s")
        return results
    
    def get_latest_ma_values(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Get the latest moving average values for a symbol"""
        if df.empty:
            return {}
        
        latest_data = df.iloc[-1]  # Get the most recent row
        result = {
            'symbol': symbol,
            'timestamp': df.index[-1].isoformat(),
            'close_price': float(latest_data['close']),
            'volume': float(latest_data.get('volume', 0)),
        }
        
        # Add moving average values
        for period in self.ma_periods:
            sma_col = f'SMA_{period}'
            ema_col = f'EMA_{period}'
            
            if sma_col in df.columns:
                result[sma_col] = float(latest_data[sma_col]) if pd.notna(latest_data[sma_col]) else None
            
            if ema_col in df.columns:
                result[ema_col] = float(latest_data[ema_col]) if pd.notna(latest_data[ema_col]) else None
        
        return result
    
    def calculate_ma_slopes(self, df: pd.DataFrame, periods: int = 5) -> Dict[str, float]:
        """Calculate the slope of moving averages to determine trend strength"""
        slopes = {}
        
        if len(df) < periods + max(self.ma_periods):
            return slopes
        
        for period in self.ma_periods:
            for ma_type in ['SMA', 'EMA']:
                col_name = f'{ma_type}_{period}'
                if col_name in df.columns:
                    ma_series = df[col_name].dropna()
                    if len(ma_series) >= periods:
                        # Calculate slope using linear regression over last 'periods' data points
                        recent_values = ma_series.tail(periods).values
                        x = np.arange(len(recent_values))
                        slope = np.polyfit(x, recent_values, 1)[0]
                        slopes[col_name] = slope
        
        return slopes
    
    def analyze_ma_convergence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze convergence/divergence between moving averages"""
        if df.empty or len(df) < max(self.ma_periods):
            return {}
        
        latest_row = df.iloc[-1]
        analysis = {}
        
        # Compare different MA pairs
        for i, fast_period in enumerate(self.ma_periods[:-1]):
            for slow_period in self.ma_periods[i+1:]:
                for ma_type in ['SMA', 'EMA']:
                    fast_ma = f'{ma_type}_{fast_period}'
                    slow_ma = f'{ma_type}_{slow_period}'
                    
                    if fast_ma in df.columns and slow_ma in df.columns:
                        fast_val = latest_row[fast_ma]
                        slow_val = latest_row[slow_ma]
                        
                        if pd.notna(fast_val) and pd.notna(slow_val) and slow_val != 0:
                            diff_percent = ((fast_val - slow_val) / slow_val) * 100
                            
                            analysis[f'{fast_ma}_{slow_ma}_diff'] = {
                                'percentage_diff': diff_percent,
                                'fast_above_slow': fast_val > slow_val,
                                'convergence_strength': abs(diff_percent)
                            }
        
        return analysis
    
    def calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate price volatility using standard deviation"""
        if len(df) < period or 'close' not in df.columns:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        if len(returns) < period:
            return 0.0
        
        return float(returns.rolling(window=period).std().iloc[-1] * np.sqrt(252))  # Annualized
    
    def get_support_resistance_levels(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Identify potential support and resistance levels"""
        if len(df) < window:
            return {}
        
        recent_data = df.tail(window * 2)  # Use more data for better analysis
        
        # Simple support/resistance based on recent highs and lows
        resistance = float(recent_data['high'].max())
        support = float(recent_data['low'].min())
        
        # More sophisticated approach using local maxima/minima
        highs = recent_data['high'].rolling(window=5, center=True).max()
        lows = recent_data['low'].rolling(window=5, center=True).min()
        
        local_highs = recent_data[recent_data['high'] == highs]['high'].values
        local_lows = recent_data[recent_data['low'] == lows]['low'].values
        
        return {
            'resistance': resistance,
            'support': support,
            'local_resistance_avg': float(np.mean(local_highs)) if len(local_highs) > 0 else resistance,
            'local_support_avg': float(np.mean(local_lows)) if len(local_lows) > 0 else support
        }
    
    def generate_technical_summary(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a comprehensive technical analysis summary"""
        if df.empty:
            return {'symbol': symbol, 'error': 'No data available'}
        
        summary = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'data_points': len(df),
            'date_range': {
                'start': df.index[0].isoformat(),
                'end': df.index[-1].isoformat()
            }
        }
        
        # Latest values
        summary.update(self.get_latest_ma_values(df, symbol))
        
        # MA slopes for trend analysis
        summary['ma_slopes'] = self.calculate_ma_slopes(df)
        
        # Convergence analysis
        summary['convergence_analysis'] = self.analyze_ma_convergence(df)
        
        # Volatility
        summary['volatility'] = self.calculate_volatility(df)
        
        # Support/Resistance
        summary['support_resistance'] = self.get_support_resistance_levels(df)
        
        return summary
    
    def export_ma_data(self, symbol_data: Dict[str, pd.DataFrame], 
                      output_file: str) -> bool:
        """Export moving average data to CSV"""
        try:
            all_data = []
            
            for symbol, df in symbol_data.items():
                if df.empty:
                    continue
                
                df_copy = df.copy()
                df_copy['symbol'] = symbol
                df_copy['date'] = df_copy.index.date
                all_data.append(df_copy)
            
            if not all_data:
                self.logger.warning("No data to export")
                return False
            
            combined_df = pd.concat(all_data, ignore_index=False)
            combined_df.to_csv(output_file)
            
            self.logger.info(f"Exported MA data to {output_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting MA data: {e}")
            return False