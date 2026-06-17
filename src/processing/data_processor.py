"""
Data Processing Pipeline for Health Monitoring
Handles data cleaning, aggregation, and real-time processing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import json


class HealthDataProcessor:
    """Processes and analyzes health sensor data"""
    
    def __init__(self, window_size=10):
        """
        Initialize data processor
        
        Args:
            window_size: Number of recent readings to keep for rolling statistics
        """
        self.window_size = window_size
        self.data_buffer = deque(maxlen=window_size)
        self.all_data = []
        
    def validate_reading(self, reading):
        """
        Validate sensor reading for data quality
        
        Returns:
            is_valid: Boolean
            errors: List of validation errors
        """
        errors = []
        
        # Check for required fields
        required_fields = ['heart_rate', 'spo2', 'temperature', 
                          'systolic_bp', 'diastolic_bp']
        
        for field in required_fields:
            if field not in reading:
                errors.append(f"Missing field: {field}")
        
        if errors:
            return False, errors
        
        # Check for valid ranges
        validations = {
            'heart_rate': (20, 300, 'bpm'),
            'spo2': (0, 100, '%'),
            'temperature': (30, 45, '°C'),
            'systolic_bp': (50, 250, 'mmHg'),
            'diastolic_bp': (30, 150, 'mmHg'),
        }
        
        for field, (min_val, max_val, unit) in validations.items():
            value = reading.get(field)
            if value is None:
                continue
            if not (min_val <= value <= max_val):
                errors.append(
                    f"{field} out of valid range ({min_val}-{max_val} {unit}): {value}"
                )
        
        # Check blood pressure relationship
        if reading.get('systolic_bp') and reading.get('diastolic_bp'):
            if reading['systolic_bp'] <= reading['diastolic_bp']:
                errors.append("Systolic BP must be greater than diastolic BP")
        
        return len(errors) == 0, errors
    
    def clean_reading(self, reading):
        """Clean and normalize a sensor reading"""
        cleaned = reading.copy()
        
        # Add timestamp if missing
        if 'timestamp' not in cleaned:
            cleaned['timestamp'] = datetime.now()
        elif isinstance(cleaned['timestamp'], str):
            cleaned['timestamp'] = pd.to_datetime(cleaned['timestamp'])
        
        # Round numeric values
        numeric_fields = ['heart_rate', 'spo2', 'temperature', 
                         'systolic_bp', 'diastolic_bp', 'activity_level']
        
        for field in numeric_fields:
            if field in cleaned and cleaned[field] is not None:
                cleaned[field] = round(float(cleaned[field]), 1)
        
        return cleaned
    
    def process_reading(self, reading):
        """
        Process a new reading and update statistics
        
        Returns:
            processed_reading: Enhanced reading with computed metrics
        """
        # Validate and clean
        is_valid, errors = self.validate_reading(reading)
        
        if not is_valid:
            print(f"Warning: Invalid reading - {errors}")
            return None
        
        cleaned_reading = self.clean_reading(reading)
        
        # Add to buffers
        self.data_buffer.append(cleaned_reading)
        self.all_data.append(cleaned_reading)
        
        # Compute additional metrics
        enhanced_reading = self._enhance_reading(cleaned_reading)
        
        return enhanced_reading
    
    def _enhance_reading(self, reading):
        """Add computed metrics to reading"""
        enhanced = reading.copy()
        
        # Mean Arterial Pressure
        enhanced['map'] = round(
            (reading['systolic_bp'] + 2 * reading['diastolic_bp']) / 3, 1
        )
        
        # Pulse Pressure
        enhanced['pulse_pressure'] = round(
            reading['systolic_bp'] - reading['diastolic_bp'], 1
        )
        
        # Add rolling statistics if enough data
        if len(self.data_buffer) >= 2:
            enhanced['hr_trend'] = self._calculate_trend('heart_rate')
            enhanced['temp_trend'] = self._calculate_trend('temperature')
        
        return enhanced
    
    def _calculate_trend(self, metric):
        """
        Calculate trend direction for a metric
        
        Returns:
            'increasing', 'decreasing', or 'stable'
        """
        if len(self.data_buffer) < 2:
            return 'stable'
        
        values = [r[metric] for r in self.data_buffer]
        recent_avg = np.mean(values[-3:])
        earlier_avg = np.mean(values[:-3]) if len(values) > 3 else values[0]
        
        diff = recent_avg - earlier_avg
        
        if diff > 2:
            return 'increasing'
        elif diff < -2:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_statistics(self):
        """Get statistics from buffered data"""
        if len(self.data_buffer) == 0:
            return {}
        
        df = pd.DataFrame(list(self.data_buffer))
        
        stats = {
            'count': len(df),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            },
            'metrics': {}
        }
        
        numeric_cols = ['heart_rate', 'spo2', 'temperature', 
                       'systolic_bp', 'diastolic_bp', 'activity_level']
        
        for col in numeric_cols:
            if col in df.columns:
                stats['metrics'][col] = {
                    'mean': round(df[col].mean(), 1),
                    'std': round(df[col].std(), 1),
                    'min': round(df[col].min(), 1),
                    'max': round(df[col].max(), 1),
                    'current': round(df[col].iloc[-1], 1)
                }
        
        return stats
    
    def detect_rapid_changes(self, threshold_multiplier=2):
        """
        Detect rapid changes in vital signs
        
        Returns:
            alerts: List of alert dictionaries
        """
        if len(self.data_buffer) < 3:
            return []
        
        alerts = []
        df = pd.DataFrame(list(self.data_buffer))
        
        # Check for rapid changes
        metrics_to_check = {
            'heart_rate': 15,  # Alert if change > 15 bpm in short time
            'spo2': 3,         # Alert if SpO2 drops > 3%
            'temperature': 0.5  # Alert if temp changes > 0.5°C
        }
        
        for metric, threshold in metrics_to_check.items():
            if metric not in df.columns:
                continue
            
            recent_values = df[metric].tail(3).values
            change = abs(recent_values[-1] - recent_values[0])
            
            if change > threshold:
                alerts.append({
                    'type': 'rapid_change',
                    'metric': metric,
                    'change': round(change, 1),
                    'threshold': threshold,
                    'timestamp': df['timestamp'].iloc[-1]
                })
        
        return alerts
    
    def aggregate_by_hour(self, data=None):
        """Aggregate data by hour"""
        if data is None:
            if not self.all_data:
                return pd.DataFrame()
            data = pd.DataFrame(self.all_data)
        
        if isinstance(data, list):
            data = pd.DataFrame(data)
        
        # Ensure timestamp is datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)
        
        # Resample by hour
        hourly = data.resample('H').agg({
            'heart_rate': ['mean', 'min', 'max', 'std'],
            'spo2': ['mean', 'min', 'max'],
            'temperature': ['mean', 'min', 'max'],
            'systolic_bp': ['mean', 'min', 'max'],
            'diastolic_bp': ['mean', 'min', 'max'],
            'activity_level': ['mean', 'sum']
        }).round(1)
        
        return hourly
    
    def get_daily_summary(self, date=None):
        """Generate daily health summary"""
        if not self.all_data:
            return {}
        
        df = pd.DataFrame(self.all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if date:
            df = df[df['timestamp'].dt.date == date]
        
        if len(df) == 0:
            return {}
        
        summary = {
            'date': date or datetime.now().date(),
            'readings_count': len(df),
            'duration_hours': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600,
            'vitals': {
                'heart_rate': {
                    'avg': round(df['heart_rate'].mean(), 1),
                    'min': round(df['heart_rate'].min(), 1),
                    'max': round(df['heart_rate'].max(), 1),
                    'resting': round(df[df['activity_level'] < 20]['heart_rate'].mean(), 1) if len(df[df['activity_level'] < 20]) > 0 else None
                },
                'spo2': {
                    'avg': round(df['spo2'].mean(), 1),
                    'min': round(df['spo2'].min(), 1)
                },
                'temperature': {
                    'avg': round(df['temperature'].mean(), 1),
                    'min': round(df['temperature'].min(), 1),
                    'max': round(df['temperature'].max(), 1)
                },
                'blood_pressure': {
                    'systolic_avg': round(df['systolic_bp'].mean(), 1),
                    'diastolic_avg': round(df['diastolic_bp'].mean(), 1)
                },
                'activity': {
                    'avg_level': round(df['activity_level'].mean(), 1),
                    'total_activity_mins': round(len(df[df['activity_level'] > 30]) * 5, 0)  # Assuming 5 min intervals
                }
            }
        }
        
        return summary
    
    def export_data(self, filename, format='csv'):
        """Export all collected data"""
        if not self.all_data:
            print("No data to export")
            return
        
        df = pd.DataFrame(self.all_data)
        
        if format == 'csv':
            df.to_csv(filename, index=False)
        elif format == 'json':
            df.to_json(filename, orient='records', date_format='iso', indent=2)
        elif format == 'excel':
            df.to_excel(filename, index=False)
        
        print(f"Data exported to {filename}")
    
    def clear_buffer(self):
        """Clear the data buffer"""
        self.data_buffer.clear()
    
    def clear_all(self):
        """Clear all data"""
        self.data_buffer.clear()
        self.all_data.clear()


class RealTimeMonitor:
    """Real-time health monitoring with alerts"""
    
    def __init__(self, ml_model=None):
        """
        Initialize real-time monitor
        
        Args:
            ml_model: Trained HealthMonitoringModel instance
        """
        self.processor = HealthDataProcessor(window_size=20)
        self.ml_model = ml_model
        self.alert_history = []
        
    def process_and_analyze(self, reading):
        """
        Process reading and perform ML analysis
        
        Returns:
            analysis: Complete analysis results
        """
        # Process reading
        processed = self.processor.process_reading(reading)
        
        if processed is None:
            return None
        
        # Get ML insights if model available
        if self.ml_model:
            insights = self.ml_model.get_health_insights(reading)
        else:
            insights = {}
        
        # Check for rapid changes
        rapid_change_alerts = self.processor.detect_rapid_changes()
        
        # Combine results
        analysis = {
            'reading': processed,
            'insights': insights,
            'rapid_changes': rapid_change_alerts,
            'statistics': self.processor.get_statistics()
        }
        
        # Generate alerts
        alerts = self._generate_alerts(analysis)
        if alerts:
            self.alert_history.extend(alerts)
            analysis['alerts'] = alerts
        
        return analysis
    
    def _generate_alerts(self, analysis):
        """Generate health alerts based on analysis"""
        alerts = []
        reading = analysis['reading']
        insights = analysis.get('insights', {})
        
        # Critical vital sign alerts
        if reading['heart_rate'] > 120 or reading['heart_rate'] < 50:
            alerts.append({
                'severity': 'high',
                'type': 'vital_sign',
                'message': f"Critical heart rate: {reading['heart_rate']} bpm",
                'timestamp': reading['timestamp']
            })
        
        if reading['spo2'] < 90:
            alerts.append({
                'severity': 'high',
                'type': 'vital_sign',
                'message': f"Critical SpO2 level: {reading['spo2']}%",
                'timestamp': reading['timestamp']
            })
        
        if reading['temperature'] > 38.5 or reading['temperature'] < 35.5:
            alerts.append({
                'severity': 'high',
                'type': 'vital_sign',
                'message': f"Critical temperature: {reading['temperature']}°C",
                'timestamp': reading['timestamp']
            })
        
        # ML-based alerts
        if insights.get('risk_level', 0) >= 3:
            alerts.append({
                'severity': 'high',
                'type': 'ml_prediction',
                'message': f"High health risk detected: {insights.get('risk_label')}",
                'timestamp': reading['timestamp']
            })
        elif insights.get('is_anomaly'):
            alerts.append({
                'severity': 'medium',
                'type': 'ml_prediction',
                'message': "Anomalous health pattern detected",
                'timestamp': reading['timestamp']
            })
        
        # Rapid change alerts
        for change_alert in analysis.get('rapid_changes', []):
            alerts.append({
                'severity': 'medium',
                'type': 'rapid_change',
                'message': f"Rapid change in {change_alert['metric']}: {change_alert['change']}",
                'timestamp': change_alert['timestamp']
            })
        
        return alerts
    
    def get_recent_alerts(self, hours=24):
        """Get alerts from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [a for a in self.alert_history 
                 if a['timestamp'] >= cutoff]
        return recent


