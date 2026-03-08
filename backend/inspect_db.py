from database import SessionLocal
from models import RiskAssessment
import uuid
from datetime import datetime

db = SessionLocal()
# Insert sample risk assessments
risks = [
    {
        "id": str(uuid.uuid4()),
        "product_category": "Electronics",
        "risk_score": 0.85,
        "risk_type": "STOCKOUT",
        "confidence_level": 0.92,
        "detection_timestamp": datetime.utcnow(),
        "contributing_factors": ["High demand variability", "Supply chain delays"],
        "historical_comparison": {"previous_quarter": 0.75, "last_year": 0.80}
    },
    {
        "id": str(uuid.uuid4()),
        "product_category": "Clothing",
        "risk_score": 0.65,
        "risk_type": "OVERSTOCK",
        "confidence_level": 0.78,
        "detection_timestamp": datetime.utcnow(),
        "contributing_factors": ["Seasonal mismatch", "Overproduction"],
        "historical_comparison": {"previous_quarter": 0.60, "last_year": 0.70}
    },
    {
        "id": str(uuid.uuid4()),
        "product_category": "Home Goods",
        "risk_score": 0.45,
        "risk_type": "SEASONAL_MISMATCH",
        "confidence_level": 0.85,
        "detection_timestamp": datetime.utcnow(),
        "contributing_factors": ["Weather patterns", "Consumer trends"],
        "historical_comparison": {"previous_quarter": 0.50, "last_year": 0.55}
    }
]

for risk_data in risks:
    risk = RiskAssessment(**risk_data)
    db.add(risk)

db.commit()
print("Inserted sample risk assessments")
db.close()