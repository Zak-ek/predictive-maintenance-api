# Predictive Maintenance API

> En microservice der modtager telemetri fra ladestandere, analyserer målinger og identificerer anomalier — bygget som en del af **VoltEdge Mobility A/S** Smart EV Charging Platform.

Dette projekt er en MVP (Minimum Viable Product) udviklet som del af 6. semester eksamen i *Design og implementering af digitale løsninger* på Erhvervsakademi København.

---

##  Indhold

- [Forretningskontekst](#-forretningskontekst)
- [Arkitektur](#-arkitektur)
- [Tech Stack](#-tech-stack)
- [Datamodel (ER-diagram)](#-datamodel-er-diagram)
- [Sådan kører du projektet](#-sådan-kører-du-projektet)
- [API Endpoints](#-api-endpoints)
- [DDD: Charger Aggregate](#-ddd-charger-aggregate)
- [Test](#-test)
- [CI/CD](#-cicd)
- [Sikkerhed og Secrets](#-sikkerhed-og-secrets)
- [Projektstruktur](#-projektstruktur)

---

##  Forretningskontekst

VoltEdge Mobility A/S driver en digital platform til styring og optimering af ladeinfrastruktur for elbiler. En af deres centrale udfordringer er **manuel incident-håndtering** og **ustabil telemetri** fra heterogene ladestandere.

Denne service løser problemet ved at:

-  Modtage realtime-telemetri fra ladestandere (temperatur, tryk, vibration, fugtighed)
-  Analysere målinger mod definerede threshold-værdier
-  Automatisk detektere og registrere anomalier
-  Stille data til rådighed for driftspersonale via REST API

Servicen understøtter dermed VoltEdges strategiske mål om **data-driven services** og en mere robust, skalérbar platform.

---

##  Arkitektur

Servicen er bygget som en **microservice** efter Domain-Driven Design (DDD) principper:

​```
┌─────────────────────────────────────┐
│         REST API (Flask)            │  ← routes.py
├─────────────────────────────────────┤
│   Domain Layer (Charger Aggregate)  │  ← charger.py
├─────────────────────────────────────┤
│   Persistence Layer (SQLAlchemy)    │  ← models.py
├─────────────────────────────────────┤
│         MySQL Database              │
└─────────────────────────────────────┘
​```

Hele løsningen kører i **Docker containers** og deployes automatisk via **GitHub Actions CI/CD**.

---

## Tech Stack

| Lag | Teknologi |
|---|---|
| **Backend** | Python 3.11, Flask |
| **ORM** | SQLAlchemy |
| **Database** | MySQL 8.0 |
| **Container** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Test** | pytest |
| **API testing** | Postman |

---

## Datamodel (ER-diagram)

​```mermaid
erDiagram
    SENSOR_READINGS ||--o{ ANOMALIES : "kan have"

    SENSOR_READINGS {
        int id PK
        string device_id "ladestander ID"
        string sensor_type "temperature/pressure/vibration/humidity"
        float value "målt værdi"
        string unit "celsius/bar/mm/s/percent"
        string status "normal/warning/critical"
        datetime timestamp
    }

    ANOMALIES {
        int id PK
        int sensor_reading_id FK
        string device_id
        string sensor_type
        float value
        float threshold "overskredet grænseværdi"
        string severity "warning/critical"
        string message "beskrivelse"
        datetime timestamp
    }
​```

**Forklaring:**

- **`sensor_readings`** opbevarer rådata fra alle telemetri-events
- **`anomalies`** opbevarer kun de målinger, der overskrider thresholds
- Relationen er **1:N** — én sensor-måling kan have én tilknyttet anomali (eller ingen)

---

##  Sådan kører du projektet

### Forudsætninger

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installeret
- [Git](https://git-scm.com/) installeret
- (Valgfrit) [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) til at inspicere databasen
- (Valgfrit) [Postman](https://www.postman.com/downloads/) til at teste API'et

### 1. Klon repository

​```bash
git clone https://github.com/Zak-ek/predictive-maintenance-api.git
cd predictive-maintenance-api
​```

### 2. Opret `.env` fil

Filen `.env` indeholder følsomme oplysninger og er **ikke** med i repoet. Opret den i projektets rod:

​```env
DB_HOST=db
DB_PORT=3306
DB_NAME=predictive_maintenance
DB_USER=root
DB_PASSWORD=dit_password_her
​```

### 3. Start containere

​```bash
docker-compose up --build
​```

Når containerne kører:
- API'et er tilgængeligt på **http://127.0.0.1:5000**
- MySQL-databasen er tilgængelig på **localhost:3306**

### 4. Test at API'et kører

​```bash
curl http://127.0.0.1:5000/api/health
​```

---

##  API Endpoints

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| `GET`  | `/api/health` | Health check — tjek om API'et kører |
| `GET`  | `/api/sensor-data` | Hent alle sensor-målinger |
| `POST` | `/api/sensor-data` | Send ny sensor-måling |
| `GET`  | `/api/anomalies` | Hent alle registrerede anomalier |
| `POST` | `/api/chargers/<device_id>/evaluate` | Evaluér ny måling via Charger-aggregat (DDD) |

### Eksempel: POST `/api/sensor-data`

​```json
{
  "device_id": "CHARGER-001",
  "sensor_type": "temperature",
  "value": 92.5,
  "unit": "celsius"
}
​```

### Postman Collection

Projektet inkluderer en Postman collection: `Postman/Sensor Monitoring API.postman_collection.json`

Importér den i Postman via **Import → Vælg filen**.

---

##  DDD: Charger Aggregate

Servicens forretningslogik er organiseret efter **Domain-Driven Design** med `Charger` som aggregate root:

​```python
charger = Charger(device_id='CHARGER-001', location='København NV')

reading, severity = charger.add_reading(
    sensor_type='temperature',
    value=95.0,
    unit='celsius'
)

print(charger.status)          # 'critical'
print(charger.has_anomalies()) # True
​```

**Hvorfor et aggregat?**

I stedet for at sprede forretningslogikken ud i forskellige hjælpefunktioner, ejer `Charger`-klassen:

-  Sin egen tilstand (`healthy` / `warning` / `critical`)
-  Sine sensor-målinger
-  Sine anomalier
-  Domæneregler for anomali-detektion (`_evaluate_severity`)

Se implementeringen i [`app/charger.py`](app/charger.py).

---

##  Test

Unit tests ligger i `tests/`-mappen og kører automatisk i CI/CD pipelinen.

### Kør tests lokalt:

​```bash
python -m pytest tests/ -v
​```

### Test coverage:

- Input-validering
- Threshold-logik
- Anomali-detektion
- API-endpoints

---

##  CI/CD

Projektet bruger **GitHub Actions** til automatisk:

1.  **Lint** ved hver push
2.  **Kør tests** mod en isoleret MySQL-test database
3.  **Build Docker image**
4.  **Deploy** (klargjort til produktion)

Pipeline-konfigurationen ligger i `.github/workflows/ci.yml`.

### Workflow trigger:
- Push til `main`
- Pull requests til `main`

---

##  Sikkerhed og Secrets

Følsomme oplysninger håndteres som følger:

| Kontekst | Hvor opbevares secrets? |
|----------|------------------------|
| **Lokal udvikling** | `.env` fil (lokal, ikke i Git) |
| **Docker Compose** | Læses fra `.env` via environment variables |
| **CI/CD pipeline** | [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets) |
| **Produktion** | Cloud secret manager (klargjort til Azure Key Vault) |

**Vigtige sikkerhedsforholdsregler:**

-  `.env` er tilføjet til `.gitignore` og kommer **aldrig** med i repoet
-  YAML-filer indeholder **ingen** hardcodede passwords
-  GitHub Secret `DB_PASSWORD` bruges i CI/CD via `${{ secrets.DB_PASSWORD }}`
-  Input-validering på alle POST-endpoints (`validate_sensor_data`)

---

##  Projektstruktur

​```
predictive-maintenance-api/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions pipeline
├── app/
│   ├── __init__.py
│   ├── charger.py              # Charger Aggregate (DDD)
│   ├── database.py             # DB-konfiguration
│   ├── logic.py                # Threshold-regler og validering
│   ├── models.py               # SQLAlchemy models
│   └── routes.py               # REST API endpoints
├── Database/
│   └── database_backup.sql     # Eksempel-data
├── Postman/
│   └── Sensor Monitoring API.postman_collection.json
├── tests/
│   └── test_api.py             # Unit tests
├── .env                        # Lokale secrets (IKKE i Git)
├── .gitignore
├── docker-compose.yml          # Container-orkestrering
├── Dockerfile                  # Image-definition
├── requirements.txt            # Python dependencies
├── run.py                      # App entry point
└── README.md
​```

---

##  Bidragsydere

Udviklet af en gruppe på 4 studerende ved Erhvervsakademi København, 6. semester Økonomi og IT.

---

##  Licens

Dette projekt er udviklet som eksamensopgave og er kun til uddannelsesmæssige formål.