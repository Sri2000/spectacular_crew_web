"""
User Action audit trail database model
"""
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class UserAction(Base):
    __tablename__ = "user_actions"

    action_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True, index=True)  # Nullable for now (no auth)
    action_type = Column(String(100), nullable=False)
    action_details = Column(JSON, nullable=True)
    related_entity_type = Column(String(100), nullable=True)
    related_entity_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "action_id": self.action_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "action_details": self.action_details,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
