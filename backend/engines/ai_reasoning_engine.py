"""
AI Reasoning Engine — Google Gemini
Generates structured executive summaries using the Gemini API.

Model is controlled by GEMINI_MODEL_ID in .env:
    gemini-2.0-flash   ← default (fast, cost-efficient)
    gemini-1.5-pro     ← deep reasoning
    gemini-1.5-flash   ← fast, lower cost

Falls back to rule-based deterministic logic on any API error.

Output schema (enforced):
{
  "revenue_risk":         "...",
  "market_reason":        "...",
  "urgency_level":        "Critical|High|Medium|Low",
  "recommended_actions":  ["...", ...],
  "trade_offs":           ["...", ...],
  "explanation":          "...",
  "confidence_score":     "0.00"
}
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ── System instruction sent to Gemini ────────────────────────────────────────
_SYSTEM_INSTRUCTION = (
    "You are a senior retail risk strategist AI for the AI Bharat platform. "
    "Your job is to analyse retail failure simulations and produce executive-level risk briefings.\n\n"
    "STRICT RULES:\n"
    "1. Output ONLY a single valid JSON object — no markdown fences, no prose, no preamble.\n"
    "2. Never invent or extrapolate numerical figures beyond those provided in the prompt.\n"
    "3. Base all statements strictly on the supplied simulation metrics.\n"
    "4. Use only these urgency levels: Critical, High, Medium, Low.\n"
    "5. confidence_score must be a decimal string between '0.00' and '1.00'.\n"
    "6. recommended_actions must be a JSON array of strings (3–5 items).\n"
    "7. trade_offs must be a JSON array of strings describing option trade-offs.\n"
    "8. Explain the reasoning chain clearly in the explanation field."
)

_REQUIRED_KEYS = {
    "revenue_risk", "market_reason", "urgency_level",
    "recommended_actions", "trade_offs", "explanation", "confidence_score",
}


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that some models wrap around JSON."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        inner = parts[1] if len(parts) > 1 else ""
        if inner.startswith("json"):
            inner = inner[4:]
        text = inner.strip()
    return text


class AIReasoningEngine:
    """
    AI reasoning engine — tries AWS Bedrock first, then Google Gemini, then rule-based.
    """

    def __init__(self):
        # Gemini state
        self._model = None
        self._available: bool | None = None   # None = untested
        self._model_id: str | None = None
        # Bedrock state
        self._bedrock_client = None
        self._bedrock_available: bool | None = None
        self._bedrock_model_id: str | None = None

    # ── Lazy client init ──────────────────────────────────────────────────────

    def _get_bedrock_client(self):
        if self._bedrock_available is False:
            return None
        if self._bedrock_client is not None:
            return self._bedrock_client
        try:
            import boto3
            from config import settings
            self._bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
            self._bedrock_model_id = settings.AWS_BEDROCK_MODEL_ID
            self._bedrock_available = True
            logger.info(f"Bedrock client ready | model={self._bedrock_model_id}")
        except Exception as exc:
            logger.warning(f"Bedrock unavailable: {exc}")
            self._bedrock_available = False
        return self._bedrock_client

    def _get_model(self):
        if self._available is False:
            return None
        if self._model is not None:
            return self._model

        try:
            import google.generativeai as genai
            from config import settings

            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set in .env")

            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model_id = settings.GEMINI_MODEL_ID

            self._model = genai.GenerativeModel(
                model_name=self._model_id,
                system_instruction=_SYSTEM_INSTRUCTION,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 1024,
                    "response_mime_type": "application/json",
                },
            )
            self._available = True
            logger.info(f"Gemini client ready | model={self._model_id}")

        except Exception as exc:
            logger.warning(f"Gemini unavailable — rule-based fallback active: {exc}")
            self._available = False

        return self._model

    # ── Core invoke ───────────────────────────────────────────────────────────

    def _bedrock_invoke(self, prompt: str) -> Dict[str, Any]:
        client = self._get_bedrock_client()
        if client is None:
            raise RuntimeError("Bedrock client not available")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": _SYSTEM_INSTRUCTION,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = client.invoke_model(
            modelId=self._bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        text = json.loads(response["body"].read())["content"][0]["text"].strip()
        text = _strip_fences(text)
        data = json.loads(text)
        missing = _REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"Bedrock response missing keys: {missing}")
        logger.info(f"Bedrock response received | model={self._bedrock_model_id}")
        return data

    def _gemini_invoke(self, prompt: str) -> Dict[str, Any]:
        model = self._get_model()
        if model is None:
            raise RuntimeError("Gemini model not available")

        response = model.generate_content(prompt)
        text = response.text.strip()
        text = _strip_fences(text)
        data = json.loads(text)   # ValueError triggers fallback

        missing = _REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"Gemini response missing keys: {missing}")

        logger.info(f"Gemini response received | model={self._model_id}")
        return data

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_executive_summary(
        self,
        scenario: Dict[str, Any],
        propagation_score: Dict[str, Any],
        simulation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate 7-field executive summary.
        Priority: Bedrock → Gemini → rule-based fallback.
        """
        prompt = self._build_prompt(scenario, propagation_score, simulation_result)

        # 1. Try Bedrock (Claude)
        try:
            data = self._bedrock_invoke(prompt)
            logger.info(f"Executive summary generated by Bedrock ({self._bedrock_model_id})")
            return self._wrap(scenario, data, source=f"bedrock:{self._bedrock_model_id}")
        except Exception as exc:
            logger.warning(f"Bedrock summary failed ({exc}), trying Gemini")

        # 2. Try Gemini
        try:
            data = self._gemini_invoke(prompt)
            logger.info(f"Executive summary generated by Gemini ({self._model_id})")
            return self._wrap(scenario, data, source=f"gemini:{self._model_id}")
        except Exception as exc:
            logger.warning(f"Gemini summary failed ({exc}), using rule-based fallback")

        # 3. Rule-based fallback
        return self._rule_based_summary(scenario, propagation_score, simulation_result)

    async def generate_explanation(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured explanation — Gemini with rule-based fallback."""
        try:
            prompt = self._build_explanation_prompt(decision_context)
            data = self._gemini_invoke(prompt)
            data["generated_by"] = f"gemini:{self._model_id}"
            return data
        except Exception as exc:
            logger.warning(f"Gemini explanation failed ({exc}), using rule-based fallback")
            return self._rule_based_explanation(decision_context)

    # ── Prompt builders ───────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(
        scenario: Dict[str, Any],
        ps: Dict[str, Any],
        sim: Dict[str, Any],
    ) -> str:
        stype = scenario.get("scenario_type", "UNKNOWN")
        products = scenario.get("affected_products", [])
        horizon = scenario.get("time_horizon", 30)
        overall = ps.get("overall_score", 0)
        depth = ps.get("cascade_depth", 0)
        fi = ps.get("function_impacts", {})
        rev_loss = sim.get("projected_revenue_loss", 0)
        sd = sim.get("stockout_days", 0)
        ov = sim.get("overstock_units", 0)
        cb = sim.get("cost_breakdown", {})

        return (
            f"Scenario Type: {stype}\n"
            f"Affected Products: {', '.join(products) if products else 'N/A'}\n"
            f"Time Horizon: {horizon} days\n\n"
            f"=== Propagation Analysis ===\n"
            f"Overall Propagation Score: {overall}/10\n"
            f"Cascade Depth: {depth} hops\n"
            f"Inventory Impact: {fi.get('inventory', 0)}/10\n"
            f"Pricing Impact: {fi.get('pricing', 0)}/10\n"
            f"Fulfillment Impact: {fi.get('fulfillment', 0)}/10\n"
            f"Revenue Impact: {fi.get('revenue', 0)}/10\n\n"
            f"=== Simulation Results (Monte Carlo, 1000 iterations) ===\n"
            f"Projected Revenue Loss: ${rev_loss:,.0f}\n"
            f"Stockout Days (avg): {sd:.1f}\n"
            f"Overstock Units (avg): {ov:.0f}\n"
            f"Revenue Loss: ${cb.get('revenue_loss', 0):,.0f}\n"
            f"Holding Cost: ${cb.get('holding_cost', 0):,.0f}\n"
            f"Lost Sales: ${cb.get('lost_sales', 0):,.0f}\n\n"
            "Based ONLY on these metrics, return a JSON object with these exact keys:\n"
            "revenue_risk, market_reason, urgency_level, recommended_actions, "
            "trade_offs, explanation, confidence_score"
        )

    @staticmethod
    def _build_explanation_prompt(context: Dict[str, Any]) -> str:
        safe = {k: v for k, v in context.items() if not isinstance(v, (dict, list))}
        return (
            f"Decision context: {json.dumps(safe, default=str)}\n\n"
            "Return JSON with keys: factors (array), confidence (float), reasoning (string)."
        )

    # ── Rule-based fallback ───────────────────────────────────────────────────

    def _rule_based_summary(
        self,
        scenario: Dict[str, Any],
        ps: Dict[str, Any],
        sim: Dict[str, Any],
    ) -> Dict[str, Any]:
        overall = ps.get("overall_score", 0)
        fi = ps.get("function_impacts", {})
        rev_loss = sim.get("projected_revenue_loss", 0)

        explanation = (
            f"Rule-based analysis: propagation score {overall}/10 driven by "
            f"revenue impact ({fi.get('revenue', 0):.1f}/10) and "
            f"fulfillment impact ({fi.get('fulfillment', 0):.1f}/10). "
            f"Monte Carlo projected revenue loss: ${rev_loss:,.0f}. "
            "Confidence: 85 % (deterministic model)."
        )
        data = {
            "revenue_risk": self._calc_revenue_risk(ps, sim),
            "market_reason": self._market_reason(scenario, ps),
            "urgency_level": self._urgency(ps),
            "recommended_actions": self._recommendations(scenario, ps),
            "trade_offs": self._trade_offs_list(scenario),
            "explanation": explanation,
            "confidence_score": "0.85",
        }
        return self._wrap(scenario, data, source="rule-based")

    @staticmethod
    def _wrap(scenario, data, source):
        return {
            "summary_id": str(uuid.uuid4()),
            "scenario_id": scenario.get("scenario_id"),
            "revenue_risk": data["revenue_risk"],
            "market_reason": data["market_reason"],
            "urgency_level": data["urgency_level"],
            "recommended_actions": data.get("recommended_actions", []),
            "trade_offs": data.get("trade_offs", []),
            "explanation": data.get("explanation", ""),
            "confidence_score": str(data.get("confidence_score", "0.85")),
            "generated_by": source,
            "generated_timestamp": datetime.utcnow(),
        }

    @staticmethod
    def _calc_revenue_risk(ps: Dict, sim: Dict) -> str:
        rev_impact = ps.get("function_impacts", {}).get("revenue", 0)
        rev_loss = sim.get("projected_revenue_loss", 0)
        if rev_impact >= 8:
            level = "Critical"
        elif rev_impact >= 6:
            level = "High"
        elif rev_impact >= 4:
            level = "Medium"
        else:
            level = "Low"
        return f"{level} — Estimated ${rev_loss:,.0f} revenue at risk over simulation period"

    @staticmethod
    def _urgency(ps: Dict) -> str:
        score = ps.get("overall_score", 0)
        if score >= 8:
            return "Critical"
        if score >= 6:
            return "High"
        if score >= 4:
            return "Medium"
        return "Low"

    @staticmethod
    def _market_reason(scenario: Dict, ps: Dict) -> str:
        stype = scenario.get("scenario_type", "UNKNOWN")
        score = ps.get("overall_score", 0)
        reasons = {
            "OVERSTOCK": (
                f"Excess inventory buildup due to demand forecast mismatch. "
                f"Propagation score {score}/10 indicates significant cross-functional "
                "impact on pricing flexibility and working capital."
            ),
            "STOCKOUT": (
                f"Insufficient inventory creating fulfillment risk. "
                f"Propagation score {score}/10 shows cascading effects on customer "
                "satisfaction and revenue realisation."
            ),
            "SEASONAL_MISMATCH": (
                f"Seasonal demand patterns misaligned with inventory strategy. "
                f"Score {score}/10 reflects market timing misalignment across supply chain."
            ),
            "PRICING_FAILURE": (
                f"Pricing strategy misaligned with market conditions. "
                f"Score {score}/10 indicates elasticity-driven revenue and competitive risks."
            ),
            "FULFILLMENT_FAILURE": (
                f"Fulfillment capacity constraints impacting order delivery. "
                f"Score {score}/10 shows customer experience and revenue implications."
            ),
        }
        return reasons.get(stype, f"Business function failure with propagation score {score}/10")

    @staticmethod
    def _recommendations(scenario: Dict, ps: Dict) -> List[str]:
        recs = {
            "OVERSTOCK": [
                "Launch promotional pricing to accelerate inventory turnover",
                "Negotiate return-to-vendor agreements with key suppliers",
                "Activate liquidation channels for excess stock",
            ],
            "STOCKOUT": [
                "Expedite emergency inventory replenishment via priority suppliers",
                "Implement backorder management with customer ETA commitments",
                "Review and recalibrate demand forecasting models",
            ],
            "SEASONAL_MISMATCH": [
                "Realign inventory planning with seasonal demand patterns",
                "Implement dynamic pricing tied to seasonal demand curves",
                "Enhance forecasting with seasonal decomposition models",
            ],
            "PRICING_FAILURE": [
                "Conduct competitive pricing analysis and reset to market rate",
                "Implement elasticity-based dynamic pricing strategy",
                "Review pricing tiers and adjust value proposition",
            ],
            "FULFILLMENT_FAILURE": [
                "Activate surge workforce and extend shift capacity immediately",
                "Route overflow orders to pre-contracted 3PL partners",
                "Re-slot high-velocity SKUs to optimise warehouse throughput",
            ],
        }
        return recs.get(scenario.get("scenario_type"), [
            "Investigate root cause and deploy cross-functional task force",
            "Monitor KPIs closely and escalate if situation worsens",
        ])

    @staticmethod
    def _trade_offs_list(scenario: Dict) -> List[str]:
        tmap = {
            "OVERSTOCK": [
                "Promotional pricing: faster clearance vs. reduced margins",
                "Liquidation: immediate cash vs. brand value dilution",
                "Hold inventory: preserve margin vs. growing holding costs",
            ],
            "STOCKOUT": [
                "Expedited shipping: faster replenishment vs. higher logistics cost",
                "Backorders: retain customers vs. delayed revenue recognition",
                "Alternative suppliers: faster availability vs. quality risk",
            ],
            "SEASONAL_MISMATCH": [
                "Aggressive discounting: clear seasonal stock vs. margin erosion",
                "Carry forward: preserve price vs. obsolescence risk",
                "Dynamic pricing: optimise revenue vs. customer trust",
            ],
            "PRICING_FAILURE": [
                "Price cut: demand recovery vs. margin concession",
                "Bundling: value perception vs. complexity and cost",
                "Hold price: margin preservation vs. volume loss",
            ],
            "FULFILLMENT_FAILURE": [
                "Surge staffing: rapid capacity vs. elevated labour cost",
                "3PL activation: flexible scale vs. reduced margin per unit",
                "Demand throttle: protect service levels vs. lost sales",
            ],
        }
        return tmap.get(scenario.get("scenario_type"), [
            "Quick action: faster resolution vs. higher cost",
            "Measured response: lower cost vs. extended timeline",
        ])

    @staticmethod
    def _rule_based_explanation(context: Dict[str, Any]) -> Dict[str, Any]:
        keys = list(context.keys())
        return {
            "factors": keys[:3] if len(keys) >= 3 else keys,
            "confidence": 0.85,
            "reasoning": (
                f"Analysis based on {', '.join(keys[:5])}. "
                "Deterministic rule-based model applied scenario-specific thresholds. "
                "Confidence: 85 %."
            ),
            "generated_by": "rule-based",
        }
