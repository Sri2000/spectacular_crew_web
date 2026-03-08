"""
Failure Propagation Score Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class FailurePropagationScoreSchema(BaseModel):
    scenario_id: str
    overall_score: float = Field(ge=0.0, le=10.0)
    function_impacts: Dict[str, float]  # inventory, pricing, fulfillment, revenue
    cascade_depth: int = Field(ge=0)
    affected_business_units: Optional[List[str]] = None
    calculation_timestamp: datetime
    confidence_metrics: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class FailurePropagationScoreCreate(BaseModel):
    scenario_id: str
    overall_score: float = Field(ge=0.0, le=10.0)
    function_impacts: Dict[str, float]
    cascade_depth: int = Field(ge=0)
    affected_business_units: Optional[List[str]] = None
    confidence_metrics: Optional[Dict[str, float]] = None


class FailurePropagationScoreResponse(FailurePropagationScoreSchema):
    id: str

    class Config:
        from_attributes = True
