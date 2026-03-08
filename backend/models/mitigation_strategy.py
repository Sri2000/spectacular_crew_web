"""
Mitigation Strategy database model
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class ComplexityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class MitigationStrategy(Base):
    __tablename__ = "mitigation_strategies"

    strategy_id = Column(String(36), primary_key=True)
    scenario_id = Column(String(36), ForeignKey("failure_scenarios.scenario_id"), nullable=False, index=True)
    strategy_name = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    effectiveness_score = Column(Float, nullable=False)  # 0.0 to 1.0
    implementation_complexity = Column(SQLEnum(ComplexityLevel), nullable=False)
    resource_requirements = Column(JSON, nullable=True)
    timeline_days = Column(Integer, nullable=False)
    cost_estimate = Column(Float, nullable=True)
    trade_offs = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "strategy_id": self.strategy_id,
            "scenario_id": self.scenario_id,
            "strategy_name": self.strategy_name,
            "description": self.description,
            "effectiveness_score": self.effectiveness_score,
            "implementation_complexity": self.implementation_complexity.value if self.implementation_complexity else None,
            "resource_requirements": self.resource_requirements,
            "timeline_days": self.timeline_days,
            "cost_estimate": self.cost_estimate,
            "trade_offs": self.trade_offs,
        }
