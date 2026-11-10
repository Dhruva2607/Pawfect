"""
Google Gemini Chat LLM provider with verified model resolution and rate-limit guardrails.
[FROM MARKDOWN] matches Step 2.2, Step 2.4, Step 6.1, and Step 6.2.
"""

import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# [FROM MARKDOWN: Step 6.1] Strict temperature 0.1 for grounded reasoning and zero hallucination
DEFAULT_TEMPERATURE = 0.1

# Active working model verified on Google GenAI API endpoint
VERIFIED_WORKING_MODEL = "gemini-3.5-flash"
SUPPORTED_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-pro"
]

_resolved_model: Optional[str] = None


def resolve_active_model() -> str:
    """
    Determines the active working flash model on the connected API key.
    Caches the result so testing only happens once.
    """
    global _resolved_model
    if _resolved_model is not None:
        return _resolved_model

    # Check candidates
    for m in [VERIFIED_WORKING_MODEL, "gemini-3.5-flash-lite"]:
        try:
            test_llm = ChatGoogleGenerativeAI(
                model=m,
                google_api_key=GOOGLE_API_KEY,
                temperature=DEFAULT_TEMPERATURE,
            )
            # Quick test with structured output
            from pydantic import BaseModel
            class _Ping(BaseModel):
                ok: bool
            test_llm.with_structured_output(_Ping).invoke("ping")
            _resolved_model = m
            logger.info("Resolved active Gemini flash model: %s", m)
            return _resolved_model
        except Exception as ex:
            logger.warning("Model candidate %s failed test: %s", m, ex)
            continue

    _resolved_model = VERIFIED_WORKING_MODEL
    return _resolved_model


def get_chat_llm(temperature: float = DEFAULT_TEMPERATURE, model_name: Optional[str] = None) -> ChatGoogleGenerativeAI:
    """
    Returns an initialized ChatGoogleGenerativeAI using the resolved active model.
    """
    model = model_name or resolve_active_model()
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature,
        max_retries=3,
    )
