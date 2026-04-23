THRESHOLDS = {
    'temperature': {
        'warning': 75.0,
        'critical': 90.0,
        'unit': 'celsius'
    },
    'pressure': {
        'warning': 8.0,
        'critical': 12.0,
        'unit': 'bar'
    },
    'vibration': {
        'warning': 5.0,
        'critical': 10.0,
        'unit': 'mm/s'
    },
    'humidity': {
        'warning': 80.0,
        'critical': 95.0,
        'unit': 'percent'
    }
}


def check_threshold(sensor_type, value):
    if sensor_type not in THRESHOLDS:
        return {
            'is_anomaly': False,
            'severity': 'normal',
            'threshold': None,
            'message': f'Ukendt sensortype: {sensor_type}'
        }
    
    limits = THRESHOLDS[sensor_type]
    
    if value >= limits['critical']:
        return {
            'is_anomaly': True,
            'severity': 'critical',
            'threshold': limits['critical'],
            'message': (
                f'KRITISK: {sensor_type} er {value} {limits["unit"]} '
                f'- overskrider kritisk grænse på {limits["critical"]} {limits["unit"]}! '
                f'Øjeblikkelig handling påkrævet.'
            )
        }
    elif value >= limits['warning']:
        return {
            'is_anomaly': True,
            'severity': 'warning',
            'threshold': limits['warning'],
            'message': (
                f'ADVARSEL: {sensor_type} er {value} {limits["unit"]} '
                f'- overskrider advarselsgrænse på {limits["warning"]} {limits["unit"]}. '
                f'Kontrollér maskinen snarest.'
            )
        }
    else:
        return {
            'is_anomaly': False,
            'severity': 'normal',
            'threshold': None,
            'message': f'{sensor_type} er normal: {value} {limits["unit"]}'
        }


def validate_sensor_data(data):
    required_fields = ['device_id', 'sensor_type', 'value', 'unit']
    
    for field in required_fields:
        if field not in data:
            return False, f'Manglende felt: {field}'
    
    try:
        float(data['value'])
    except (TypeError, ValueError):
        return False, 'Feltet "value" skal være et tal'
    
    return True, None