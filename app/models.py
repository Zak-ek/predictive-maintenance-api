from datetime import datetime
from app.database import db

class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='normal')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }


class Anomaly(db.Model):
    __tablename__ = 'anomalies'
    
    id = db.Column(db.Integer, primary_key=True)
    sensor_reading_id = db.Column(db.Integer, db.ForeignKey('sensor_readings.id'))
    device_id = db.Column(db.String(100), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    message = db.Column(db.String(255))
    severity = db.Column(db.String(20), default='warning')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sensor_reading_id': self.sensor_reading_id,
            'device_id': self.device_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'threshold': self.threshold,
            'message': self.message,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat()
        }