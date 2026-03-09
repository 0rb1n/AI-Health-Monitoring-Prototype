# Quick Start Guide

## Installation

1. **Install Python 3.8+** (if not already installed)

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Command Line Interface

#### Step 1: Generate Sample Data
```bash
python main.py generate-data --duration 1440 --interval 300
```
This generates 24 hours of sensor data with readings every 5 minutes.

#### Step 2: Train ML Models
```bash
python main.py train-model
```
This trains the anomaly detection and risk assessment models.

#### Step 3: Launch Dashboard
```bash
python main.py dashboard
```
Then open http://localhost:5000 in your browser.

#### Alternative: Console Simulation
```bash
python main.py simulate --interval 5
```
This runs a real-time simulation in the console.

### Option 2: Use Individual Modules

#### Generate and Save Data
```python
from sensors.simulator import HealthSensorSimulator

simulator = HealthSensorSimulator(user_profile={
    'age': 30,
    'gender': 'M',
    'baseline_health': 'normal'
})

data = simulator.generate_stream(duration_minutes=1440, interval_seconds=300)
simulator.save_to_csv(data, 'data/sensor_data.csv')
```

#### Train Models
```python
from models.health_monitor import train_models_from_data

model = train_models_from_data(
    data_path='data/sensor_data.csv',
    save_path='models'
)
```

#### Analyze Single Reading
```python
from sensors.simulator import HealthSensorSimulator
from models.health_monitor import HealthMonitoringModel

simulator = HealthSensorSimulator()
model = HealthMonitoringModel()
model.load_models('models')

reading = simulator.generate_reading(minutes_elapsed=100)
insights = model.get_health_insights(reading)

print(f"Risk Level: {insights['risk_label']}")
print(f"Anomaly: {insights['is_anomaly']}")
print(f"Recommendation: {insights['recommendation']}")
```

## Dashboard Features

1. **Real-time Monitoring**: Live updates of all vital signs
2. **AI Risk Assessment**: ML-powered health risk predictions
3. **Interactive Charts**: Trend visualization for all metrics
4. **Alert System**: Automatic alerts for critical conditions
5. **Statistics**: Rolling statistics and aggregations

## Project Structure

```
├── src/
│   ├── sensors/          # Data simulation
│   ├── models/           # ML models
│   ├── processing/       # Data processing
│   └── dashboard/        # Web interface
├── data/                 # Generated data
├── models/               # Trained models
├── main.py              # CLI entry point
├── requirements.txt     # Dependencies
└── config.yaml          # Configuration
```

## Customization

### Adjust User Profile
Edit the user profile in the simulator:
```python
simulator = HealthSensorSimulator(user_profile={
    'age': 45,
    'gender': 'F',
    'baseline_health': 'normal'
})
```

### Modify Normal Ranges
Edit `config.yaml` to change thresholds and normal ranges.

### Adjust Anomaly Detection
Change contamination parameter:
```python
model.train_anomaly_detector(data, contamination=0.15)
```

## Troubleshooting

**Issue**: Models not found error
- **Solution**: Run `python main.py train-model` first

**Issue**: No data available
- **Solution**: Run `python main.py generate-data` first

**Issue**: Port 5000 already in use
- **Solution**: Use a different port: `python main.py dashboard --port 8080`

## Next Steps

1. Integrate with real hardware sensors
2. Add more ML models (LSTM for predictions)
3. Implement user authentication
4. Add data persistence (database)
5. Create mobile app interface
6. Add export and reporting features

## Safety Notice

⚠️ **This is a prototype for educational purposes only.** Do not use for actual medical diagnosis or treatment decisions. Always consult healthcare professionals for medical advice.
