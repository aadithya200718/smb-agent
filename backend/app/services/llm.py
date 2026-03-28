"""
Groq LLM Service.

Wraps the Groq client to provide intent classification,
entity extraction, and response generation for the WhatsApp agent.
"""

import json
from typing import Any, Dict, Optional

from groq import AsyncGroq

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Model to use for all LLM operations
_MODEL_ID = "llama-3.3-70b-versatile"


class GroqService:
    """Singleton wrapper around the Groq client."""

    _client: Optional[AsyncGroq] = None

    @classmethod
    def _ensure_configured(cls) -> None:
        """Initialise the Groq Client with the API key (once)."""
        if cls._client is None:
            api_key = settings.GROQ_API_KEY
            if not api_key:
                raise RuntimeError(
                    "GROQ_API_KEY is not set. Add it to your .env file."
                )
            cls._client = AsyncGroq(api_key=api_key)
            logger.info("Groq client configured (model: %s)", _MODEL_ID)

    # ── Intent Classification ──────────────────────────────────────────

    @classmethod
    async def classify_intent(cls, message: str, conversation_history: str = "") -> str:
        """
        Classify the user's intent from their message.

        Returns one of: menu_inquiry, place_order, check_status,
        faq, booking, greeting, unknown.
        """
        cls._ensure_configured()

        from app.agent.prompts import INTENT_CLASSIFICATION_PROMPT

        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            conversation_history=conversation_history or "(none)",
            user_message=message,
        )

        try:
            response = await cls._client.chat.completions.create(
                model=_MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50,
            )

            text = (response.choices[0].message.content or "").strip().lower().replace('"', "").replace("'", "")

            valid_intents = {
                "menu_inquiry", "place_order",
                "faq", "unknown",
            }
            if text not in valid_intents:
                logger.warning(
                    "LLM returned unexpected intent '%s', defaulting to 'unknown'", text
                )
                return "unknown"

            logger.info("Classified intent: %s", text)
            return text

        except Exception as exc:
            logger.error("Intent classification failed: %s", exc)
            return "unknown"

    # ── Entity Extraction ──────────────────────────────────────────────

    @classmethod
    async def extract_entities(
        cls, message: str, intent: str, conversation_history: str = ""
    ) -> Dict[str, Any]:
        """
        Extract structured entities (item, quantity, etc.) from a message.

        Returns a dict with keys like item, quantity, date, time, etc.
        """
        cls._ensure_configured()

        from app.agent.prompts import ENTITY_EXTRACTION_PROMPT

        prompt = ENTITY_EXTRACTION_PROMPT.format(
            intent=intent,
            conversation_history=conversation_history or "(none)",
            user_message=message,
        )

        try:
            response = await cls._client.chat.completions.create(
                model=_MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )

            raw = (response.choices[0].message.content or "").strip()

            # Strip markdown code fences if the LLM wraps them
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            if raw.startswith("json"):
                raw = raw[4:].strip()

            entities = json.loads(raw)
            logger.info("Extracted entities: %s", entities)
            return entities

        except (json.JSONDecodeError, Exception) as exc:
            logger.error("Entity extraction failed: %s", exc)
            return {}

    # ── Response Generation ────────────────────────────────────────────

    @classmethod
    async def generate_response(
        cls,
        user_message: str,
        intent: str,
        tool_results: Dict[str, Any],
        user_memory: Dict[str, Any] = None,
        conversation_history: str = "",
        **kwargs,
    ) -> str:
        """
        Generate the final customer-facing response.

        Returns a friendly WhatsApp-ready response string.
        """
        cls._ensure_configured()

        from app.agent.prompts import RESPONSE_GENERATION_PROMPT

        prompt = RESPONSE_GENERATION_PROMPT.format(
            conversation_history=conversation_history or "(none)",
            user_message=user_message,
            intent=intent,
            tool_results=json.dumps(tool_results, default=str),
        )

        try:
            response = await cls._client.chat.completions.create(
                model=_MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            text = (response.choices[0].message.content or "").strip()
            if not text:
                logger.warning("Empty response from Groq, using fallback")
                return "Sorry, I couldn't process that. Could you try again?"

            logger.info("Generated response (%d chars)", len(text))
            return text

        except Exception as exc:
            logger.error("Response generation failed: %s", exc)
            return (
                "I'm having a little trouble right now. "
                "Could you please try again in a moment?"
            )