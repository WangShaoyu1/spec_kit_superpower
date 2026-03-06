"""Reference resolver: entity stack + rule-based coreference resolution."""
import re
import logging

logger = logging.getLogger(__name__)

PRONOUN_PATTERNS = [
    r"它|这个|那个|刚才的|上面的|这道|那道",
    r"这|那|上一个",
]


def resolve_references(
    text: str,
    entity_stack: list[dict],
) -> tuple[str, list[dict]]:
    """Resolve pronouns and references using entity stack.
    
    Args:
        text: current user input
        entity_stack: list of dicts with keys: type, value, turn
        
    Returns:
        (resolved_text, resolved_entities)
    """
    if not entity_stack:
        return text, []

    resolved_text = text
    resolved_entities = []

    for pattern in PRONOUN_PATTERNS:
        match = re.search(pattern, resolved_text)
        if match:
            most_recent = entity_stack[-1]
            resolved_text = resolved_text[:match.start()] + most_recent["value"] + resolved_text[match.end():]
            resolved_entities.append({
                "pronoun": match.group(),
                "resolved_to": most_recent["value"],
                "entity_type": most_recent["type"],
            })
            logger.info(f"Resolved '{match.group()}' -> '{most_recent['value']}'")
            break

    return resolved_text, resolved_entities
