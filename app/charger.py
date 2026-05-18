"""
Charger Aggregate (DDD)
========================
Repræsenterer en ladestander (charger) som et aggregat i Domain-Driven Design.

I VoltEdges domæne er en Charger det centrale forretningsobjekt. Den ejer:
- Sin egen tilstand (status: healthy, warning, critical)
- Sine sensor-målinger (telemetri)
- Sine anomalier
- Forretningslogikken for anomali-detektion

Dette aggregat samler relateret data og adfærd ét sted, så domænelogikken
ikke er spredt ud i forskellige funktioner.
"""

from datetime import datetime


# Domænets threshold-regler (samme som i logic.py)
THRESHOLDS = {
    'temperature': {'warning': 75.0, 'critical': 90.0, 'unit': 'celsius'},
    'pressure':    {'warning': 8.0,  'critical': 12.0, 'unit': 'bar'},
    'vibration':   {'warning': 5.0,  'critical': 10.0, 'unit': 'mm/s'},
    'humidity':    {'warning': 80.0, 'critical': 95.0, 'unit': 'percent'},
}


class Charger:
    """
    Aggregate Root for en ladestander.

    En Charger ejer sine readings, anomalier og sin egen status.
    Forretningslogikken (er en måling kritisk?) lever inde i klassen,
    så domænelogikken ikke er spredt ud i hjælpefunktioner.
    """

    # Statusværdier (value objects)
    STATUS_HEALTHY  = 'healthy'
    STATUS_WARNING  = 'warning'
    STATUS_CRITICAL = 'critical'

    def __init__(self, device_id, location=None):
        self.device_id = device_id
        self.location = location
        self.readings = []      # liste af målinger (SensorReading)
        self.anomalies = []     # liste af registrerede anomalier
        self.status = self.STATUS_HEALTHY

    # --- Forretningsmetoder ---

    def add_reading(self, sensor_type, value, unit=None, timestamp=None):
        """
        Tilføj en ny sensor-måling til denne charger.
        Aggregatet beslutter selv om målingen er en anomali,
        og opdaterer sin egen status.
        """
        reading = {
            'sensor_type': sensor_type,
            'value': value,
            'unit': unit,
            'timestamp': timestamp or datetime.utcnow(),
        }
        self.readings.append(reading)

        # Domænelogik: er denne måling en anomali?
        severity = self._evaluate_severity(sensor_type, value)

        if severity in (self.STATUS_WARNING, self.STATUS_CRITICAL):
            self._register_anomaly(reading, severity)
            self._update_status(severity)

        return reading, severity

    def _evaluate_severity(self, sensor_type, value):
        """
        Privat domæneregel: vurder hvor alvorlig en måling er
        ud fra de definerede thresholds.
        """
        if sensor_type not in THRESHOLDS:
            return self.STATUS_HEALTHY

        limits = THRESHOLDS[sensor_type]

        if value >= limits['critical']:
            return self.STATUS_CRITICAL
        elif value >= limits['warning']:
            return self.STATUS_WARNING
        else:
            return self.STATUS_HEALTHY

    def _register_anomaly(self, reading, severity):
        """Privat: opret en anomali-record på aggregatet."""
        anomaly = {
            'device_id': self.device_id,
            'sensor_type': reading['sensor_type'],
            'value': reading['value'],
            'severity': severity,
            'timestamp': reading['timestamp'],
        }
        self.anomalies.append(anomaly)

    def _update_status(self, severity):
        """
        Privat: opdater charger-status. Critical 'vinder' over warning,
        så vi nedgraderer aldrig fra critical til warning ved nye målinger.
        """
        if severity == self.STATUS_CRITICAL:
            self.status = self.STATUS_CRITICAL
        elif severity == self.STATUS_WARNING and self.status != self.STATUS_CRITICAL:
            self.status = self.STATUS_WARNING

    # --- Query-metoder ---

    def is_healthy(self):
        return self.status == self.STATUS_HEALTHY

    def has_anomalies(self):
        return len(self.anomalies) > 0

    def latest_reading(self):
        return self.readings[-1] if self.readings else None

    def to_dict(self):
        """Serialisér aggregatet til JSON-venlig form."""
        return {
            'device_id': self.device_id,
            'location': self.location,
            'status': self.status,
            'readings_count': len(self.readings),
            'anomalies_count': len(self.anomalies),
        }