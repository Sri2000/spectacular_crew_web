# Testing Framework for Retail Failure Simulator

This directory contains the testing infrastructure for the AI-powered Retail Failure Simulator & Market Intelligence Platform.

## Overview

The testing strategy employs a dual approach:
- **Unit Tests**: Verify specific examples and edge cases
- **Property-Based Tests**: Validate universal correctness properties using Hypothesis

## Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── README.md                   # This file
├── property_tests/             # Property-based tests using Hypothesis
│   ├── __init__.py
│   ├── strategies.py           # Hypothesis strategies for test data generation
│   ├── test_helpers.py         # Helper utilities for property tests
│   └── test_*.py               # Property test modules
└── unit_tests/                 # Unit tests for specific scenarios
    ├── __init__.py
    └── test_*.py               # Unit test modules
```

## Hypothesis Configuration

The Hypothesis framework is configured with the following profiles:

### Default Profile
- **Max Examples**: 100 iterations per property test (as per design requirements)
- **Deadline**: Disabled for complex simulations
- **Verbosity**: Normal
- **Print Blob**: Enabled for failure reproduction

### CI Profile
- **Max Examples**: 200 iterations for thorough testing
- **Verbosity**: Verbose for detailed CI logs

### Dev Profile
- **Max Examples**: 50 iterations for faster feedback during development
- **Verbosity**: Verbose for debugging

## Running Tests

### Run All Tests
```bash
cd backend
pytest tests/
```

### Run Only Property-Based Tests
```bash
pytest tests/property_tests/
```

### Run Only Unit Tests
```bash
pytest tests/unit_tests/
```

### Run with Specific Hypothesis Profile
```bash
# Development profile (faster)
HYPOTHESIS_PROFILE=dev pytest tests/property_tests/

# CI profile (more thorough)
HYPOTHESIS_PROFILE=ci pytest tests/property_tests/
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run Specific Property Test
```bash
pytest tests/property_tests/test_seasonal_risk.py -v
```

## Writing Property-Based Tests

### Test Tagging Convention

Each property test must be tagged with the format:
```
Feature: retail-failure-simulator, Property {number}: {property_text}
```

### Example Property Test Structure

```python
from hypothesis import given
from tests.property_tests.strategies import seasonal_data_strategy, threshold_strategy

@given(
    seasonal_data=seasonal_data_strategy(),
    thresholds=threshold_strategy()
)
def test_threshold_based_risk_flagging(seasonal_data, thresholds):
    """
    Feature: retail-failure-simulator, Property 2: Threshold-based risk flagging
    
    For any demand variance data, when variance exceeds configured thresholds,
    the system should flag potential seasonal mismatches.
    """
    # Test implementation
    pass
```

### Available Strategies

The `strategies.py` module provides pre-built Hypothesis strategies for:
- Product categories and IDs
- Risk scores and confidence levels
- Seasonal market data
- Inventory scenarios
- Simulation parameters
- Failure scenarios
- Business function impacts
- Market conditions
- Mitigation strategies

### Helper Utilities

The `test_helpers.py` module provides assertion helpers for:
- Validating score ranges
- Checking required fields
- Verifying timestamps
- Testing monotonic sequences
- Validating business function completeness
- Checking compound effects

## Test Coverage Requirements

- **Core Business Logic**: Minimum 90% code coverage
- **Critical Decision Paths**: 100% coverage
- **Error Paths**: Comprehensive testing
- **Performance**: Benchmarking for all SLA requirements

## Property Test Categories

1. **Data Processing Properties**: Test data ingestion, validation, and transformation
2. **Simulation Properties**: Test failure scenario modeling with varied parameters
3. **Analysis Properties**: Test impact analysis and propagation scoring
4. **AI Reasoning Properties**: Test explanation generation and recommendations
5. **Interface Properties**: Test dashboard behavior and user interactions

## Debugging Failed Property Tests

When a property test fails, Hypothesis will:
1. Show the failing example that triggered the failure
2. Attempt to shrink the example to the minimal failing case
3. Print a reproduction blob for re-running the exact failure

To reproduce a failure:
```python
@reproduce_failure('6.98.0', b'AXic...')  # Use blob from failure output
@given(...)
def test_my_property(...):
    pass
```

## Best Practices

1. **Keep properties simple**: Test one property at a time
2. **Use appropriate strategies**: Choose strategies that match your domain
3. **Add assumptions**: Use `hypothesis.assume()` to filter invalid inputs
4. **Document properties**: Clearly state what property is being tested
5. **Use helper functions**: Leverage test_helpers.py for common assertions
6. **Tag tests properly**: Always include the Feature and Property tags
7. **Test edge cases**: Ensure strategies cover boundary conditions

## Continuous Integration

Tests are automatically run in CI with the following configuration:
- Hypothesis profile: `ci` (200 examples per test)
- Coverage reporting enabled
- Parallel test execution
- Failure artifacts preserved

## Troubleshooting

### Tests Running Slowly
- Use the `dev` profile during development
- Reduce `max_examples` for specific tests if needed
- Check for expensive operations in test setup

### Flaky Tests
- Review test assumptions and constraints
- Check for non-deterministic behavior
- Ensure proper test isolation

### Hypothesis Errors
- Verify strategy constraints are satisfiable
- Check for conflicting assumptions
- Review Hypothesis documentation for strategy composition

## Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- Design Document: `.kiro/specs/retail-failure-simulator/design.md`
- Requirements Document: `.kiro/specs/retail-failure-simulator/requirements.md`
