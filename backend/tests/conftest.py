"""
Pytest configuration and shared fixtures for all tests.

This module configures Hypothesis settings and provides common fixtures
for both unit tests and property-based tests.
"""

import pytest
from hypothesis import settings, Verbosity, Phase
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

# Configure Hypothesis settings globally
settings.register_profile(
    "default",
    max_examples=100,  # Minimum 100 iterations per property test as per design
    deadline=None,  # Disable deadline for complex simulations
    verbosity=Verbosity.normal,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target, Phase.shrink],
    print_blob=True,  # Print reproduction blob on failure
)

settings.register_profile(
    "ci",
    max_examples=200,  # More thorough testing in CI
    deadline=None,
    verbosity=Verbosity.verbose,
    print_blob=True,
)

settings.register_profile(
    "dev",
    max_examples=50,  # Faster feedback during development
    deadline=None,
    verbosity=Verbosity.verbose,
    print_blob=True,
)

# Load the appropriate profile based on environment
profile = os.getenv("HYPOTHESIS_PROFILE", "default")
settings.load_profile(profile)


# Shared test fixtures
@pytest.fixture
def sample_product_categories() -> List[str]:
    """Provides a list of sample product categories for testing."""
    return [
        "Electronics",
        "Clothing",
        "Home & Garden",
        "Sports & Outdoors",
        "Books",
        "Toys & Games",
    ]


@pytest.fixture
def sample_risk_thresholds() -> Dict[str, float]:
    """Provides sample risk threshold configuration."""
    return {
        "variance_threshold": 0.25,
        "confidence_threshold": 0.7,
        "revenue_impact_threshold": 10000.0,
    }


@pytest.fixture
def sample_simulation_parameters() -> Dict[str, Any]:
    """Provides sample simulation parameters."""
    return {
        "time_horizon_days": 90,
        "confidence_level": 0.95,
        "monte_carlo_iterations": 1000,
        "overstock_threshold": 1.5,
        "stockout_threshold": 0.2,
    }


@pytest.fixture
def sample_market_conditions() -> Dict[str, Any]:
    """Provides sample market conditions for testing."""
    return {
        "market_volatility": 0.15,
        "seasonal_factor": 1.2,
        "competitive_pressure": "medium",
        "economic_indicator": "stable",
    }


@pytest.fixture
def base_timestamp() -> datetime:
    """Provides a consistent base timestamp for testing."""
    return datetime(2024, 1, 1, 0, 0, 0)


@pytest.fixture
def time_series_dates(base_timestamp) -> List[datetime]:
    """Provides a series of dates for time-series testing."""
    return [base_timestamp + timedelta(days=i) for i in range(90)]
