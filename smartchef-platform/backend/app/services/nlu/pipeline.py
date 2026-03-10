"""NLU Pipeline core: text → preprocess → route → intent/knowledge/chitchat → response."""
import time
import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.services.nlu.preprocessor import preprocess
from app.services.nlu.router import route_input
from app.services.nlu.intent_classifier import classify_intent
from app.services.nlu.slot_extractor import extract_slots
from app.services.nlu.dialog_manager import (
    DialogState, process_command_state, build_progressive_error_response,
)
from app.services.nlu.reference_resolver import resolve_references
from app.services.knowledge.qa_generator import generate_knowledge_answer
from app.services.chitchat.llm_adapter import chat_completion
from app.services.chitchat.persona import build_system_prompt
from app.services.chitchat.web_search import needs_web_search, brave_search, format_search_context
from app.services.session.device_session import get_session, create_session, update_session, add_dialog_turn
from app.services.session.context import build_chat_messages, get_entity_stack

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    domain: str
    route_confidence: float
    intent: str | None = None
    intent_confidence: float | None = None
    slots: dict = field(default_factory=dict)
    response_text: str = ""
    needs_followup: bool = False
    session_id: str | None = None
    language: str = "zh"
    latency_ms: int = 0
    debug_info: dict = field(default_factory=dict)


@dataclass
class PipelineConfig:
    profile_id: UUID | None = None
    llm_provider: str = "gpt-4o-mini"
    llm_config: dict = field(default_factory=dict)
    persona_data: dict | None = None
    routing_strategy: str = "command_first"
    session_timeout_minutes: int = 10
    registered_intents: list[dict] = field(default_factory=list)
    knowledge_base_ids: list[UUID] = field(default_factory=list)
    has_knowledge_base: bool = False

HIGH_RISK_INTENTS = {
    "set_cooking_temp": {"param": "number", "threshold": 200, "unit": "℃"},
    "set_cooking_time": {"param": "duration", "threshold": 30, "unit": "分钟"},
}


async def run_pipeline(
    db: AsyncSession,
    redis: aioredis.Redis,
    text: str,
    device_id: str,
    device_context: dict | None = None,
    config: PipelineConfig | None = None,
) -> PipelineResult:
    start_time = time.time()
    config = config or PipelineConfig()
    debug_info = {}

    cleaned_text, language, was_truncated = preprocess(text)
    debug_info["preprocessed"] = {"text": cleaned_text, "language": language, "truncated": was_truncated}

    if not cleaned_text:
        return PipelineResult(
            domain="error", route_confidence=0, response_text="请说点什么吧~",
            language=language, latency_ms=int((time.time() - start_time) * 1000),
        )

    session = await get_session(redis, device_id)
    if not session:
        session = await create_session(redis, device_id, timeout_minutes=config.session_timeout_minutes)

    entity_stack = get_entity_stack(session)
    resolved_text, resolved_refs = resolve_references(cleaned_text, entity_stack)
    if resolved_refs:
        debug_info["reference_resolution"] = resolved_refs
        cleaned_text = resolved_text

    if session.get("state") == "SLOT_PROMPTING" and session.get("active_intent"):
        result = await _handle_slot_filling(
            db, redis, cleaned_text, language, session, config, device_id, device_context, start_time, debug_info
        )
        return result

    route_result = await route_input(
        cleaned_text, language,
        intent_keys=[i["intent_key"] for i in config.registered_intents],
        has_knowledge_base=config.has_knowledge_base,
        strategy=config.routing_strategy,
    )
    debug_info["routing"] = {"domain": route_result.domain, "confidence": route_result.confidence}

    if route_result.domain == "command":
        result = await _handle_command(
            db, redis, cleaned_text, language, session, config, device_id, device_context, route_result, start_time, debug_info
        )
    elif route_result.domain == "knowledge":
        result = await _handle_knowledge(
            db, redis, cleaned_text, language, session, config, device_id, route_result, start_time, debug_info
        )
    else:
        result = await _handle_chitchat(
            db, redis, cleaned_text, language, session, config, device_id, route_result, start_time, debug_info
        )

    return result


