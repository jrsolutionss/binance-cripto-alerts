#!/usr/bin/env python3
"""
Binance Crypto Alerts - Technical Analysis System
Main execution script for cryptocurrency moving average analysis
"""

import os
import sys
import argparse
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Settings
from src.binance_client import BinanceClient
from src.technical_analysis import TechnicalAnalysis
from src.signal_detector import SignalDetector
from src.alert_manager import AlertManager
from src.utils import setup_logging, PerformanceTimer, create_summary_stats


class CryptoAnalysisApp:
    """Main application class for cryptocurrency analysis"""
    
    def __init__(self, log_level='INFO', demo_mode=False):
        # Ensure directories exist
        Settings.ensure_directories()
        
        # Setup logging
        log_file = os.path.join(Settings.LOGS_DIR, f"crypto_analysis_{datetime.now().strftime('%Y%m%d')}.log")
        self.logger = setup_logging(log_level, log_file)
        
        self.demo_mode = demo_mode
        
        # Initialize components
        if demo_mode:
            from src.mock_data import MockDataGenerator
            self.mock_generator = MockDataGenerator()
            self.binance_client = None  # Don't initialize for demo
            self.logger.info("Running in DEMO mode with mock data")
        else:
            self.binance_client = BinanceClient()
            self.mock_generator = None
            
        self.technical_analysis = TechnicalAnalysis()
        self.signal_detector = SignalDetector()
        self.alert_manager = AlertManager()
        
        self.logger.info("Crypto Analysis Application initialized")
    
    def run_analysis(self, symbol_count: int = None, days_back: int = None) -> dict:
        """Run the complete analysis pipeline"""
        symbol_count = symbol_count or Settings.TOP_SYMBOLS_COUNT
        days_back = days_back or Settings.HISTORICAL_DAYS
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'symbol_count': symbol_count,
                'days_back': days_back,
                'ma_periods': Settings.MA_PERIODS,
                'crossover_types': Settings.CROSSOVER_TYPES
            },
            'success': False
        }
        
        try:
            with PerformanceTimer("Complete Analysis Pipeline") as total_timer:
                
                if self.demo_mode:
                    return self._run_demo_analysis(symbol_count, days_back, results, total_timer)
                
                # Step 1: Test API connection
                self.logger.info("Step 1: Testing Binance API connection...")
                if not self.binance_client.test_connection():
                    raise Exception("Failed to connect to Binance API")
                
                # Step 2: Get top symbols
                self.logger.info(f"Step 2: Fetching top {symbol_count} symbols by volume...")
                top_symbols = self.binance_client.get_top_symbols_by_volume(symbol_count)
                
                if not top_symbols:
                    raise Exception("Failed to fetch top symbols")
                
                results['symbols_found'] = len(top_symbols)
                self.logger.info(f"Found {len(top_symbols)} symbols")
                
                # Step 3: Get historical data
                self.logger.info(f"Step 3: Fetching {days_back} days of historical data...")
                symbol_data = self.binance_client.get_multiple_symbols_data(top_symbols, days_back)
                
                if not symbol_data:
                    raise Exception("Failed to fetch historical data")
                
                results['symbols_with_data'] = len(symbol_data)
                self.logger.info(f"Retrieved data for {len(symbol_data)} symbols")
                
                return self._process_analysis_data(symbol_data, results, total_timer)
        
        except Exception as e:
            import traceback
            self.logger.error(f"Analysis failed: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            results['error'] = str(e)
            print(f"❌ Analysis failed: {e}")
            print(f"🔍 Full traceback: {traceback.format_exc()}")
        
        return results
    
    def _run_demo_analysis(self, symbol_count: int, days_back: int, results: dict, total_timer) -> dict:
        """Run analysis with demo/mock data"""
        self.logger.info("🎭 Running DEMO analysis with mock data...")
        print("🎭 DEMO MODE - Using mock cryptocurrency data")
        
        # Get mock symbols and data
        top_symbols = self.mock_generator.get_mock_top_symbols(symbol_count)
        symbol_data = self.mock_generator.generate_mock_symbol_data(top_symbols, days_back)
        
        results['symbols_found'] = len(top_symbols)
        results['symbols_with_data'] = len(symbol_data)
        
        self.logger.info(f"Generated mock data for {len(symbol_data)} symbols")
        return self._process_analysis_data(symbol_data, results, total_timer)
    
    def _process_analysis_data(self, symbol_data: dict, results: dict, total_timer) -> dict:
        """Process analysis data (common logic for real and demo modes)"""
        # Step 4: Calculate moving averages
        self.logger.info("Step 4: Calculating moving averages...")
        ma_data = self.technical_analysis.calculate_moving_average_data(symbol_data)
        results['symbols_analyzed'] = len(ma_data)
        
        # Step 5: Detect crossovers
        self.logger.info("Step 5: Detecting crossover signals...")
        crossovers = self.signal_detector.detect_all_crossovers(ma_data)
        results['crossovers_found'] = len(crossovers)
        
        # Step 6: Rank and filter signals
        self.logger.info("Step 6: Processing signals...")
        ranked_crossovers = self.signal_detector.rank_signals_by_importance(crossovers)
        signal_stats = self.signal_detector.get_signal_statistics(crossovers)
        results['signal_statistics'] = signal_stats
        
        # Step 7: Generate alerts
        self.logger.info("Step 7: Generating alerts...")
        alerts = self.alert_manager.process_crossovers_to_alerts(
            ranked_crossovers, 
            self.signal_detector.classify_signal_importance
        )
        
        # Add alerts to history
        if alerts:
            self.alert_manager.add_alerts_to_history(alerts)
        
        results['alerts_generated'] = len(alerts)
        results['alert_summary'] = self.alert_manager.get_alert_summary(alerts)
        
        # Step 8: Export data
        self.logger.info("Step 8: Exporting data...")
        self._export_results(ma_data, crossovers, alerts)
        
        # Step 9: Display dashboard
        self.logger.info("Step 9: Displaying results...")
        self.alert_manager.print_alert_dashboard(alerts)
        self._print_performance_summary(total_timer, results)
        
        results['success'] = True
        results['execution_time_seconds'] = total_timer.elapsed_seconds
        
        self.logger.info(f"Analysis completed successfully in {total_timer.elapsed_seconds:.2f}s")
        return results
    
    def _export_results(self, ma_data: dict, crossovers: list, alerts: list):
        """Export analysis results to files"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            
            # Export moving averages
            ma_filename = os.path.join(Settings.DATA_DIR, f'moving_averages_{timestamp}.csv')
            self.technical_analysis.export_ma_data(ma_data, ma_filename)
            
            # Export crossover alerts
            alerts_csv = os.path.join(Settings.DATA_DIR, f'crossover_alerts_{timestamp}.csv')
            self.alert_manager.export_alerts_csv(alerts, alerts_csv)
            
            # Export JSON summary
            alerts_json = os.path.join(Settings.DATA_DIR, f'analysis_results_{timestamp}.json')
            summary_data = {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_symbols_analyzed': len(ma_data),
                'crossovers_detected': crossovers,
                'alerts_generated': alerts,
                'signal_statistics': self.signal_detector.get_signal_statistics(crossovers),
                'alert_summary': self.alert_manager.get_alert_summary(alerts),
                'configuration': {
                    'ma_periods': Settings.MA_PERIODS,
                    'crossover_types': Settings.CROSSOVER_TYPES,
                    'top_symbols_count': Settings.TOP_SYMBOLS_COUNT
                }
            }
            
            with open(alerts_json, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, default=str)
            
            self.logger.info("Results exported successfully")
            print(f"📁 Results exported to {Settings.DATA_DIR}/")
        
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
    
    def _print_performance_summary(self, timer, results: dict):
        """Print performance summary"""
        print("\n" + "="*60)
        print("⚡ PERFORMANCE SUMMARY")
        print("="*60)
        print(f"⏱️  Total Execution Time: {timer.elapsed_seconds:.2f} seconds")
        print(f"📊 Symbols Processed: {results.get('symbols_analyzed', 0)}")
        print(f"🔍 Crossovers Found: {results.get('crossovers_found', 0)}")
        print(f"🚨 Alerts Generated: {results.get('alerts_generated', 0)}")
        
        if results.get('symbols_analyzed', 0) > 0 and timer.elapsed_seconds > 0:
            rate = results.get('symbols_analyzed', 0) / timer.elapsed_seconds
            print(f"📈 Processing Rate: {rate:.2f} symbols/second")
        
        print("="*60)
    
    def run_historical_backtest(self, days_back: int = 30):
        """Run a historical backtest of the strategy"""
        self.logger.info(f"Running historical backtest for {days_back} days")
        # This could be extended to run analysis on historical periods
        # and evaluate the performance of the signals
        pass
    
    def get_single_symbol_analysis(self, symbol: str) -> dict:
        """Get detailed analysis for a single symbol"""
        self.logger.info(f"Analyzing single symbol: {symbol}")
        
        try:
            # Get historical data
            df = self.binance_client.get_historical_klines(symbol)
            if df.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Calculate moving averages
            ma_df = self.technical_analysis.calculate_all_moving_averages(df)
            
            # Detect crossovers
            crossovers = self.signal_detector.analyze_symbol_crossovers(symbol, ma_df)
            
            # Generate technical summary
            technical_summary = self.technical_analysis.generate_technical_summary(symbol, ma_df)
            
            return {
                'symbol': symbol,
                'technical_summary': technical_summary,
                'crossovers': crossovers,
                'data_points': len(ma_df),
                'latest_price': float(ma_df['close'].iloc[-1]) if not ma_df.empty else None
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return {'error': str(e)}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Binance Crypto Alerts - Technical Analysis System')
    parser.add_argument('--symbols', type=int, default=Settings.TOP_SYMBOLS_COUNT,
                      help=f'Number of top symbols to analyze (default: {Settings.TOP_SYMBOLS_COUNT})')
    parser.add_argument('--days', type=int, default=Settings.HISTORICAL_DAYS,
                      help=f'Days of historical data (default: {Settings.HISTORICAL_DAYS})')
    parser.add_argument('--symbol', type=str, help='Analyze single symbol (e.g., BTCUSDT)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                      default='INFO', help='Set logging level')
    parser.add_argument('--export-only', action='store_true', 
                      help='Export existing data without running new analysis')
    parser.add_argument('--demo', action='store_true',
                      help='Run in demo mode with mock data (no API required)')
    
    args = parser.parse_args()
    
    print("🚀 Binance Crypto Alerts - Technical Analysis System")
    print("=" * 60)
    
    try:
        app = CryptoAnalysisApp(args.log_level, demo_mode=args.demo)
        
        if args.symbol:
            # Single symbol analysis
            if args.demo:
                print("📊 Demo mode: Single symbol analysis not supported with mock data")
                print("Run full analysis instead: python main.py --demo")
                return
            print(f"🔍 Analyzing single symbol: {args.symbol}")
            result = app.get_single_symbol_analysis(args.symbol)
            print(json.dumps(result, indent=2, default=str))
        
        elif args.export_only:
            # Export existing data only
            print("📁 Export mode - processing existing data...")
            # This would load existing data and export it
            print("Export functionality would be implemented here")
        
        else:
            # Full analysis
            mode_text = "DEMO analysis" if args.demo else f"full analysis for {args.symbols} symbols"
            print(f"📊 Running {mode_text}...")
            results = app.run_analysis(args.symbols, args.days)
            
            # Debug print results
            print(f"🔍 DEBUG: Results type: {type(results)}")
            if results:
                print(f"🔍 DEBUG: Results keys: {results.keys()}")
                print(f"🔍 DEBUG: Success status: {results.get('success', 'NOT SET')}")
            
            if results and results.get('success'):
                print("✅ Analysis completed successfully!")
            else:
                print("❌ Analysis failed!")
                if results and 'error' in results:
                    print(f"Error: {results['error']}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"💥 Unexpected error: {e}")
        print("🔍 Full traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()