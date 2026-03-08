# Local Development Setup Guide

## Prerequisites Check

You have:
- ✅ Python 3.13.3
- ✅ Node.js v22.15.0

## Step-by-Step Setup

### Step 1: Backend Setup

Open a **new terminal/command prompt** and run:

```bash
start_backend.bat
```

This will:
1. Install Python dependencies (takes 2-5 minutes first time)
2. Initialize SQLite database
3. Start the FastAPI server on http://localhost:8000

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Frontend Setup

Open a **second terminal/command prompt** and run:

```bash
start_frontend.bat
```

This will:
1. Install Node.js dependencies (takes 2-5 minutes first time)
2. Start the Vite development server on http://localhost:5173

**Wait for this message:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Step 3: Access the Application

Open your browser and go to:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## Manual Setup (If Scripts Don't Work)

### Backend Manual Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database import init_db; init_db()"

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Manual Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
```bash
cd backend
pip install -r requirements.txt
```

**Port 8000 already in use:**
```bash
# Change port in start_backend.bat or use:
uvicorn main:app --reload --port 8001
```

**Database errors:**
```bash
# Delete the database file and reinitialize
del backend\retail_simulator.db
python -c "from database import init_db; init_db()"
```

### Frontend Issues

**"npm not found":**
- Install Node.js from https://nodejs.org/

**Port 5173 already in use:**
- Edit `frontend/vite.config.ts` and change the port number

**Dependencies won't install:**
```bash
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
```

## Quick Test

Once both servers are running:

1. Go to http://localhost:5173
2. Click "Data Upload" in the navigation
3. Fill in the simulation form:
   - Scenario Type: Overstock
   - Time Horizon: 30
   - Affected Products: PROD001, PROD002
   - Base Inventory: 1000
   - Demand Rate: 50
4. Click "Run Simulation"
5. You should see "Simulation completed successfully!"

## Stopping the Servers

Press `CTRL+C` in each terminal window to stop the servers.

## Next Steps

- Upload sample data from `sample_data/market_trends_sample.csv`
- Explore the Analyst Dashboard
- Check out the Executive Dashboard
- View API documentation at http://localhost:8000/docs
