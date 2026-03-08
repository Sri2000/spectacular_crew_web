"""
Executive Summary Pydantic schemas
"""
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class ExecutiveSummarySchema(BaseModel):
    summary_id: str
    scenario_id: str
    revenue_risk: str
    market_reason: str
    urgency_level: str
    recommended_actions: Optional[List[str]] = None
    trade_offs: Optional[Dict[str, str]] = None
    generated_timestamp: datetime

    class Config:
        from_attributes = True


class ExecutiveSummaryCreate(BaseModel):
    scenario_id: str
    revenue_risk: str
    market_reason: str
    urgency_level: str
    recommended_actions: Optional[List[str]] = None
    trade_offs: Optional[Dict[str, str]] = None


class ExecutiveSummaryResponse(ExecutiveSummarySchema):
    class Config:
        from_attributes = True
