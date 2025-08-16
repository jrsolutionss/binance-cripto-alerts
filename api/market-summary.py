"""
Market Summary API Endpoint for Vercel
GET /api/market-summary - Returns overall market analysis summary
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import parse_qs, urlparse
import time

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from binance_client import BinanceClient
from technical import TechnicalAnalysis

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            count = int(query_params.get('count', [25])[0])  # Smaller sample for summary
            count = min(count, 50)  # Max 50 symbols for summary
            days = int(query_params.get('days', [60])[0])
            days = min(days, 100)
            
            # Initialize clients
            binance_client = BinanceClient()
            tech_analysis = TechnicalAnalysis()
            
            start_time = time.time()
            
            # Get top symbols
            top_symbols_data = binance_client.get_top_symbols_by_volume(count)
            
            # Analyze symbols
            symbols_analysis = []
            processed_count = 0
            
            for symbol_data in top_symbols_data:
                symbol = symbol_data['symbol']
                
                # Timeout protection
                if time.time() - start_time > 8:
                    break
                
                try:
                    # Get historical data
                    df = binance_client.get_historical_klines(symbol, '1d', days)
                    
                    if not df.empty:
                        # Calculate analysis
                        ma_analysis = tech_analysis.calculate_all_ma(df, symbol)
                        crossovers = tech_analysis.detect_crossovers(df, symbol)
                        
                        symbol_analysis = {
                            'symbol': symbol,
                            'rank': symbol_data['rank'],
                            'price': symbol_data['price'],
                            'change_24h': symbol_data['change_24h'],
                            'volume_24h': symbol_data['quote_volume_24h'],
                            'moving_averages': ma_analysis.get('moving_averages', {}),
                            'crossovers': crossovers
                        }
                        symbols_analysis.append(symbol_analysis)
                        processed_count += 1
                
                except Exception:
                    continue
            
            # Generate market summary
            market_summary = tech_analysis.get_market_summary(symbols_analysis)
            
            # Additional statistics
            total_volume_24h = sum(s['volume_24h'] for s in top_symbols_data[:processed_count])
            avg_change_24h = sum(s['change_24h'] for s in top_symbols_data[:processed_count]) / max(processed_count, 1)
            
            # Top gainers and losers
            sorted_by_change = sorted(top_symbols_data[:processed_count], key=lambda x: x['change_24h'])
            top_gainers = sorted_by_change[-5:][::-1]  # Top 5 gainers
            top_losers = sorted_by_change[:5]  # Top 5 losers
            
            response_data = {
                'success': True,
                'timestamp': market_summary.get('timestamp'),
                'processing_info': {
                    'symbols_analyzed': processed_count,
                    'processing_time_seconds': round(time.time() - start_time, 2),
                    'data_period_days': days
                },
                'market_overview': {
                    'total_market_cap_analyzed': len(symbols_analysis),
                    'total_volume_24h': total_volume_24h,
                    'average_change_24h': round(avg_change_24h, 2),
                    'market_sentiment': market_summary.get('market_sentiment', {}),
                    'market_strength': market_summary.get('market_strength', 'neutral')
                },
                'crossover_analysis': market_summary.get('crossover_summary', {}),
                'top_movers': {
                    'gainers': [
                        {
                            'rank': g['rank'],
                            'symbol': g['symbol'],
                            'change_24h': g['change_24h'],
                            'price': g['price'],
                            'volume_24h': g['quote_volume_24h']
                        } for g in top_gainers
                    ],
                    'losers': [
                        {
                            'rank': l['rank'],
                            'symbol': l['symbol'],
                            'change_24h': l['change_24h'],
                            'price': l['price'],
                            'volume_24h': l['quote_volume_24h']
                        } for l in top_losers
                    ]
                },
                'technical_summary': {
                    'symbols_above_ma20': sum(1 for s in symbols_analysis 
                                            if s.get('moving_averages', {}).get('ma_20', {}).get('price_vs_sma') == 'above'),
                    'symbols_above_ma50': sum(1 for s in symbols_analysis 
                                            if s.get('moving_averages', {}).get('ma_50', {}).get('price_vs_sma') == 'above'),
                    'symbols_above_ma200': sum(1 for s in symbols_analysis 
                                             if s.get('moving_averages', {}).get('ma_200', {}).get('price_vs_sma') == 'above'),
                    'total_symbols': len(symbols_analysis)
                }
            }
            
            # Set response headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Cache-Control', 'public, max-age=900')  # 15 minutes cache
            self.end_headers()
            
            # Send response
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except ValueError as e:
            # Client error
            error_response = {
                'success': False,
                'error': str(e),
                'message': 'Invalid request parameters'
            }
            
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(error_response, indent=2).encode())
            
        except Exception as e:
            # Server error
            error_response = {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate market summary'
            }
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()