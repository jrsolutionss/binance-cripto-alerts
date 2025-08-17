"""
Test API endpoint for debugging Binance connection
GET /api/test-binance - Tests connection to Binance API
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import requests
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from binance_client import BinanceClient

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Initialize client
            client = BinanceClient()
            
            # Test basic connectivity
            test_results = {
                'timestamp': datetime.now().isoformat(),
                'tests': {}
            }
            
            # Test 1: Direct ping to Binance
            try:
                response = requests.get('https://api.binance.com/api/v3/ping', timeout=10)
                test_results['tests']['ping'] = {
                    'status': 'success' if response.status_code == 200 else 'failed',
                    'status_code': response.status_code,
                    'response': response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                test_results['tests']['ping'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Test 2: Server time
            try:
                response = requests.get('https://api.binance.com/api/v3/time', timeout=10)
                test_results['tests']['server_time'] = {
                    'status': 'success' if response.status_code == 200 else 'failed',
                    'status_code': response.status_code,
                    'response': response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                test_results['tests']['server_time'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Test 3: Exchange info (small request)
            try:
                response = requests.get('https://api.binance.com/api/v3/exchangeInfo', timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    symbols_count = len(data.get('symbols', []))
                    test_results['tests']['exchange_info'] = {
                        'status': 'success',
                        'symbols_count': symbols_count,
                        'rate_limits': data.get('rateLimits', [])
                    }
                else:
                    test_results['tests']['exchange_info'] = {
                        'status': 'failed',
                        'status_code': response.status_code
                    }
            except Exception as e:
                test_results['tests']['exchange_info'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Test 4: Small ticker test (just one symbol)
            try:
                response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=10)
                test_results['tests']['single_ticker'] = {
                    'status': 'success' if response.status_code == 200 else 'failed',
                    'status_code': response.status_code,
                    'response': response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                test_results['tests']['single_ticker'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Test 5: Client connection test
            try:
                connection_test = client.test_connection()
                test_results['tests']['client_connection'] = {
                    'status': 'success' if connection_test else 'failed'
                }
            except Exception as e:
                test_results['tests']['client_connection'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Response
            response_data = {
                'success': True,
                'debug_info': test_results
            }
            
            # Set response headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Send response
            self.wfile.write(json.dumps(response_data, indent=2).encode('utf-8'))
            
        except Exception as e:
            # Error response
            error_response = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
