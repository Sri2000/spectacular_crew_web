# RetailSense AI — Retail Failure Simulator & Market Intelligence Platform

> Built for the **AWS AI for Bharat Hackathon** · Team SpectacularCrew

A pre-emptive decision-making platform that simulates retail failure scenarios, propagates risk across business functions, and surfaces AI-generated mitigation strategies — enabling retailers to act before problems escalate.

---

## Features

- **Risk Engine** — Detects seasonal demand mismatches and computes real-time risk scores per product category
- **Failure Simulator** — Models overstock, stockout, and seasonal mismatch scenarios with time-series projections
- **Propagation Engine** — Traces failure impact across interconnected business functions using graph analysis
- **AI Reasoning Engine** — Generates executive summaries and ranked mitigation strategies (AWS Bedrock-ready)
- **Stock Transfer Optimizer** — Recommends cross-store inventory rebalancing to prevent waste and shortages
- **Fleet Dashboard** — Monitors logistics and distribution health
- **Store Drill-Through** — Zooms into individual store performance and risk exposure
- **Dual Dashboards**
  - *Analyst Dashboard* — Full risk monitoring, scenario history, and detailed analysis
  - *Executive Dashboard* — Mobile-responsive 30-second decision flows

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11), SQLAlchemy, Alembic, SQLite / MySQL 8.0 |
| Data & ML | Pandas, NumPy, Scikit-learn, NetworkX |
| Cloud | AWS S3 (data ingestion), AWS DynamoDB (event store), AWS Bedrock (AI — pluggable) |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Recharts, React Router, Axios |
| Infrastructure | Docker, Docker Compose |

---

## Quick Start

### Option 1 — Docker (Recommended)

**Windows**
```bash
setup.bat
```

**Linux / macOS**
```bash
chmod +x setup.sh && ./setup.sh
```

The script checks for Docker, creates environment files, starts all services, and seeds the database.

### Option 2 — Docker Compose Manual

```bash
cp backend/.env.example backend/.env   # configure your env
docker-compose up -d                   # start all services
docker-compose logs -f                 # tail logs
docker-compose down                    # stop
```

### Access

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |
| MySQL | localhost:3306 (root / password) |

---

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+
- Node.js 20+
- MySQL 8.0+ (or use the bundled SQLite fallback)

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL
alembic upgrade head           # run migrations
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
ai_bharat/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Configuration management
│   ├── database.py                 # DB connection & session
│   ├── models/                     # SQLAlchemy ORM models
│   ├── schemas/                    # Pydantic request/response schemas
│   ├── engines/                    # Core analytical engines
│   │   ├── ai_reasoning_engine.py
│   │   ├── mitigation_engine.py
│   │   ├── propagation_engine.py
│   │   ├── risk_engine.py
│   │   ├── simulation_engine.py
│   │   └── transfer_engine.py
│   ├── services/                   # External integrations
│   │   ├── s3_service.py
│   │   ├── dynamodb_service.py
│   │   ├── seasonal_risk_engine.py
│   │   ├── failure_simulator.py
│   │   └── impact_analyzer.py
│   ├── api/                        # Route handlers
│   │   ├── analysis_routes.py
│   │   ├── data_ingestion_routes.py
│   │   └── transfer_routes.py
│   ├── alembic/                    # DB migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── AnalystDashboard.tsx
│       │   ├── ExecutiveDashboard.tsx
│       │   ├── SimulateDashboard.tsx
│       │   ├── FleetDashboard.tsx
│       │   ├── StoreDashboard.tsx
│       │   ├── StoreTransfer.tsx
│       │   ├── DataUpload.tsx
│       │   └── ScenarioDetails.tsx
│       ├── components/
│       ├── services/api.ts
│       ├── App.tsx
│       └── main.tsx
├── docker-compose.yml
├── setup.sh / setup.bat
└── README.md
```

---

## API Reference

### Data Ingestion

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/data/upload/csv/{data_type}` | Upload CSV (sales / inventory / market_trends) |
| POST | `/api/data/upload/json/{data_type}` | Upload JSON data |

### Analysis & Simulation

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analysis/risk/analyze` | Analyze seasonal risks |
| POST | `/api/analysis/simulate` | Run a failure simulation |
| GET | `/api/analysis/scenarios` | List all scenarios |
| GET | `/api/analysis/scenarios/{id}` | Get scenario details |
| GET | `/api/analysis/risks` | List all risk assessments |

### Stock Transfer

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/transfer/optimize` | Run cross-store transfer optimization |

Full interactive docs at `/docs` when the backend is running.

---

## Usage Guide

### 1. Upload Data

Go to **Data Upload** and provide CSV files in these formats:

**Sales** (`date, product_id, quantity, revenue`)
```csv
2024-01-01,PROD001,100,5000
```

**Inventory** (`date, product_id, stock_level`)
```csv
2024-01-01,PROD001,1000
```

**Market Trends** (`date, product_category, demand_forecast`)
```csv
2024-01-01,Electronics,500
```

### 2. Run a Simulation

On the **Simulate Dashboard**:
1. Select scenario type: `Overstock`, `Stockout`, or `Seasonal Mismatch`
2. Set time horizon, affected products, base inventory, and demand rate
3. Click **Run Simulation**

### 3. Interpret Results

- **Analyst Dashboard** — Risk scores, trends, and raw scenario data
- **Executive Dashboard** — 3-point summary (Revenue Risk · Market Reason · Urgency) with ranked mitigation actions
- **Scenario Details** — Time-series charts, propagation impact, and mitigation cost/timeline estimates
- **Store Transfer** — Cross-store rebalancing recommendations

---

## Troubleshooting

**Services won't start**
```bash
docker-compose down -v && docker-compose up -d --build
```

**Database connection error**
```bash
docker-compose logs mysql     # inspect MySQL logs
docker-compose down -v        # reset volumes and retry
```

**Frontend not loading**
```bash
docker-compose up -d --build frontend
# or locally:
rm -rf node_modules && npm install && npm run dev
```

**Backend won't start locally**
- Confirm MySQL is running and `DATABASE_URL` in `.env` is correct
- Run `pip install -r requirements.txt` again to ensure all deps are present

---

## Roadmap

- [ ] AWS Bedrock live integration for AI reasoning
- [ ] WebSocket real-time risk updates
- [ ] User authentication & role-based access
- [ ] PDF report export
- [ ] Email / SMS alerts for critical risk thresholds
- [ ] Multi-tenant support

---

## License

Proprietary — All rights reserved · Team SpectacularCrew
