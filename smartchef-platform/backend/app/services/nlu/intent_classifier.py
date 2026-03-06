"""Intent classifier: classify text into registered intents.

In production, this loads a trained JointBERT ONNX model.
Current implementation uses keyword matching as a foundation.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    intent_key: str
    confidence: float
    top_k: list[dict] | None = None


async def classify_intent(
    text: str,
    language: str,
    registered_intents: list[dict],
) -> IntentResult:
    """Classify user text into one of the registered intents.

    Args:
        text: preprocessed user text
        language: detected language (zh/en)
        registered_intents: list of dicts with keys: intent_key, display_name, category, training_texts
    """
    if not registered_intents:
        return IntentResult(intent_key="unknown", confidence=0.0)

    text_lower = text.lower()
    scores = []

    for intent in registered_intents:
        score = 0.0
        intent_key = intent["intent_key"].lower()
        display_name = intent.get("display_name", "").lower()
        training_texts = intent.get("training_texts", [])

        for tt in training_texts:
            if tt.lower() in text_lower or text_lower in tt.lower():
                score += 0.8
                break
            common_chars = set(text_lower) & set(tt.lower())
            if len(common_chars) > len(text_lower) * 0.5:
                score += 0.3

        keywords = display_name.replace("_", " ").split()
        for kw in keywords:
            if kw in text_lower:
                score += 0.4

        key_parts = intent_key.replace("voice_cmd_", "").replace("_", " ").split()
        for part in key_parts:
            if part in text_lower:
                score += 0.2

        scores.append({"intent_key": intent["intent_key"], "score": score})

    scores.sort(key=lambda x: x["score"], reverse=True)
    top = scores[0] if scores else {"intent_key": "unknown", "score": 0.0}

    confidence = min(top["score"], 1.0)
    top_k = [{"intent_key": s["intent_key"], "confidence": round(min(s["score"], 1.0), 4)} for s in scores[:3]]

    logger.info(f"Intent: text='{text[:30]}...' -> {top['intent_key']} ({confidence:.2f})")
    return IntentResult(
        intent_key=top["intent_key"],
        confidence=round(confidence, 4),
        top_k=top_k,
    )
