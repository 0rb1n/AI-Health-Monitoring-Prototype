"""
Health Monitoring ML Model
Includes anomaly detection and health risk assessment
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import json
from datetime import datetime
import os


class HealthMonitoringModel:
    """Machine Learning model for health monitoring and anomaly detection"""
    
    def __init__(self):
        self.anomaly_detector = None
        self.risk_classifier = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'heart_rate', 'spo2', 'temperature',
            'systolic_bp', 'diastolic_bp', 'activity_level'
        ]
        
    def prepare_features(self, data):
        """Extract and prepare features from sensor data"""
        if isinstance(data, dict):
            # Single reading
            features = np.array([[
                data['heart_rate'],
                data['spo2'],
                data['temperature'],
                data['systolic_bp'],
                data['diastolic_bp'],
                data['activity_level']
            ]])
        else:
            # DataFrame
            features = data[self.feature_columns].values
        
        return features
    
    def add_derived_features(self, df):
        """Add derived features for better prediction"""
        df = df.copy()
        
        # Mean Arterial Pressure
        df['map'] = (df['systolic_bp'] + 2 * df['diastolic_bp']) / 3
        
        # Pulse Pressure
        df['pulse_pressure'] = df['systolic_bp'] - df['diastolic_bp']
        
        # Heart rate variability indicators (if we have time series)
        if 'timestamp' in df.columns:
            df['hr_diff'] = df['heart_rate'].diff().fillna(0)
            df['hr_rolling_std'] = df['heart_rate'].rolling(window=5, min_periods=1).std().fillna(0)
        
        return df
    
    def train_anomaly_detector(self, data, contamination=0.1):
        """
        Train Isolation Forest for anomaly detection
        
        Args:
            data: Training data (DataFrame or features array)
            contamination: Expected proportion of anomalies
        """
        print("Training anomaly detection model...")

        from sklearn.metrics import accuracy_score
        y_true = None

        if isinstance(data, pd.DataFrame):
            data = self.add_derived_features(data)
            print(data.head())
            # Use all numeric columns
            feature_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            # Remove the anomaly label if present
            if 'anomaly_injected' in feature_cols:
                y_true = data['anomaly_injected'].values.astype(bool)
                feature_cols.remove('anomaly_injected')
            features = data[feature_cols].values
        else:
            features = data
        
        # Train / Test split
        if y_true is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                features, y_true, test_size=0.2, random_state=42
            )
        else:
            X_train, X_test = train_test_split(
                features, test_size=0.2, random_state=42
            )
            y_train = None
            y_test = None

        # Fit scaler
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Isolation Forest
        self.anomaly_detector = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.anomaly_detector.fit(X_train_scaled)
        
        print(f"Anomaly detector trained on {len(X_train)} samples")

        # Evaluate accuracy if true labels (anomaly_injected) are available
        if y_test is not None:
            y_pred_test = self.anomaly_detector.predict(X_test_scaled)
            # IsolationForest returns -1 for anomaly, 1 for normal
            y_pred_mapped = (y_pred_test == -1)
            acc = accuracy_score(y_test, y_pred_mapped)
            print(f"Anomaly detection testing accuracy: {acc:.3f}")
        
        return self
    
    def detect_anomaly(self, reading):
        """
        Detect if a reading is anomalous
        
        Args:
            reading: Single sensor reading (dict or DataFrame row)
        
        Returns:
            is_anomaly: Boolean indicating if reading is anomalous
            anomaly_score: Anomaly score (lower is more anomalous)
        """
        if self.anomaly_detector is None:
            raise ValueError("Anomaly detector not trained. Call train_anomaly_detector first.")
        
        # Prepare features with derived features if needed
        if isinstance(reading, dict):
            df = pd.DataFrame([reading])
            df = self.add_derived_features(df)
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'anomaly_injected' in feature_cols:
                feature_cols.remove('anomaly_injected')
            features = df[feature_cols].values
        else:
            features = self.prepare_features(reading)
            
        features_scaled = self.scaler.transform(features)
        
        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.anomaly_detector.predict(features_scaled)[0]
        anomaly_score = self.anomaly_detector.score_samples(features_scaled)[0]
        
        is_anomaly = prediction == -1
        
        return is_anomaly, anomaly_score
    
    def create_risk_labels(self, data):
        """
        Create risk labels based on health metrics
        
        Risk levels:
        0 - Normal
        1 - Low Risk
        2 - Moderate Risk
        3 - High Risk
        """
        risks = []
        
        for _, row in data.iterrows():
            risk_score = 0
            
            # Heart rate risk
            if row['heart_rate'] < 50 or row['heart_rate'] > 100:
                risk_score += 1
            if row['heart_rate'] < 40 or row['heart_rate'] > 120:
                risk_score += 2
            
            # SpO2 risk
            if row['spo2'] < 95:
                risk_score += 1
            if row['spo2'] < 90:
                risk_score += 2
            
            # Temperature risk
            if row['temperature'] < 36.0 or row['temperature'] > 37.5:
                risk_score += 1
            if row['temperature'] < 35.0 or row['temperature'] > 38.5:
                risk_score += 2
            
            # Blood pressure risk
            if row['systolic_bp'] > 130 or row['diastolic_bp'] > 85:
                risk_score += 1
            if row['systolic_bp'] > 140 or row['diastolic_bp'] > 90:
                risk_score += 2
            if row['systolic_bp'] < 90 or row['diastolic_bp'] < 60:
                risk_score += 1
            
            # Determine final risk level
            if risk_score == 0:
                risk_level = 0  # Normal
            elif risk_score <= 2:
                risk_level = 1  # Low Risk
            elif risk_score <= 4:
                risk_level = 2  # Moderate Risk
            else:
                risk_level = 3  # High Risk
            
            risks.append(risk_level)
        
        return np.array(risks)
    
    def train_risk_classifier(self, data):
        """Train Random Forest for risk classification"""
        print("Training risk classification model...")
        
        data = self.add_derived_features(data)
        
        # Create labels
        y = self.create_risk_labels(data)
        
        # Prepare features
        feature_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if 'anomaly_injected' in feature_cols:
            feature_cols.remove('anomaly_injected')
        
        X = data[feature_cols].values
        
        # Split data - check if stratification is possible
        # Stratify only if each class has at least 2 samples
        unique, counts = np.unique(y, return_counts=True)
        can_stratify = all(counts >= 2)
        
        if can_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Train classifier
        self.risk_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.risk_classifier.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.risk_classifier.score(X_train, y_train)
        test_score = self.risk_classifier.score(X_test, y_test)
        
        print(f"Risk classifier trained on {len(X_train)} samples")
        print(f"Training accuracy: {train_score:.3f}")
        print(f"Testing accuracy: {test_score:.3f}")
        
        return self
    
    def assess_risk(self, reading):
        """
        Assess health risk level for a reading
        
        Returns:
            risk_level: 0 (Normal), 1 (Low), 2 (Moderate), 3 (High)
            risk_probability: Probability distribution over risk levels
        """
        if self.risk_classifier is None:
            raise ValueError("Risk classifier not trained. Call train_risk_classifier first.")
        
        # Prepare features (need to handle derived features)
        if isinstance(reading, dict):
            df = pd.DataFrame([reading])
            df = self.add_derived_features(df)
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'anomaly_injected' in feature_cols:
                feature_cols.remove('anomaly_injected')
            features = df[feature_cols].values
        else:
            features = reading
        
        # Predict
        risk_level = self.risk_classifier.predict(features)[0]
        risk_proba = self.risk_classifier.predict_proba(features)[0]
        
        risk_labels = ['Normal', 'Low Risk', 'Moderate Risk', 'High Risk']
        
        return risk_level, risk_proba, risk_labels[risk_level]
    
    def get_health_insights(self, reading):
        """
        Get comprehensive health insights for a reading
        
        Returns:
            Dictionary with anomaly detection and risk assessment results
        """
        is_anomaly, anomaly_score = self.detect_anomaly(reading)
        risk_level, risk_proba, risk_label = self.assess_risk(reading)
        
        # Identify specific concerns
        concerns = []
        if reading['heart_rate'] < 60:
            concerns.append("Low heart rate (bradycardia)")
        elif reading['heart_rate'] > 100:
            concerns.append("High heart rate (tachycardia)")
        
        if reading['spo2'] < 95:
            concerns.append("Low blood oxygen")
        
        if reading['temperature'] > 37.5:
            concerns.append("Elevated temperature")
        elif reading['temperature'] < 36.0:
            concerns.append("Low temperature")
        
        if reading['systolic_bp'] > 130 or reading['diastolic_bp'] > 85:
            concerns.append("Elevated blood pressure")
        elif reading['systolic_bp'] < 90 or reading['diastolic_bp'] < 60:
            concerns.append("Low blood pressure")
        
        insights = {
            'timestamp': reading.get('timestamp', datetime.now()),
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': float(anomaly_score),
            'risk_level': int(risk_level),
            'risk_label': risk_label,
            'risk_probabilities': {
                'Normal': float(risk_proba[0]),
                'Low Risk': float(risk_proba[1]) if len(risk_proba) > 1 else 0.0,
                'Moderate Risk': float(risk_proba[2]) if len(risk_proba) > 2 else 0.0,
                'High Risk': float(risk_proba[3]) if len(risk_proba) > 3 else 0.0
            },
            'concerns': concerns,
            'recommendation': self._get_recommendation(risk_level, concerns)
        }
        
        return insights
    
    def _get_recommendation(self, risk_level, concerns):
        """Generate health recommendation based on risk level"""
        if risk_level == 0:
            return "All vitals are within normal range. Continue monitoring."
        elif risk_level == 1:
            return "Minor concerns detected. Monitor closely and maintain healthy habits."
        elif risk_level == 2:
            return "Moderate risk detected. Consider consulting a healthcare professional if symptoms persist."
        else:
            return "High risk detected. Seek immediate medical attention if you experience symptoms."
    
    def save_models(self, model_dir='models'):
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        if self.anomaly_detector:
            joblib.dump(self.anomaly_detector, f'{model_dir}/anomaly_detector.pkl')
            joblib.dump(self.scaler, f'{model_dir}/scaler.pkl')
            print(f"Anomaly detector saved to {model_dir}/")
        
        if self.risk_classifier:
            joblib.dump(self.risk_classifier, f'{model_dir}/risk_classifier.pkl')
            print(f"Risk classifier saved to {model_dir}/")
    
    def load_models(self, model_dir='models'):
        """Load trained models from disk"""
        try:
            self.anomaly_detector = joblib.load(f'{model_dir}/anomaly_detector.pkl')
            self.scaler = joblib.load(f'{model_dir}/scaler.pkl')
            self.risk_classifier = joblib.load(f'{model_dir}/risk_classifier.pkl')
            print("Models loaded successfully")
            return True
        except FileNotFoundError as e:
            print(f"Error loading models: {e}")
            return False


def train_models_from_data(data_path='data/sensor_data.csv', save_path='models'):
    """Train models from sensor data file"""
    print(f"Loading data from {data_path}...")
    data = pd.read_csv(data_path)
    
    print(f"Loaded {len(data)} sensor readings")
    print("\nData preview:")
    print(data.head())
    
    # Initialize model
    model = HealthMonitoringModel()
    
    # Train models
    model.train_anomaly_detector(data, contamination=0.1)
    model.train_risk_classifier(data)
    
    # Save models
    model.save_models(save_path)
    
    print("\nModel training complete!")
    
    return model


if __name__ == "__main__":
    # Example usage
    import sys
    import os
    
    # Ensure src is in the python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    root_dir = os.path.dirname(src_dir)
    sys.path.append(src_dir)
    
    from sensors.simulator import HealthSensorSimulator
    
    print("Generating sample data for training...")
    simulator = HealthSensorSimulator()
    data = simulator.generate_stream(duration_minutes=1440, interval_seconds=300)
    
    # Save data
    data_dir = os.path.join(root_dir, 'data')
    models_dir = os.path.join(root_dir, 'models')
    os.makedirs(data_dir, exist_ok=True)
    data_path = os.path.join(data_dir, 'sensor_data.csv')
    data.to_csv(data_path, index=False)
    
    # Train models
    model = train_models_from_data(data_path, models_dir)
    
    # Test on a sample reading
    print("\n" + "="*60)
    print("Testing model on sample readings...")
    print("="*60)
    
    # Normal reading
    normal_reading = simulator.generate_reading(minutes_elapsed=100, inject_anomaly=False)
    insights = model.get_health_insights(normal_reading)
    
    print("\nNormal Reading Analysis:")
    print(f"Heart Rate: {normal_reading['heart_rate']} bpm")
    print(f"SpO2: {normal_reading['spo2']}%")
    print(f"Temperature: {normal_reading['temperature']}°C")
    print(f"Is Anomaly: {insights['is_anomaly']} (Score: {insights['anomaly_score']:.3f})")
    print(f"Risk Level: {insights['risk_label']}")
    print(f"Concerns: {', '.join(insights['concerns']) if insights['concerns'] else 'None'}")
    print(f"Recommendation: {insights['recommendation']}")

    # Anomalous reading
    anomalous_reading = simulator.generate_reading(minutes_elapsed=110, inject_anomaly=True)
    anomalous_insights = model.get_health_insights(anomalous_reading)
    
    print("\nAnomalous Reading Analysis:")
    print(f"Heart Rate: {anomalous_reading['heart_rate']} bpm")
    print(f"SpO2: {anomalous_reading['spo2']}%")
    print(f"Temperature: {anomalous_reading['temperature']}°C")
    print(f"Is Anomaly: {anomalous_insights['is_anomaly']} (Score: {anomalous_insights['anomaly_score']:.3f})")
    print(f"Risk Level: {anomalous_insights['risk_label']}")
    print(f"Concerns: {', '.join(anomalous_insights['concerns']) if anomalous_insights['concerns'] else 'None'}")
    print(f"Recommendation: {anomalous_insights['recommendation']}")
