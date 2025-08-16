"""
Technical Analysis API Endpoint for Vercel
GET /api/analysis?symbol=BTCUSDT - Returns technical analysis for a specific symbol
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import parse_qs, urlparse

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
            
            symbol = query_params.get('symbol', [None])[0]
            days = int(query_params.get('days', [100])[0])
            days = min(days, 365)  # Limit to prevent timeouts
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            # Initialize clients
            binance_client = BinanceClient()
            tech_analysis = TechnicalAnalysis()
            
            # Fetch historical data
            df = binance_client.get_historical_klines(symbol, '1d', days)
            
            if df.empty:
                response_data = {
                    'success': False,
                    'symbol': symbol,
                    'error': 'No historical data available for this symbol'
                }
            else:
                # Calculate technical analysis
                ma_data = tech_analysis.calculate_all_ma(df, symbol)
                crossovers = tech_analysis.detect_crossovers(df, symbol)
                
                response_data = {
                    'success': True,
                    'symbol': symbol,
                    'analysis': ma_data,
                    'crossovers': crossovers,
                    'data_period': {
                        'days_requested': days,
                        'data_points': len(df),
                        'start_date': df.index[0].isoformat() if not df.empty else None,
                        'end_date': df.index[-1].isoformat() if not df.empty else None
                    },
                    'summary': {
                        'total_crossovers': len(crossovers),
                        'golden_crosses': len([c for c in crossovers if c['type'] == 'GOLDEN_CROSS']),
                        'death_crosses': len([c for c in crossovers if c['type'] == 'DEATH_CROSS'])
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
                'message': 'Failed to analyze cryptocurrency data'
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