"""
Helper utilities for property-based testing.

This module provides common utilities and assertion helpers for
property-based tests across the retail failure simulator platform.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


def assert_all_categories_present(
    result: Dict[str, Any],
    expected_categories: List[str],
    result_key: str = "categories"
) -> None:
    """
    Assert that all expected categories are present in the result.
    
    Args:
        result: The result dictionary to check
        expected_categories: List of categories that should be present
        result_key: The key in result dict containing categories
    """
    result_categories = result.get(result_key, [])
    for category in expected_categories:
        assert category in result_categories, \
            f"Category '{category}' not found in result"


def assert_score_in_range(
    score: float,
    min_value: float = 0.0,
    max_value: float = 1.0,
    score_name: str = "score"
) -> None:
    """
    Assert that a score is within the expected range.
    
    Args:
        score: The score value to check
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        score_name: Name of the score for error messages
    """
    assert min_value <= score <= max_value, \
        f"{score_name} {score} is outside valid range [{min_value}, {max_value}]"


def assert_timestamp_valid(
    timestamp: datetime,
    min_year: int = 2020,
    max_year: int = 2030
) -> None:
    """
    Assert that a timestamp is valid and within reasonable bounds.
    
    Args:
        timestamp: The timestamp to validate
        min_year: Minimum allowed year
        max_year: Maximum allowed year
    """
    assert isinstance(timestamp, datetime), \
        f"Expected datetime, got {type(timestamp)}"
    assert min_year <= timestamp.year <= max_year, \
        f"Timestamp year {timestamp.year} is outside valid range [{min_year}, {max_year}]"


def assert_required_fields_present(
    data: Dict[str, Any],
    required_fields: List[str],
    data_name: str = "data"
) -> None:
    """
    Assert that all required fields are present in a data dictionary.
    
    Args:
        data: The data dictionary to check
        required_fields: List of field names that must be present
        data_name: Name of the data structure for error messages
    """
    for field in required_fields:
        assert field in data, \
            f"Required field '{field}' not found in {data_name}"


def assert_list_not_empty(
    items: List[Any],
    list_name: str = "list"
) -> None:
    """
    Assert that a list is not empty.
    
    Args:
        items: The list to check
        list_name: Name of the list for error messages
    """
    assert len(items) > 0, f"{list_name} should not be empty"


def assert_dict_not_empty(
    data: Dict[str, Any],
    dict_name: str = "dictionary"
) -> None:
    """
    Assert that a dictionary is not empty.
    
    Args:
        data: The dictionary to check
        dict_name: Name of the dictionary for error messages
    """
    assert len(data) > 0, f"{dict_name} should not be empty"


def assert_monotonic_increasing(
    values: List[float],
    strict: bool = False,
    values_name: str = "values"
) -> None:
    """
    Assert that a list of values is monotonically increasing.
    
    Args:
        values: List of numeric values to check
        strict: If True, requires strictly increasing (no equal consecutive values)
        values_name: Name of the values for error messages
    """
    for i in range(len(values) - 1):
        if strict:
            assert values[i] < values[i + 1], \
                f"{values_name} not strictly increasing at index {i}: {values[i]} >= {values[i + 1]}"
        else:
            assert values[i] <= values[i + 1], \
                f"{values_name} not monotonically increasing at index {i}: {values[i]} > {values[i + 1]}"


def assert_sum_equals(
    values: List[float],
    expected_sum: float,
    tolerance: float = 0.01,
    values_name: str = "values"
) -> None:
    """
    Assert that the sum of values equals an expected sum within tolerance.
    
    Args:
        values: List of numeric values to sum
        expected_sum: Expected sum value
        tolerance: Allowed difference from expected sum
        values_name: Name of the values for error messages
    """
    actual_sum = sum(values)
    assert abs(actual_sum - expected_sum) <= tolerance, \
        f"Sum of {values_name} ({actual_sum}) differs from expected ({expected_sum}) by more than {tolerance}"


def assert_all_positive(
    values: List[float],
    values_name: str = "values"
) -> None:
    """
    Assert that all values in a list are positive.
    
    Args:
        values: List of numeric values to check
        values_name: Name of the values for error messages
    """
    for i, value in enumerate(values):
        assert value > 0, \
            f"{values_name}[{i}] = {value} is not positive"


def assert_all_non_negative(
    values: List[float],
    values_name: str = "values"
) -> None:
    """
    Assert that all values in a list are non-negative.
    
    Args:
        values: List of numeric values to check
        values_name: Name of the values for error messages
    """
    for i, value in enumerate(values):
        assert value >= 0, \
            f"{values_name}[{i}] = {value} is negative"


def assert_percentage_valid(
    percentage: float,
    percentage_name: str = "percentage"
) -> None:
    """
    Assert that a percentage value is between 0 and 100.
    
    Args:
        percentage: The percentage value to check
        percentage_name: Name of the percentage for error messages
    """
    assert 0 <= percentage <= 100, \
        f"{percentage_name} {percentage} is outside valid range [0, 100]"


def assert_correlation_exists(
    values1: List[float],
    values2: List[float],
    expected_direction: str = "positive",
    values1_name: str = "values1",
    values2_name: str = "values2"
) -> None:
    """
    Assert that two lists of values have the expected correlation direction.
    
    Args:
        values1: First list of values
        values2: Second list of values
        expected_direction: "positive" or "negative"
        values1_name: Name of first values for error messages
        values2_name: Name of second values for error messages
    """
    assert len(values1) == len(values2), \
        f"Length mismatch: {values1_name} has {len(values1)} items, {values2_name} has {len(values2)} items"
    
    # Simple correlation check: count agreements vs disagreements in direction
    agreements = 0
    disagreements = 0
    
    for i in range(len(values1) - 1):
        delta1 = values1[i + 1] - values1[i]
        delta2 = values2[i + 1] - values2[i]
        
        if delta1 * delta2 > 0:  # Same sign
            agreements += 1
        elif delta1 * delta2 < 0:  # Opposite sign
            disagreements += 1
    
    if expected_direction == "positive":
        assert agreements > disagreements, \
            f"Expected positive correlation between {values1_name} and {values2_name}, " \
            f"but found {agreements} agreements vs {disagreements} disagreements"
    elif expected_direction == "negative":
        assert disagreements > agreements, \
            f"Expected negative correlation between {values1_name} and {values2_name}, " \
            f"but found {agreements} agreements vs {disagreements} disagreements"


def assert_business_functions_complete(
    impacts: Dict[str, float]
) -> None:
    """
    Assert that all four business functions have impact scores.
    
    Args:
        impacts: Dictionary of business function impacts
    """
    required_functions = ["inventory", "pricing", "fulfillment", "revenue"]
    for function in required_functions:
        assert function in impacts, \
            f"Business function '{function}' missing from impact analysis"
        assert_score_in_range(impacts[function], 0.0, 10.0, f"{function} impact score")


def assert_compound_effect_valid(
    individual_effects: List[float],
    compound_effect: float
) -> None:
    """
    Assert that compound effect is greater than or equal to sum of individual effects.
    
    Args:
        individual_effects: List of individual failure effects
        compound_effect: The calculated compound effect
    """
    sum_individual = sum(individual_effects)
    assert compound_effect >= sum_individual, \
        f"Compound effect {compound_effect} is less than sum of individual effects {sum_individual}"
