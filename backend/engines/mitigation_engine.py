"""
Mitigation Strategy Engine
Generates 3–5 ranked mitigation strategies per scenario type.

Ranking formula:
    composite_score = effectiveness_score × (1 / complexity_weight)

Complexity weights:
    LOW=1.0  MEDIUM=1.5  HIGH=2.0  VERY_HIGH=3.0
"""
import logging
import uuid
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_COMPLEXITY_WEIGHTS = {
    "LOW": 1.0,
    "MEDIUM": 1.5,
    "HIGH": 2.0,
    "VERY_HIGH": 3.0,
}

# ── Strategy templates ─────────────────────────────────────────────────────────
_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {

    "OVERSTOCK": [
        {
            "strategy_name": "Promotional Clearance Campaign",
            "description": (
                "Launch time-limited promotions (flash sales, bundle deals) "
                "to accelerate inventory turnover and free working capital."
            ),
            "effectiveness_score": 0.85,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 14,
            "cost_estimate": 25_000,
            "trade_offs": "Faster clearance vs. reduced profit margins; brand perception risk.",
        },
        {
            "strategy_name": "Supplier Renegotiation",
            "description": (
                "Negotiate return-to-vendor agreements or reduced future order quantities "
                "to prevent further inventory accumulation."
            ),
            "effectiveness_score": 0.70,
            "implementation_complexity": "LOW",
            "timeline_days": 21,
            "cost_estimate": 5_000,
            "trade_offs": "Low cost but depends on supplier relationships; may affect future allocation priority.",
        },
        {
            "strategy_name": "Liquidation Channel Strategy",
            "description": (
                "Route excess inventory through B2B liquidators, off-price retailers, "
                "or discount marketplaces for immediate cash recovery."
            ),
            "effectiveness_score": 0.75,
            "implementation_complexity": "LOW",
            "timeline_days": 10,
            "cost_estimate": 8_000,
            "trade_offs": "Immediate cash recovery vs. brand value dilution and below-cost recovery.",
        },
        {
            "strategy_name": "Bundle Pricing Strategy",
            "description": (
                "Create product bundles pairing slow-moving overstock with popular items "
                "to improve perceived value and velocity."
            ),
            "effectiveness_score": 0.68,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 7,
            "cost_estimate": 10_000,
            "trade_offs": "Preserves brand better than liquidation; requires marketing investment.",
        },
        {
            "strategy_name": "Demand Seeding Programme",
            "description": (
                "Distribute product samples to influencers and loyalty customers "
                "to stimulate organic demand and reviews."
            ),
            "effectiveness_score": 0.55,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 30,
            "cost_estimate": 15_000,
            "trade_offs": "Long-tail demand benefit but slow to materialise; indirect cost of goods.",
        },
    ],

    "STOCKOUT": [
        {
            "strategy_name": "Emergency Replenishment",
            "description": (
                "Expedite inventory from alternate suppliers or activate safety-stock "
                "reserves using air freight to meet immediate demand."
            ),
            "effectiveness_score": 0.90,
            "implementation_complexity": "HIGH",
            "timeline_days": 5,
            "cost_estimate": 40_000,
            "trade_offs": "Fastest recovery vs. significantly higher logistics cost and margin erosion.",
        },
        {
            "strategy_name": "Backorder Management System",
            "description": (
                "Implement structured backorder queuing with ETA commitments, "
                "customer notifications, and partial shipment capabilities."
            ),
            "effectiveness_score": 0.65,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 3,
            "cost_estimate": 12_000,
            "trade_offs": "Retains customer intent vs. delayed revenue recognition and cancellation risk.",
        },
        {
            "strategy_name": "Demand Dampening",
            "description": (
                "Temporarily limit per-customer purchase quantities and pause promotional "
                "spend to manage demand within available supply."
            ),
            "effectiveness_score": 0.60,
            "implementation_complexity": "LOW",
            "timeline_days": 1,
            "cost_estimate": 2_000,
            "trade_offs": "Immediate to execute; may frustrate high-value customers and reduce short-term revenue.",
        },
        {
            "strategy_name": "Safety Stock Build-up",
            "description": (
                "Increase safety-stock thresholds based on revised demand variability analysis "
                "to prevent future stockouts."
            ),
            "effectiveness_score": 0.80,
            "implementation_complexity": "VERY_HIGH",
            "timeline_days": 45,
            "cost_estimate": 60_000,
            "trade_offs": "Long-term resilience vs. capital lock-up and higher holding costs.",
        },
        {
            "strategy_name": "Supplier Diversification",
            "description": (
                "Onboard secondary and tertiary suppliers with pre-negotiated contracts "
                "to reduce single-source dependency."
            ),
            "effectiveness_score": 0.75,
            "implementation_complexity": "HIGH",
            "timeline_days": 60,
            "cost_estimate": 30_000,
            "trade_offs": "Reduces concentration risk vs. vendor management complexity and qualification lead time.",
        },
    ],

    "SEASONAL_MISMATCH": [
        {
            "strategy_name": "Dynamic Seasonal Pricing",
            "description": (
                "Deploy algorithmic pricing that adjusts in real time to seasonal demand curves, "
                "marking up during peak demand and marking down heading into off-season."
            ),
            "effectiveness_score": 0.85,
            "implementation_complexity": "HIGH",
            "timeline_days": 21,
            "cost_estimate": 35_000,
            "trade_offs": "Maximises revenue yield vs. pricing complexity and potential customer perception issues.",
        },
        {
            "strategy_name": "Pre-season Inventory Rebalancing",
            "description": (
                "Rebalance inventory across distribution centres by region and channel "
                "before peak season to align stock placement with predicted demand."
            ),
            "effectiveness_score": 0.75,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 30,
            "cost_estimate": 20_000,
            "trade_offs": "Improves availability where needed vs. inter-DC logistics cost.",
        },
        {
            "strategy_name": "Demand Forecasting Overhaul",
            "description": (
                "Adopt ensemble forecasting (statistical + ML) with seasonal decomposition "
                "to improve baseline predictions by 20–30 %."
            ),
            "effectiveness_score": 0.80,
            "implementation_complexity": "VERY_HIGH",
            "timeline_days": 90,
            "cost_estimate": 75_000,
            "trade_offs": "Foundational improvement vs. significant time and investment; benefits lag by one season.",
        },
    ],

    "PRICING_FAILURE": [
        {
            "strategy_name": "Competitive Price Reset",
            "description": (
                "Conduct rapid competitive intelligence and reset prices to within "
                "5 % of market rate across affected SKUs."
            ),
            "effectiveness_score": 0.88,
            "implementation_complexity": "LOW",
            "timeline_days": 3,
            "cost_estimate": 5_000,
            "trade_offs": "Quick revenue recovery vs. margin concession; risk of price war.",
        },
        {
            "strategy_name": "Elasticity-based Dynamic Pricing",
            "description": (
                "Implement price optimisation engine that continuously adjusts prices "
                "using demand elasticity coefficients and competitor signals."
            ),
            "effectiveness_score": 0.82,
            "implementation_complexity": "VERY_HIGH",
            "timeline_days": 60,
            "cost_estimate": 80_000,
            "trade_offs": "Optimal long-term pricing vs. high implementation cost and customer trust concerns.",
        },
        {
            "strategy_name": "Bundling & Value-added Strategy",
            "description": (
                "Bundle products or add complementary services to improve perceived value "
                "without lowering headline prices."
            ),
            "effectiveness_score": 0.65,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 14,
            "cost_estimate": 18_000,
            "trade_offs": "Preserves price integrity vs. slower demand response; bundle design complexity.",
        },
    ],

    "FULFILLMENT_FAILURE": [
        {
            "strategy_name": "Capacity Surge Plan",
            "description": (
                "Activate surge workforce (contract staff, overtime), add shift capacity, "
                "and prioritise high-value order processing to clear fulfillment backlogs."
            ),
            "effectiveness_score": 0.88,
            "implementation_complexity": "HIGH",
            "timeline_days": 7,
            "cost_estimate": 50_000,
            "trade_offs": "Rapid capacity boost vs. elevated labour cost and potential quality variance.",
        },
        {
            "strategy_name": "3PL Network Activation",
            "description": (
                "Route overflow orders to pre-contracted third-party logistics partners "
                "to absorb volume spikes without internal capacity build."
            ),
            "effectiveness_score": 0.80,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 5,
            "cost_estimate": 35_000,
            "trade_offs": "Flexible scaling vs. higher per-unit cost and reduced visibility/control.",
        },
        {
            "strategy_name": "Warehouse Operations Optimisation",
            "description": (
                "Re-slot high-velocity SKUs, optimise pick paths, and deploy zone-batch "
                "picking to increase throughput without adding headcount."
            ),
            "effectiveness_score": 0.72,
            "implementation_complexity": "MEDIUM",
            "timeline_days": 14,
            "cost_estimate": 15_000,
            "trade_offs": "Sustainable throughput gain vs. disruption during re-slotting transition period.",
        },
    ],
}

