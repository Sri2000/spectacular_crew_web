import pandas as pd
import numpy as np
from datetime import datetime
import random

np.random.seed(42)

# -----------------------------
# CONFIGURATION
# -----------------------------
START_DATE = "2023-01-01"
END_DATE = "2024-06-30"
NUM_PRODUCTS = 40
NUM_REGIONS = 3
STORES_PER_REGION = 4

BASE_PRICE_RANGE = (300, 3000)
BASE_DEMAND_RANGE = (20, 150)
HOLDING_COST_RATE = 0.015
INFLATION_RATE = 0.06  # annual inflation
FULFILLMENT_CAPACITY_PER_STORE = 500

dates = pd.date_range(START_DATE, END_DATE, freq="D")

regions = ["North", "South", "West"]
categories = ["Electronics", "Apparel", "Home", "Grocery", "Sports"]

products = [f"P{i:03d}" for i in range(1, NUM_PRODUCTS + 1)]

# -----------------------------
# PRODUCT MASTER DATA
# -----------------------------
product_master = {}

for p in products:
    product_master[p] = {
        "category": random.choice(categories),
        "base_price": np.random.randint(*BASE_PRICE_RANGE),
        "base_demand": np.random.randint(*BASE_DEMAND_RANGE),
        "supplier_lead_time": np.random.randint(5, 20),
        "seller_quality": np.random.uniform(0.8, 1.0)  # 1.0 = perfect
    }

# -----------------------------
# DEMAND CORRELATION FACTOR
# -----------------------------
regional_correlation = {
    "North": 1.0,
    "South": 0.95,
    "West": 1.05
}

# -----------------------------
# GENERATE DATA
# -----------------------------
data = []

for region in regions:
    for store_id in range(1, STORES_PER_REGION + 1):
        store_name = f"{region}_S{store_id}"

        for product in products:

            stock_level = np.random.randint(800, 2000)
            pending_replenishment = []

            for date in dates:

                # Apply inflation-adjusted pricing
                days_passed = (date - pd.to_datetime(START_DATE)).days
                inflation_multiplier = 1 + (INFLATION_RATE * days_passed / 365)

                base_price = product_master[product]["base_price"]
                price = base_price * inflation_multiplier

                # Seasonality
                month_factor = 1 + 0.3 * np.sin(2 * np.pi * date.month / 12)

                # Promotion
                promotion_flag = np.random.choice([0, 1], p=[0.85, 0.15])
                promo_boost = 0.25 if promotion_flag else 0

                # Seller degradation shock
                if np.random.rand() < 0.01:
                    product_master[product]["seller_quality"] *= 0.9

                seller_quality = product_master[product]["seller_quality"]

                base_demand = product_master[product]["base_demand"]

                # Correlated regional demand
                regional_factor = regional_correlation[region]

                demand = base_demand * month_factor * regional_factor
                demand *= (1 + promo_boost)
                demand *= seller_quality
                demand *= np.random.normal(1, 0.1)

                demand = max(int(demand), 0)

                # Fulfillment capacity constraint
                fulfillment_capacity = FULFILLMENT_CAPACITY_PER_STORE
                demand = min(demand, fulfillment_capacity)

                # Process incoming replenishment
                for delivery in pending_replenishment[:]:
                    if delivery["date"] == date:
                        stock_level += delivery["qty"]
                        pending_replenishment.remove(delivery)

                # Stockout handling
                actual_sales = min(demand, stock_level)
                lost_sales = max(demand - stock_level, 0)
                stockout_flag = 1 if lost_sales > 0 else 0

                revenue = actual_sales * price
                holding_cost = stock_level * price * HOLDING_COST_RATE

                # Reorder logic
                reorder_point = 400
                replenishment_qty = 0

                if stock_level < reorder_point:
                    replenishment_qty = np.random.randint(800, 1500)

                    lead_time = product_master[product]["supplier_lead_time"]
                    delay = np.random.choice([0, 2, 5], p=[0.8, 0.15, 0.05])

                    delivery_date = date + pd.Timedelta(days=lead_time + delay)

                    pending_replenishment.append({
                        "date": delivery_date,
                        "qty": replenishment_qty
                    })

                stock_level = stock_level - actual_sales

                overstock_flag = 1 if stock_level > 2500 else 0

                data.append([
                    date,
                    region,
                    store_name,
                    product,
                    product_master[product]["category"],
                    round(price, 2),
                    demand,
                    actual_sales,
                    lost_sales,
                    revenue,
                    stock_level,
                    replenishment_qty,
                    holding_cost,
                    stockout_flag,
                    overstock_flag,
                    seller_quality,
                    promotion_flag
                ])

# -----------------------------
# DATAFRAME
# -----------------------------
columns = [
    "date",
    "region",
    "store_id",
    "product_id",
    "product_category",
    "price",
    "demand",
    "actual_sales",
    "lost_sales",
    "revenue",
    "stock_level",
    "replenishment_qty",
    "holding_cost",
    "stockout_flag",
    "overstock_flag",
    "seller_quality_score",
    "promotion_flag"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv("enterprise_retail_risk_dataset.csv", index=False)

print("Enterprise retail dataset generated successfully!")
print("Total rows:", len(df))
print(df.head())