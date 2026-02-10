"""Intent classification router for the Director Agent."""

from src.agents.director.prompts import INTENT_CLASSIFICATION_PROMPT
from src.llm.base import LLMMessage, LLMProvider

VALID_INTENTS = {
    "course_inquiry",
    "enrollment",
    "fee_query",
    "attendance_query",
    "counseling",
    "complaint",
    "general",
    "class_related",
    "lab_related",
}


class IntentRouter:
    """Classifies user messages into intent categories using LLM."""

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    async def classify(self, message: str) -> str:
        """Classify a message into one of the 9 intent categories."""
        prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)
        messages = [LLMMessage(role="user", content=prompt)]

        try:
            response = await self._llm.generate(messages, temperature=0.1, max_tokens=20)
            intent = response.content.strip().lower().replace(" ", "_")

            # Clean up common variations
            if intent in VALID_INTENTS:
                return intent

            # Fuzzy match
            for valid in VALID_INTENTS:
                if valid in intent or intent in valid:
                    return valid

            return "general"
        except Exception:
            return "general"
