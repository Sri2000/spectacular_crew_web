"""
Impact Propagation Engine
Models retail ecosystem as a weighted directed graph using NetworkX.

Graph topology:
    inventory → pricing      (0.80)
    inventory → fulfillment  (0.90)
    inventory → revenue      (0.70)
    pricing   → revenue      (0.95)
    fulfillment → revenue    (0.85)

Propagation:
    1st-order: direct edge weight × source impact
    2nd-order: path product × 0.70 attenuation (30 % dampening)
    Normalized to 0–10 scale
    Weighted overall: revenue(35%) + pricing(25%) + inventory(20%) + fulfillment(20%)
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

import networkx as nx

logger = logging.getLogger(__name__)

# ── Graph definition ──────────────────────────────────────────────────────────
_EDGES = [
    ("inventory", "pricing",     0.80),
    ("inventory", "fulfillment", 0.90),
    ("inventory", "revenue",     0.70),
    ("pricing",   "revenue",     0.95),
    ("fulfillment","revenue",    0.85),
]

# Weighted importance for overall score
_WEIGHTS = {"revenue": 0.35, "pricing": 0.25, "inventory": 0.20, "fulfillment": 0.20}

# 2nd-order attenuation factor
_ATTENUATION = 0.70

# Normalisation cap (raw score above this → 10/10)
_NORM_CAP = 1.0


def _build_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    for src, dst, w in _EDGES:
        G.add_edge(src, dst, weight=w)
    return G


class PropagationEngine:
    """
    Computes how a retail failure propagates across business functions.

    Returns a dict compatible with the FailurePropagationScore DB model.
    """

    def __init__(self):
        self._G = _build_graph()

    async def compute_propagation(
        self,
        scenario: Dict[str, Any],
        simulation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            return self._compute(scenario, simulation_result)
        except Exception as exc:
            logger.error(f"PropagationEngine error: {exc}", exc_info=True)
            return self._empty_result(scenario)

    # Public alias
    async def analyze_impact(self, scenario, simulation_result):
        return await self.compute_propagation(scenario, simulation_result)

    # ── Core computation ──────────────────────────────────────────────────────

    def _compute(
        self, scenario: Dict[str, Any], sim: Dict[str, Any]
    ) -> Dict[str, Any]:
        scenario_type = scenario.get("scenario_type", "STOCKOUT")
        time_horizon = int(scenario.get("time_horizon", 30))

        revenue_loss = float(sim.get("projected_revenue_loss", 0))
        stockout_days = float(sim.get("stockout_days", 0))
        overstock_units = float(sim.get("overstock_units", 0))
        holding_cost = float((sim.get("cost_breakdown") or {}).get("holding_cost", 0))

        # ── Raw direct impact per function (0–1 scale) ────────────────────────
        inv_raw = self._inventory_impact(scenario_type, stockout_days, overstock_units, time_horizon)
        pri_raw = self._pricing_impact(scenario_type, revenue_loss, holding_cost)
        ful_raw = self._fulfillment_impact(scenario_type, stockout_days, time_horizon)
        rev_raw = self._revenue_impact(revenue_loss, time_horizon)

        direct = {
            "inventory": inv_raw,
            "pricing": pri_raw,
            "fulfillment": ful_raw,
            "revenue": rev_raw,
        }

        # ── 2nd-order propagation through graph ───────────────────────────────
        propagated = dict(direct)  # start with direct scores
        for src, dst, edge_w in _EDGES:
            indirect = direct[src] * edge_w * _ATTENUATION
            if indirect > propagated[dst]:
                propagated[dst] = indirect

        # ── Normalise to 0–10 ────────────────────────────────────────────────
        function_impacts = {
            k: round(min(v / _NORM_CAP, 1.0) * 10, 2)
            for k, v in propagated.items()
        }

        # ── Weighted overall score ────────────────────────────────────────────
        overall_score = sum(
            function_impacts[fn] * w for fn, w in _WEIGHTS.items()
        )
        overall_score = round(min(overall_score, 10.0), 2)

        # ── Cascade depth: longest simple path from source node ───────────────
        source = self._source_node(scenario_type)
        try:
            paths = list(nx.all_simple_paths(self._G, source, "revenue"))
            cascade_depth = max((len(p) - 1 for p in paths), default=1)
        except Exception:
            cascade_depth = 1

        # ── Confidence metrics ────────────────────────────────────────────────
        confidence_metrics = {
            "direct_impact_confidence": 0.90,
            "indirect_impact_confidence": round(0.90 * _ATTENUATION, 2),
        }

        return {
            "id": str(uuid.uuid4()),
            "scenario_id": scenario.get("scenario_id"),
            "overall_score": overall_score,
            "cascade_depth": cascade_depth,
            "function_impacts": function_impacts,
            "affected_business_units": list(function_impacts.keys()),
            "confidence_metrics": confidence_metrics,
            "calculation_timestamp": datetime.utcnow(),
            # Flat aliases expected by some frontend fields
            "inventory_score": function_impacts.get("inventory", 0),
            "pricing_score": function_impacts.get("pricing", 0),
            "fulfillment_score": function_impacts.get("fulfillment", 0),
            "revenue_score": function_impacts.get("revenue", 0),
        }

    # ── Direct impact calculators ─────────────────────────────────────────────

    @staticmethod
    def _inventory_impact(scenario_type, stockout_days, overstock_units, horizon) -> float:
        if scenario_type in ("STOCKOUT", "FULFILLMENT_FAILURE"):
            return min(stockout_days / max(horizon, 1), 1.0)
        if scenario_type == "OVERSTOCK":
            return min(overstock_units / 5000, 1.0)
        return 0.40

    @staticmethod
    def _pricing_impact(scenario_type, revenue_loss, holding_cost) -> float:
        if scenario_type == "PRICING_FAILURE":
            return min(revenue_loss / 100_000, 1.0)
        if scenario_type == "OVERSTOCK":
            return min(holding_cost / 50_000, 1.0)
        return min(revenue_loss / 200_000, 0.60)

    @staticmethod
    def _fulfillment_impact(scenario_type, stockout_days, horizon) -> float:
        if scenario_type == "FULFILLMENT_FAILURE":
            return min(stockout_days / max(horizon, 1) * 1.2, 1.0)
        if scenario_type == "STOCKOUT":
            return min(stockout_days / max(horizon, 1) * 0.8, 1.0)
        return 0.20

    @staticmethod
    def _revenue_impact(revenue_loss, horizon) -> float:
        daily_rev_ref = 10_000 * max(horizon, 1)
        return min(revenue_loss / daily_rev_ref, 1.0)

    @staticmethod
    def _source_node(scenario_type: str) -> str:
        mapping = {
            "STOCKOUT": "inventory",
            "OVERSTOCK": "inventory",
            "SEASONAL_MISMATCH": "inventory",
            "PRICING_FAILURE": "pricing",
            "FULFILLMENT_FAILURE": "fulfillment",
        }
        return mapping.get(scenario_type, "inventory")

    @staticmethod
    def _empty_result(scenario: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "scenario_id": scenario.get("scenario_id"),
            "overall_score": 0.0,
            "cascade_depth": 0,
            "function_impacts": {"inventory": 0, "pricing": 0, "fulfillment": 0, "revenue": 0},
            "affected_business_units": [],
            "confidence_metrics": {},
            "calculation_timestamp": datetime.utcnow(),
            "inventory_score": 0,
            "pricing_score": 0,
            "fulfillment_score": 0,
            "revenue_score": 0,
        }
