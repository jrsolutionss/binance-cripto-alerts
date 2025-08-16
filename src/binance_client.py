# Binance API Client for cryptocurrency data retrieval
import time
import requests
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from config.settings import Settings
from src.utils import setup_logging, retry_on_exception, PerformanceTimer


class BinanceClient:
    """Client for interacting with Binance API"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or Settings.BINANCE_API_KEY
        self.secret_key = secret_key or Settings.BINANCE_SECRET_KEY
        self.logger = setup_logging()
        
        # Initialize Binance client (can work without API keys for public endpoints)
        try:
            if self.api_key and self.secret_key:
                self.client = Client(self.api_key, self.secret_key)
                self.logger.info("Initialized Binance client with API credentials")
            else:
                self.client = Client()  # Public endpoints only
                self.logger.info("Initialized Binance client for public endpoints only")
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance client: {e}")
            self.client = None
    
    @retry_on_exception(max_retries=Settings.MAX_RETRIES, delay=Settings.RETRY_DELAY)
    def get_24hr_ticker_stats(self) -> List[Dict[str, Any]]:
        """Get 24hr ticker statistics for all symbols"""
        try:
            with PerformanceTimer("24hr ticker stats") as timer:
                if self.client:
                    tickers = self.client.get_ticker()
                else:
                    # Fallback to direct API call
                    response = requests.get('https://api.binance.com/api/v3/ticker/24hr')
                    response.raise_for_status()
                    tickers = response.json()
                
                self.logger.info(f"Retrieved {len(tickers)} ticker stats in {timer.elapsed_seconds:.2f}s")
                return tickers
        
        except (BinanceAPIException, requests.RequestException) as e:
            self.logger.error(f"Error fetching 24hr ticker stats: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_24hr_ticker_stats: {e}")
            raise
    
    def get_top_symbols_by_volume(self, count: int = Settings.TOP_SYMBOLS_COUNT) -> List[str]:
        """Get top symbols by 24hr volume in USDT"""
        try:
            tickers = self.get_24hr_ticker_stats()
            
            # Filter for USDT pairs and valid volume data
            usdt_pairs = []
            for ticker in tickers:
                symbol = ticker.get('symbol', '')
                if symbol.endswith('USDT'):
                    try:
                        volume = float(ticker.get('quoteVolume', 0))
                        if volume > 0:
                            usdt_pairs.append({
                                'symbol': symbol,
                                'volume': volume,
                                'price_change_percent': float(ticker.get('priceChangePercent', 0))
                            })
                    except (ValueError, TypeError):
                        continue
            
            # Sort by volume and get top symbols
            usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
            top_symbols = [pair['symbol'] for pair in usdt_pairs[:count]]
            
            self.logger.info(f"Selected top {len(top_symbols)} symbols by 24hr volume")
            return top_symbols
        
        except Exception as e:
            self.logger.error(f"Error getting top symbols: {e}")
            return []
    
    @retry_on_exception(max_retries=Settings.MAX_RETRIES, delay=Settings.RETRY_DELAY)
    def get_historical_klines(self, symbol: str, interval: str = Settings.TIMEFRAME, 
                            days_back: int = Settings.HISTORICAL_DAYS) -> pd.DataFrame:
        """Get historical kline/candlestick data for a symbol"""
        try:
            # Calculate start date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_str = start_date.strftime('%Y-%m-%d')
            
            with PerformanceTimer(f"Historical data for {symbol}") as timer:
                if self.client:
                    klines = self.client.get_historical_klines(
                        symbol, interval, start_str
                    )
                else:
                    # Fallback to direct API call
                    start_timestamp = int(start_date.timestamp() * 1000)
                    url = f'https://api.binance.com/api/v3/klines'
                    params = {
                        'symbol': symbol,
                        'interval': interval,
                        'startTime': start_timestamp,
                        'limit': 1000
                    }
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    klines = response.json()
            
            if not klines:
                self.logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_timestamp', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ]
            
            df = pd.DataFrame(klines, columns=columns)
            
            # Convert numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert timestamp to datetime
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('datetime')
            
            # Sort by datetime
            df = df.sort_index()
            
            self.logger.debug(f"Retrieved {len(df)} records for {symbol} in {timer.elapsed_seconds:.2f}s")
            return df[['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']]
        
        except (BinanceAPIException, requests.RequestException) as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Unexpected error in get_historical_klines for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            if self.client:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return float(ticker['price'])
            else:
                response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
                response.raise_for_status()
                data = response.json()
                return float(data['price'])
        
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get exchange information for a symbol"""
        try:
            if self.client:
                exchange_info = self.client.get_exchange_info()
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        return symbol_info
            else:
                response = requests.get('https://api.binance.com/api/v3/exchangeInfo')
                response.raise_for_status()
                exchange_info = response.json()
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        return symbol_info
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_multiple_symbols_data(self, symbols: List[str], 
                                 days_back: int = Settings.HISTORICAL_DAYS) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols with rate limiting"""
        results = {}
        total_symbols = len(symbols)
        
        self.logger.info(f"Fetching historical data for {total_symbols} symbols")
        
        with PerformanceTimer(f"Batch data fetch for {total_symbols} symbols") as timer:
            for i, symbol in enumerate(symbols, 1):
                try:
                    df = self.get_historical_klines(symbol, days_back=days_back)
                    if not df.empty:
                        results[symbol] = df
                        self.logger.debug(f"✓ {symbol} ({i}/{total_symbols}) - {len(df)} records")
                    else:
                        self.logger.warning(f"✗ {symbol} ({i}/{total_symbols}) - No data")
                    
                    # Rate limiting
                    if i < total_symbols:  # Don't sleep after the last request
                        time.sleep(Settings.API_REQUEST_DELAY)
                
                except Exception as e:
                    self.logger.error(f"Failed to fetch data for {symbol}: {e}")
                    continue
        
        self.logger.info(f"Successfully fetched data for {len(results)}/{total_symbols} symbols "
                        f"in {timer.elapsed_seconds:.2f}s")
        return results
    
    def test_connection(self) -> bool:
        """Test connection to Binance API"""
        try:
            if self.client:
                self.client.ping()
            else:
                response = requests.get('https://api.binance.com/api/v3/ping')
                response.raise_for_status()
            
            self.logger.info("Binance API connection test successful")
            return True
        
        except Exception as e:
            self.logger.error(f"Binance API connection test failed: {e}")
            return False