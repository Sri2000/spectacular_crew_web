"""
TransferOptimizationEngine

Given per-store × per-category inventory stats and a user-supplied transport cost,
finds economically viable stock transfers that avoid unnecessary procurement.

A transfer from Store A → Store B for product category X is viable when:
    net_benefit = saved_holding_cost + saved_procurement_cost - transport_cost > 0
"""
import uuid
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Strength thresholds (ROI % on transport spend)
_ROI_STRONG   = 100.0   # net_benefit ≥ transport_cost  (≥ 100 % ROI)
_ROI_MODERATE =  30.0   # net_benefit ≥ 30 % of transport_cost


class TransferOptimizationEngine:
    """Recommends inter-store stock transfers based on supply/demand imbalances."""

    async def recommend_transfers(
        self,
        store_stats: List[Dict[str, Any]],
        transport_cost_per_unit: float,
        time_horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Parameters
        ----------
        store_stats : flat list of {store_id, region, product_category, avg_stock_level,
                      avg_demand, avg_price, avg_holding_cost, ...} dicts
                      (produced by DataIngestionService._compute_store_stats)
        transport_cost_per_unit : cost in currency units to move one unit between stores
        time_horizon_days : planning window used to estimate holding-cost savings

        Returns
        -------
        dict with summary metrics and a ranked list of transfer recommendations
        """
        if not store_stats:
            return self._empty_result(transport_cost_per_unit)

        # Group rows by product_category
        by_category: Dict[str, List[Dict]] = {}
        for row in store_stats:
            cat = row["product_category"]
            by_category.setdefault(cat, []).append(row)

        transfers: List[Dict[str, Any]] = []

        for category, rows in by_category.items():
            # Classify each store-row as surplus or deficit for this category
            surplus_stores = []
            deficit_stores = []
            for row in rows:
                excess  = row["avg_stock_level"] - row["avg_demand"]
                deficit = row["avg_demand"] - row["avg_stock_level"]
                if excess > 0:
                    surplus_stores.append({**row, "excess_units": round(excess, 2)})
                elif deficit > 0:
                    deficit_stores.append({**row, "deficit_units": round(deficit, 2)})

            # Pair every surplus store with every deficit store
            for src in surplus_stores:
                for dst in deficit_stores:
                    # Skip same-store (shouldn't happen but guard it)
                    if src["store_id"] == dst["store_id"]:
                        continue

                    transfer_qty = min(src["excess_units"], dst["deficit_units"])
                    if transfer_qty <= 0:
                        continue

                    # Economics
                    saved_holding = round(
                        transfer_qty * src["avg_holding_cost"] * time_horizon_days, 2
                    )
                    saved_procurement = round(transfer_qty * dst["avg_price"], 2)
                    total_benefit = saved_holding + saved_procurement
                    transport_cost = round(transfer_qty * transport_cost_per_unit, 2)
                    net_benefit = round(total_benefit - transport_cost, 2)

                    if transport_cost > 0:
                        roi_pct = round(net_benefit / transport_cost * 100, 1)
                    else:
                        roi_pct = 100.0 if net_benefit >= 0 else -100.0

                    is_viable = net_benefit > 0

                    if is_viable and roi_pct >= _ROI_STRONG:
                        strength = "Strong"
                    elif is_viable and roi_pct >= _ROI_MODERATE:
                        strength = "Moderate"
                    elif is_viable:
                        strength = "Marginal"
                    else:
                        strength = "Not Viable"

                    transfers.append({
                        "transfer_id": str(uuid.uuid4()),
                        "product_category": category,
                        "source_store": {
                            "store_id": src["store_id"],
                            "region": src["region"],
                            "avg_stock_level": src["avg_stock_level"],
                            "avg_demand": src["avg_demand"],
                            "excess_units": src["excess_units"],
                            "avg_holding_cost": src["avg_holding_cost"],
                        },
                        "destination_store": {
                            "store_id": dst["store_id"],
                            "region": dst["region"],
                            "avg_stock_level": dst["avg_stock_level"],
                            "avg_demand": dst["avg_demand"],
                            "deficit_units": dst["deficit_units"],
                            "avg_lost_sales_units": dst.get("avg_lost_sales_units", 0),
                        },
                        "transfer_quantity": round(transfer_qty, 2),
                        "economics": {
                            "saved_holding_cost": saved_holding,
                            "saved_procurement_cost": saved_procurement,
                            "transport_cost": transport_cost,
                            "net_benefit": net_benefit,
                            "roi_percent": roi_pct,
                        },
                        "recommendation_strength": strength,
                        "is_viable": is_viable,
                        "priority_rank": 0,  # filled after sorting
                    })

        # Sort by net_benefit descending, assign ranks
        transfers.sort(key=lambda t: t["economics"]["net_benefit"], reverse=True)
        for rank, t in enumerate(transfers, start=1):
            t["priority_rank"] = rank

        viable = [t for t in transfers if t["is_viable"]]
        total_savings = round(sum(t["economics"]["net_benefit"] for t in viable), 2)

        # Unique stores touched
        stores_involved: set = set()
        for t in viable:
            stores_involved.add(t["source_store"]["store_id"])
            stores_involved.add(t["destination_store"]["store_id"])

        return {
            "total_opportunities": len(transfers),
            "viable_transfers": len(viable),
            "total_potential_savings": total_savings,
            "stores_involved": len(stores_involved),
            "transport_cost_per_unit": transport_cost_per_unit,
            "time_horizon_days": time_horizon_days,
            "transfers": transfers,
        }

    @staticmethod
    def _empty_result(transport_cost_per_unit: float) -> Dict[str, Any]:
        return {
            "total_opportunities": 0,
            "viable_transfers": 0,
            "total_potential_savings": 0.0,
            "stores_involved": 0,
            "transport_cost_per_unit": transport_cost_per_unit,
            "time_horizon_days": 30,
            "transfers": [],
        }
