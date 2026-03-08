"""
Data Ingestion Service
Handles CSV, Excel, and JSON data uploads with validation.

Columns are mapped flexibly using keyword aliases — no fixed header format required.
The service recognises common naming variations and auto-maps them to canonical names.
"""
import io
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Chunk / sample settings ───────────────────────────────────────────────────
_CHUNK_SIZE = 50_000
_SAMPLE_ROWS = 500

# ── Column alias map ──────────────────────────────────────────────────────────
# Maps canonical column name → list of recognised aliases (all lowercase).
# The first alias that exists in the uploaded file wins.
COLUMN_ALIASES: Dict[str, List[str]] = {
    "date":                 ["date", "transaction_date", "sale_date", "order_date",
                             "record_date", "time", "timestamp", "period", "day", "week", "month"],
    "region":               ["region", "area", "zone", "territory", "geography", "location"],
    "store_id":             ["store_id", "store", "store_name", "shop_id", "branch", "outlet"],
    "product_id":           ["product_id", "product", "sku", "item_id", "item", "code",
                             "product_code", "article", "barcode"],
    "product_category":     ["product_category", "category", "department", "segment",
                             "product_type", "type", "class"],
    "price":                ["price", "unit_price", "selling_price", "cost", "mrp", "rate",
                             "sale_price", "amount_per_unit"],
    "demand":               ["demand", "forecasted_demand", "forecast", "expected_demand",
                             "demand_forecast", "projected_demand"],
    "actual_sales":         ["actual_sales", "sales", "units_sold", "qty_sold",
                             "quantity_sold", "sold", "sales_qty", "sales_quantity"],
    "quantity":             ["quantity", "qty", "units", "volume", "count",
                             "quantity_sold", "units_sold", "actual_sales", "sales"],
    "lost_sales":           ["lost_sales", "lost_qty", "missed_sales", "stockout_qty",
                             "unfulfilled", "unmet_demand"],
    "revenue":              ["revenue", "sales_revenue", "total_revenue", "turnover",
                             "gross_revenue", "income", "total_sales", "amount",
                             "total_amount", "sales_value", "value"],
    "stock_level":          ["stock_level", "stock", "inventory", "inventory_level",
                             "on_hand", "on_hand_qty", "closing_stock", "ending_inventory",
                             "available_stock", "qty_on_hand"],
    "replenishment_qty":    ["replenishment_qty", "replenishment", "reorder_qty",
                             "order_qty", "po_qty", "replenish"],
    "holding_cost":         ["holding_cost", "carrying_cost", "storage_cost",
                             "inventory_cost", "warehousing_cost"],
    "stockout_flag":        ["stockout_flag", "stockout", "out_of_stock", "oos",
                             "stockout_indicator"],
    "overstock_flag":       ["overstock_flag", "overstock", "excess_stock",
                             "overstock_indicator"],
    "seller_quality_score": ["seller_quality_score", "seller_quality", "quality_score",
                             "supplier_quality", "vendor_quality", "service_level"],
    "promotion_flag":       ["promotion_flag", "promotion", "promo", "on_promo",
                             "is_promo", "discount_flag", "offer_flag"],
}


