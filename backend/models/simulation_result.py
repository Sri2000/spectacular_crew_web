"""
Simulation Result database model
"""
from sqlalchemy import Column, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    result_id = Column(String(36), primary_key=True)
    scenario_id = Column(String(36), ForeignKey("failure_scenarios.scenario_id"), nullable=False, index=True)
    simulation_data = Column(JSON, nullable=False)  # Time series data
    inventory_levels = Column(JSON, nullable=True)
    stockout_probabilities = Column(JSON, nullable=True)
    overstock_costs = Column(JSON, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    simulation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "result_id": self.result_id,
            "scenario_id": self.scenario_id,
            "simulation_data": self.simulation_data,
            "inventory_levels": self.inventory_levels,
            "stockout_probabilities": self.stockout_probabilities,
            "overstock_costs": self.overstock_costs,
            "execution_time_seconds": self.execution_time_seconds,
            "simulation_timestamp": self.simulation_timestamp.isoformat() if self.simulation_timestamp else None,
        }
