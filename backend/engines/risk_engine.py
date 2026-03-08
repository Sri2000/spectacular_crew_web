"""
Risk Detection Engine
Two operational modes:

1. Standard mode — analyze_risks(records)
   Inputs: generic market-data / sales records
   Uses: CV, rolling deviation, seasonal volatility, demand-change

2. Enterprise mode — analyze_enterprise_risks(records | category_stats)
   Inputs: enterprise dataset rows OR pre-aggregated category_stats from
           DataIngestionService (recommended for large files)
   Uses direct risk signals already present in the data:
     stockout_flag, overstock_flag, lost_sales, holding_cost,
     seller_quality_score, promotion_flag, demand CV, rolling deviation
   Returns richer RiskAssessment objects with financial exposure metrics.

Output model (both modes):
  RiskAssessment:
    product_category, risk_type, variance_score, demand_change_score,
    risk_score, severity_level, confidence_level,
    contributing_factors, historical_comparison
"""
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Severity thresholds ───────────────────────────────────────────────────────
_SEVERITY = [
    (0.70, "CRITICAL"),
    (0.50, "HIGH"),
    (0.30, "MEDIUM"),
    (0.00, "LOW"),
]

def _severity(score: float) -> str:
    for threshold, label in _SEVERITY:
        if score >= threshold:
            return label
    return "LOW"

def _classify_risk_type(demand_change: float, cv: float,
                        stockout_rate: float = 0.0, overstock_rate: float = 0.0) -> str:
    """Classify dominant risk type. Enterprise signals take priority."""
    if stockout_rate > 0.02:
        return "STOCKOUT"
    if overstock_rate > 0.40:
        return "OVERSTOCK"
    if cv > 0.40:
        return "SEASONAL_MISMATCH"
    if demand_change > 0.15:
        return "STOCKOUT"
    if demand_change < -0.15:
        return "OVERSTOCK"
    return "SEASONAL_MISMATCH"