def _map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise column names and apply alias mapping so any naming convention works.
    Columns that don't match any alias are kept as-is.
    """
    # Step 1: strip whitespace + lowercase
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_")
                  for c in df.columns]

    # Step 2: build a rename map — first matching alias wins
    rename: Dict[str, str] = {}
    available = set(df.columns)
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in available:
            continue  # already has the canonical name
        for alias in aliases:
            if alias in available and alias not in rename:
                rename[alias] = canonical
                break

    if rename:
        logger.info("Column mapping applied: %s", rename)
        df = df.rename(columns=rename)

    return df


class DataIngestionService:
    """Service for ingesting retail data from various sources."""

    def __init__(self):
        self.ingestion_id: Optional[str] = None
        self.data_lineage: List[Dict[str, Any]] = []

    # ── File reading ──────────────────────────────────────────────────────────

    def _read_file_to_df(self, content: bytes, filename: str) -> pd.DataFrame:
        """Auto-detect CSV vs Excel by filename extension and parse."""
        ext = (filename or "").lower().rsplit(".", 1)[-1]
        if ext in ("xlsx", "xls"):
            return pd.read_excel(io.BytesIO(content), engine="openpyxl")
        return pd.read_csv(io.BytesIO(content))

    def _read_large_csv_chunked(self, content: bytes) -> pd.DataFrame:
        """Read a large CSV in chunks to avoid OOM; return combined DataFrame."""
        chunks = pd.read_csv(io.BytesIO(content), chunksize=_CHUNK_SIZE)
        return pd.concat(list(chunks), ignore_index=True)

    # ── Public ingestion API ──────────────────────────────────────────────────

    async def ingest_csv(
        self,
        file_content: bytes,
        data_type: str,
        filename: str = "upload.csv",
    ) -> Dict[str, Any]:
        """
        Ingest CSV or Excel file.
        Column names are mapped flexibly — no fixed header format required.
        """
        self.ingestion_id = str(uuid.uuid4())

        try:
            ext = (filename or "").lower().rsplit(".", 1)[-1]
            fmt = "EXCEL" if ext in ("xlsx", "xls") else "CSV"

            if data_type == "enterprise" and fmt == "CSV":
                df = self._read_large_csv_chunked(file_content)
            else:
                df = self._read_file_to_df(file_content, filename)

            if df.empty:
                return {
                    "success": False,
                    "ingestion_id": self.ingestion_id,
                    "errors": ["The uploaded file is empty."],
                    "data": None,
                }

            # Flexible column mapping — no fixed headers required
            df = _map_columns(df)

            if data_type == "enterprise":
                result = self._process_enterprise(df)
            else:
                result = {
                    "records": self._process_dataframe(df, data_type),
                    "aggregate_stats": None,
                    "category_stats": None,
                    "region_stats": None,
                    "simulation_seeds": None,
                }

            self._track_lineage(data_type, fmt, len(df))

            return {
                "success": True,
                "ingestion_id": self.ingestion_id,
                "data_type": data_type,
                "records_count": len(df),
                "columns_detected": list(df.columns),
                "data": result["records"],
                "aggregate_stats": result.get("aggregate_stats"),
                "category_stats": result.get("category_stats"),
                "region_stats": result.get("region_stats"),
                "simulation_seeds": result.get("simulation_seeds"),
                "store_stats": result.get("store_stats"),
                "lineage": self.data_lineage,
            }

        except Exception as exc:
            logger.error(f"CSV ingestion error: {exc}", exc_info=True)
            return {
                "success": False,
                "ingestion_id": self.ingestion_id,
                "errors": [str(exc)],
                "data": None,
            }

    async def ingest_json(
        self, json_data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Ingest JSON data."""
        self.ingestion_id = str(uuid.uuid4())

        try:
            records = json_data.get("records", [json_data])
            df = pd.DataFrame(records)

            if df.empty:
                return {
                    "success": False,
                    "ingestion_id": self.ingestion_id,
                    "errors": ["No records found in JSON payload."],
                    "data": None,
                }

            df = _map_columns(df)

            if data_type == "enterprise":
                result = self._process_enterprise(df)
            else:
                result = {
                    "records": self._process_dataframe(df, data_type),
                    "aggregate_stats": None,
                    "category_stats": None,
                    "region_stats": None,
                    "simulation_seeds": None,
                }

            self._track_lineage(data_type, "JSON", len(df))

            return {
                "success": True,
                "ingestion_id": self.ingestion_id,
                "data_type": data_type,
                "records_count": len(df),
                "columns_detected": list(df.columns),
                "data": result["records"],
                "aggregate_stats": result.get("aggregate_stats"),
                "category_stats": result.get("category_stats"),
                "region_stats": result.get("region_stats"),
                "simulation_seeds": result.get("simulation_seeds"),
                "store_stats": result.get("store_stats"),
                "lineage": self.data_lineage,
            }

        except Exception as exc:
            logger.error(f"JSON ingestion error: {exc}", exc_info=True)
            return {
                "success": False,
                "ingestion_id": self.ingestion_id,
                "errors": [str(exc)],
                "data": None,
            }

    # ── Standard processing ───────────────────────────────────────────────────

    def _process_dataframe(self, df: pd.DataFrame, data_type: str) -> List[Dict[str, Any]]:
        if "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return json.loads(df.to_json(orient="records", date_format="iso"))

    # ── Enterprise processing ─────────────────────────────────────────────────

    def _process_enterprise(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = df.copy()

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        numeric_cols = [
            "price", "demand", "actual_sales", "lost_sales", "revenue",
            "stock_level", "replenishment_qty", "holding_cost",
            "stockout_flag", "overstock_flag", "seller_quality_score", "promotion_flag",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Also handle 'quantity' as a fallback for 'actual_sales'
        if "actual_sales" not in df.columns and "quantity" in df.columns:
            df["actual_sales"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)

        sample_df = df.head(_SAMPLE_ROWS)
        records = json.loads(sample_df.to_json(orient="records", date_format="iso"))

        aggregate_stats = self._compute_aggregate_stats(df)
        category_stats = self._compute_category_stats(df)
        region_stats = self._compute_region_stats(df)
        simulation_seeds = self._compute_simulation_seeds(df)
        store_stats = self._compute_store_stats(df)

        return {
            "records": records,
            "aggregate_stats": aggregate_stats,
            "category_stats": category_stats,
            "region_stats": region_stats,
            "simulation_seeds": simulation_seeds,
            "store_stats": store_stats,
        }

    @staticmethod
    def _safe_col(df: pd.DataFrame, col: str, default=0) -> pd.Series:
        """Return the column if it exists, otherwise a series of the default value."""
        return df[col] if col in df.columns else pd.Series([default] * len(df), index=df.index)

    @staticmethod
    def _compute_aggregate_stats(df: pd.DataFrame) -> Dict[str, Any]:
        def scol(c):
            return df[c] if c in df.columns else pd.Series([0] * len(df), index=df.index)

        revenue = scol("revenue")
        lost_sales = scol("lost_sales")
        price = scol("price")
        demand_s = scol("demand")
        actual_sales = scol("actual_sales") if "actual_sales" in df.columns else scol("quantity")
        holding_cost = scol("holding_cost")

        total_revenue = float(revenue.sum())
        total_lost_sales_value = float((lost_sales * price).sum())
        total_holding_cost = float(holding_cost.sum())
        total_demand = int(demand_s.sum())
        total_actual = int(actual_sales.sum())
        fulfillment_rate = total_actual / total_demand if total_demand > 0 else 1.0

        date_range = None
        if "date" in df.columns and df["date"].notna().any():
            date_range = {
                "start": str(df["date"].min().date()),
                "end": str(df["date"].max().date()),
                "days": int((df["date"].max() - df["date"].min()).days + 1),
            }

        return {
            "total_records": len(df),
            "date_range": date_range,
            "unique_products": int(df["product_id"].nunique()) if "product_id" in df.columns else None,
            "unique_stores": int(df["store_id"].nunique()) if "store_id" in df.columns else None,
            "unique_regions": int(df["region"].nunique()) if "region" in df.columns else None,
            "unique_categories": int(df["product_category"].nunique()) if "product_category" in df.columns else None,
            "total_revenue": round(total_revenue, 2),
            "total_lost_sales_value": round(total_lost_sales_value, 2),
            "total_holding_cost": round(total_holding_cost, 2),
            "fulfillment_rate": round(fulfillment_rate, 4),
            "stockout_rate": round(float(scol("stockout_flag").mean()), 4) if "stockout_flag" in df.columns else None,
            "overstock_rate": round(float(scol("overstock_flag").mean()), 4) if "overstock_flag" in df.columns else None,
            "avg_seller_quality": round(float(scol("seller_quality_score").mean()), 4) if "seller_quality_score" in df.columns else None,
            "promotion_rate": round(float(scol("promotion_flag").mean()), 4) if "promotion_flag" in df.columns else None,
        }

    @staticmethod
    def _compute_category_stats(df: pd.DataFrame) -> List[Dict[str, Any]]:
        if "product_category" not in df.columns:
            return []

        def scol(grp, c):
            return grp[c] if c in grp.columns else pd.Series([0] * len(grp), index=grp.index)

        grouped = df.groupby("product_category")
        stats = []
        for cat, grp in grouped:
            demand_series = grp.groupby("date")["demand"].sum() if ("date" in grp.columns and "demand" in grp.columns) else scol(grp, "demand")
            cv = float(demand_series.std() / demand_series.mean()) if "demand" in grp.columns and demand_series.mean() > 0 else 0.0
            total_demand = int(scol(grp, "demand").sum())
            total_lost = float((scol(grp, "lost_sales") * scol(grp, "price")).sum())
            actual_sales = grp["actual_sales"] if "actual_sales" in grp.columns else scol(grp, "quantity")
            stats.append({
                "product_category": str(cat),
                "avg_demand": round(float(scol(grp, "demand").mean()), 2),
                "demand_cv": round(cv, 4),
                "avg_price": round(float(scol(grp, "price").mean()), 2),
                "avg_stock_level": round(float(scol(grp, "stock_level").mean()), 2),
                "avg_holding_cost": round(float(scol(grp, "holding_cost").mean()), 2),
                "total_holding_cost": round(float(scol(grp, "holding_cost").sum()), 2),
                "stockout_rate": round(float(scol(grp, "stockout_flag").mean()), 4),
                "overstock_rate": round(float(scol(grp, "overstock_flag").mean()), 4),
                "avg_lost_sales_units": round(float(scol(grp, "lost_sales").mean()), 4),
                "lost_sales_value": round(total_lost, 2),
                "avg_seller_quality": round(float(scol(grp, "seller_quality_score").mean()), 4),
                "promotion_rate": round(float(scol(grp, "promotion_flag").mean()), 4),
                "total_revenue": round(float(scol(grp, "revenue").sum()), 2),
                "fulfillment_rate": round(
                    float(actual_sales.sum()) / total_demand if total_demand > 0 else 1.0, 4
                ),
            })
        return stats

    @staticmethod
    def _compute_region_stats(df: pd.DataFrame) -> List[Dict[str, Any]]:
        if "region" not in df.columns:
            return []

        def scol(grp, c):
            return grp[c] if c in grp.columns else pd.Series([0] * len(grp), index=grp.index)

        grouped = df.groupby("region")
        stats = []
        for region, grp in grouped:
            total_demand = int(scol(grp, "demand").sum())
            actual_sales = grp["actual_sales"] if "actual_sales" in grp.columns else scol(grp, "quantity")
            stats.append({
                "region": str(region),
                "unique_stores": int(grp["store_id"].nunique()) if "store_id" in grp.columns else None,
                "avg_demand": round(float(scol(grp, "demand").mean()), 2),
                "total_revenue": round(float(scol(grp, "revenue").sum()), 2),
                "total_holding_cost": round(float(scol(grp, "holding_cost").sum()), 2),
                "stockout_rate": round(float(scol(grp, "stockout_flag").mean()), 4),
                "overstock_rate": round(float(scol(grp, "overstock_flag").mean()), 4),
                "avg_lost_sales_units": round(float(scol(grp, "lost_sales").mean()), 4),
                "lost_sales_value": round(float((scol(grp, "lost_sales") * scol(grp, "price")).sum()), 2),
                "avg_seller_quality": round(float(scol(grp, "seller_quality_score").mean()), 4),
                "fulfillment_rate": round(
                    float(actual_sales.sum()) / total_demand if total_demand > 0 else 1.0, 4
                ),
            })
        return stats

    @staticmethod
    def _compute_store_stats(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Per store × product_category aggregated signals for transfer optimization.
        Returns a flat list — one entry per (store_id, product_category) pair.
        """
        grouped = df.groupby(["store_id", "product_category"])
        stats = []
        for (store_id, category), grp in grouped:
            total_demand = int(grp["demand"].sum())
            region = str(grp["region"].iloc[0]) if "region" in grp.columns else ""
            stats.append({
                "store_id": str(store_id),
                "region": region,
                "product_category": str(category),
                "avg_stock_level": round(float(grp["stock_level"].mean()), 2),
                "avg_demand": round(float(grp["demand"].mean()), 2),
                "avg_price": round(float(grp["price"].mean()), 2),
                "avg_holding_cost": round(float(grp["holding_cost"].mean()), 4),
                "stockout_rate": round(float(grp["stockout_flag"].mean()), 4),
                "overstock_rate": round(float(grp["overstock_flag"].mean()), 4),
                "avg_lost_sales_units": round(float(grp["lost_sales"].mean()), 4),
                "total_revenue": round(float(grp["revenue"].sum()), 2),
                "fulfillment_rate": round(
                    float(grp["actual_sales"].sum()) / total_demand if total_demand > 0 else 1.0, 4
                ),
            })
        return stats

    @staticmethod
    def _compute_simulation_seeds(df: pd.DataFrame) -> List[Dict[str, Any]]:
        if "product_category" not in df.columns:
            return []

        def scol(grp, c):
            return grp[c] if c in grp.columns else pd.Series([0] * len(grp), index=grp.index)

        grouped = df.groupby("product_category")
        seeds = []
        for cat, grp in grouped:
            avg_demand = float(scol(grp, "demand").mean())
            std_demand = float(scol(grp, "demand").std()) if "demand" in grp.columns else 0.0
            avg_price = float(scol(grp, "price").mean())
            avg_stock = float(scol(grp, "stock_level").mean())
            stockout_rate = float(scol(grp, "stockout_flag").mean()) if "stockout_flag" in grp.columns else 0.0
            overstock_rate = float(scol(grp, "overstock_flag").mean()) if "overstock_flag" in grp.columns else 0.0
            promo_rate = float(scol(grp, "promotion_flag").mean()) if "promotion_flag" in grp.columns else 0.0

            if stockout_rate > 0.05:
                dominant_scenario = "STOCKOUT"
            elif overstock_rate > 0.50:
                dominant_scenario = "OVERSTOCK"
            elif promo_rate > 0.20:
                dominant_scenario = "SEASONAL_MISMATCH"
            else:
                dominant_scenario = "OVERSTOCK"

            seeds.append({
                "product_category": str(cat),
                "dominant_scenario": dominant_scenario,
                "simulation_parameters": {
                    "demand_rate": round(avg_demand, 2),
                    "demand_std": round(std_demand, 2),
                    "demand_cv": round(std_demand / avg_demand if avg_demand > 0 else 0, 4),
                    "stockout_factor": round(max(0.1, 1.0 - stockout_rate * 10), 2),
                    "overstock_factor": round(min(3.0, 1.0 + overstock_rate * 2), 2),
                    "price_elasticity": 1.0,
                    "fulfillment_capacity": round(
                        float(scol(grp, "seller_quality_score").mean()) + 0.5, 2
                    ),
                },
                "initial_conditions": {
                    "base_inventory": round(avg_stock, 0),
                    "unit_price": round(avg_price, 2),
                },
            })
        return seeds

    # ── Lineage tracking ──────────────────────────────────────────────────────

    def _track_lineage(self, data_type: str, source_format: str, record_count: int):
        self.data_lineage.append({
            "ingestion_id": self.ingestion_id,
            "data_type": data_type,
            "source_format": source_format,
            "record_count": record_count,
            "timestamp": datetime.utcnow().isoformat(),
        })
