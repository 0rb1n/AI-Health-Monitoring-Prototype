"""
Wearable Health Sensor Data Simulator
Generates realistic health monitoring data with configurable anomaly injection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import random


class HealthSensorSimulator:
    """Simulates wearable health sensor data"""
    
    def __init__(self, user_profile=None):
        """
        Initialize the sensor simulator
        
        Args:
            user_profile: Dictionary containing user information (age, gender, baseline_health)
        """
        self.user_profile = user_profile or {
            'age': 30,
            'gender': 'M',
            'baseline_health': 'normal'
        }
        
        # Normal ranges for health metrics
        self.normal_ranges = {
            'heart_rate': (60, 100),
            'spo2': (95, 100),
            'temperature': (36.1, 37.2),
            'systolic_bp': (90, 120),
            'diastolic_bp': (60, 80),
            'activity_level': (0, 100)
        }
        
        # Adjust baseline based on age
        self.age_adjustment = self._get_age_adjustment()
        
    def _get_age_adjustment(self):
        """Adjust normal ranges based on age"""
        age = self.user_profile['age']
        
        if age < 20:
            return {'heart_rate': 5, 'spo2': 0, 'temperature': 0.1}
        elif age > 60:
            return {'heart_rate': -5, 'spo2': -1, 'temperature': -0.2}
        else:
            return {'heart_rate': 0, 'spo2': 0, 'temperature': 0}
    
    def generate_heart_rate(self, minutes_elapsed=0, activity='resting', anomaly=False):
        """
        Generate heart rate data
        
        Args:
            minutes_elapsed: Time in minutes since start
            activity: Current activity level ('resting', 'light', 'moderate', 'intense')
            anomaly: Whether to inject an anomaly
        """
        base_hr = 70 + self.age_adjustment['heart_rate']
        
        # Activity adjustments
        activity_multipliers = {
            'resting': 1.0,
            'light': 1.2,
            'moderate': 1.5,
            'intense': 1.8
        }
        
        multiplier = activity_multipliers.get(activity, 1.0)
        hr = base_hr * multiplier
        
        # Add natural variation
        hr += np.random.normal(0, 3)
        
        # Add circadian rhythm effect (lower at night)
        hour = (minutes_elapsed // 60) % 24
        if 0 <= hour < 6:
            hr -= 5
        
        # Inject anomaly if requested
        if anomaly:
            anomaly_type = random.choice(['tachycardia', 'bradycardia', 'irregular'])
            if anomaly_type == 'tachycardia':
                hr += random.uniform(30, 50)
            elif anomaly_type == 'bradycardia':
                hr -= random.uniform(20, 30)
            else:
                hr += random.uniform(-15, 15) * random.choice([-1, 1])
        
        return max(40, min(200, hr))
    
    def generate_spo2(self, anomaly=False):
        """Generate SpO2 (blood oxygen) data"""
        base_spo2 = 98 + self.age_adjustment['spo2']
        spo2 = base_spo2 + np.random.normal(0, 0.5)
        
        if anomaly:
            spo2 -= random.uniform(5, 15)  # Hypoxia
        
        return max(70, min(100, spo2))
    
    def generate_temperature(self, minutes_elapsed=0, anomaly=False):
        """Generate body temperature data"""
        base_temp = 36.6 + self.age_adjustment['temperature']
        
        # Add circadian rhythm (slightly higher in evening)
        hour = (minutes_elapsed // 60) % 24
        if 14 <= hour < 20:
            base_temp += 0.2
        
        temp = base_temp + np.random.normal(0, 0.1)
        
        if anomaly:
            # Fever or hypothermia
            if random.random() > 0.3:
                temp += random.uniform(1.5, 3.0)  # Fever
            else:
                temp -= random.uniform(1.0, 2.0)  # Hypothermia
        
        return round(temp, 1)
    
    def generate_blood_pressure(self, activity='resting', anomaly=False):
        """Generate blood pressure data (systolic/diastolic)"""
        systolic = 110 + np.random.normal(0, 5)
        diastolic = 70 + np.random.normal(0, 3)
        
        # Activity effect
        if activity in ['moderate', 'intense']:
            systolic += 10
            diastolic += 5
        
        if anomaly:
            if random.random() > 0.5:
                # Hypertension
                systolic += random.uniform(20, 40)
                diastolic += random.uniform(10, 20)
            else:
                # Hypotension
                systolic -= random.uniform(15, 25)
                diastolic -= random.uniform(10, 15)
        
        return round(systolic), round(diastolic)
    
    def generate_activity_level(self, minutes_elapsed=0):
        """Generate activity level data"""
        hour = (minutes_elapsed // 60) % 24
        
        # Most active during day hours
        if 7 <= hour < 22:
            base_activity = random.uniform(20, 80)
        else:
            base_activity = random.uniform(0, 10)  # Sleep
        
        return round(base_activity, 1)

    def generate_sleep_quality(self, minutes_elapsed=0, has_anomaly=False):
        """
        Generate sleep stage and quality index based on time of night.

        Uses an ultradian rhythm model (~90-minute cycles) to simulate realistic
        sleep architecture. Sleep quality degrades when health anomalies occur
        during the sleep window (e.g. tachycardia, apnea-induced hypoxia).

        Args:
            minutes_elapsed: Time in minutes since monitoring started
            has_anomaly: Whether a health anomaly is active during this reading

        Returns:
            dict with:
                sleep_stage (str): 'Deep', 'Light', 'REM', 'Awake', or 'Awake (daytime)'
                sleep_quality_index (float or None): 0-100 score; None outside sleep window
        """
        hour = (minutes_elapsed // 60) % 24

        # Sleep window: 11 PM (23:00) to 7 AM (07:00)
        is_sleep_window = hour >= 23 or hour < 7

        if not is_sleep_window:
            return {
                'sleep_stage': 'Awake (daytime)',
                'sleep_quality_index': None
            }

        # Minutes elapsed since sleep started at 23:00
        if hour >= 23:
            mins_since_sleep = (hour - 23) * 60
        else:
            mins_since_sleep = (hour + 1) * 60  # 00:00 onward

        # Ultradian cycle: ~90-minute cycles transitioning through stages
        # Deep Sleep -> Light Sleep -> REM -> brief Awake -> repeat
        cycle_position = mins_since_sleep % 90

        if cycle_position < 25:
            stage = 'Deep'
        elif cycle_position < 55:
            stage = 'Light'
        elif cycle_position < 80:
            stage = 'REM'
        else:
            stage = 'Awake'

        # Base quality score with natural variation
        base_quality = random.uniform(75, 95)

        # Anomalies during sleep (tachycardia, hypoxia, fever) degrade quality
        if has_anomaly:
            base_quality -= random.uniform(15, 30)

        sleep_quality_index = round(max(0.0, min(100.0, base_quality)), 1)

        return {
            'sleep_stage': stage,
            'sleep_quality_index': sleep_quality_index
        }

    def generate_reading(self, minutes_elapsed=0, inject_anomaly=False):
        """
        Generate a complete sensor reading
        
        Args:
            minutes_elapsed: Time in minutes since monitoring started
            inject_anomaly: Whether to inject anomalies
        """
        activity = self._determine_activity(minutes_elapsed)
        
        # Randomly inject anomalies (5% chance if not forced)
        has_anomaly = inject_anomaly or (random.random() < 0.05)
        
        systolic, diastolic = self.generate_blood_pressure(activity, has_anomaly)

        sleep_data = self.generate_sleep_quality(minutes_elapsed, has_anomaly)

        reading = {
            'timestamp': datetime.now() + timedelta(minutes=minutes_elapsed),
            'heart_rate': round(self.generate_heart_rate(minutes_elapsed, activity, has_anomaly), 1),
            'spo2': round(self.generate_spo2(has_anomaly), 1),
            'temperature': self.generate_temperature(minutes_elapsed, has_anomaly),
            'systolic_bp': systolic,
            'diastolic_bp': diastolic,
            'activity_level': self.generate_activity_level(minutes_elapsed),
            'sleep_stage': sleep_data['sleep_stage'],
            'sleep_quality_index': sleep_data['sleep_quality_index'],
            'anomaly_injected': has_anomaly
        }
        
        return reading
    
    def _determine_activity(self, minutes_elapsed):
        """Determine activity level based on time of day"""
        hour = (minutes_elapsed // 60) % 24
        
        if 0 <= hour < 6 or 22 <= hour < 24:
            return 'resting'
        elif 6 <= hour < 9 or 17 <= hour < 19:
            return random.choice(['light', 'moderate'])
        else:
            return random.choice(['resting', 'light'])
    
    def generate_stream(self, duration_minutes=60, interval_seconds=10):
        """
        Generate a continuous stream of sensor data
        
        Args:
            duration_minutes: How long to generate data for
            interval_seconds: Interval between readings
        """
        readings = []
        num_readings = (duration_minutes * 60) // interval_seconds
        
        print(f"Generating {num_readings} sensor readings over {duration_minutes} minutes...")
        
        for i in range(num_readings):
            minutes_elapsed = (i * interval_seconds) / 60
            reading = self.generate_reading(minutes_elapsed)
            readings.append(reading)
            
            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1}/{num_readings} readings...")
        
        return pd.DataFrame(readings)
    
    def save_to_csv(self, data, filename='sensor_data.csv'):
        """Save generated data to CSV file"""
        data.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    
    def save_to_json(self, data, filename='sensor_data.json'):
        """Save generated data to JSON file"""
        data['timestamp'] = data['timestamp'].astype(str)
        data.to_json(filename, orient='records', indent=2)
        print(f"Data saved to {filename}")


def simulate_realtime_monitoring(duration_seconds=60):
    """Simulate real-time monitoring"""
    simulator = HealthSensorSimulator()
    
    print("Starting real-time health monitoring...")
    print("=" * 60)
    
    start_time = datetime.now()
    elapsed_seconds = 0
    
    while elapsed_seconds < duration_seconds:
        reading = simulator.generate_reading(elapsed_seconds / 60)
        
        print(f"\n[{reading['timestamp'].strftime('%H:%M:%S')}]")
        print(f"Heart Rate: {reading['heart_rate']} bpm")
        print(f"SpO2: {reading['spo2']}%")
        print(f"Temperature: {reading['temperature']}°C")
        print(f"Blood Pressure: {reading['systolic_bp']}/{reading['diastolic_bp']} mmHg")
        print(f"Activity: {reading['activity_level']}%")

        if reading['sleep_stage'] != 'Awake (daytime)':
            print(f"Sleep Stage: {reading['sleep_stage']}")
            print(f"Sleep Quality: {reading['sleep_quality_index']}%")

        if reading['anomaly_injected']:
            print("⚠️  ANOMALY DETECTED!")
        
        print("-" * 60)
        
        time.sleep(5)  # Update every 5 seconds
        elapsed_seconds += 5


if __name__ == "__main__":
    # Example 1: Generate historical data
    print("Example 1: Generating 24 hours of historical data...\n")
    simulator = HealthSensorSimulator(user_profile={
        'age': 35,
        'gender': 'M',
        'baseline_health': 'normal'
    })
    
    # Generate 24 hours of data with readings every 5 minutes
    data = simulator.generate_stream(duration_minutes=1440, interval_seconds=300)
    
    # Save to file
    simulator.save_to_csv(data, 'data/sensor_data.csv')
    
    # Display statistics
    print("\nData Statistics:")
    print(data.describe())
    
    # Example 2: Real-time monitoring (uncomment to run)
    # print("\n\nExample 2: Real-time monitoring for 60 seconds...\n")
    # simulate_realtime_monitoring(duration_seconds=60)