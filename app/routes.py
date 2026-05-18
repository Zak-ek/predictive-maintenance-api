from flask import Blueprint, request, jsonify
from app.database import db
from app.models import SensorReading, Anomaly
from app.logic import check_threshold, validate_sensor_data
from app.charger import Charger
from datetime import datetime

api = Blueprint('api', __name__)


@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'Predictive Maintenance API kører',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@api.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Ingen JSON data modtaget'}), 400
    
    is_valid, error_message = validate_sensor_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    result = check_threshold(data['sensor_type'], float(data['value']))
    
    reading = SensorReading(
        device_id=data['device_id'],
        sensor_type=data['sensor_type'],
        value=float(data['value']),
        unit=data['unit'],
        status='anomaly' if result['is_anomaly'] else 'normal'
    )
    db.session.add(reading)
    db.session.flush()
    
    if result['is_anomaly']:
        anomaly = Anomaly(
            sensor_reading_id=reading.id,
            device_id=data['device_id'],
            sensor_type=data['sensor_type'],
            value=float(data['value']),
            threshold=result['threshold'],
            message=result['message'],
            severity=result['severity']
        )
        db.session.add(anomaly)
    
    db.session.commit()
    
    response = {
        'reading_id': reading.id,
        'device_id': data['device_id'],
        'sensor_type': data['sensor_type'],
        'value': float(data['value']),
        'unit': data['unit'],
        'status': reading.status,
        'analysis': result['message'],
        'severity': result['severity'],
        'timestamp': reading.timestamp.isoformat()
    }
    
    status_code = 201 if not result['is_anomaly'] else 200
    return jsonify(response), status_code


@api.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    query = SensorReading.query
    
    device_id = request.args.get('device_id')
    sensor_type = request.args.get('sensor_type')
    status = request.args.get('status')
    
    if device_id:
        query = query.filter_by(device_id=device_id)
    if sensor_type:
        query = query.filter_by(sensor_type=sensor_type)
    if status:
        query = query.filter_by(status=status)
    
    readings = query.order_by(SensorReading.timestamp.desc()).limit(100).all()
    
    return jsonify({
        'count': len(readings),
        'readings': [r.to_dict() for r in readings]
    }), 200


@api.route('/anomalies', methods=['GET'])
def get_anomalies():
    anomalies = Anomaly.query.order_by(Anomaly.timestamp.desc()).limit(100).all()
    
    return jsonify({
        'count': len(anomalies),
        'anomalies': [a.to_dict() for a in anomalies]
    }), 200

# ============================================================
# Endpoint der bruger Charger Aggregate (DDD)
# ============================================================
# Dette endpoint demonstrerer brugen af Charger-aggregatet.
# I stedet for at lade routes/logic håndtere forretningslogikken,
# delegerer vi til Charger-objektet, som ejer reglerne.

@api.route('/chargers/<device_id>/evaluate', methods=['POST'])
def evaluate_charger_reading(device_id):
    """
    Modtag en sensor-måling, og lad Charger-aggregatet vurdere
    om målingen er en anomali. Aggregatet styrer selv sin status.
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Ingen JSON data modtaget'}), 400

    # Valider input
    is_valid, error_message = validate_sensor_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400

    # Opret Charger-aggregat (in-memory for denne request)
    charger = Charger(device_id=device_id, location=data.get('location'))

    # Lad aggregatet håndtere måling + anomali-detektion
    reading, severity = charger.add_reading(
        sensor_type=data['sensor_type'],
        value=float(data['value']),
        unit=data.get('unit'),
    )

    # Persistér via eksisterende SensorReading-model
    db_reading = SensorReading(
        device_id=device_id,
        sensor_type=data['sensor_type'],
        value=float(data['value']),
        unit=data.get('unit'),
        status=severity,
    )
    db.session.add(db_reading)
    db.session.commit()

    # Hvis aggregatet registrerede en anomali, persistér den også
    if charger.has_anomalies():
        latest_anomaly = charger.anomalies[-1]
        db_anomaly = Anomaly(
            sensor_reading_id=db_reading.id,
            device_id=device_id,
            sensor_type=latest_anomaly['sensor_type'],
            value=latest_anomaly['value'],
            severity=latest_anomaly['severity'],
            message=f"Charger {device_id} reported {latest_anomaly['severity']} level",
        )
        db.session.add(db_anomaly)
        db.session.commit()

    return jsonify({
        'charger': charger.to_dict(),
        'reading_severity': severity,
        'is_anomaly': severity != Charger.STATUS_HEALTHY,
    }), 200