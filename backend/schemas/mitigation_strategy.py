"""
Mitigation Strategy Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class MitigationStrategySchema(BaseModel):
    strategy_id: str
    scenario_id: str
    strategy_name: str
    description: str
    effectiveness_score: float = Field(ge=0.0, le=1.0)
    implementation_complexity: ComplexityLevel
    resource_requirements: Optional[Dict[str, Any]] = None
    timeline_days: int = Field(gt=0)
    cost_estimate: Optional[float] = None
    trade_offs: Optional[List[str]] = None

    class Config:
        from_attributes = True


class MitigationStrategyCreate(BaseModel):
    scenario_id: str
    strategy_name: str
    description: str
    effectiveness_score: float = Field(ge=0.0, le=1.0)
    implementation_complexity: ComplexityLevel
    resource_requirements: Optional[Dict[str, Any]] = None
    timeline_days: int = Field(gt=0)
    cost_estimate: Optional[float] = None
    trade_offs: Optional[List[str]] = None


class MitigationStrategyResponse(MitigationStrategySchema):
    class Config:
        from_attributes = True
