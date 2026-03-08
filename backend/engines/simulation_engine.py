"""
Failure Simulation Engine
Monte Carlo simulation for all 5 retail failure scenarios:
  STOCKOUT, OVERSTOCK, SEASONAL_MISMATCH, PRICING_FAILURE, FULFILLMENT_FAILURE

Outputs:
  projected_revenue_loss, stockout_days, overstock_units,
  cost_breakdown, time_series (mean trajectory across iterations)
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)

# ── Monte Carlo config ────────────────────────────────────────────────────────
_MC_ITERATIONS = 1_000
_DAILY_HOLDING_RATE = 0.002   # 0.2 % of unit value per day
_UNIT_PRICE = 50.0             # default fallback unit price


class SimulationEngine:
    """
    Monte Carlo retail failure simulator.

    scenario dict expected keys:
        scenario_id         str
        scenario_type       STOCKOUT|OVERSTOCK|SEASONAL_MISMATCH|PRICING_FAILURE|FULFILLMENT_FAILURE
        time_horizon        int  (days, default 30)
        affected_products   list[str]
        initial_conditions  {base_inventory, unit_price}
        simulation_parameters {demand_rate, overstock_factor, stockout_factor,
                               price_elasticity, fulfillment_capacity}
    """

    async def simulate(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self._run(scenario)
        except Exception as exc:
            logger.error(f"SimulationEngine error: {exc}", exc_info=True)
            return self._empty_result(scenario)

    # ── Public alias (backward compat) ───────────────────────────────────────
    async def simulate_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        return await self.simulate(scenario)

    # ── Core simulation ───────────────────────────────────────────────────────

    def _run(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        scenario_type = scenario.get("scenario_type", "STOCKOUT")
        time_horizon = int(scenario.get("time_horizon", 30))
        products = scenario.get("affected_products") or ["PROD001"]
        ic = scenario.get("initial_conditions") or {}
        sp = scenario.get("simulation_parameters") or {}

        base_inventory = float(ic.get("base_inventory", 1000))
        unit_price = float(ic.get("unit_price", _UNIT_PRICE))
        demand_rate = float(sp.get("demand_rate", 30))
        overstock_factor = float(sp.get("overstock_factor", 1.5))
        stockout_factor = float(sp.get("stockout_factor", 0.5))
        price_elasticity = float(sp.get("price_elasticity", 1.0))
        fulfillment_capacity = float(sp.get("fulfillment_capacity", 1.0))

        # ── Dispatch by scenario type ─────────────────────────────────────────
        dispatch = {
            "STOCKOUT": self._sim_stockout,
            "OVERSTOCK": self._sim_overstock,
            "SEASONAL_MISMATCH": self._sim_seasonal,
            "PRICING_FAILURE": self._sim_pricing,
            "FULFILLMENT_FAILURE": self._sim_fulfillment,
        }
        fn = dispatch.get(scenario_type, self._sim_stockout)

        params = dict(
            time_horizon=time_horizon,
            base_inventory=base_inventory,
            unit_price=unit_price,
            demand_rate=demand_rate,
            overstock_factor=overstock_factor,
            stockout_factor=stockout_factor,
            price_elasticity=price_elasticity,
            fulfillment_capacity=fulfillment_capacity,
        )

        # Run Monte Carlo
        all_revenue_loss = np.zeros(_MC_ITERATIONS)
        all_stockout_days = np.zeros(_MC_ITERATIONS)
        all_overstock_units = np.zeros(_MC_ITERATIONS)
        all_holding_cost = np.zeros(_MC_ITERATIONS)
        trajectories: List[List[float]] = []

        rng = np.random.default_rng(seed=42)

        for i in range(_MC_ITERATIONS):
            result = fn(rng=rng, **params)
            all_revenue_loss[i] = result["revenue_loss"]
            all_stockout_days[i] = result["stockout_days"]
            all_overstock_units[i] = result["overstock_units"]
            all_holding_cost[i] = result["holding_cost"]
            if i < 1:   # store one trajectory for time-series display
                trajectories = result["trajectory"]

        mean_loss = float(np.mean(all_revenue_loss))
        mean_stockout = float(np.mean(all_stockout_days))
        mean_overstock = float(np.mean(all_overstock_units))
        mean_holding = float(np.mean(all_holding_cost))

        # Build per-product wrappers (frontend expects product-keyed dicts)
        inventory_levels: Dict[str, List[float]] = {}
        stockout_probs: Dict[str, float] = {}
        overstock_costs: Dict[str, float] = {}
        simulation_data: List[Dict[str, Any]] = []

        for prod in products:
            inventory_levels[prod] = [t["inventory"] for t in trajectories]
            stockout_probs[prod] = float(np.mean(all_stockout_days) / time_horizon)
            overstock_costs[prod] = mean_holding / max(len(products), 1)

        # Time-series for chart (one row per product with per-day data)
        for prod in products:
            simulation_data.append({
                "product_id": prod,
                "data": trajectories,
            })

        return {
            "result_id": str(uuid.uuid4()),
            "scenario_id": scenario.get("scenario_id"),
            "simulation_data": simulation_data,
            "inventory_levels": inventory_levels,
            "stockout_probabilities": stockout_probs,
            "overstock_costs": overstock_costs,
            "simulation_timestamp": datetime.utcnow(),
            "execution_time_seconds": 0.0,          # filled by route if needed
            # Extended outputs for executive summary & propagation
            "projected_revenue_loss": round(mean_loss, 2),
            "stockout_days": round(mean_stockout, 1),
            "overstock_units": round(mean_overstock, 1),
            "cost_breakdown": {
                "revenue_loss": round(mean_loss, 2),
                "holding_cost": round(mean_holding, 2),
                "lost_sales": round(mean_loss - mean_holding, 2),
            },
        }

    # ── Scenario implementations ──────────────────────────────────────────────

    def _sim_stockout(self, *, rng, time_horizon, base_inventory, unit_price,
                      demand_rate, stockout_factor, **_) -> Dict[str, Any]:
        """Inventory depletes faster than replenishment."""
        inventory = base_inventory * stockout_factor
        revenue_loss = 0.0
        stockout_days = 0
        trajectory = []

        for day in range(time_horizon):
            demand = max(0, rng.normal(demand_rate, demand_rate * 0.15))
            replenishment = max(0, rng.normal(demand_rate * 0.7, demand_rate * 0.1))
            fulfilled = min(inventory + replenishment, demand)
            lost_sales = max(0, demand - fulfilled)
            revenue_loss += lost_sales * unit_price
            inventory = max(0, inventory + replenishment - demand)
            if inventory == 0:
                stockout_days += 1
            trajectory.append({"day": day + 1, "inventory": round(inventory, 1), "demand": round(demand, 1)})

        return {"revenue_loss": revenue_loss, "stockout_days": stockout_days,
                "overstock_units": 0.0, "holding_cost": 0.0, "trajectory": trajectory}

    def _sim_overstock(self, *, rng, time_horizon, base_inventory, unit_price,
                       demand_rate, overstock_factor, **_) -> Dict[str, Any]:
        """Excess inventory accumulates holding costs."""
        inventory = base_inventory * overstock_factor
        holding_cost = 0.0
        revenue_loss = 0.0
        trajectory = []

        for day in range(time_horizon):
            demand = max(0, rng.normal(demand_rate, demand_rate * 0.15))
            sold = min(inventory, demand)
            inventory -= sold
            daily_holding = inventory * unit_price * _DAILY_HOLDING_RATE
            holding_cost += daily_holding
            # markdown pressure: if overstock > 2× demand_rate, revenue lost to discounting
            discount_loss = max(0, (inventory - demand_rate * 2)) * unit_price * 0.15 / time_horizon
            revenue_loss += discount_loss
            trajectory.append({"day": day + 1, "inventory": round(inventory, 1), "demand": round(demand, 1)})

        return {"revenue_loss": revenue_loss, "stockout_days": 0, "overstock_units": max(0, inventory),
                "holding_cost": holding_cost, "trajectory": trajectory}

    def _sim_seasonal(self, *, rng, time_horizon, base_inventory, unit_price,
                      demand_rate, overstock_factor, stockout_factor, **_) -> Dict[str, Any]:
        """Demand pattern misaligns with inventory; first half oversupplied, second undersupplied."""
        inventory = base_inventory
        holding_cost = 0.0
        revenue_loss = 0.0
        stockout_days = 0
        trajectory = []
        midpoint = time_horizon // 2

        for day in range(time_horizon):
            seasonal_factor = overstock_factor if day < midpoint else stockout_factor
            demand = max(0, rng.normal(demand_rate * seasonal_factor, demand_rate * 0.20))
            replenishment = demand_rate * 0.9  # flat replenishment
            fulfilled = min(inventory + replenishment, demand)
            lost = max(0, demand - fulfilled)
            revenue_loss += lost * unit_price
            inventory = max(0, inventory + replenishment - demand)
            if inventory == 0:
                stockout_days += 1
            holding_cost += inventory * unit_price * _DAILY_HOLDING_RATE
            trajectory.append({"day": day + 1, "inventory": round(inventory, 1), "demand": round(demand, 1)})

        return {"revenue_loss": revenue_loss, "stockout_days": stockout_days,
                "overstock_units": max(0, inventory), "holding_cost": holding_cost, "trajectory": trajectory}

    def _sim_pricing(self, *, rng, time_horizon, base_inventory, unit_price,
                     demand_rate, price_elasticity, **_) -> Dict[str, Any]:
        """Pricing mismatch suppresses demand and erodes margin."""
        inventory = base_inventory
        revenue_loss = 0.0
        trajectory = []

        for day in range(time_horizon):
            price_shock = rng.normal(1.15, 0.05)          # 15 % overpriced on average
            effective_demand = demand_rate * (1.0 / price_shock) ** price_elasticity
            effective_demand = max(0, rng.normal(effective_demand, effective_demand * 0.10))
            normal_demand = max(0, rng.normal(demand_rate, demand_rate * 0.10))
            lost_demand = max(0, normal_demand - effective_demand)
            revenue_loss += lost_demand * unit_price
            sold = min(inventory, effective_demand)
            inventory = max(0, inventory - sold)
            trajectory.append({"day": day + 1, "inventory": round(inventory, 1), "demand": round(effective_demand, 1)})

        return {"revenue_loss": revenue_loss, "stockout_days": 0,
                "overstock_units": max(0, inventory), "holding_cost": 0.0, "trajectory": trajectory}

    def _sim_fulfillment(self, *, rng, time_horizon, base_inventory, unit_price,
                         demand_rate, fulfillment_capacity, **_) -> Dict[str, Any]:
        """Fulfillment bottlenecks prevent revenue realisation."""
        inventory = base_inventory
        revenue_loss = 0.0
        stockout_days = 0
        trajectory = []

        for day in range(time_horizon):
            demand = max(0, rng.normal(demand_rate, demand_rate * 0.15))
            capacity_shock = rng.normal(fulfillment_capacity, 0.15)
            max_fulfillable = demand_rate * max(0.1, capacity_shock)
            fulfilled = min(inventory, demand, max_fulfillable)
            lost = max(0, demand - fulfilled)
            revenue_loss += lost * unit_price
            inventory -= fulfilled
            if inventory <= 0:
                stockout_days += 1
            inventory = max(0, inventory)
            trajectory.append({"day": day + 1, "inventory": round(inventory, 1), "demand": round(demand, 1)})

        return {"revenue_loss": revenue_loss, "stockout_days": stockout_days,
                "overstock_units": 0.0, "holding_cost": 0.0, "trajectory": trajectory}

    # ── Fallback empty result ────────────────────────────────────────────────

    @staticmethod
    def _empty_result(scenario: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "result_id": str(uuid.uuid4()),
            "scenario_id": scenario.get("scenario_id"),
            "simulation_data": [],
            "inventory_levels": {},
            "stockout_probabilities": {},
            "overstock_costs": {},
            "simulation_timestamp": datetime.utcnow(),
            "execution_time_seconds": 0.0,
            "projected_revenue_loss": 0.0,
            "stockout_days": 0.0,
            "overstock_units": 0.0,
            "cost_breakdown": {"revenue_loss": 0.0, "holding_cost": 0.0, "lost_sales": 0.0},
        }
