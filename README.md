# Binance Crypto Alerts - Technical Analysis System

A comprehensive Python system that captures data from the Binance API and calculates moving average crossovers for the top 100 cryptocurrencies by trading volume.

## Features

- **Binance API Integration**: Connects to Binance public API to fetch real-time and historical cryptocurrency data
- **Top 100 Crypto Tracking**: Automatically identifies and analyzes the top cryptocurrencies by 24h trading volume
- **Technical Analysis**: Calculates Simple Moving Averages (SMA) and Exponential Moving Averages (EMA) for configurable periods (20, 50, 200 days)
- **Signal Detection**: Detects golden cross (bullish) and death cross (bearish) crossovers between moving averages
- **Smart Alerts**: Generates classified alerts with importance levels and avoids duplicates
- **Data Export**: Exports results to CSV and JSON formats for further analysis
- **Performance Monitoring**: Tracks execution time and API call efficiency
- **Comprehensive Logging**: Detailed logging with rotation for debugging and monitoring

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/jrsolutionss/binance-cripto-alerts.git
cd binance-cripto-alerts

# Install dependencies
pip install -r requirements.txt

# Run the analysis
python main.py
```

### Basic Usage

```bash
# Run full analysis for top 100 cryptocurrencies
python main.py

# Analyze top 50 symbols with 30 days of history
python main.py --symbols 50 --days 30

# Analyze a specific cryptocurrency
python main.py --symbol BTCUSDT

# Enable debug logging
python main.py --log-level DEBUG
```

## Project Structure

```
/
├── main.py                    # Main execution script
├── src/
│   ├── __init__.py
│   ├── binance_client.py      # Binance API client with rate limiting
│   ├── technical_analysis.py  # Moving averages calculations
│   ├── signal_detector.py     # Crossover signal detection
│   ├── alert_manager.py       # Alert system with deduplication
│   └── utils.py              # Utility functions and helpers
├── config/
│   ├── __init__.py
│   └── settings.py           # System configuration
├── data/                     # Generated reports and exports
├── logs/                     # Application logs
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Configuration

The system can be configured through environment variables or by modifying `config/settings.py`:

```python
# Moving Average Periods
MA_PERIODS = [20, 50, 200]

# Data Configuration
TOP_SYMBOLS_COUNT = 100
HISTORICAL_DAYS = 365
TIMEFRAME = '1d'

# Crossover Detection Types
CROSSOVER_TYPES = [
    {'fast': 20, 'slow': 50, 'type': 'SMA'},
    {'fast': 50, 'slow': 200, 'type': 'SMA'},
    {'fast': 20, 'slow': 50, 'type': 'EMA'}
]
```

### Environment Variables

```bash
# Optional: Binance API credentials (not required for public data)
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET_KEY="your_secret_key"
```

## Output Files

The system generates several output files in the `data/` directory:

- **`moving_averages_YYYY-MM-DD.csv`**: Complete moving averages data for all symbols
- **`crossover_alerts_YYYY-MM-DD.csv`**: Detected crossover signals with details
- **`analysis_results_YYYY-MM-DD.json`**: Complete analysis results in JSON format
- **`alert_history.json`**: Persistent alert history to avoid duplicates

## Signal Types

### Golden Cross (Bullish Signal)
- Fast moving average crosses above slow moving average
- Indicates potential upward price movement
- Classified by strength based on percentage difference

### Death Cross (Bearish Signal)
- Fast moving average crosses below slow moving average
- Indicates potential downward price movement
- Classified by strength and historical significance

### Alert Classification

Alerts are automatically classified into importance levels:

- **HIGH**: Strong signals with significant MA separation (>5%) on longer timeframes
- **MEDIUM**: Moderate signals with decent separation (2-5%)
- **LOW**: Weak signals with minimal separation (<2%)

## Example Output

```
📊 CRYPTO ALERTS DASHBOARD
============================================================
🔍 Total Alerts: 15
📈 Golden Crosses: 8
📉 Death Crosses: 7
💼 Unique Symbols: 12
🚨 High Priority: 3
⚠️  Medium Priority: 7
ℹ️  Low Priority: 5
============================================================

🚨 HIGH PRIORITY ALERTS:
----------------------------------------
• BTCUSDT: GOLDEN_CROSS (SMA_50_200)
  Price: $43,250.5000, Strength: STRONG
• ETHUSDT: DEATH_CROSS (EMA_20_50)
  Price: $2,890.7500, Strength: MEDIUM
```

## Performance Features

- **Rate Limiting**: Respects Binance API limits with configurable delays
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **Batch Processing**: Efficiently processes multiple symbols with progress tracking
- **Memory Optimization**: Processes data in chunks to handle large datasets
- **Caching**: Avoids redundant API calls and duplicate alert generation

## Dependencies

- `requests`: HTTP client for API calls
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computations
- `python-binance`: Official Binance API client
- `python-dotenv`: Environment variable management

## API Usage

The system uses Binance's public API endpoints and doesn't require API keys for basic functionality:

- `/api/v3/ticker/24hr` - 24hr ticker statistics
- `/api/v3/klines` - Historical candlestick data
- `/api/v3/exchangeInfo` - Symbol information

## Error Handling

- Comprehensive exception handling for API failures
- Graceful degradation when symbols have insufficient data
- Detailed logging of errors with context
- Automatic cleanup of corrupted data

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. It is not financial advice. Always do your own research before making any investment decisions.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the logs in the `logs/` directory for debugging information
- Ensure you have the latest version of dependencies