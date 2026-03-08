"""
Transfer Optimization API routes

  POST /api/transfers/recommend
       Body: { "store_stats": [...], "transport_cost_per_unit": float, "time_horizon_days": int }
       Returns ranked inter-store stock transfer recommendations.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import uuid
import datetime
import logging

from database import get_db
from engines.transfer_engine import TransferOptimizationEngine
from models import UserAction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transfers", tags=["Stock Transfers"])

_engine = TransferOptimizationEngine()


def _log_action(
    db: Session,
    action_type: str,
    action_details: Dict[str, Any],
    entity_type: str = None,
    entity_id: str = None,
):
    try:
        record = UserAction(
            action_id=str(uuid.uuid4()),
            action_type=action_type,
            action_details=action_details,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            timestamp=datetime.datetime.utcnow(),
        )
        db.add(record)
        db.commit()
    except Exception as exc:
        logger.warning(f"Audit log write failed (non-fatal): {exc}")
        db.rollback()


@router.post("/recommend")
async def recommend_transfers(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Analyse per-store inventory imbalances and return ranked transfer recommendations.

    Body fields:
      store_stats             – list of store×category stat dicts
                                (from enterprise ingestion response → store_stats)
      transport_cost_per_unit – cost to move one unit between any two stores
      time_horizon_days       – planning window for holding-cost savings (default 30)
    """
    store_stats: List[Dict] = payload.get("store_stats", [])
    transport_cost_per_unit: float = float(payload.get("transport_cost_per_unit", 0.0))
    time_horizon_days: int = int(payload.get("time_horizon_days", 30))

    if not store_stats:
        raise HTTPException(status_code=422, detail="store_stats is required and must not be empty")
    if transport_cost_per_unit < 0:
        raise HTTPException(status_code=422, detail="transport_cost_per_unit must be ≥ 0")
    if time_horizon_days <= 0:
        raise HTTPException(status_code=422, detail="time_horizon_days must be > 0")

    try:
        result = await _engine.recommend_transfers(
            store_stats=store_stats,
            transport_cost_per_unit=transport_cost_per_unit,
            time_horizon_days=time_horizon_days,
        )

        _log_action(
            db,
            action_type="TRANSFER_RECOMMENDATION",
            action_details={
                "store_count": len({r["store_id"] for r in store_stats}),
                "category_count": len({r["product_category"] for r in store_stats}),
                "transport_cost_per_unit": transport_cost_per_unit,
                "time_horizon_days": time_horizon_days,
                "viable_transfers": result["viable_transfers"],
                "total_potential_savings": result["total_potential_savings"],
            },
        )

        return {"success": True, **result}

    except Exception as exc:
        logger.error(f"Transfer recommendation error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
