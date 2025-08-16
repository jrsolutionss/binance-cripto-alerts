# Configuration module for Binance Crypto Alerts
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuration settings for the Binance Crypto Alerts system"""
    
    # API Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    
    # Moving Average Periods
    MA_PERIODS = [20, 50, 200]
    
    # Data Configuration
    TOP_SYMBOLS_COUNT = 100
    HISTORICAL_DAYS = 365
    TIMEFRAME = '1d'  # Daily timeframe
    
    # Rate Limiting
    API_REQUEST_DELAY = 0.1  # seconds between requests
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # Alert Configuration
    ALERT_LEVELS = {
        'HIGH': {'color': 'red', 'priority': 3},
        'MEDIUM': {'color': 'yellow', 'priority': 2},
        'LOW': {'color': 'green', 'priority': 1}
    }
    
    # File Paths
    DATA_DIR = 'data'
    LOGS_DIR = 'logs'
    
    # Export Configuration
    EXPORT_FORMATS = ['csv', 'json']
    
    # Crossover Detection
    CROSSOVER_TYPES = [
        {'fast': 20, 'slow': 50, 'type': 'SMA'},
        {'fast': 50, 'slow': 200, 'type': 'SMA'},
        {'fast': 20, 'slow': 50, 'type': 'EMA'}
    ]
    
    @classmethod
    def get_output_filename(cls, prefix: str, extension: str) -> str:
        """Generate timestamped filename"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d')
        return f"{prefix}_{timestamp}.{extension}"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)