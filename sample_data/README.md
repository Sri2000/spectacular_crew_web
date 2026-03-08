# Sample Data Files

This directory contains sample CSV files to help you get started with the Retail Failure Simulator.

## Files

### market_trends_sample.csv
Sample market trend data showing demand forecasts for Electronics and Clothing categories over 30 days.

**Format:**
- `date`: Date in YYYY-MM-DD format
- `product_category`: Product category name
- `demand_forecast`: Forecasted demand (units)

## Usage

1. Navigate to the **Data Upload** page in the application
2. Click "Upload CSV" under "Market Trends"
3. Select `market_trends_sample.csv`
4. Wait for successful upload confirmation
5. Go to **Analyst Dashboard** to see risk analysis results

## Creating Your Own Data Files

### Sales Data Format
```csv
date,product_id,quantity,revenue
2024-01-01,PROD001,100,5000
2024-01-02,PROD001,95,4750
```

### Inventory Data Format
```csv
date,product_id,stock_level
2024-01-01,PROD001,1000
2024-01-02,PROD001,900
```

### Market Trends Format
```csv
date,product_category,demand_forecast
2024-01-01,Electronics,500
2024-01-02,Electronics,520
```

## Tips

- Ensure dates are in YYYY-MM-DD format
- Use consistent product IDs and category names
- Include at least 7-30 days of data for meaningful analysis
- Higher variance in demand forecasts will trigger more risk alerts
