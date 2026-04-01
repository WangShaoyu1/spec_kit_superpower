from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = REPO_ROOT / "temp_data" / "config.json"
TARGET_PATH = REPO_ROOT / ".specify" / "harness" / "core-validation-set.json"


def build_case(intent_key: str, intent_config: dict) -> dict:
    slots = intent_config.get("slots", {})
    ordered_slots = sorted(slots.items(), key=lambda item: item[1].get("order", 0))

    required_slots = []
    optional_slots = []
    prompt_samples = []
    for slot_name, slot_config in ordered_slots:
        slot_payload = {
            "name": slot_name,
            "entity": slot_config.get("entity"),
        }
        prompts = slot_config.get("elicitation", {}).get("prompts", [])
        if prompts:
            prompt_samples.extend(prompts)

        if slot_config.get("elicitation", {}).get("required"):
            required_slots.append(slot_payload)
        else:
            optional_slots.append(slot_payload)

    return {
        "intent_key": intent_key,
        "display_name": intent_config.get("chineseName", intent_key),
        "entrance_intent": bool(intent_config.get("entranceIntent")),
        "required_slots": required_slots,
        "optional_slots": optional_slots,
        "prompt_samples": prompt_samples,
    }


def main() -> None:
    config = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    intents = config["intents"]
    cases = [build_case(intent_key, intents[intent_key]) for intent_key in sorted(intents)]

    payload = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "path": "temp_data/config.json",
            "config_version": config.get("version"),
        },
        "summary": {
            "intent_count": len(cases),
            "entrance_intent_count": sum(1 for item in cases if item["entrance_intent"]),
            "required_slot_count": sum(len(item["required_slots"]) for item in cases),
        },
        "cases": cases,
    }

    TARGET_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
