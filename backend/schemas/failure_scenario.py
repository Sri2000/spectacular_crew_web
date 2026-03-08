"""
Failure Scenario Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ScenarioType(str, Enum):
    OVERSTOCK = "OVERSTOCK"
    STOCKOUT = "STOCKOUT"
    SEASONAL_MISMATCH = "SEASONAL_MISMATCH"
    PRICING_FAILURE = "PRICING_FAILURE"
    FULFILLMENT_FAILURE = "FULFILLMENT_FAILURE"


class FailureScenarioSchema(BaseModel):
    scenario_id: str
    scenario_type: ScenarioType
    affected_products: List[str]
    time_horizon: int = Field(gt=0)  # days
    initial_conditions: Optional[Dict[str, Any]] = None
    simulation_parameters: Optional[Dict[str, float]] = None
    created_timestamp: datetime

    class Config:
        from_attributes = True


class FailureScenarioCreate(BaseModel):
    scenario_type: ScenarioType
    affected_products: List[str]
    time_horizon: int = Field(gt=0)
    initial_conditions: Optional[Dict[str, Any]] = None
    simulation_parameters: Optional[Dict[str, float]] = None


class FailureScenarioResponse(FailureScenarioSchema):
    class Config:
        from_attributes = True
