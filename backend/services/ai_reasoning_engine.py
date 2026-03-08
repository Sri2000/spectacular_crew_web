"""
Deprecated: AI reasoning logic has moved to engines/ai_reasoning_engine.py (Google Gemini).
This shim preserves backward compatibility for any code that still imports from services.
"""
from engines.ai_reasoning_engine import AIReasoningEngine

__all__ = ["AIReasoningEngine"]
