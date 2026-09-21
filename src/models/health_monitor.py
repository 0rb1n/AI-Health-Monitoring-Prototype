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
from datetime import datetime
import os


class HealthMonitoringModel:
    """Machine Learning model for health monitoring and anomaly detection"""

    # Fixed base sensors used for both training and inference
    BASE_FEATURE_COLUMNS = [
        'heart_rate', 'spo2', 'temperature',
        'systolic_bp', 'diastolic_bp', 'activity_level'
    ]

    # Derived features computed from base sensors (no time-series window required)
    DERIVED_FEATURE_COLUMNS = [
        'map',            # Mean Arterial Pressure
        'pulse_pressure'  # Systolic - Diastolic
    ]

    def __init__(self):
        self.anomaly_detector = None
        self.risk_classifier = None
        self.scaler = StandardScaler()
        # Canonical ordered feature list used at train + inference
        self.feature_columns = self.BASE_FEATURE_COLUMNS + self.DERIVED_FEATURE_COLUMNS

    def _compute_derived(self, df):
        """Add derived features that can be computed from a single reading."""
        df = df.copy()
        df['map'] = (df['systolic_bp'] + 2 * df['diastolic_bp']) / 3
        df['pulse_pressure'] = df['systolic_bp'] - df['diastolic_bp']
        return df

    def _to_feature_matrix(self, data):
        """
        Convert a single reading (dict) or DataFrame into the fixed feature matrix
        used by both training and inference.
        """
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data.copy()

        df = self._compute_derived(df)

        # Ensure all expected columns exist
        missing = [c for c in self.feature_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")

        return df[self.feature_columns].values

    def train_anomaly_detector(self, data, contamination=0.1):
        """
        Train Isolation Forest for anomaly detection.

        Args:
            data: Training data (DataFrame)
            contamination: Expected proportion of anomalies
        """
        print("Training anomaly detection model...")

        if not isinstance(data, pd.DataFrame):
            raise TypeError("train_anomaly_detector expects a pandas DataFrame")

        features = self._to_feature_matrix(data)
        features_scaled = self.scaler.fit_transform(features)

        self.anomaly_detector = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.anomaly_detector.fit(features_scaled)

        print(f"Anomaly detector trained on {len(features)} samples "
              f"with {len(self.feature_columns)} features")
        return self

    def detect_anomaly(self, reading):
        """
        Detect if a reading is anomalous.

        Returns:
            is_anomaly: bool
            anomaly_score: float (lower is more anomalous)
        """
        if self.anomaly_detector is None:
            raise ValueError("Anomaly detector not trained. Call train_anomaly_detector first.")

        features = self._to_feature_matrix(reading)
        features_scaled = self.scaler.transform(features)

        prediction = self.anomaly_detector.predict(features_scaled)[0]
        anomaly_score = self.anomaly_detector.score_samples(features_scaled)[0]
        is_anomaly = prediction == -1

        return is_anomaly, anomaly_score

    def create_risk_labels(self, data):
        """
        Create risk labels based on health metrics.

        Risk levels:
        0 - Normal
        1 - Low Risk
        2 - Moderate Risk
        3 - High Risk
        """
        risks = []

        for _, row in data.iterrows():
            risk_score = 0

            if row['heart_rate'] < 50 or row['heart_rate'] > 100:
                risk_score += 1
            if row['heart_rate'] < 40 or row['heart_rate'] > 120:
                risk_score += 2

            if row['spo2'] < 95:
                risk_score += 1
            if row['spo2'] < 90:
                risk_score += 2

            if row['temperature'] < 36.0 or row['temperature'] > 37.5:
                risk_score += 1
            if row['temperature'] < 35.0 or row['temperature'] > 38.5:
                risk_score += 2

            if row['systolic_bp'] > 130 or row['diastolic_bp'] > 85:
                risk_score += 1
            if row['systolic_bp'] > 140 or row['diastolic_bp'] > 90:
                risk_score += 2
            if row['systolic_bp'] < 90 or row['diastolic_bp'] < 60:
                risk_score += 1

            if risk_score == 0:
                risk_level = 0
            elif risk_score <= 2:
                risk_level = 1
            elif risk_score <= 4:
                risk_level = 2
            else:
                risk_level = 3

            risks.append(risk_level)

        return np.array(risks)

    def train_risk_classifier(self, data):
        """Train Random Forest for risk classification."""
        print("Training risk classification model...")

        if not isinstance(data, pd.DataFrame):
            raise TypeError("train_risk_classifier expects a pandas DataFrame")

        y = self.create_risk_labels(data)
        X = self._to_feature_matrix(data)

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

        self.risk_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.risk_classifier.fit(X_train, y_train)

        train_score = self.risk_classifier.score(X_train, y_train)
        test_score = self.risk_classifier.score(X_test, y_test)

        print(f"Risk classifier trained on {len(X_train)} samples")
        print(f"Training accuracy: {train_score:.3f}")
        print(f"Testing accuracy: {test_score:.3f}")
        return self

    def assess_risk(self, reading):
        """
        Assess health risk level for a reading.

        Returns:
            risk_level: int 0-3
            risk_probability: length-4 array (Normal, Low, Moderate, High)
            risk_label: str
        """
        if self.risk_classifier is None:
            raise ValueError("Risk classifier not trained. Call train_risk_classifier first.")

        features = self._to_feature_matrix(reading)
        risk_level = int(self.risk_classifier.predict(features)[0])
        raw_proba = self.risk_classifier.predict_proba(features)[0]

        # Always return a full 4-class probability vector
        risk_probability = np.zeros(4, dtype=float)
        for cls_idx, cls_label in enumerate(self.risk_classifier.classes_):
            if 0 <= int(cls_label) < 4:
                risk_probability[int(cls_label)] = float(raw_proba[cls_idx])

        risk_labels = ['Normal', 'Low Risk', 'Moderate Risk', 'High Risk']
        return risk_level, risk_probability, risk_labels[risk_level]

    def get_health_insights(self, reading):
        """Get comprehensive health insights for a reading."""
        is_anomaly, anomaly_score = self.detect_anomaly(reading)
        risk_level, risk_proba, risk_label = self.assess_risk(reading)

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
                'Low Risk': float(risk_proba[1]),
                'Moderate Risk': float(risk_proba[2]),
                'High Risk': float(risk_proba[3]),
            },
            'concerns': concerns,
            'recommendation': self._get_recommendation(risk_level, concerns)
        }
        return insights

    def _get_recommendation(self, risk_level, concerns):
        """Generate health recommendation based on risk level."""
        if risk_level == 0:
            return "All vitals are within normal range. Continue monitoring."
        elif risk_level == 1:
            return "Minor concerns detected. Monitor closely and maintain healthy habits."
        elif risk_level == 2:
            return "Moderate risk detected. Consider consulting a healthcare professional if symptoms persist."
        else:
            return "High risk detected. Seek immediate medical attention if you experience symptoms."

    def save_models(self, model_dir='models'):
        """Save trained models and feature metadata to disk."""
        os.makedirs(model_dir, exist_ok=True)

        if self.anomaly_detector:
            joblib.dump(self.anomaly_detector, f'{model_dir}/anomaly_detector.pkl')
            joblib.dump(self.scaler, f'{model_dir}/scaler.pkl')
            joblib.dump(self.feature_columns, f'{model_dir}/feature_columns.pkl')
            print(f"Anomaly detector saved to {model_dir}/")

        if self.risk_classifier:
            joblib.dump(self.risk_classifier, f'{model_dir}/risk_classifier.pkl')
            print(f"Risk classifier saved to {model_dir}/")

    def load_models(self, model_dir='models'):
        """Load trained models and feature metadata from disk."""
        try:
            self.anomaly_detector = joblib.load(f'{model_dir}/anomaly_detector.pkl')
            self.scaler = joblib.load(f'{model_dir}/scaler.pkl')
            self.risk_classifier = joblib.load(f'{model_dir}/risk_classifier.pkl')
            try:
                self.feature_columns = joblib.load(f'{model_dir}/feature_columns.pkl')
            except FileNotFoundError:
                # Backward-compatible default for older model artifacts
                self.feature_columns = self.BASE_FEATURE_COLUMNS + self.DERIVED_FEATURE_COLUMNS
            print("Models loaded successfully")
            return True
        except FileNotFoundError as e:
            print(f"Error loading models: {e}")
            return False


