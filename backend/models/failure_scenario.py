"""
Failure Scenario database model
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class ScenarioType(str, enum.Enum):
    OVERSTOCK = "OVERSTOCK"
    STOCKOUT = "STOCKOUT"
    SEASONAL_MISMATCH = "SEASONAL_MISMATCH"
    PRICING_FAILURE = "PRICING_FAILURE"
    FULFILLMENT_FAILURE = "FULFILLMENT_FAILURE"


class FailureScenario(Base):
    __tablename__ = "failure_scenarios"

    scenario_id = Column(String(36), primary_key=True)
    scenario_type = Column(SQLEnum(ScenarioType), nullable=False)
    affected_products = Column(JSON, nullable=False)
    time_horizon = Column(Integer, nullable=False)  # days
    initial_conditions = Column(JSON, nullable=True)
    simulation_parameters = Column(JSON, nullable=True)
    created_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type.value if hasattr(self.scenario_type, 'value') else self.scenario_type,
            "affected_products": self.affected_products,
            "time_horizon": self.time_horizon,
            "initial_conditions": self.initial_conditions,
            "simulation_parameters": self.simulation_parameters,
            "created_timestamp": self.created_timestamp.isoformat() if hasattr(self.created_timestamp, 'isoformat') else str(self.created_timestamp) if self.created_timestamp else None,
        }
