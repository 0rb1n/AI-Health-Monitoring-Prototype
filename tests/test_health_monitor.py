"""
Unit tests for Health Monitoring System
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sensors.simulator import HealthSensorSimulator
from models.health_monitor import HealthMonitoringModel
from processing.data_processor import HealthDataProcessor
import pandas as pd


class TestSensorSimulator:
    """Test sensor simulator"""
    
    def test_simulator_initialization(self):
        """Test simulator creates successfully"""
        simulator = HealthSensorSimulator()
        assert simulator is not None
        assert simulator.user_profile['age'] == 30
    
    def test_generate_heart_rate(self):
        """Test heart rate generation"""
        simulator = HealthSensorSimulator()
        hr = simulator.generate_heart_rate(activity='resting')
        assert 40 <= hr <= 200
    
    def test_generate_spo2(self):
        """Test SpO2 generation"""
        simulator = HealthSensorSimulator()
        spo2 = simulator.generate_spo2()
        assert 70 <= spo2 <= 100
    
    def test_generate_reading(self):
        """Test complete reading generation"""
        simulator = HealthSensorSimulator()
        reading = simulator.generate_reading(minutes_elapsed=100)
        
        assert 'heart_rate' in reading
        assert 'spo2' in reading
        assert 'temperature' in reading
        assert 'systolic_bp' in reading
        assert 'diastolic_bp' in reading
    
    def test_anomaly_injection(self):
        """Test anomaly injection"""
        simulator = HealthSensorSimulator()
        reading = simulator.generate_reading(inject_anomaly=True)
        assert reading['anomaly_injected'] == True


class TestHealthMonitoringModel:
    """Test ML models"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        simulator = HealthSensorSimulator()
        return simulator.generate_stream(duration_minutes=120, interval_seconds=60)
    
    def test_model_initialization(self):
        """Test model initialization"""
        model = HealthMonitoringModel()
        assert model is not None
        assert model.feature_columns is not None
    
    def test_train_anomaly_detector(self, sample_data):
        """Test anomaly detector training"""
        model = HealthMonitoringModel()
        model.train_anomaly_detector(sample_data)
        assert model.anomaly_detector is not None
    
    def test_train_risk_classifier(self, sample_data):
        """Test risk classifier training"""
        model = HealthMonitoringModel()
        model.train_risk_classifier(sample_data)
        assert model.risk_classifier is not None
    
    def test_detect_anomaly(self, sample_data):
        """Test anomaly detection"""
        model = HealthMonitoringModel()
        model.train_anomaly_detector(sample_data)
        
        simulator = HealthSensorSimulator()
        reading = simulator.generate_reading()
        
        is_anomaly, score = model.detect_anomaly(reading)
        assert isinstance(is_anomaly, bool)
        assert isinstance(score, float)
    
    def test_assess_risk(self, sample_data):
        """Test risk assessment"""
        model = HealthMonitoringModel()
        model.train_risk_classifier(sample_data)
        
        simulator = HealthSensorSimulator()
        reading = simulator.generate_reading()
        
        risk_level, risk_proba, risk_label = model.assess_risk(reading)
        assert 0 <= risk_level <= 3
        assert len(risk_proba) == 4
        assert risk_label in ['Normal', 'Low Risk', 'Moderate Risk', 'High Risk']


class TestDataProcessor:
    """Test data processing"""
    
    def test_processor_initialization(self):
        """Test processor initialization"""
        processor = HealthDataProcessor()
        assert processor is not None
        assert len(processor.data_buffer) == 0
    
    def test_validate_reading(self):
        """Test reading validation"""
        processor = HealthDataProcessor()
        
        valid_reading = {
            'heart_rate': 70,
            'spo2': 98,
            'temperature': 36.6,
            'systolic_bp': 120,
            'diastolic_bp': 80
        }
        
        is_valid, errors = processor.validate_reading(valid_reading)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_invalid_reading(self):
        """Test invalid reading detection"""
        processor = HealthDataProcessor()
        
        invalid_reading = {
            'heart_rate': 500,  # Invalid
            'spo2': 98,
            'temperature': 36.6
        }
        
        is_valid, errors = processor.validate_reading(invalid_reading)
        assert is_valid == False
        assert len(errors) > 0
    
    def test_process_reading(self):
        """Test reading processing"""
        processor = HealthDataProcessor()
        simulator = HealthSensorSimulator()
        
        reading = simulator.generate_reading()
        processed = processor.process_reading(reading)
        
        assert processed is not None
        assert 'map' in processed
        assert 'pulse_pressure' in processed
    
    def test_statistics(self):
        """Test statistics calculation"""
        processor = HealthDataProcessor()
        simulator = HealthSensorSimulator()
        
        # Process multiple readings
        for i in range(10):
            reading = simulator.generate_reading(minutes_elapsed=i)
            processor.process_reading(reading)
        
        stats = processor.get_statistics()
        assert 'count' in stats
        assert stats['count'] == 10
        assert 'metrics' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
