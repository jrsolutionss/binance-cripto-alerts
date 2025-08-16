# Binance Crypto Alerts - Vercel Dashboard

A modern web dashboard for cryptocurrency technical analysis, built on Vercel with serverless Python API and responsive frontend.

## 🚀 Features

### Backend API (Serverless)
- **`/api/top100`** - Get top 100 cryptocurrencies by trading volume
- **`/api/analysis?symbol=BTCUSDT`** - Technical analysis for specific symbols
- **`/api/crossovers`** - Detect golden/death cross signals across multiple symbols
- **`/api/market-summary`** - Overall market sentiment and statistics

### Frontend Dashboard
- **Real-time Data**: Top 100 cryptocurrencies with live prices and volume
- **Technical Analysis**: Moving averages (20, 50, 200 periods) with visual indicators
- **Signal Detection**: Golden cross and death cross notifications
- **Interactive Features**: Search, filter, sort, and detailed analysis modals
- **Responsive Design**: Mobile-first approach with modern UI
- **Auto-refresh**: Optional 5-minute auto-refresh for live monitoring

## 🛠️ Technology Stack

- **Backend**: Python 3.9 serverless functions on Vercel
- **Frontend**: Vanilla JavaScript with modern CSS3 and HTML5
- **API**: Binance public API for real-time cryptocurrency data
- **Caching**: Smart caching system to handle Vercel timeout limits
- **Charts**: Chart.js for data visualization

## 📦 Deployment

### Prerequisites
- Node.js 16+ (for Vercel CLI)
- Vercel account

### Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Local Development
```bash
# Install Vercel CLI and start development server
npm i -g vercel
vercel dev
```

## 🔧 API Configuration

The system uses Binance's public API endpoints and doesn't require API keys:
- `/api/v3/ticker/24hr` - 24hr ticker statistics
- `/api/v3/klines` - Historical candlestick data
- `/api/v3/ping` - Connection testing

### API Response Caching
- Market data: 5 minutes
- Technical analysis: 10 minutes  
- Market summary: 15 minutes

## 📊 Usage Examples

### Dashboard Access
Open your deployed Vercel URL to access the dashboard

### API Usage
```bash
# Get top 100 cryptocurrencies
curl https://your-app.vercel.app/api/top100

# Analyze Bitcoin
curl https://your-app.vercel.app/api/analysis?symbol=BTCUSDT

# Get recent crossovers
curl https://your-app.vercel.app/api/crossovers?count=50

# Market summary
curl https://your-app.vercel.app/api/market-summary
```

## 🎯 Dashboard Features

### Market Overview
- Real-time market sentiment indicators
- Percentage of cryptos above key moving averages
- Total crossover signals detected
- Market strength assessment (Bullish/Bearish/Neutral)

### Cryptocurrency Table
- Top 100 cryptocurrencies by volume
- Real-time prices and 24h changes
- Moving average position indicators
- Crossover signal badges
- Search and filter capabilities
- Sortable columns

### Signal Alerts
- Golden Cross (bullish) detection
- Death Cross (bearish) detection
- Signal strength calculation
- Recent crossover timeline

### Interactive Analysis
- Click "Analyze" on any cryptocurrency
- Detailed moving average data
- Historical crossover events
- Price vs. moving average relationships

## ⚡ Performance Optimizations

### Serverless Constraints
- Functions optimized for 10-second Vercel timeout
- Intelligent batch processing
- Graceful degradation on API failures
- Memory-efficient data processing

### Frontend Performance
- Lazy loading for non-critical data
- Efficient DOM updates
- Debounced search functionality
- Progressive enhancement

## 🔒 Error Handling

- Comprehensive API error responses
- Fallback to cached data when possible
- User-friendly error messages
- Graceful degradation of features

## 📱 Mobile Support

- Responsive grid layouts
- Touch-friendly interface
- Optimized for mobile networks
- Adaptive font sizes and spacing

## 🛡️ Rate Limiting

The system respects Binance API rate limits through:
- Intelligent caching strategies
- Request batching
- Exponential backoff on failures
- Connection pooling

## 🔮 Future Enhancements

- WebSocket integration for real-time updates
- Custom alert notifications
- Portfolio tracking
- Historical performance charts
- Advanced technical indicators

## 📄 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

This software is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

## 🆘 Support

- Check API status at your Vercel deployment URL
- Review browser console for JavaScript errors
- Verify Vercel function logs for backend issues
- Ensure network connectivity to Binance API

---

**Original System**: The core technical analysis algorithms are adapted from the existing Python CLI system, maintaining the same proven logic for moving average calculations and crossover detection.