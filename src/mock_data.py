# Mock data generator for testing the system without API access
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random


class MockDataGenerator:
    """Generate mock cryptocurrency data for testing"""
    
    def __init__(self):
        self.mock_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'SOLUSDT', 'DOTUSDT', 'MATICUSDT', 'LTCUSDT', 'AVAXUSDT'
        ]
    
    def generate_mock_ohlcv_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Generate mock OHLCV data for a symbol"""
        
        # Set base price based on symbol
        base_prices = {
            'BTCUSDT': 45000,
            'ETHUSDT': 3000,
            'BNBUSDT': 400,
            'XRPUSDT': 0.6,
            'ADAUSDT': 0.5,
            'SOLUSDT': 100,
            'DOTUSDT': 7,
            'MATICUSDT': 0.8,
            'LTCUSDT': 150,
            'AVAXUSDT': 35
        }
        
        base_price = base_prices.get(symbol, 1000)
        
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate price data with trend and noise
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
        
        price_changes = np.random.normal(0, 0.02, len(dates))  # 2% daily volatility
        
        # Add some trending behavior
        trend = np.linspace(-0.1, 0.1, len(dates))  # Slight trend over time
        
        prices = [base_price]
        for i, change in enumerate(price_changes[1:], 1):
            new_price = prices[-1] * (1 + change + trend[i] * 0.1)
            new_price = max(new_price, base_price * 0.5)  # Floor at 50% of base
            prices.append(new_price)
        
        # Generate OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Generate realistic OHLC from close price
            volatility = abs(np.random.normal(0, 0.01))  # Daily volatility
            high = close * (1 + volatility)
            low = close * (1 - volatility)
            open_price = prices[i-1] if i > 0 else close
            
            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            # Generate volume (more volume on volatile days)
            base_volume = random.uniform(1000000, 5000000)
            volume_multiplier = 1 + abs(close - open_price) / open_price
            volume = base_volume * volume_multiplier
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'quote_asset_volume': volume * close
            })
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def get_mock_top_symbols(self, count: int = 10) -> List[str]:
        """Get mock top symbols by volume"""
        return self.mock_symbols[:count]
    
    def get_mock_24hr_stats(self) -> List[Dict[str, Any]]:
        """Get mock 24hr ticker statistics"""
        stats = []
        for symbol in self.mock_symbols:
            base_volume = random.uniform(100000000, 1000000000)  # Large volume numbers
            price_change = random.uniform(-10, 10)  # ±10% change
            
            stats.append({
                'symbol': symbol,
                'quoteVolume': str(base_volume),
                'priceChangePercent': str(price_change),
                'lastPrice': str(random.uniform(0.1, 50000))
            })
        
        # Sort by volume (descending)
        stats.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        return stats
    
    def generate_mock_symbol_data(self, symbols: List[str], days: int = 100) -> Dict[str, pd.DataFrame]:
        """Generate mock data for multiple symbols"""
        symbol_data = {}
        for symbol in symbols:
            symbol_data[symbol] = self.generate_mock_ohlcv_data(symbol, days)
        return symbol_data