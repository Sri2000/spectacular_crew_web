"""
Failure Propagation Score database model
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from database import Base


class FailurePropagationScore(Base):
    __tablename__ = "failure_propagation_scores"

    id = Column(String(36), primary_key=True)
    scenario_id = Column(String(36), ForeignKey("failure_scenarios.scenario_id"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)  # 0.0 to 10.0
    function_impacts = Column(JSON, nullable=False)  # inventory, pricing, fulfillment, revenue
    cascade_depth = Column(Integer, nullable=False)
    affected_business_units = Column(JSON, nullable=True)
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confidence_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "overall_score": self.overall_score,
            "function_impacts": self.function_impacts,
            "cascade_depth": self.cascade_depth,
            "affected_business_units": self.affected_business_units,
            "calculation_timestamp": self.calculation_timestamp.isoformat() if self.calculation_timestamp else None,
            "confidence_metrics": self.confidence_metrics,
        }
