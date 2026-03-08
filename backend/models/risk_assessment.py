"""
Risk Assessment database model
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class RiskType(str, enum.Enum):
    SEASONAL_MISMATCH = "SEASONAL_MISMATCH"
    OVERSTOCK = "OVERSTOCK"
    STOCKOUT = "STOCKOUT"


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True)
    product_category = Column(String(255), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_type = Column(SQLEnum(RiskType), nullable=False)
    confidence_level = Column(Float, nullable=False)
    detection_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    contributing_factors = Column(JSON, nullable=True)
    historical_comparison = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "product_category": self.product_category,
            "risk_score": self.risk_score,
            "risk_type": self.risk_type.value if hasattr(self.risk_type, 'value') else self.risk_type if self.risk_type else None,
            "confidence_level": self.confidence_level,
            "detection_timestamp": self.detection_timestamp.isoformat() if hasattr(self.detection_timestamp, 'isoformat') else str(self.detection_timestamp) if self.detection_timestamp else None,
            "contributing_factors": self.contributing_factors,
            "historical_comparison": self.historical_comparison,
        }
