# Alert Management System for Cryptocurrency Trading Signals
import json
import os
import csv
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import hashlib

from config.settings import Settings
from src.utils import setup_logging, PerformanceTimer


class AlertManager:
    """Manage cryptocurrency trading alerts and notifications"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.alert_history: List[Dict[str, Any]] = []
        self.sent_alerts: Set[str] = set()  # Track sent alerts to avoid duplicates
        self.alert_file = os.path.join(Settings.DATA_DIR, 'alert_history.json')
        self.load_alert_history()
    
    def generate_alert_id(self, alert_data: Dict[str, Any]) -> str:
        """Generate unique ID for an alert to prevent duplicates"""
        # Create hash based on symbol, crossover type, and timestamp (to hour precision)
        key_data = {
            'symbol': alert_data.get('symbol', ''),
            'crossover_name': alert_data.get('crossover_name', ''),
            'type': alert_data.get('type', ''),
            'timestamp_hour': alert_data.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H')
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def create_alert(self, crossover_data: Dict[str, Any], importance: str = 'MEDIUM') -> Dict[str, Any]:
        """Create an alert from crossover data"""
        alert = {
            'id': self.generate_alert_id(crossover_data),
            'timestamp': datetime.now().isoformat(),
            'symbol': crossover_data.get('symbol', 'UNKNOWN'),
            'alert_type': 'CROSSOVER',
            'signal_type': crossover_data.get('type', 'UNKNOWN'),
            'importance': importance,
            'crossover_name': crossover_data.get('crossover_name', ''),
            'ma_type': crossover_data.get('ma_type', ''),
            'fast_period': crossover_data.get('fast_period', 0),
            'slow_period': crossover_data.get('slow_period', 0),
            'current_price': crossover_data.get('current_price', 0),
            'fast_ma_value': crossover_data.get('fast_ma_value', 0),
            'slow_ma_value': crossover_data.get('slow_ma_value', 0),
            'percentage_diff': crossover_data.get('percentage_diff', 0),
            'strength': crossover_data.get('strength', 'UNKNOWN'),
            'direction': crossover_data.get('direction', 'NEUTRAL'),
            'crossover_timestamp': crossover_data.get('timestamp', datetime.now()).isoformat() if hasattr(crossover_data.get('timestamp', datetime.now()), 'isoformat') else str(crossover_data.get('timestamp', datetime.now()))
        }
        
        return alert
    
    def process_crossovers_to_alerts(self, crossovers: List[Dict[str, Any]], 
                                   importance_classifier_func=None) -> List[Dict[str, Any]]:
        """Convert crossover signals to alerts"""
        alerts = []
        new_alerts_count = 0
        
        self.logger.info(f"Processing {len(crossovers)} crossovers into alerts")
        
        for crossover in crossovers:
            # Determine importance
            if importance_classifier_func:
                importance = importance_classifier_func(crossover)
            else:
                importance = self._classify_default_importance(crossover)
            
            alert = self.create_alert(crossover, importance)
            alert_id = alert['id']
            
            # Check for duplicates
            if alert_id not in self.sent_alerts:
                alerts.append(alert)
                self.sent_alerts.add(alert_id)
                new_alerts_count += 1
                self.logger.debug(f"New alert created: {alert['symbol']} - {alert['signal_type']}")
            else:
                self.logger.debug(f"Duplicate alert skipped: {alert['symbol']} - {alert['signal_type']}")
        
        self.logger.info(f"Created {new_alerts_count} new alerts, skipped {len(crossovers) - new_alerts_count} duplicates")
        return alerts
    
    def _classify_default_importance(self, crossover: Dict[str, Any]) -> str:
        """Default importance classification logic"""
        strength = crossover.get('strength', 'MINIMAL')
        slow_period = crossover.get('slow_period', 20)
        percentage_diff = crossover.get('percentage_diff', 0)
        
        score = 0
        
        # Score based on strength
        if strength == 'STRONG':
            score += 3
        elif strength == 'MEDIUM':
            score += 2
        elif strength == 'WEAK':
            score += 1
        
        # Score based on MA periods
        if slow_period >= 200:
            score += 3
        elif slow_period >= 50:
            score += 2
        else:
            score += 1
        
        # Score based on percentage difference
        if percentage_diff > 5:
            score += 2
        elif percentage_diff > 2:
            score += 1
        
        # Classify
        if score >= 6:
            return 'HIGH'
        elif score >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def filter_alerts_by_importance(self, alerts: List[Dict[str, Any]], 
                                   min_importance: str = 'LOW') -> List[Dict[str, Any]]:
        """Filter alerts by minimum importance level"""
        importance_levels = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        min_level = importance_levels.get(min_importance, 1)
        
        filtered = [
            alert for alert in alerts 
            if importance_levels.get(alert.get('importance', 'LOW'), 1) >= min_level
        ]
        
        self.logger.info(f"Filtered {len(filtered)}/{len(alerts)} alerts with importance >= {min_importance}")
        return filtered
    
    def add_alerts_to_history(self, alerts: List[Dict[str, Any]]):
        """Add alerts to the persistent history"""
        self.alert_history.extend(alerts)
        self.save_alert_history()
        self.logger.info(f"Added {len(alerts)} alerts to history. Total: {len(self.alert_history)}")
    
    def get_recent_alerts(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        recent_alerts = []
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if alert_time >= cutoff_time:
                recent_alerts.append(alert)
        
        return recent_alerts
    
    def get_alert_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for alerts"""
        if not alerts:
            return {
                'total_alerts': 0,
                'high_importance': 0,
                'medium_importance': 0,
                'low_importance': 0,
                'golden_crosses': 0,
                'death_crosses': 0,
                'unique_symbols': 0
            }
        
        summary = {
            'total_alerts': len(alerts),
            'high_importance': 0,
            'medium_importance': 0,
            'low_importance': 0,
            'golden_crosses': 0,
            'death_crosses': 0,
            'unique_symbols': len(set(alert['symbol'] for alert in alerts)),
            'timestamp': datetime.now().isoformat(),
            'symbols': list(set(alert['symbol'] for alert in alerts))
        }
        
        for alert in alerts:
            # Count by importance
            importance = alert.get('importance', 'LOW')
            if importance == 'HIGH':
                summary['high_importance'] += 1
            elif importance == 'MEDIUM':
                summary['medium_importance'] += 1
            else:
                summary['low_importance'] += 1
            
            # Count by signal type
            signal_type = alert.get('signal_type', '')
            if signal_type == 'GOLDEN_CROSS':
                summary['golden_crosses'] += 1
            elif signal_type == 'DEATH_CROSS':
                summary['death_crosses'] += 1
        
        return summary
    
    def format_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format alert into readable message"""
        signal_emoji = "🔴" if alert['signal_type'] == 'DEATH_CROSS' else "🟢"
        importance_emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "ℹ️"}.get(alert['importance'], "ℹ️")
        
        message = f"{importance_emoji} {signal_emoji} {alert['symbol']}\n"
        message += f"Signal: {alert['signal_type']} ({alert['crossover_name']})\n"
        message += f"Price: ${alert['current_price']:.4f}\n"
        message += f"Strength: {alert['strength']} ({alert['percentage_diff']:.2f}%)\n"
        message += f"Time: {alert['crossover_timestamp']}\n"
        
        return message
    
    def export_alerts_csv(self, alerts: List[Dict[str, Any]], filename: str) -> bool:
        """Export alerts to CSV file"""
        try:
            if not alerts:
                self.logger.warning("No alerts to export")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'symbol', 'signal_type', 'importance', 'crossover_name',
                    'ma_type', 'fast_period', 'slow_period', 'current_price',
                    'fast_ma_value', 'slow_ma_value', 'percentage_diff', 'strength',
                    'direction', 'crossover_timestamp'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for alert in alerts:
                    writer.writerow({field: alert.get(field, '') for field in fieldnames})
            
            self.logger.info(f"Exported {len(alerts)} alerts to {filename}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting alerts to CSV: {e}")
            return False
    
    def export_alerts_json(self, alerts: List[Dict[str, Any]], filename: str) -> bool:
        """Export alerts to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump({
                    'alerts': alerts,
                    'summary': self.get_alert_summary(alerts),
                    'export_timestamp': datetime.now().isoformat(),
                    'total_count': len(alerts)
                }, jsonfile, indent=2, default=str)
            
            self.logger.info(f"Exported {len(alerts)} alerts to {filename}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting alerts to JSON: {e}")
            return False
    
    def save_alert_history(self):
        """Save alert history to file"""
        try:
            os.makedirs(Settings.DATA_DIR, exist_ok=True)
            with open(self.alert_file, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving alert history: {e}")
    
    def load_alert_history(self):
        """Load alert history from file"""
        try:
            if os.path.exists(self.alert_file):
                with open(self.alert_file, 'r', encoding='utf-8') as f:
                    self.alert_history = json.load(f)
                    
                # Rebuild sent alerts set from history (last 24 hours)
                recent_alerts = self.get_recent_alerts(24)
                self.sent_alerts = {alert['id'] for alert in recent_alerts}
                
                self.logger.info(f"Loaded {len(self.alert_history)} alerts from history")
        except Exception as e:
            self.logger.error(f"Error loading alert history: {e}")
            self.alert_history = []
    
    def cleanup_old_alerts(self, days_to_keep: int = 30):
        """Remove old alerts from history to prevent file from growing too large"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        original_count = len(self.alert_history)
        self.alert_history = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')) >= cutoff_date
        ]
        
        removed_count = original_count - len(self.alert_history)
        if removed_count > 0:
            self.save_alert_history()
            self.logger.info(f"Cleaned up {removed_count} old alerts, kept {len(self.alert_history)}")
    
    def print_alert_dashboard(self, alerts: List[Dict[str, Any]]):
        """Print a simple text dashboard of current alerts"""
        if not alerts:
            print("\n" + "="*50)
            print("📊 CRYPTO ALERTS DASHBOARD")
            print("="*50)
            print("No alerts at this time.")
            print("="*50 + "\n")
            return
        
        summary = self.get_alert_summary(alerts)
        
        print("\n" + "="*60)
        print("📊 CRYPTO ALERTS DASHBOARD")
        print("="*60)
        print(f"🔍 Total Alerts: {summary['total_alerts']}")
        print(f"📈 Golden Crosses: {summary['golden_crosses']}")
        print(f"📉 Death Crosses: {summary['death_crosses']}")
        print(f"💼 Unique Symbols: {summary['unique_symbols']}")
        print(f"🚨 High Priority: {summary['high_importance']}")
        print(f"⚠️  Medium Priority: {summary['medium_importance']}")
        print(f"ℹ️  Low Priority: {summary['low_importance']}")
        print("="*60)
        
        # Show top alerts by importance
        high_importance_alerts = [a for a in alerts if a['importance'] == 'HIGH']
        if high_importance_alerts:
            print("\n🚨 HIGH PRIORITY ALERTS:")
            print("-" * 40)
            for alert in high_importance_alerts[:10]:  # Show top 10
                print(f"• {alert['symbol']}: {alert['signal_type']} ({alert['crossover_name']})")
                print(f"  Price: ${alert['current_price']:.4f}, Strength: {alert['strength']}")
        
        print("="*60 + "\n")