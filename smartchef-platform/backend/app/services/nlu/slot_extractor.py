"""Slot extractor: extract slot values from user text.

In production, this uses JointBERT's BIO sequence labeling output.
Current implementation uses regex patterns as a foundation.
"""
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SlotValue:
    slot_key: str
    value: str
    start: int
    end: int


ENTITY_PATTERNS = {
    "number": [
        r'(\d+(?:\.\d+)?)\s*(?:度|℃|°)',
        r'(\d+(?:\.\d+)?)\s*(?:分钟|分|min)',
        r'(\d+(?:\.\d+)?)\s*(?:秒|s)',
        r'(\d+(?:\.\d+)?)\s*(?:克|g|kg|千克)',
        r'(\d+)',
    ],
    "time": [
        r'(\d+)\s*(?:分钟|分|min)',
        r'(\d+)\s*(?:小时|时|hour|h)',
        r'(\d+)\s*(?:秒|second|s)',
    ],
    "food_name": [
        r'(?:做|烧|炒|煮|蒸|烤|炖|煎)\s*([\u4e00-\u9fff]{2,8})',
        r'([\u4e00-\u9fff]{2,8})\s*(?:怎么做|的做法|菜谱|需要)',
        r'搜[索个一]?\s*([\u4e00-\u9fff]{2,8})',
    ],
}


async def extract_slots(
    text: str,
    slot_definitions: list[dict],
) -> list[SlotValue]:
    """Extract slot values from text based on slot definitions.
    
    Args:
        text: user input text
        slot_definitions: list of dicts with keys: slot_key, entity_type, is_required
    """
    extracted = []

    for slot_def in slot_definitions:
        slot_key = slot_def["slot_key"]
        entity_type = slot_def["entity_type"]

        patterns = ENTITY_PATTERNS.get(entity_type, [])
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
                extracted.append(SlotValue(
                    slot_key=slot_key,
                    value=value,
                    start=match.start(),
                    end=match.end(),
                ))
                break

    logger.info(f"Slots: extracted {len(extracted)} from '{text[:30]}...'")
    return extracted
