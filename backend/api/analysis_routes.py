"""
Analysis API routes (Risk, Simulation, Propagation, Executive Summary, Mitigation)

Existing routes (frontend-compatible):
  POST /api/analysis/risk/analyze
  POST /api/analysis/simulate
  GET  /api/analysis/scenarios
  GET  /api/analysis/scenarios/{id}
  GET  /api/analysis/risks
  GET  /api/analysis/audit

Spec routes:
  GET  /api/analysis/propagation/{id}
  GET  /api/analysis/executive-summary/{id}
  GET  /api/analysis/mitigation/{id}

Enterprise routes (for 17-column enterprise dataset):
  POST /api/analysis/risk/analyze-enterprise
       Accepts: { "records": [...] }   (raw enterprise rows)
            OR: { "category_stats": [...] } (pre-aggregated from ingestion response)

  POST /api/analysis/simulate-seeded
       Accepts a simulation_seeds item from ingestion response to auto-populate
       simulation params from real data.  Optional overrides accepted.

  GET  /api/analysis/enterprise-summary
       Returns a cross-category enterprise risk dashboard (most recent risks).
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict, List
import uuid
import datetime
import logging
import time

from database import get_db
from services.dynamodb_service import DynamoDBService
from config import settings
from engines.risk_engine import RiskEngine
from engines.simulation_engine import SimulationEngine
from engines.propagation_engine import PropagationEngine
from engines.ai_reasoning_engine import AIReasoningEngine
from engines.mitigation_engine import MitigationEngine
from models import (
    RiskAssessment, FailureScenario, FailurePropagationScore,
    ExecutiveSummary, MitigationStrategy, SimulationResult, UserAction,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "dummy_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return "admin"

router = APIRouter(prefix="/api/analysis", tags=["Analysis"], dependencies=[Depends(get_current_user)])


# ── Audit helper ─────────────────────────────────────────────────────────────

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


# ── POST /api/analysis/risk/analyze ─────────────────────────────────────────

@router.post("/risk/analyze")
async def analyze_risks(
    market_data: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze seasonal/demand risks from market data records using RiskEngine."""
    try:
        engine = RiskEngine()
        risk_assessments = await engine.analyze_risks(market_data.get("records", []))

        saved_risks = []
        for risk in risk_assessments:
            db_risk = RiskAssessment(
                id=risk.get("id", str(uuid.uuid4())),
                product_category=risk.get("product_category", "UNKNOWN"),
                risk_score=risk.get("risk_score", 0.0),
                risk_type=risk.get("risk_type", "SEASONAL_MISMATCH"),
                confidence_level=risk.get("confidence_level", 0.0),
                detection_timestamp=risk.get("detection_timestamp", datetime.datetime.utcnow()),
                contributing_factors=risk.get("contributing_factors"),
                historical_comparison=risk.get("historical_comparison"),
            )
            db.add(db_risk)
            saved_risks.append({
                **risk,
                "detection_timestamp": risk["detection_timestamp"].isoformat()
                    if hasattr(risk.get("detection_timestamp"), "isoformat") else str(risk.get("detection_timestamp")),
            })

        db.commit()

        _log_action(
            db, "RISK_ANALYSIS",
            {"risk_count": len(saved_risks)},
            entity_type="RiskAssessment",
        )
        return {"success": True, "risk_count": len(saved_risks), "risks": saved_risks}

    except Exception as exc:
        logger.error(f"Risk analysis error: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /api/analysis/simulate ─────────────────────────────────────────────

@router.post("/simulate")
async def simulate_scenario(
    scenario_data: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Run full simulation pipeline: simulate → propagate → AI summary → strategies."""
    summary = None
    strategies: List[Dict[str, Any]] = []
    impact_result = None

    try:
        t_start = time.time()
        scenario_id = str(uuid.uuid4())
        scenario_data["scenario_id"] = scenario_id

        # Persist scenario
        db_scenario = FailureScenario(
            scenario_id=scenario_id,
            scenario_type=scenario_data["scenario_type"],
            affected_products=scenario_data.get("affected_products", []),
            time_horizon=scenario_data.get("time_horizon", 30),
            initial_conditions=scenario_data.get("initial_conditions"),
            simulation_parameters=scenario_data.get("simulation_parameters"),
        )
        db.add(db_scenario)

        # ── 1. Run simulation ──────────────────────────────────────────────
        simulation_result = await SimulationEngine().simulate(scenario_data)
        if not simulation_result:
            raise HTTPException(status_code=500, detail="Simulation failed to produce results")

        exec_time = round(time.time() - t_start, 3)
        simulation_result["execution_time_seconds"] = exec_time

        db_result = SimulationResult(
            result_id=simulation_result["result_id"],
            scenario_id=scenario_id,
            simulation_data=simulation_result.get("simulation_data"),
            inventory_levels=simulation_result.get("inventory_levels"),
            stockout_probabilities=simulation_result.get("stockout_probabilities"),
            overstock_costs=simulation_result.get("overstock_costs"),
            execution_time_seconds=exec_time,
            simulation_timestamp=simulation_result.get("simulation_timestamp", datetime.datetime.utcnow()),
        )
        db.add(db_result)

        # ── 2. Propagation analysis ────────────────────────────────────────
        impact_result = await PropagationEngine().compute_propagation(scenario_data, simulation_result)

        if impact_result:
            db_impact = FailurePropagationScore(
                id=impact_result["id"],
                scenario_id=scenario_id,
                overall_score=impact_result.get("overall_score", 0),
                cascade_depth=impact_result.get("cascade_depth", 0),
                function_impacts=impact_result.get("function_impacts"),
                affected_business_units=impact_result.get("affected_business_units"),
                confidence_metrics=impact_result.get("confidence_metrics"),
                calculation_timestamp=impact_result.get("calculation_timestamp", datetime.datetime.utcnow()),
            )
            db.add(db_impact)

            # ── 3. AI executive summary ────────────────────────────────────
            summary = await AIReasoningEngine().generate_executive_summary(
                scenario_data, impact_result, simulation_result
            )

            if summary:
                db_summary = ExecutiveSummary(
                    summary_id=summary["summary_id"],
                    scenario_id=scenario_id,
                    revenue_risk=summary.get("revenue_risk", ""),
                    market_reason=summary.get("market_reason", ""),
                    urgency_level=summary.get("urgency_level", "Low"),
                    recommended_actions=summary.get("recommended_actions"),
                    trade_offs=summary.get("trade_offs"),
                    explanation=summary.get("explanation", ""),
                    confidence_score=summary.get("confidence_score"),
                )
                db.add(db_summary)

            # ── 4. Mitigation strategies ───────────────────────────────────
            strategies = await MitigationEngine().generate_strategies(scenario_data, impact_result)
            for strat in strategies:
                db.add(MitigationStrategy(
                    strategy_id=strat["strategy_id"],
                    scenario_id=scenario_id,
                    strategy_name=strat["strategy_name"],
                    description=strat["description"],
                    effectiveness_score=strat["effectiveness_score"],
                    implementation_complexity=strat["implementation_complexity"],
                    resource_requirements=strat.get("resource_requirements"),
                    timeline_days=strat["timeline_days"],
                    cost_estimate=strat.get("cost_estimate"),
                    trade_offs=strat.get("trade_offs"),
                ))

        db.commit()

        # Save simulation summary to DynamoDB (non-blocking)
        DynamoDBService().put_item(
            settings.DYNAMO_TABLE_SIMULATIONS,
            {
                "scenario_id": scenario_id,
                "scenario_type": scenario_data.get("scenario_type", ""),
                "affected_products": ", ".join(scenario_data.get("affected_products", [])),
                "urgency_level": summary.get("urgency_level", "Unknown") if summary else "Unknown",
                "projected_revenue_loss": str(simulation_result.get("projected_revenue_loss", 0)),
                "propagation_score": str(impact_result.get("overall_score", 0) if impact_result else 0),
                "generated_by": summary.get("generated_by", "none") if summary else "none",
                "simulated_at": datetime.datetime.utcnow().isoformat(),
            },
            hash_key="scenario_id",
        )

        # Audit log
        _log_action(
            db, "SIMULATION",
            {
                "scenario_type": scenario_data.get("scenario_type"),
                "affected_products": scenario_data.get("affected_products", []),
                "time_horizon": scenario_data.get("time_horizon"),
                "propagation_score": impact_result.get("overall_score") if impact_result else None,
                "urgency_level": summary.get("urgency_level") if summary else None,
                "generated_by": summary.get("generated_by", "none") if summary else "none",
                "projected_revenue_loss": simulation_result.get("projected_revenue_loss"),
            },
            entity_type="FailureScenario",
            entity_id=scenario_id,
        )

        return {
            "success": True,
            "scenario_id": scenario_id,
            "simulation": _serialise(simulation_result),
            "impact": _serialise(impact_result),
            "summary": _serialise(summary),
            "strategies": [_serialise(s) for s in strategies],
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Simulation error: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/scenarios ─────────────────────────────────────────────

@router.get("/scenarios")
async def get_scenarios(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List last 50 scenarios."""
    print("Getting scenarios")
    try:
        rows = (
            db.query(FailureScenario)
            .order_by(FailureScenario.created_timestamp.desc())
            .limit(50)
            .all()
        )
        return [s.to_dict() for s in rows]
    except Exception as exc:
        logger.error(f"Get scenarios error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/scenarios/{scenario_id} ────────────────────────────────

@router.get("/scenarios/{scenario_id}")
async def get_scenario_details(
    scenario_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Full scenario detail (simulation, impact, summary, strategies)."""
    try:
        scenario = (
            db.query(FailureScenario)
            .filter(FailureScenario.scenario_id == scenario_id)
            .first()
        )
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

        simulation = (
            db.query(SimulationResult)
            .filter(SimulationResult.scenario_id == scenario_id)
            .first()
        )
        impact = (
            db.query(FailurePropagationScore)
            .filter(FailurePropagationScore.scenario_id == scenario_id)
            .first()
        )
        summary = (
            db.query(ExecutiveSummary)
            .filter(ExecutiveSummary.scenario_id == scenario_id)
            .first()
        )
        strategies = (
            db.query(MitigationStrategy)
            .filter(MitigationStrategy.scenario_id == scenario_id)
            .all()
        )

        return {
            "scenario": scenario.to_dict(),
            "simulation": simulation.to_dict() if simulation else None,
            "impact": impact.to_dict() if impact else None,
            "summary": summary.to_dict() if summary else None,
            "strategies": [s.to_dict() for s in strategies],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Get scenario details error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/risks ─────────────────────────────────────────────────

@router.get("/risks")
async def get_risks(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Last 100 risk assessments."""
    print("Getting risks")
    try:
        rows = (
            db.query(RiskAssessment)
            .order_by(RiskAssessment.detection_timestamp.desc())
            .limit(100)
            .all()
        )
        return [r.to_dict() for r in rows]
    except Exception as exc:
        logger.error(f"Get risks error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/audit ─────────────────────────────────────────────────

@router.get("/audit")
async def get_audit_trail(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Audit trail (last 100 actions)."""
    try:
        rows = (
            db.query(UserAction)
            .order_by(UserAction.timestamp.desc())
            .limit(100)
            .all()
        )
        return [a.to_dict() for a in rows]
    except Exception as exc:
        logger.error(f"Audit trail error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/propagation/{scenario_id}  (NEW) ──────────────────────

@router.get("/propagation/{scenario_id}")
async def get_propagation(
    scenario_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Return propagation score for a scenario."""
    try:
        row = (
            db.query(FailurePropagationScore)
            .filter(FailurePropagationScore.scenario_id == scenario_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Propagation data not found for this scenario")
        return row.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Get propagation error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/executive-summary/{scenario_id}  (NEW) ────────────────

@router.get("/executive-summary/{scenario_id}")
async def get_executive_summary(
    scenario_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Return executive summary (AI or rule-based) for a scenario."""
    try:
        row = (
            db.query(ExecutiveSummary)
            .filter(ExecutiveSummary.scenario_id == scenario_id)
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Executive summary not found for this scenario")
        return row.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Get executive summary error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/mitigation/{scenario_id}  (NEW) ───────────────────────

@router.get("/mitigation/{scenario_id}")
async def get_mitigation(
    scenario_id: str, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Return ranked mitigation strategies for a scenario."""
    try:
        rows = (
            db.query(MitigationStrategy)
            .filter(MitigationStrategy.scenario_id == scenario_id)
            .all()
        )
        if not rows:
            raise HTTPException(status_code=404, detail="No mitigation strategies found for this scenario")
        return [s.to_dict() for s in rows]
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Get mitigation error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# Enterprise Dataset Routes
# ═══════════════════════════════════════════════════════════════════════════════

# ── POST /api/analysis/risk/analyze-enterprise ───────────────────────────────

@router.post("/risk/analyze-enterprise")
async def analyze_enterprise_risks(
    payload: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze the enterprise 17-column dataset.

    Accepts ONE of:
      { "records": [...] }          – raw enterprise rows (all 17 columns)
      { "category_stats": [...] }   – pre-aggregated stats from ingestion response
                                      (RECOMMENDED for large files: avoids re-processing
                                       262k+ rows through the API)

    Returns per-category RiskAssessments with financial exposure metrics.
    """
    try:
        engine = RiskEngine()

        if "category_stats" in payload and payload["category_stats"]:
            # Fast path: use pre-aggregated stats from DataIngestionService
            risk_assessments = await engine.analyze_from_category_stats(
                payload["category_stats"]
            )
            mode = "category_stats"
        elif "records" in payload and payload["records"]:
            risk_assessments = await engine.analyze_enterprise_risks(payload["records"])
            mode = "records"
        else:
            raise HTTPException(
                status_code=400,
                detail="Payload must contain 'records' (enterprise rows) or 'category_stats'",
            )

        saved_risks: List[Dict[str, Any]] = []
        for risk in risk_assessments:
            db_risk = RiskAssessment(
                id=risk.get("id", str(uuid.uuid4())),
                product_category=risk.get("product_category", "UNKNOWN"),
                risk_score=risk.get("risk_score", 0.0),
                risk_type=risk.get("risk_type", "SEASONAL_MISMATCH"),
                confidence_level=risk.get("confidence_level", 0.0),
                detection_timestamp=risk.get("detection_timestamp", datetime.datetime.utcnow()),
                contributing_factors=risk.get("contributing_factors"),
                historical_comparison=risk.get("historical_comparison"),
            )
            db.add(db_risk)
            saved_risks.append(_serialise(risk))

        db.commit()

        _log_action(
            db, "ENTERPRISE_RISK_ANALYSIS",
            {"risk_count": len(saved_risks), "input_mode": mode},
            entity_type="RiskAssessment",
        )

        # Build quick financial summary across categories
        total_exposure = sum(
            r.get("financial_exposure", {}).get("estimated_revenue_at_risk", 0)
            for r in saved_risks
        )
        critical_categories = [
            r["product_category"]
            for r in saved_risks
            if r.get("severity_level") in ("CRITICAL", "HIGH")
        ]

        return {
            "success": True,
            "input_mode": mode,
            "risk_count": len(saved_risks),
            "risks": saved_risks,
            "dashboard": {
                "total_estimated_revenue_at_risk": round(total_exposure, 2),
                "critical_and_high_categories": critical_categories,
                "severity_breakdown": _severity_breakdown(saved_risks),
                "dominant_risk_types": _risk_type_breakdown(saved_risks),
            },
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Enterprise risk analysis error: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /api/analysis/simulate-seeded ───────────────────────────────────────

@router.post("/simulate-seeded")
async def simulate_seeded(
    payload: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run simulation pre-seeded from enterprise dataset statistics.

    Accepts a simulation_seed dict from DataIngestionService output:
    {
      "product_category": "Electronics",
      "dominant_scenario": "OVERSTOCK",        # auto-detected; can be overridden
      "simulation_parameters": { ... },         # from real data
      "initial_conditions": { ... },            # from real data
      "time_horizon": 30,                       # optional override (default 30)
      "affected_products": ["Electronics"]      # optional override
    }

    All fields from the seed can be overridden in the payload.
    """
    try:
        seed = payload.get("seed") or payload  # accept either wrapper or flat

        scenario_type = (
            payload.get("scenario_type")
            or seed.get("dominant_scenario", "OVERSTOCK")
        )
        product_category = seed.get("product_category", "UNKNOWN")
        time_horizon = int(payload.get("time_horizon", seed.get("time_horizon", 30)))
        affected_products = payload.get(
            "affected_products", [product_category]
        )

        scenario_data = {
            "scenario_type": scenario_type,
            "affected_products": affected_products,
            "time_horizon": time_horizon,
            "initial_conditions": {
                **seed.get("initial_conditions", {}),
                **payload.get("initial_conditions", {}),
            },
            "simulation_parameters": {
                **seed.get("simulation_parameters", {}),
                **payload.get("simulation_parameters", {}),
            },
        }

        t_start = time.time()
        scenario_id = str(uuid.uuid4())
        scenario_data["scenario_id"] = scenario_id

        db_scenario = FailureScenario(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            affected_products=affected_products,
            time_horizon=time_horizon,
            initial_conditions=scenario_data["initial_conditions"],
            simulation_parameters=scenario_data["simulation_parameters"],
        )
        db.add(db_scenario)

        simulation_result = await SimulationEngine().simulate(scenario_data)
        if not simulation_result:
            raise HTTPException(status_code=500, detail="Seeded simulation failed")

        exec_time = round(time.time() - t_start, 3)
        simulation_result["execution_time_seconds"] = exec_time

        db_result = SimulationResult(
            result_id=simulation_result["result_id"],
            scenario_id=scenario_id,
            simulation_data=simulation_result.get("simulation_data"),
            inventory_levels=simulation_result.get("inventory_levels"),
            stockout_probabilities=simulation_result.get("stockout_probabilities"),
            overstock_costs=simulation_result.get("overstock_costs"),
            execution_time_seconds=exec_time,
            simulation_timestamp=simulation_result.get(
                "simulation_timestamp", datetime.datetime.utcnow()
            ),
        )
        db.add(db_result)

        impact_result = await PropagationEngine().compute_propagation(
            scenario_data, simulation_result
        )
        if impact_result:
            db_impact = FailurePropagationScore(
                id=impact_result["id"],
                scenario_id=scenario_id,
                overall_score=impact_result.get("overall_score", 0),
                cascade_depth=impact_result.get("cascade_depth", 0),
                function_impacts=impact_result.get("function_impacts"),
                affected_business_units=impact_result.get("affected_business_units"),
                confidence_metrics=impact_result.get("confidence_metrics"),
                calculation_timestamp=impact_result.get(
                    "calculation_timestamp", datetime.datetime.utcnow()
                ),
            )
            db.add(db_impact)

        summary = await AIReasoningEngine().generate_executive_summary(
            scenario_data, impact_result or {}, simulation_result
        )
        if summary:
            db.add(ExecutiveSummary(
                summary_id=summary["summary_id"],
                scenario_id=scenario_id,
                revenue_risk=summary.get("revenue_risk", ""),
                market_reason=summary.get("market_reason", ""),
                urgency_level=summary.get("urgency_level", "Low"),
                recommended_actions=summary.get("recommended_actions"),
                trade_offs=summary.get("trade_offs"),
                explanation=summary.get("explanation", ""),
                confidence_score=summary.get("confidence_score"),
            ))

        strategies = await MitigationEngine().generate_strategies(
            scenario_data, impact_result or {}
        )
        for strat in strategies:
            db.add(MitigationStrategy(
                strategy_id=strat["strategy_id"],
                scenario_id=scenario_id,
                strategy_name=strat["strategy_name"],
                description=strat["description"],
                effectiveness_score=strat["effectiveness_score"],
                implementation_complexity=strat["implementation_complexity"],
                resource_requirements=strat.get("resource_requirements"),
                timeline_days=strat["timeline_days"],
                cost_estimate=strat.get("cost_estimate"),
                trade_offs=strat.get("trade_offs"),
            ))

        db.commit()

        _log_action(
            db, "SEEDED_SIMULATION",
            {
                "product_category": product_category,
                "scenario_type": scenario_type,
                "seeded_from": "enterprise_dataset",
                "projected_revenue_loss": simulation_result.get("projected_revenue_loss"),
            },
            entity_type="FailureScenario",
            entity_id=scenario_id,
        )

        return {
            "success": True,
            "scenario_id": scenario_id,
            "seeded_from": {
                "product_category": product_category,
                "scenario_type": scenario_type,
                "time_horizon": time_horizon,
            },
            "simulation": _serialise(simulation_result),
            "impact": _serialise(impact_result),
            "summary": _serialise(summary),
            "strategies": [_serialise(s) for s in strategies],
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Seeded simulation error: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /api/analysis/enterprise-summary ─────────────────────────────────────

@router.get("/enterprise-summary")
async def get_enterprise_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Cross-category enterprise risk dashboard.
    Returns the most recent risk assessment per product category
    along with aggregated financial exposure metrics.
    """
    try:
        all_risks = (
            db.query(RiskAssessment)
            .order_by(RiskAssessment.detection_timestamp.desc())
            .limit(200)
            .all()
        )

        # De-duplicate: keep most recent per category
        seen: Dict[str, Any] = {}
        for r in all_risks:
            cat = r.product_category
            if cat not in seen:
                seen[cat] = r.to_dict()

        category_risks = list(seen.values())

        # Financial exposure (from contributing_factors if available)
        total_revenue_at_risk = 0.0
        for r in category_risks:
            cf = r.get("contributing_factors") or {}
            # Try financial_exposure if stored
            fe = r.get("financial_exposure") or {}
            total_revenue_at_risk += fe.get("estimated_revenue_at_risk", 0)

        return {
            "success": True,
            "categories_assessed": len(category_risks),
            "category_risks": category_risks,
            "severity_breakdown": _severity_breakdown(category_risks),
            "dominant_risk_types": _risk_type_breakdown(category_risks),
            "total_revenue_at_risk_estimate": round(total_revenue_at_risk, 2),
        }

    except Exception as exc:
        logger.error(f"Enterprise summary error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Serialisation helper ─────────────────────────────────────────────────────

def _serialise(obj):
    """Recursively convert datetime and other non-JSON-serialisable objects."""
    if obj is None:
        return None
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialise(v) for v in obj]
    return obj


# ── Dashboard helpers ────────────────────────────────────────────────────────

def _severity_breakdown(risks: List[Dict[str, Any]]) -> Dict[str, int]:
    breakdown: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in risks:
        sev = (r.get("severity_level") or "LOW").upper()
        breakdown[sev] = breakdown.get(sev, 0) + 1
    return breakdown


def _risk_type_breakdown(risks: List[Dict[str, Any]]) -> Dict[str, int]:
    breakdown: Dict[str, int] = {}
    for r in risks:
        rt = r.get("risk_type") or "UNKNOWN"
        breakdown[rt] = breakdown.get(rt, 0) + 1
    return breakdown
