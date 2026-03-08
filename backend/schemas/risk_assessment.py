"""
Risk Assessment Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class RiskType(str, Enum):
    SEASONAL_MISMATCH = "SEASONAL_MISMATCH"
    OVERSTOCK = "OVERSTOCK"
    STOCKOUT = "STOCKOUT"


class RiskAssessmentSchema(BaseModel):
    product_category: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_type: RiskType
    confidence_level: float = Field(ge=0.0, le=1.0)
    detection_timestamp: datetime
    contributing_factors: Optional[List[str]] = None
    historical_comparison: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class RiskAssessmentCreate(BaseModel):
    product_category: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_type: RiskType
    confidence_level: float = Field(ge=0.0, le=1.0)
    contributing_factors: Optional[List[str]] = None
    historical_comparison: Optional[Dict[str, float]] = None


class RiskAssessmentResponse(RiskAssessmentSchema):
    id: str

    class Config:
        from_attributes = True