def train_models_from_data(data_path='data/sensor_data.csv', save_path='models'):
    """Train models from sensor data file."""
    print(f"Loading data from {data_path}...")
    data = pd.read_csv(data_path)

    print(f"Loaded {len(data)} sensor readings")
    print("\nData preview:")
    print(data.head())

    model = HealthMonitoringModel()
    model.train_anomaly_detector(data, contamination=0.1)
    model.train_risk_classifier(data)
    model.save_models(save_path)

    print("\nModel training complete!")
    return model


if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from sensors.simulator import HealthSensorSimulator

    print("Generating sample data for training...")
    simulator = HealthSensorSimulator()
    data = simulator.generate_stream(duration_minutes=1440, interval_seconds=300)

    os.makedirs('../../data', exist_ok=True)
    data.to_csv('../../data/sensor_data.csv', index=False)

    model = train_models_from_data('../../data/sensor_data.csv', '../../models')

    print("\n" + "=" * 60)
    print("Testing model on sample readings...")
    print("=" * 60)

    normal_reading = simulator.generate_reading(minutes_elapsed=100, inject_anomaly=False)
    insights = model.get_health_insights(normal_reading)

    print("\nNormal Reading Analysis:")
    print(f"Heart Rate: {normal_reading['heart_rate']} bpm")
    print(f"SpO2: {normal_reading['spo2']}%")
    print(f"Temperature: {normal_reading['temperature']}°C")
    print(f"Risk Level: {insights['risk_label']}")
    print(f"Anomaly Detected: {insights['is_anomaly']}")
    print(f"Recommendation: {insights['recommendation']}")

    anomaly_reading = simulator.generate_reading(minutes_elapsed=200, inject_anomaly=True)
    insights = model.get_health_insights(anomaly_reading)

    print("\nAnomalous Reading Analysis:")
    print(f"Heart Rate: {anomaly_reading['heart_rate']} bpm")
    print(f"SpO2: {anomaly_reading['spo2']}%")
    print(f"Temperature: {anomaly_reading['temperature']}°C")
    print(f"Risk Level: {insights['risk_label']}")
    print(f"Anomaly Detected: {insights['is_anomaly']}")
    print(f"Concerns: {', '.join(insights['concerns']) if insights['concerns'] else 'None'}")
    print(f"Recommendation: {insights['recommendation']}")