async def _handle_command(db, redis, text, language, session, config, device_id, device_context, route_result, start_time, debug_info):
    intent_result = await classify_intent(text, language, config.registered_intents)
    debug_info["intent"] = {
        "intent_key": intent_result.intent_key, "confidence": intent_result.confidence,
        "top_k": intent_result.top_k,
    }

    intent_def = next((i for i in config.registered_intents if i["intent_key"] == intent_result.intent_key), None)
    slot_defs = intent_def.get("slots", []) if intent_def else []

    extracted = await extract_slots(text, slot_defs)
    slots_dict = {s.slot_key: s.value for s in extracted}
    debug_info["slots"] = [{"key": s.slot_key, "value": s.value} for s in extracted]

    dialog_state = DialogState(
        state=session.get("state", "IDLE"),
        active_intent=session.get("active_intent"),
        filled_slots=session.get("filled_slots", {}),
        unrecognized_count=session.get("unrecognized_count", 0),
    )

    dialog_state, prompt, is_complete = process_command_state(
        dialog_state, intent_result.intent_key, extracted, slot_defs, intent_result.confidence
    )
    debug_info["dialog_state"] = {"state": dialog_state.state, "is_complete": is_complete}

    if prompt and not is_complete:
        session["state"] = dialog_state.state
        session["active_intent"] = dialog_state.active_intent
        session["pending_slots"] = [s for s in dialog_state.pending_slots]
        session["filled_slots"] = dialog_state.filled_slots
        session["unrecognized_count"] = dialog_state.unrecognized_count
        session = await add_dialog_turn(session, text, "command", intent_result.intent_key, slots_dict, prompt)
        await update_session(redis, device_id, session, config.session_timeout_minutes)

        return PipelineResult(
            domain="command", route_confidence=route_result.confidence,
            intent=intent_result.intent_key, intent_confidence=intent_result.confidence,
            slots=slots_dict, response_text=prompt, needs_followup=True,
            session_id=session["session_id"], language=language,
            latency_ms=int((time.time() - start_time) * 1000), debug_info=debug_info,
        )

    all_slots = dialog_state.filled_slots
    response_text = _build_command_response(intent_result.intent_key, all_slots, intent_def, language)

    needs_confirmation = _check_high_risk(intent_result.intent_key, all_slots)
    if needs_confirmation:
        response_text = f"⚠️ {needs_confirmation}\n\n请确认是否继续？（说'确认'或'取消'）"
        debug_info["high_risk"] = True

    session["state"] = "IDLE"
    session["active_intent"] = None
    session["filled_slots"] = {}
    session["pending_slots"] = None
    session = await add_dialog_turn(session, text, "command", intent_result.intent_key, all_slots, response_text)
    await update_session(redis, device_id, session, config.session_timeout_minutes)

    return PipelineResult(
        domain="command", route_confidence=route_result.confidence,
        intent=intent_result.intent_key, intent_confidence=intent_result.confidence,
        slots=all_slots, response_text=response_text, needs_followup=needs_confirmation,
        session_id=session["session_id"], language=language,
        latency_ms=int((time.time() - start_time) * 1000), debug_info=debug_info,
    )