# Default fallback for unknown scenario types
_DEFAULT_STRATEGIES = [
    {
        "strategy_name": "Root Cause Analysis & Action Plan",
        "description": "Conduct rapid root cause analysis and deploy a cross-functional task force.",
        "effectiveness_score": 0.70,
        "implementation_complexity": "MEDIUM",
        "timeline_days": 14,
        "cost_estimate": 20_000,
        "trade_offs": "Structured response vs. slower initial action.",
    },
]


class MitigationEngine:
    """
    Generates and ranks mitigation strategies for a given failure scenario.
    """

    async def generate_strategies(
        self,
        scenario: Dict[str, Any],
        propagation: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        try:
            return self._generate(scenario, propagation)
        except Exception as exc:
            logger.error(f"MitigationEngine error: {exc}", exc_info=True)
            return []

    def _generate(
        self, scenario: Dict[str, Any], propagation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        scenario_type = scenario.get("scenario_type", "STOCKOUT")
        scenario_id = scenario.get("scenario_id", str(uuid.uuid4()))
        templates = _TEMPLATES.get(scenario_type, _DEFAULT_STRATEGIES)

        strategies = []
        for tmpl in templates:
            complexity = tmpl["implementation_complexity"]
            weight = _COMPLEXITY_WEIGHTS.get(complexity, 1.5)
            composite = tmpl["effectiveness_score"] * (1.0 / weight)

            strategies.append({
                "strategy_id": str(uuid.uuid4()),
                "scenario_id": scenario_id,
                "strategy_name": tmpl["strategy_name"],
                "description": tmpl["description"],
                "effectiveness_score": tmpl["effectiveness_score"],
                "implementation_complexity": complexity,
                "timeline_days": tmpl["timeline_days"],
                "cost_estimate": tmpl["cost_estimate"],
                "trade_offs": tmpl.get("trade_offs", ""),
                "resource_requirements": {
                    "complexity_weight": weight,
                    "composite_rank_score": round(composite, 4),
                },
                # Composite score for sorting (not exposed to client directly)
                "_composite": composite,
            })

        # Rank: highest composite first
        strategies.sort(key=lambda s: s["_composite"], reverse=True)
        for s in strategies:
            del s["_composite"]

        logger.info(
            f"MitigationEngine generated {len(strategies)} strategies for {scenario_type}"
        )
        return strategies
