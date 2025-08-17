"""
Diagnostic API endpoint for Vercel - Tests Binance API connection
GET /api/test-binance - Comprehensive tests for debugging production issues
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
            
            # Test results container
            test_results = {
                'timestamp': datetime.now().isoformat(),
                'environment': 'vercel_production',
                'tests': {},
                'debug_info': {}
            }
            
            # Test 1: Direct ping to Binance API
            print("Testing Binance API ping...")
            try:
                response = requests.get('https://api.binance.com/api/v3/ping', timeout=8)
                test_results['tests']['ping'] = {
                    'status': 'success' if response.status_code == 200 else 'failed',
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'response': response.json() if response.status_code == 200 else None
                }
                print(f"Ping result: {response.status_code}")
            except Exception as e:
                test_results['tests']['ping'] = {
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"Ping error: {str(e)}")
            
            # Test 2: Server time test
            print("Testing Binance server time...")
            try:
                response = requests.get('https://api.binance.com/api/v3/time', timeout=8)
                if response.status_code == 200:
                    server_data = response.json()
                    test_results['tests']['server_time'] = {
                        'status': 'success',
                        'server_timestamp': server_data['serverTime'],
                        'response_time': response.elapsed.total_seconds()
                    }
                    print(f"Server time: {server_data['serverTime']}")
                else:
                    test_results['tests']['server_time'] = {
                        'status': 'failed',
                        'status_code': response.status_code
                    }
            except Exception as e:
                test_results['tests']['server_time'] = {
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"Server time error: {str(e)}")
            
            # Test 3: Single ticker test (BTCUSDT)
            print("Testing single ticker...")
            try:
                response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=8)
                if response.status_code == 200:
                    ticker_data = response.json()
                    test_results['tests']['single_ticker'] = {
                        'status': 'success',
                        'symbol': ticker_data['symbol'],
                        'price': float(ticker_data['lastPrice']),
                        'change_percent': float(ticker_data['priceChangePercent']),
                        'volume': float(ticker_data['volume']),
                        'quote_volume': float(ticker_data['quoteVolume']),
                        'response_time': response.elapsed.total_seconds()
                    }
                    print(f"BTCUSDT price: {ticker_data['lastPrice']}")
                else:
                    test_results['tests']['single_ticker'] = {
                        'status': 'failed',
                        'status_code': response.status_code
                    }
            except Exception as e:
                test_results['tests']['single_ticker'] = {
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"Single ticker error: {str(e)}")
            
            # Test 4: Client connection test
            print("Testing BinanceClient connection...")
            try:
                connection_test = client.test_connection()
                test_results['tests']['client_connection'] = {
                    'status': 'success' if connection_test else 'failed',
                    'result': connection_test
                }
                print(f"Client connection: {connection_test}")
            except Exception as e:
                test_results['tests']['client_connection'] = {
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"Client connection error: {str(e)}")
            
            # Test 5: Full ticker stats test (what top100 uses)
            print("Testing full ticker stats...")
            try:
                tickers = client.get_24hr_ticker_stats()
                if tickers and len(tickers) > 0:
                    usdt_tickers = [t for t in tickers if t['symbol'].endswith('USDT')]
                    test_results['tests']['full_ticker_stats'] = {
                        'status': 'success',
                        'total_symbols': len(tickers),
                        'usdt_symbols': len(usdt_tickers),
                        'sample_ticker': tickers[0] if tickers else None
                    }
                    print(f"Full ticker stats: {len(tickers)} total, {len(usdt_tickers)} USDT")
                else:
                    test_results['tests']['full_ticker_stats'] = {
                        'status': 'failed',
                        'error': 'No data returned'
                    }
            except Exception as e:
                test_results['tests']['full_ticker_stats'] = {
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"Full ticker stats error: {str(e)}")
            
            # Test 6: Top symbols method (the actual failing method)
            print("Testing get_top_symbols_by_volume...")
            try:
                top_symbols = client.get_top_symbols_by_volume(5)  # Small count for test
                if top_symbols and len(top_symbols) > 0:
                    # Check if it's mock data (mock BTC price is 50000)
                    is_mock_data = top_symbols[0]['price'] == 50000.0
                    test_results['tests']['top_symbols'] = {
                        'status': 'success',
                        'count': len(top_symbols),
                        'is_mock_data': is_mock_data,
                        'sample_data': top_symbols[0],
                        'all_symbols': [s['symbol'] for s in top_symbols]
                    }
                    print(f"Top symbols: {len(top_symbols)} returned, mock: {is_mock_data}")
                else:
                    test_results['tests']['top_symbols'] = {
                        'status': 'failed',
                        'error': 'No symbols returned'
                    }
            except Exception as e:
                test_results['tests']['top_symbols'] = {
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"Top symbols error: {str(e)}")
            
            # Add environment debug info
            test_results['debug_info'] = {
                'python_path': sys.path,
                'working_directory': os.getcwd(),
                'environment_vars': {
                    'PATH': os.environ.get('PATH', 'Not set'),
                    'PYTHONPATH': os.environ.get('PYTHONPATH', 'Not set')
                }
            }
            
            # Determine overall status
            success_count = sum(1 for test in test_results['tests'].values() if test.get('status') == 'success')
            total_tests = len(test_results['tests'])
            
            response_data = {
                'success': True,
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': success_count,
                    'failed_tests': total_tests - success_count,
                    'overall_status': 'PASS' if success_count == total_tests else 'PARTIAL' if success_count > 0 else 'FAIL'
                },
                'test_results': test_results
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
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat()
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
