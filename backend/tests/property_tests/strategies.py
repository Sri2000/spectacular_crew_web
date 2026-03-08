"""
Hypothesis strategies for generating test data.

This module provides custom strategies for generating domain-specific
test data for property-based testing of the retail failure simulator.
"""

from hypothesis import strategies as st
from hypothesis.strategies import composite
from datetime import datetime, timedelta
from typing import Dict, List, Any
import string


# Basic data strategies
@composite
def product_category_strategy(draw) -> str:
    """Generate valid product category names."""
    categories = [
        "Electronics",
        "Clothing",
        "Home & Garden",
        "Sports & Outdoors",
        "Books",
        "Toys & Games",
        "Food & Beverage",
        "Health & Beauty",
        "Automotive",
        "Pet Supplies",
    ]
    return draw(st.sampled_from(categories))


@composite
def product_id_strategy(draw) -> str:
    """Generate valid product IDs."""
    prefix = draw(st.sampled_from(["PROD", "SKU", "ITEM"]))
    number = draw(st.integers(min_value=1000, max_value=9999))
    return f"{prefix}-{number}"


@composite
def risk_score_strategy(draw) -> float:
    """Generate valid risk scores (0.0 to 1.0)."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@composite
def confidence_level_strategy(draw) -> float:
    """Generate valid confidence levels (0.0 to 1.0)."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@composite
def variance_value_strategy(draw) -> float:
    """Generate variance values for demand analysis."""
    return draw(st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False))


@composite
def threshold_strategy(draw) -> float:
    """Generate threshold values."""
    return draw(st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False))


@composite
def revenue_impact_strategy(draw) -> float:
    """Generate revenue impact values."""
    return draw(st.floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False))


@composite
def timestamp_strategy(draw, start_year: int = 2020, end_year: int = 2025) -> datetime:
    """Generate valid timestamps."""
    year = draw(st.integers(min_value=start_year, max_value=end_year))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return datetime(year, month, day, hour, minute, second)


@composite
def time_horizon_strategy(draw) -> int:
    """Generate time horizon in days."""
    return draw(st.integers(min_value=1, max_value=365))


# Complex data strategies
@composite
def seasonal_data_strategy(draw) -> Dict[str, Any]:
    """Generate seasonal market data for testing."""
    num_categories = draw(st.integers(min_value=1, max_value=10))
    categories = [draw(product_category_strategy()) for _ in range(num_categories)]
    
    return {
        "timestamp": draw(timestamp_strategy()),
        "categories": categories,
        "variances": {
            category: draw(variance_value_strategy())
            for category in categories
        },
        "historical_averages": {
            category: draw(st.floats(min_value=100.0, max_value=10000.0, allow_nan=False))
            for category in categories
        },
        "current_values": {
            category: draw(st.floats(min_value=100.0, max_value=10000.0, allow_nan=False))
            for category in categories
        },
    }


@composite
def risk_threshold_config_strategy(draw) -> Dict[str, float]:
    """Generate risk threshold configuration."""
    return {
        "variance_threshold": draw(threshold_strategy()),
        "confidence_threshold": draw(confidence_level_strategy()),
        "revenue_impact_threshold": draw(revenue_impact_strategy()),
    }


@composite
def inventory_scenario_strategy(draw) -> Dict[str, Any]:
    """Generate inventory scenario parameters."""
    scenario_type = draw(st.sampled_from(["overstock", "stockout", "mixed"]))
    num_products = draw(st.integers(min_value=1, max_value=20))
    
    return {
        "scenario_type": scenario_type,
        "affected_products": [draw(product_id_strategy()) for _ in range(num_products)],
        "time_horizon_days": draw(time_horizon_strategy()),
        "initial_inventory_levels": {
            draw(product_id_strategy()): draw(st.floats(min_value=0.0, max_value=10000.0, allow_nan=False))
            for _ in range(num_products)
        },
        "demand_forecast": {
            draw(product_id_strategy()): draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False))
            for _ in range(num_products)
        },
    }


@composite
def simulation_parameters_strategy(draw) -> Dict[str, Any]:
    """Generate simulation parameters."""
    return {
        "time_horizon_days": draw(time_horizon_strategy()),
        "confidence_level": draw(confidence_level_strategy()),
        "monte_carlo_iterations": draw(st.integers(min_value=100, max_value=5000)),
        "overstock_threshold": draw(st.floats(min_value=1.1, max_value=3.0, allow_nan=False)),
        "stockout_threshold": draw(st.floats(min_value=0.0, max_value=0.5, allow_nan=False)),
    }


@composite
def failure_scenario_strategy(draw) -> Dict[str, Any]:
    """Generate failure scenario data."""
    scenario_type = draw(st.sampled_from([
        "seasonal_mismatch",
        "overstock",
        "stockout",
        "promotion_failure",
        "supply_chain_disruption",
    ]))
    
    num_products = draw(st.integers(min_value=1, max_value=15))
    
    return {
        "scenario_id": f"SCENARIO-{draw(st.integers(min_value=1000, max_value=9999))}",
        "scenario_type": scenario_type,
        "affected_products": [draw(product_id_strategy()) for _ in range(num_products)],
        "severity": draw(st.sampled_from(["low", "medium", "high", "critical"])),
        "timestamp": draw(timestamp_strategy()),
    }


@composite
def business_function_impacts_strategy(draw) -> Dict[str, float]:
    """Generate business function impact scores."""
    functions = ["inventory", "pricing", "fulfillment", "revenue"]
    return {
        function: draw(st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))
        for function in functions
    }


@composite
def market_conditions_strategy(draw) -> Dict[str, Any]:
    """Generate market conditions data."""
    return {
        "market_volatility": draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
        "seasonal_factor": draw(st.floats(min_value=0.5, max_value=2.0, allow_nan=False)),
        "competitive_pressure": draw(st.sampled_from(["low", "medium", "high"])),
        "economic_indicator": draw(st.sampled_from(["recession", "stable", "growth"])),
        "consumer_confidence": draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
    }


@composite
def mitigation_strategy_data_strategy(draw) -> Dict[str, Any]:
    """Generate mitigation strategy data."""
    return {
        "strategy_name": draw(st.text(alphabet=string.ascii_letters + " ", min_size=5, max_size=50)),
        "effectiveness_score": draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
        "implementation_complexity": draw(st.sampled_from(["low", "medium", "high", "very_high"])),
        "timeline_days": draw(st.integers(min_value=1, max_value=180)),
        "cost_estimate": draw(st.floats(min_value=1000.0, max_value=1000000.0, allow_nan=False)),
    }


# List strategies
@composite
def product_list_strategy(draw, min_size: int = 1, max_size: int = 20) -> List[str]:
    """Generate a list of product IDs."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(product_id_strategy()) for _ in range(size)]


@composite
def category_list_strategy(draw, min_size: int = 1, max_size: int = 10) -> List[str]:
    """Generate a list of product categories."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    categories = set()
    while len(categories) < size:
        categories.add(draw(product_category_strategy()))
    return list(categories)


@composite
def time_series_strategy(draw, min_length: int = 7, max_length: int = 90) -> List[datetime]:
    """Generate a time series of dates."""
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    start_date = draw(timestamp_strategy())
    return [start_date + timedelta(days=i) for i in range(length)]
