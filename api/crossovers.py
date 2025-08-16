"""
Crossovers Detection API Endpoint for Vercel
GET /api/crossovers - Returns all detected crossovers for top cryptocurrencies
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
            
            count = int(query_params.get('count', [50])[0])  # Limit to prevent timeout
            count = min(count, 100)  # Max 100 symbols
            days = int(query_params.get('days', [60])[0])
            days = min(days, 100)  # Limit historical data
            
            # Initialize clients
            binance_client = BinanceClient()
            tech_analysis = TechnicalAnalysis()
            
            # Get top symbols
            top_symbols_data = binance_client.get_top_symbols_by_volume(count)
            symbols = [s['symbol'] for s in top_symbols_data]
            
            all_crossovers = []
            processed_symbols = 0
            start_time = time.time()
            
            # Process symbols (with timeout protection)
            for symbol_data in top_symbols_data:
                symbol = symbol_data['symbol']
                
                # Check timeout (Vercel has 10-second limit)
                if time.time() - start_time > 8:  # Leave 2 seconds buffer
                    break
                
                try:
                    # Get historical data
                    df = binance_client.get_historical_klines(symbol, '1d', days)
                    
                    if not df.empty:
                        # Detect crossovers
                        crossovers = tech_analysis.detect_crossovers(df, symbol)
                        
                        # Add additional symbol info to crossovers
                        for crossover in crossovers:
                            crossover.update({
                                'rank': symbol_data['rank'],
                                'current_price': symbol_data['price'],
                                'change_24h': symbol_data['change_24h'],
                                'volume_24h': symbol_data['quote_volume_24h']
                            })
                        
                        all_crossovers.extend(crossovers)
                    
                    processed_symbols += 1
                    
                except Exception as e:
                    # Continue with other symbols if one fails
                    continue
            
            # Sort crossovers by timestamp (most recent first)
            all_crossovers.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Separate by type
            golden_crosses = [c for c in all_crossovers if c['type'] == 'GOLDEN_CROSS']
            death_crosses = [c for c in all_crossovers if c['type'] == 'DEATH_CROSS']
            
            response_data = {
                'success': True,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'processing_info': {
                    'symbols_requested': count,
                    'symbols_processed': processed_symbols,
                    'processing_time_seconds': round(time.time() - start_time, 2),
                    'days_analyzed': days
                },
                'summary': {
                    'total_crossovers': len(all_crossovers),
                    'golden_crosses': len(golden_crosses),
                    'death_crosses': len(death_crosses)
                },
                'crossovers': {
                    'all': all_crossovers[:100],  # Limit response size
                    'golden_crosses': golden_crosses[:50],
                    'death_crosses': death_crosses[:50]
                }
            }
            
            # Set response headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Cache-Control', 'public, max-age=600')  # 10 minutes cache
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
                'message': 'Failed to detect crossovers'
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