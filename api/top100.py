"""
Top 100 Cryptocurrencies API Endpoint for Vercel
GET /api/top100 - Returns top 100 cryptocurrencies by trading volume
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from binance_client import BinanceClient

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Initialize client
            client = BinanceClient()
            
            # Parse query parameters
            query_params = {}
            if self.path.find('?') != -1:
                query_string = self.path.split('?')[1]
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            # Get parameters
            count = int(query_params.get('count', 100))
            count = min(count, 200)  # Limit to prevent timeouts
            
            # Fetch top symbols
            top_symbols = client.get_top_symbols_by_volume(count)
            
            response_data = {
                'success': True,
                'timestamp': client._get_cache_key('timestamp', {'now': 'true'}),
                'count': len(top_symbols),
                'data': top_symbols,
                'cache_info': {
                    'cached': any(key.startswith('ticker/24hr') for key in client._cache.keys()),
                    'cache_duration_seconds': client.cache_duration
                }
            }
            
            # Set response headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Cache-Control', 'public, max-age=300')  # 5 minutes cache
            self.end_headers()
            
            # Send response
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            # Error response
            error_response = {
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch cryptocurrency data'
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