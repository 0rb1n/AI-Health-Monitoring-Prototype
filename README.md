# AI-Based Wearable Health Monitoring Prototype

A comprehensive prototype for real-time health monitoring using simulated wearable sensor data and machine learning algorithms.

## Features

- **Real-time Sensor Data Simulation**: Simulates heart rate, SpO2, body temperature, and activity levels
- **AI-Powered Anomaly Detection**: Machine learning models to detect health anomalies
- **Health Risk Assessment**: Risk scoring based on multiple vital signs
- **Interactive Dashboard**: Web-based visualization for monitoring health metrics
- **Alert System**: Automatic alerts for critical health conditions

## Project Structure

```
.
├── src/
│   ├── sensors/           # Sensor data simulation
│   ├── models/            # ML models for health monitoring
│   ├── processing/        # Data processing pipeline
│   └── dashboard/         # Visualization dashboard
├── data/                  # Sample and generated data
├── notebooks/             # Jupyter notebooks for analysis
├── tests/                 # Unit tests
├── requirements.txt       # Python dependencies
└── config.yaml           # Configuration file
```

## Health Metrics Monitored

1. **Heart Rate**: 60-100 bpm (normal range)
2. **SpO2 (Blood Oxygen)**: 95-100% (normal range)
3. **Body Temperature**: 36.1-37.2°C (normal range)
4. **Activity Level**: Steps, movement intensity
5. **Sleep Quality**: Duration and patterns

## ML Models

- **Anomaly Detection**: Isolation Forest for detecting unusual patterns
- **Risk Prediction**: Random Forest classifier for health risk assessment
- **Time Series Analysis**: LSTM for trend prediction

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Run Sensor Simulation

```bash
python src/sensors/simulator.py
```

### Train ML Models

```bash
python src/models/train_model.py
```

### Launch Dashboard

```bash
python src/dashboard/app.py
```

## Technologies Used

- Python 3.8+
- TensorFlow/Keras for deep learning
- Scikit-learn for ML algorithms
- Flask for web dashboard
- Plotly for interactive visualizations
- Pandas & NumPy for data processing

## Safety Notice

⚠️ This is a prototype for educational and demonstration purposes only. It should NOT be used for actual medical diagnosis or treatment decisions. Always consult healthcare professionals for medical advice.

## License

MIT License