class RiskEngine:
    """
    Deterministic retail risk detection engine.

    Standard usage:
        await engine.analyze_risks(records)          # generic records
        await engine.analyze_enterprise_risks(records)   # enterprise 17-col records
        await engine.analyze_from_category_stats(stats)  # pre-aggregated stats
    """

    # ── Standard mode ─────────────────────────────────────────────────────────

    async def analyze_risks(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze generic market/sales records using statistical methods."""
        if not records:
            logger.warning("RiskEngine.analyze_risks: empty records")
            return []
        try:
            df = self._to_standard_df(records)
            return self._compute_standard_risks(df)
        except Exception as exc:
            logger.error(f"RiskEngine.analyze_risks error: {exc}", exc_info=True)
            return []

    # ── Enterprise mode ───────────────────────────────────────────────────────

    async def analyze_enterprise_risks(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze enterprise 17-column records.
        Prefers direct risk signals (stockout_flag, overstock_flag, etc.)
        combined with statistical demand analysis.
        """
        if not records:
            logger.warning("RiskEngine.analyze_enterprise_risks: empty records")
            return []
        try:
            df = self._to_enterprise_df(records)
            return self._compute_enterprise_risks(df)
        except Exception as exc:
            logger.error(f"RiskEngine.analyze_enterprise_risks error: {exc}", exc_info=True)
            return []

    async def analyze_from_category_stats(
        self, category_stats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze from pre-aggregated category stats (output of DataIngestionService
        for large enterprise files — avoids re-processing 260k+ rows).

        Input keys per item:
          product_category, stockout_rate, overstock_rate, demand_cv,
          avg_demand, avg_price, avg_stock_level, avg_holding_cost,
          avg_lost_sales_units, lost_sales_value, avg_seller_quality,
          promotion_rate, total_revenue, fulfillment_rate
        """
        if not category_stats:
            return []
        try:
            return [self._assess_from_stats(s) for s in category_stats]
        except Exception as exc:
            logger.error(f"RiskEngine.analyze_from_category_stats error: {exc}", exc_info=True)
            return []

    # ── Internal: standard computation ────────────────────────────────────────

    @staticmethod
    def _to_standard_df(records: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(records)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "product_id" not in df.columns:
            df["product_id"] = df.get("product_category", pd.Series(["UNKNOWN"] * len(df)))
        if "demand_forecast" in df.columns:
            df["demand"] = pd.to_numeric(df["demand_forecast"], errors="coerce").fillna(0)
        elif "quantity" in df.columns:
            df["demand"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
        else:
            df["demand"] = 0.0
        return df

    def _compute_standard_risks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        now = datetime.utcnow()
        for group_key, group in df.groupby("product_id"):
            group = group.sort_values("date") if "date" in group.columns else group
            demand = group["demand"].values.astype(float)
            if len(demand) < 2:
                continue
            mean_d = float(np.mean(demand))
            std_d = float(np.std(demand))
            cv = std_d / mean_d if mean_d > 0 else 0.0
            series = pd.Series(demand)
            rolling_mean = series.rolling(window=min(7, len(demand)), min_periods=1).mean()
            rolling_dev = float(np.mean(np.abs(series.values - rolling_mean.values)))
            rolling_dev_norm = rolling_dev / mean_d if mean_d > 0 else 0.0
            seasonal_vol = self._seasonal_volatility(group, demand)
            n = len(demand)
            third = max(1, n // 3)
            baseline = float(np.mean(demand[:third]))
            recent = float(np.mean(demand[-third:]))
            demand_change = (recent - baseline) / baseline if baseline > 0 else 0.0
            demand_change_norm = min(abs(demand_change), 1.0)
            risk_score = float(np.clip(
                0.40 * min(cv, 1.0) + 0.40 * demand_change_norm + 0.20 * min(seasonal_vol, 1.0),
                0.0, 1.0,
            ))
            results.append({
                "id": str(uuid.uuid4()),
                "product_category": str(group_key),
                "risk_score": round(risk_score, 4),
                "risk_type": _classify_risk_type(demand_change, cv),
                "confidence_level": round(min(0.95, 0.60 + risk_score * 0.35), 4),
                "detection_timestamp": now,
                "contributing_factors": {
                    "coefficient_of_variation": round(cv, 4),
                    "rolling_deviation_norm": round(rolling_dev_norm, 4),
                    "seasonal_volatility_norm": round(seasonal_vol, 4),
                    "demand_change_pct": round(demand_change * 100, 2),
                },
                "historical_comparison": {
                    "baseline_demand": round(baseline, 2),
                    "recent_demand": round(recent, 2),
                    "mean_demand": round(mean_d, 2),
                    "std_demand": round(std_d, 2),
                },
                "severity_level": _severity(risk_score),
                "variance_score": round(min(cv, 1.0), 4),
                "demand_change_score": round(demand_change_norm, 4),
            })
        logger.info(f"RiskEngine (standard) produced {len(results)} assessments")
        return results

    # ── Internal: enterprise computation ──────────────────────────────────────

    @staticmethod
    def _to_enterprise_df(records: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(records)
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
        return df

    def _compute_enterprise_risks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        now = datetime.utcnow()

        for cat, grp in df.groupby("product_category"):
            # ── Demand volatility ─────────────────────────────────────────────
            daily_demand = (
                grp.groupby("date")["demand"].sum()
                if "date" in grp.columns and grp["date"].notna().any()
                else grp["demand"]
            )
            mean_d = float(daily_demand.mean())
            std_d = float(daily_demand.std()) if len(daily_demand) > 1 else 0.0
            cv = std_d / mean_d if mean_d > 0 else 0.0

            # Rolling 7-day deviation
            series = daily_demand.reset_index(drop=True)
            roll_mean = series.rolling(window=min(7, len(series)), min_periods=1).mean()
            rolling_dev = float(np.mean(np.abs(series.values - roll_mean.values)))
            rolling_dev_norm = rolling_dev / mean_d if mean_d > 0 else 0.0

            # Seasonal volatility (monthly means)
            seasonal_vol = self._seasonal_volatility_grouped(grp)

            # Demand trend (first 1/3 vs last 1/3)
            vals = daily_demand.values
            n = len(vals)
            third = max(1, n // 3)
            baseline_d = float(np.mean(vals[:third]))
            recent_d = float(np.mean(vals[-third:]))
            demand_change = (recent_d - baseline_d) / baseline_d if baseline_d > 0 else 0.0
            demand_change_norm = min(abs(demand_change), 1.0)

            # ── Direct risk signals ───────────────────────────────────────────
            stockout_rate = float(grp["stockout_flag"].mean())
            overstock_rate = float(grp["overstock_flag"].mean())
            avg_lost_sales = float(grp["lost_sales"].mean())
            avg_price = float(grp["price"].mean())
            avg_holding_cost = float(grp["holding_cost"].mean())
            total_holding_cost = float(grp["holding_cost"].sum())
            lost_sales_value = float((grp["lost_sales"] * grp["price"]).sum())
            avg_seller_quality = float(grp["seller_quality_score"].mean())
            seller_risk = max(0.0, 1.0 - avg_seller_quality)
            promotion_rate = float(grp["promotion_flag"].mean())

            # Fulfillment rate
            total_demand = int(grp["demand"].sum())
            fulfillment_rate = (
                float(grp["actual_sales"].sum()) / total_demand
                if total_demand > 0 else 1.0
            )

            # ── Composite risk score ──────────────────────────────────────────
            # Normalised sub-scores (0–1):
            stockout_sub = min(stockout_rate * 20, 1.0)       # 5 % stockout → 1.0
            overstock_sub = min(overstock_rate, 1.0)           # already 0–1
            demand_vol_sub = min(cv, 1.0)
            seller_sub = min(seller_risk, 1.0)
            lost_sales_sub = min(avg_lost_sales / max(mean_d, 1), 1.0)

            # Weighted composite
            risk_score = float(np.clip(
                0.25 * stockout_sub
                + 0.25 * overstock_sub
                + 0.20 * demand_vol_sub
                + 0.15 * lost_sales_sub
                + 0.15 * seller_sub,
                0.0, 1.0,
            ))

            risk_type = _classify_risk_type(demand_change, cv, stockout_rate, overstock_rate)
            severity = _severity(risk_score)
            confidence = round(min(0.97, 0.70 + risk_score * 0.27), 4)

            results.append({
                "id": str(uuid.uuid4()),
                "product_category": str(cat),
                "risk_score": round(risk_score, 4),
                "risk_type": risk_type,
                "confidence_level": confidence,
                "detection_timestamp": now,
                "severity_level": severity,
                # Statistical signals
                "variance_score": round(min(cv, 1.0), 4),
                "demand_change_score": round(demand_change_norm, 4),
                "contributing_factors": {
                    # Statistical
                    "coefficient_of_variation": round(cv, 4),
                    "rolling_deviation_norm": round(rolling_dev_norm, 4),
                    "seasonal_volatility_norm": round(seasonal_vol, 4),
                    "demand_change_pct": round(demand_change * 100, 2),
                    # Enterprise signals
                    "stockout_rate": round(stockout_rate, 4),
                    "overstock_rate": round(overstock_rate, 4),
                    "avg_lost_sales_units": round(avg_lost_sales, 4),
                    "seller_risk_score": round(seller_risk, 4),
                    "promotion_rate": round(promotion_rate, 4),
                    "fulfillment_rate": round(fulfillment_rate, 4),
                },
                "historical_comparison": {
                    "baseline_demand": round(baseline_d, 2),
                    "recent_demand": round(recent_d, 2),
                    "mean_daily_demand": round(mean_d, 2),
                    "std_daily_demand": round(std_d, 2),
                    "avg_price": round(avg_price, 2),
                    "avg_stock_level": round(float(grp["stock_level"].mean()), 2),
                    "avg_holding_cost": round(avg_holding_cost, 2),
                },
                # Financial exposure (enterprise-only)
                "financial_exposure": {
                    "lost_sales_value": round(lost_sales_value, 2),
                    "total_holding_cost": round(total_holding_cost, 2),
                    "estimated_revenue_at_risk": round(
                        lost_sales_value + (total_holding_cost * overstock_rate), 2
                    ),
                },
            })

        logger.info(f"RiskEngine (enterprise) produced {len(results)} assessments")
        return results

    def _assess_from_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Build RiskAssessment from pre-aggregated category_stats dict."""
        cat = stats.get("product_category", "UNKNOWN")
        stockout_rate = float(stats.get("stockout_rate", 0))
        overstock_rate = float(stats.get("overstock_rate", 0))
        cv = float(stats.get("demand_cv", 0))
        avg_lost_sales = float(stats.get("avg_lost_sales_units", 0))
        avg_demand = float(stats.get("avg_demand", 1))
        seller_risk = max(0.0, 1.0 - float(stats.get("avg_seller_quality", 1.0)))
        demand_change_pct = 0.0  # not available from aggregate stats

        stockout_sub = min(stockout_rate * 20, 1.0)
        overstock_sub = min(overstock_rate, 1.0)
        demand_vol_sub = min(cv, 1.0)
        seller_sub = min(seller_risk, 1.0)
        lost_sales_sub = min(avg_lost_sales / max(avg_demand, 1), 1.0)

        risk_score = float(np.clip(
            0.25 * stockout_sub
            + 0.25 * overstock_sub
            + 0.20 * demand_vol_sub
            + 0.15 * lost_sales_sub
            + 0.15 * seller_sub,
            0.0, 1.0,
        ))

        risk_type = _classify_risk_type(demand_change_pct, cv, stockout_rate, overstock_rate)

        return {
            "id": str(uuid.uuid4()),
            "product_category": str(cat),
            "risk_score": round(risk_score, 4),
            "risk_type": risk_type,
            "confidence_level": round(min(0.97, 0.70 + risk_score * 0.27), 4),
            "detection_timestamp": datetime.utcnow(),
            "severity_level": _severity(risk_score),
            "variance_score": round(min(cv, 1.0), 4),
            "demand_change_score": 0.0,
            "contributing_factors": {
                "coefficient_of_variation": round(cv, 4),
                "stockout_rate": round(stockout_rate, 4),
                "overstock_rate": round(overstock_rate, 4),
                "avg_lost_sales_units": round(avg_lost_sales, 4),
                "seller_risk_score": round(seller_risk, 4),
                "promotion_rate": round(float(stats.get("promotion_rate", 0)), 4),
                "fulfillment_rate": round(float(stats.get("fulfillment_rate", 1)), 4),
            },
            "historical_comparison": {
                "avg_demand": round(avg_demand, 2),
                "avg_price": round(float(stats.get("avg_price", 0)), 2),
                "avg_stock_level": round(float(stats.get("avg_stock_level", 0)), 2),
                "avg_holding_cost": round(float(stats.get("avg_holding_cost", 0)), 2),
            },
            "financial_exposure": {
                "lost_sales_value": round(float(stats.get("lost_sales_value", 0)), 2),
                "total_holding_cost": round(float(stats.get("total_holding_cost", 0)), 2),
                "estimated_revenue_at_risk": round(
                    float(stats.get("lost_sales_value", 0))
                    + float(stats.get("avg_holding_cost", 0)) * overstock_rate * 365,
                    2,
                ),
            },
        }

    # ── Shared helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _seasonal_volatility(group: pd.DataFrame, demand: np.ndarray) -> float:
        if "date" not in group.columns or not group["date"].notna().any():
            return 0.0
        try:
            group = group.copy()
            group["month"] = group["date"].dt.to_period("M")
            monthly_means = group.groupby("month")["demand"].mean()
            if len(monthly_means) < 2:
                return 0.0
            max_val = float(monthly_means.max())
            return float(monthly_means.std()) / max_val if max_val > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _seasonal_volatility_grouped(group: pd.DataFrame) -> float:
        if "date" not in group.columns or not group["date"].notna().any():
            return 0.0
        try:
            tmp = group.copy()
            tmp["month"] = tmp["date"].dt.to_period("M")
            monthly = tmp.groupby("month")["demand"].sum()
            if len(monthly) < 2:
                return 0.0
            max_val = float(monthly.max())
            return float(monthly.std()) / max_val if max_val > 0 else 0.0
        except Exception:
            return 0.0
