"""
Main Entry Point for Health Monitoring System
Provides a command-line interface for various operations
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sensors.simulator import HealthSensorSimulator
from models.health_monitor import train_models_from_data, HealthMonitoringModel
from processing.data_processor import RealTimeMonitor
from dashboard.app import app, initialize_system


def generate_data(args):
    """Generate sample sensor data"""
    print(f"Generating {args.duration} minutes of sensor data...")
    
    simulator = HealthSensorSimulator(user_profile={
        'age': args.age,
        'gender': args.gender,
        'baseline_health': 'normal'
    })
    
    data = simulator.generate_stream(
        duration_minutes=args.duration,
        interval_seconds=args.interval
    )
    
    # Save data
    os.makedirs('data', exist_ok=True)
    output_file = f'data/{args.output}'
    simulator.save_to_csv(data, output_file)
    
    print(f"\nGenerated {len(data)} readings")
    print(f"Data saved to {output_file}")
    
    # Show statistics
    print("\nData Statistics:")
    print(data.describe())


def train_model(args):
    """Train ML models"""
    print(f"Training models from {args.data_file}...")
    
    if not os.path.exists(args.data_file):
        print(f"Error: Data file {args.data_file} not found!")
        print("Generate data first using: python main.py generate-data")
        return
    
    model = train_models_from_data(
        data_path=args.data_file,
        save_path=args.model_dir
    )
    
    print("\n✓ Models trained and saved successfully!")


def run_dashboard(args):
    """Launch the web dashboard"""
    print("Initializing health monitoring dashboard...")
    
    initialize_system()
    
    print(f"\nStarting dashboard on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop\n")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_reloader=False
    )


def simulate_realtime(args):
    """Run real-time simulation in console"""
    print("Starting real-time health monitoring simulation...")
    print("="*60 + "\n")
    
    simulator = HealthSensorSimulator()
    model = HealthMonitoringModel()
    
    # Try to load models
    if os.path.exists('models/anomaly_detector.pkl'):
        model.load_models('models')
        print("✓ ML models loaded\n")
    else:
        print("⚠ ML models not found. Run 'train-model' first for AI insights.\n")
        model = None
    
    monitor = RealTimeMonitor(ml_model=model)
    
    import time
    from datetime import datetime
    
    try:
        minutes_elapsed = 0
        while True:
            # Generate reading
            reading = simulator.generate_reading(minutes_elapsed=minutes_elapsed)
            
            # Process
            analysis = monitor.process_and_analyze(reading)
            
            if analysis:
                # Display
                print(f"[{datetime.now().strftime('%H:%M:%S')}]")
                print(f"❤️  Heart Rate: {reading['heart_rate']:.0f} bpm")
                print(f"🫁 SpO2: {reading['spo2']:.1f}%")
                print(f"🌡️  Temperature: {reading['temperature']:.1f}°C")
                print(f"💉 BP: {reading['systolic_bp']:.0f}/{reading['diastolic_bp']:.0f} mmHg")
                
                if 'insights' in analysis and analysis['insights']:
                    insights = analysis['insights']
                    print(f"🤖 Risk: {insights.get('risk_label', 'Unknown')}")
                    
                    if insights.get('is_anomaly'):
                        print("⚠️  ANOMALY DETECTED!")
                
                if 'alerts' in analysis and analysis['alerts']:
                    for alert in analysis['alerts']:
                        print(f"🚨 {alert['message']}")
                
                print("-" * 60)
            
            time.sleep(args.interval)
            minutes_elapsed += args.interval / 60
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        
        # Show summary
        summary = monitor.processor.get_daily_summary()
        if summary:
            print("\nSession Summary:")
            print(f"Total Readings: {summary['readings_count']}")
            print(f"Duration: {summary['duration_hours']:.1f} hours")
            
            if 'vitals' in summary:
                vitals = summary['vitals']
                print(f"\nAverage Heart Rate: {vitals['heart_rate']['avg']} bpm")
                print(f"Average SpO2: {vitals['spo2']['avg']}%")
                print(f"Average Temperature: {vitals['temperature']['avg']}°C")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AI-Based Wearable Health Monitoring Prototype',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate 24 hours of data:
    python main.py generate-data --duration 1440
  
  Train ML models:
    python main.py train-model
  
  Run web dashboard:
    python main.py dashboard
  
  Real-time console monitoring:
    python main.py simulate --interval 5
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Generate data command
    gen_parser = subparsers.add_parser('generate-data', help='Generate sensor data')
    gen_parser.add_argument('--duration', type=int, default=1440,
                           help='Duration in minutes (default: 1440 = 24 hours)')
    gen_parser.add_argument('--interval', type=int, default=300,
                           help='Interval between readings in seconds (default: 300 = 5 min)')
    gen_parser.add_argument('--age', type=int, default=30,
                           help='User age (default: 30)')
    gen_parser.add_argument('--gender', type=str, default='M',
                           choices=['M', 'F'], help='User gender (default: M)')
    gen_parser.add_argument('--output', type=str, default='sensor_data.csv',
                           help='Output filename (default: sensor_data.csv)')
    
    # Train model command
    train_parser = subparsers.add_parser('train-model', help='Train ML models')
    train_parser.add_argument('--data-file', type=str, default='data/sensor_data.csv',
                             help='Input data file (default: data/sensor_data.csv)')
    train_parser.add_argument('--model-dir', type=str, default='models',
                             help='Model output directory (default: models)')
    
    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Launch web dashboard')
    dash_parser.add_argument('--host', type=str, default='0.0.0.0',
                            help='Host address (default: 0.0.0.0)')
    dash_parser.add_argument('--port', type=int, default=5000,
                            help='Port number (default: 5000)')
    dash_parser.add_argument('--debug', action='store_true',
                            help='Enable debug mode')
    
    # Simulate command
    sim_parser = subparsers.add_parser('simulate', help='Real-time console simulation')
    sim_parser.add_argument('--interval', type=int, default=5,
                           help='Update interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate function
    if args.command == 'generate-data':
        generate_data(args)
    elif args.command == 'train-model':
        train_model(args)
    elif args.command == 'dashboard':
        run_dashboard(args)
    elif args.command == 'simulate':
        simulate_realtime(args)


if __name__ == '__main__':
    main()
