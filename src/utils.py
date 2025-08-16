# Utility functions for the Binance Crypto Alerts system
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from functools import wraps


def setup_logging(log_level: str = 'INFO', log_file: str = None) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger('binance_crypto_alerts')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
    
    return logger


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Decorator for retrying functions on specific exceptions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


def format_large_number(number: float) -> str:
    """Format large numbers with appropriate suffixes"""
    if number >= 1e9:
        return f"{number / 1e9:.2f}B"
    elif number >= 1e6:
        return f"{number / 1e6:.2f}M"
    elif number >= 1e3:
        return f"{number / 1e3:.2f}K"
    else:
        return f"{number:.2f}"


def timestamp_to_datetime(timestamp: int) -> datetime:
    """Convert timestamp to datetime object"""
    return datetime.fromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to timestamp"""
    return int(dt.timestamp() * 1000)


def get_date_range(days_back: int) -> tuple[datetime, datetime]:
    """Get start and end dates for historical data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date


def validate_symbol(symbol: str) -> bool:
    """Validate cryptocurrency symbol format"""
    if not symbol or not isinstance(symbol, str):
        return False
    return len(symbol) >= 3 and symbol.isalpha() or symbol.endswith('USDT')


def calculate_signal_strength(fast_ma: float, slow_ma: float) -> Dict[str, Any]:
    """Calculate signal strength based on moving average difference"""
    if slow_ma == 0:
        return {'strength': 0, 'percentage_diff': 0}
    
    percentage_diff = abs((fast_ma - slow_ma) / slow_ma * 100)
    
    # Classify strength based on percentage difference
    if percentage_diff > 10:
        strength = 'STRONG'
    elif percentage_diff > 5:
        strength = 'MEDIUM'
    elif percentage_diff > 1:
        strength = 'WEAK'
    else:
        strength = 'MINIMAL'
    
    return {
        'strength': strength,
        'percentage_diff': percentage_diff,
        'direction': 'BULLISH' if fast_ma > slow_ma else 'BEARISH'
    }


def safe_division(numerator: float, denominator: float, default: float = 0) -> float:
    """Safe division with default value for zero denominator"""
    return numerator / denominator if denominator != 0 else default


def clean_symbol_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and standardize symbol data"""
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = value.strip().upper()
        elif isinstance(value, (int, float)):
            cleaned[key] = float(value) if value is not None else 0.0
        else:
            cleaned[key] = value
    return cleaned


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
    
    @property
    def elapsed_seconds(self) -> float:
        return self.elapsed if hasattr(self, 'elapsed') else 0


def create_summary_stats(data: List[Dict[str, Any]], key_field: str = 'symbol') -> Dict[str, Any]:
    """Create summary statistics from data"""
    if not data:
        return {'total': 0, 'unique_symbols': 0, 'avg_processing_time': 0}
    
    unique_symbols = len(set(item.get(key_field, '') for item in data))
    
    return {
        'total_records': len(data),
        'unique_symbols': unique_symbols,
        'timestamp': datetime.now().isoformat(),
        'processing_rate': len(data) / max(1, unique_symbols)  # records per symbol
    }