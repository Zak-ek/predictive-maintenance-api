import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logic import check_threshold, validate_sensor_data


class TestThresholdLogic:
    
    def test_normal_temperature(self):
        result = check_threshold('temperature', 65.0)
        assert result['is_anomaly'] == False
        assert result['severity'] == 'normal'
    
    def test_warning_temperature(self):
        result = check_threshold('temperature', 80.0)
        assert result['is_anomaly'] == True
        assert result['severity'] == 'warning'
    
    def test_critical_temperature(self):
        result = check_threshold('temperature', 95.0)
        assert result['is_anomaly'] == True
        assert result['severity'] == 'critical'
    
    def test_unknown_sensor_type(self):
        result = check_threshold('unknown_sensor', 100.0)
        assert result['is_anomaly'] == False


class TestValidation:
    
    def test_valid_data(self):
        data = {
            'device_id': 'machine-001',
            'sensor_type': 'temperature',
            'value': 75.0,
            'unit': 'celsius'
        }
        is_valid, error = validate_sensor_data(data)
        assert is_valid == True
    
    def test_missing_field(self):
        data = {
            'device_id': 'machine-001',
            'sensor_type': 'temperature'
        }
        is_valid, error = validate_sensor_data(data)
        assert is_valid == False