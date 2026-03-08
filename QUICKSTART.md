# 🚀 Quick Start Guide

Get the Retail Failure Simulator running in 5 minutes!

## Step 1: Start the Application

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

## Step 2: Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## Step 3: Try It Out

### Option A: Quick Demo with Sample Data

1. **Go to Data Upload page** (click "Data Upload" in navigation)

2. **Run a simulation** without uploading data:
   - Scenario Type: `Overstock`
   - Time Horizon: `30` days
   - Affected Products: `PROD001, PROD002, PROD003`
   - Base Inventory: `1000`
   - Demand Rate: `50`
   - Click "Run Simulation"

3. **View Results**:
   - Click "View detailed results" link
   - See time-series charts, impact analysis, and mitigation strategies

4. **Check Executive Dashboard**:
   - Click "Executive Dashboard" in navigation
   - See 3-point executive summary with revenue risk, market reason, and urgency
   - Review ranked mitigation strategies

### Option B: Upload Your Own Data

1. **Prepare CSV files** with these formats:

**Sales Data (sales.csv):**
```csv
date,product_id,quantity,revenue
2024-01-01,PROD001,100,5000
2024-01-02,PROD001,95,4750
```

**Inventory Data (inventory.csv):**
```csv
date,product_id,stock_level
2024-01-01,PROD001,1000
2024-01-02,PROD001,900
```

**Market Trends (market_trends.csv):**
```csv
date,product_category,demand_forecast
2024-01-01,Electronics,500
2024-01-02,Electronics,520
```

2. **Upload files** on the Data Upload page

3. **Run simulation** with your data

## Step 4: Explore Features

### Analyst Dashboard
- View real-time risk scores
- Monitor all product categories
- See detailed risk assessments
- Track recent scenarios

### Executive Dashboard
- Get 30-second decision flows
- See impact propagation scores
- Review mitigation strategies with trade-offs
- Make informed decisions quickly

### Scenario Details
- Interactive time-series charts
- Business function impact analysis
- Detailed mitigation recommendations
- Cost and timeline estimates

## Common Commands

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Port Already in Use
If ports 3306, 5173, or 8000 are already in use:

1. Stop the conflicting service
2. Or edit `docker-compose.yml` to use different ports

### Database Connection Error
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Frontend Not Loading
```bash
# Rebuild frontend
docker-compose up -d --build frontend
```

## Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Run Multiple Scenarios**: Compare different failure types
3. **Analyze Impact Patterns**: See how failures propagate
4. **Review Mitigation Strategies**: Understand trade-offs

## Need Help?

- Check the full README.md for detailed documentation
- Review API docs at http://localhost:8000/docs
- Check Docker logs: `docker-compose logs -f`

---

**Ready to simulate retail failures and make proactive decisions!** 🎯
