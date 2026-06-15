"""
Flask Web Dashboard for Health Monitoring
Real-time visualization of health metrics and alerts
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.simulator import HealthSensorSimulator
from models.health_monitor import HealthMonitoringModel
from processing.data_processor import RealTimeMonitor

import pandas as pd
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
CORS(app)

# Global variables
monitor = None
simulator = None
ml_model = None
data_history = []
is_running = False
monitoring_thread = None

# Physiological limits for validation
METRIC_LIMITS = {
    'heart_rate':     {'min': 30,   'max': 250},
    'spo2':           {'min': 50,   'max': 100},
    'temperature':    {'min': 34.0, 'max': 43.0},
    'systolic_bp':    {'min': 60,   'max': 250},
    'diastolic_bp':   {'min': 30,   'max': 150},
    'activity_level': {'min': 0,    'max': 100},
}


def initialize_system():
    """Initialize the monitoring system"""
    global monitor, simulator, ml_model
    
    print("Initializing health monitoring system...")
    
    # Create simulator
    simulator = HealthSensorSimulator(user_profile={
        'age': 30,
        'gender': 'M',
        'baseline_health': 'normal'
    })
    
    # Try to load ML model
    ml_model = HealthMonitoringModel()
    model_loaded = ml_model.load_models('../../models')
    
    if not model_loaded:
        print("ML models not found. Training new models...")
        # Generate training data
        training_data = simulator.generate_stream(duration_minutes=1440, interval_seconds=300)
        ml_model.train_anomaly_detector(training_data)
        ml_model.train_risk_classifier(training_data)
        
        # Save models
        os.makedirs('../../models', exist_ok=True)
        ml_model.save_models('../../models')
    
    # Create monitor
    monitor = RealTimeMonitor(ml_model=ml_model)
    
    print("System initialized successfully!")


def background_monitoring():
    """Background thread for continuous monitoring"""
    global is_running, data_history, monitor, simulator
    
    minutes_elapsed = 0
    
    while is_running:
        # Generate new reading
        reading = simulator.generate_reading(minutes_elapsed=minutes_elapsed)
        
        # Process and analyze
        analysis = monitor.process_and_analyze(reading)
        
        if analysis:
            # Store in history (keep last 100 readings)
            data_history.append({
                'timestamp': reading['timestamp'].isoformat(),
                'reading': reading,
                'insights': analysis.get('insights', {}),
                'alerts': analysis.get('alerts', [])
            })
            
            # Keep only last 100 readings
            if len(data_history) > 100:
                data_history.pop(0)
        
        minutes_elapsed += 0.083  # ~5 seconds
        time.sleep(5)  # Update every 5 seconds


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'is_running': is_running,
        'readings_count': len(data_history),
        'model_loaded': ml_model is not None
    })


@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    global is_running, monitoring_thread
    
    if not is_running:
        is_running = True
        monitoring_thread = threading.Thread(target=background_monitoring, daemon=True)
        monitoring_thread.start()
        return jsonify({'status': 'started'})
    
    return jsonify({'status': 'already_running'})


@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    global is_running
    
    is_running = False
    return jsonify({'status': 'stopped'})


@app.route('/api/current')
def get_current_reading():
    """Get the most recent reading"""
    if not data_history:
        return jsonify({'error': 'No data available'}), 404
    
    return jsonify(data_history[-1])


@app.route('/api/history')
def get_history():
    """Get recent history"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(data_history[-limit:])


@app.route('/api/statistics')
def get_statistics():
    """Get current statistics"""
    if monitor is None:
        return jsonify({'error': 'Monitor not initialized'}), 500
    
    stats = monitor.processor.get_statistics()
    
    # Convert datetime objects to strings
    if 'time_range' in stats:
        stats['time_range'] = {
            'start': stats['time_range']['start'].isoformat(),
            'end': stats['time_range']['end'].isoformat()
        }
    
    return jsonify(stats)


@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    if monitor is None:
        return jsonify({'error': 'Monitor not initialized'}), 500
    
    hours = request.args.get('hours', 24, type=int)
    alerts = monitor.get_recent_alerts(hours=hours)
    
    # Convert datetime to string
    for alert in alerts:
        if 'timestamp' in alert:
            alert['timestamp'] = alert['timestamp'].isoformat()
    
    return jsonify(alerts)


@app.route('/api/metrics', methods=['POST'])
def submit_metric():
    """Submit a health metric reading with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    errors = {}
    for metric, limits in METRIC_LIMITS.items():
        if metric in data:
            value = data[metric]
            if not isinstance(value, (int, float)):
                errors[metric] = 'Must be a number'
            elif value < limits['min'] or value > limits['max']:
                errors[metric] = (
                    f"Value {value} is out of valid physiological range "
                    f"({limits['min']} - {limits['max']})"
                )

    if errors:
        return jsonify({'error': 'Invalid metric values', 'details': errors}), 400

    return jsonify({'status': 'ok', 'message': 'Metrics accepted', 'data': data}), 200


@app.route('/api/daily_summary')
def get_daily_summary():
    """Get daily summary"""
    if monitor is None:
        return jsonify({'error': 'Monitor not initialized'}), 500
    
    summary = monitor.processor.get_daily_summary()
    
    # Convert date to string
    if 'date' in summary:
        summary['date'] = str(summary['date'])
    
    return jsonify(summary)


@app.route('/api/chart_data')
def get_chart_data():
    """Get data formatted for charts"""
    if not data_history:
        return jsonify({'error': 'No data available'}), 404
    
    limit = request.args.get('limit', 30, type=int)
    recent_data = data_history[-limit:]
    
    chart_data = {
        'timestamps': [],
        'heart_rate': [],
        'spo2': [],
        'temperature': [],
        'systolic_bp': [],
        'diastolic_bp': [],
        'activity_level': [],
        'risk_levels': []
    }
    
    for entry in recent_data:
        reading = entry['reading']
        insights = entry.get('insights', {})
        
        chart_data['timestamps'].append(entry['timestamp'])
        chart_data['heart_rate'].append(reading.get('heart_rate'))
        chart_data['spo2'].append(reading.get('spo2'))
        chart_data['temperature'].append(reading.get('temperature'))
        chart_data['systolic_bp'].append(reading.get('systolic_bp'))
        chart_data['diastolic_bp'].append(reading.get('diastolic_bp'))
        chart_data['activity_level'].append(reading.get('activity_level'))
        chart_data['risk_levels'].append(insights.get('risk_level', 0))
    
    return jsonify(chart_data)


if __name__ == '__main__':
    # Initialize system
    initialize_system()
    
    print("\n" + "="*60)
    print("Health Monitoring Dashboard")
    print("="*60)
    print("\nStarting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)