if __name__ == "__main__":
    # Example usage
    import os
    import sys
    sys.path.append('..')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    root_dir = os.path.dirname(src_dir)
    sys.path.append(src_dir)

    from sensors.simulator import HealthSensorSimulator
    
    print("Testing Data Processing Pipeline...")
    print("=" * 60)
    
    # Create simulator and processor
    simulator = HealthSensorSimulator()
    monitor = RealTimeMonitor()
    
    # Simulate real-time monitoring
    print("\nSimulating 10 readings...")
    
    for i in range(10):
        # Generate reading
        inject_anomaly = (i == 7)  # Inject anomaly at reading 7
        reading = simulator.generate_reading(
            minutes_elapsed=i * 5,
            inject_anomaly=inject_anomaly
        )
        
        # Process and analyze
        analysis = monitor.process_and_analyze(reading)
        
        if analysis:
            print(f"\nReading {i + 1}:")
            print(f"  Heart Rate: {reading['heart_rate']} bpm")
            print(f"  SpO2: {reading['spo2']}%")
            print(f"  Temperature: {reading['temperature']}°C")
            
            if 'alerts' in analysis:
                print(f"  [!] Alerts: {len(analysis['alerts'])}")
                for alert in analysis['alerts']:
                    print(f"    - [{alert['severity'].upper()}] {alert['message']}")
    
    # Get statistics
    print("\n" + "=" * 60)
    print("Session Statistics:")
    stats = monitor.processor.get_statistics()
    for metric, values in stats.get('metrics', {}).items():
        print(f"\n{metric}:")
        print(f"  Mean: {values['mean']}, Range: {values['min']}-{values['max']}")
    
    # Export data
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    root_dir = os.path.dirname(src_dir)
    data_dir = os.path.join(root_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    export_path = os.path.join(data_dir, 'processed_data.csv')
    monitor.processor.export_data(export_path, format='csv')
    print(f"\nData exported successfully to {export_path}")