async def _handle_slot_filling(db, redis, text, language, session, config, device_id, device_context, start_time, debug_info):
    intent_key = session["active_intent"]
    intent_def = next((i for i in config.registered_intents if i["intent_key"] == intent_key), None)
    slot_defs = intent_def.get("slots", []) if intent_def else []

    extracted = await extract_slots(text, slot_defs)
    filled = session.get("filled_slots", {})
    filled.update({s.slot_key: s.value for s in extracted})
    session["filled_slots"] = filled

    from app.services.nlu.dialog_manager import check_missing_slots, get_slot_prompt
    missing = check_missing_slots(slot_defs, filled)

    if missing:
        prompt = get_slot_prompt(missing[0])
        session = await add_dialog_turn(session, text, "command", intent_key, filled, prompt)
        await update_session(redis, device_id, session, config.session_timeout_minutes)

        return PipelineResult(
            domain="command", route_confidence=0.9,
            intent=intent_key, slots=filled, response_text=prompt, needs_followup=True,
            session_id=session["session_id"], language=language,
            latency_ms=int((time.time() - start_time) * 1000), debug_info=debug_info,
        )

    response_text = _build_command_response(intent_key, filled, intent_def, language)
    session["state"] = "IDLE"
    session["active_intent"] = None
    session["filled_slots"] = {}
    session["pending_slots"] = None
    session = await add_dialog_turn(session, text, "command", intent_key, filled, response_text)
    await update_session(redis, device_id, session, config.session_timeout_minutes)

    return PipelineResult(
        domain="command", route_confidence=0.9,
        intent=intent_key, slots=filled, response_text=response_text,
        session_id=session["session_id"], language=language,
        latency_ms=int((time.time() - start_time) * 1000), debug_info=debug_info,
    )


async def _handle_knowledge(db, redis, text, language, session, config, device_id, route_result, start_time, debug_info):
    answer, hits = await generate_knowledge_answer(
        db, text, config.knowledge_base_ids, config.persona_data, config.llm_provider
    )
    debug_info["knowledge_hits"] = hits[:3]

    if answer:
        session = await add_dialog_turn(session, text, "knowledge", None, None, answer)
        await update_session(redis, device_id, session, config.session_timeout_minutes)

        return PipelineResult(
            domain="knowledge", route_confidence=route_result.confidence,
            response_text=answer, session_id=session["session_id"], language=language,
            latency_ms=int((time.time() - start_time) * 1000), debug_info=debug_info,
        )

    return await _handle_chitchat(db, redis, text, language, session, config, device_id, route_result, start_time, debug_info)


async def _handle_chitchat(db, redis, text, language, session, config, device_id, route_result, start_time, debug_info):
    system_prompt = build_system_prompt(config.persona_data)

    if needs_web_search(text):
        search_results = await brave_search(text)
        if search_results:
            search_context = format_search_context(search_results)
            system_prompt += f"\n\n{search_context}"
            debug_info["web_search"] = search_results

    messages = build_chat_messages(system_prompt, session, text)
    response_text = await chat_completion(
        messages, model=config.llm_provider,
        temperature=config.llm_config.get("temperature", 0.7),
    )

    session["current_domain"] = "chitchat"
    session = await add_dialog_turn(session, text, "chitchat", None, None, response_text)
    await update_session(redis, device_id, session, config.session_timeout_minutes)

    return PipelineResult(
        domain="chitchat", route_confidence=route_result.confidence,
        response_text=response_text, session_id=session["session_id"], language=language,
        latency_ms=int((time.time() - start_time) * 1000), debug_info=debug_info,
    )


def _build_command_response(intent_key: str, slots: dict, intent_def: dict | None, language: str) -> str:
    display = intent_def.get("display_name", intent_key) if intent_def else intent_key
    slot_parts = ", ".join(f"{k}={v}" for k, v in slots.items()) if slots else ""

    if language == "en":
        return f"OK, {display}" + (f" ({slot_parts})" if slot_parts else "")
    return f"好的，{display}" + (f"（{slot_parts}）" if slot_parts else "")


def _check_high_risk(intent_key: str, slots: dict) -> str | None:
    risk_config = HIGH_RISK_INTENTS.get(intent_key)
    if not risk_config:
        return None
    param = risk_config["param"]
    if param in slots:
        try:
            val = float(slots[param])
            if val > risk_config["threshold"]:
                return f"检测到高风险操作：{intent_key}，{param}={val}{risk_config['unit']} 超过安全阈值 {risk_config['threshold']}{risk_config['unit']}。"
        except (ValueError, TypeError):
            pass
    return None
