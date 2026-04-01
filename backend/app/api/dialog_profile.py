import json
import re
import time
import uuid
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto import decrypt_json, decrypt_text, encrypt_json, encrypt_text
from app.dependencies import ApiError, create_audit_log, get_db, require_capability, response_envelope, utc_now
from app.models import (
    CommandLibrary,
    DeviceSession,
    DialogProfile,
    DialogProfileLibraryBinding,
    LibraryModelVersion,
    PublishedVersion,
    RequestLog,
    TestSession,
    TestSessionMessage,
    UserAccount,
)


router = APIRouter(tags=["dialog-profile"])

ALLOWED_MODELS = {"gpt-4o-mini", "gpt-4o", "qwen-max"}
ALLOWED_ROUTING = {"intent_first", "knowledge_first", "hybrid"}
CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
ENGLISH_CHAR_PATTERN = re.compile(r"[A-Za-z]")


class DialogProfilePayload(BaseModel):
    name: str
    llm_model: str
    routing_strategy: str
    persona_name: str
    persona_prompt: str
    intent_threshold: float
    session_timeout_minutes: int
    knowledge_base_id: str | None = None
    library_ids: list[str] = []


class PublishPayload(BaseModel):
    note: str | None = None


class CreateSessionPayload(BaseModel):
    name: str
    device_context: dict[str, Any] = {}


class SendMessagePayload(BaseModel):
    text: str
    device_context: dict[str, Any] = {}


def parse_json_field(payload: str | None, fallback: Any):
    if not payload:
        return fallback
    return decrypt_json(payload, fallback)


def serialize_profile(profile: DialogProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "name": profile.name,
        "status": profile.status,
        "llm_model": profile.llm_model,
        "routing_strategy": profile.routing_strategy,
        "persona_name": profile.persona_name,
        "persona_prompt": profile.persona_prompt,
        "intent_threshold": profile.intent_threshold,
        "session_timeout_minutes": profile.session_timeout_minutes,
        "knowledge_base_id": profile.knowledge_base_id,
        "publish_version": profile.publish_version,
        "created_at": profile.created_at.isoformat() + "Z",
        "updated_at": profile.updated_at.isoformat() + "Z",
    }


def serialize_binding(binding: DialogProfileLibraryBinding) -> dict[str, Any]:
    return {
        "id": binding.id,
        "profile_id": binding.profile_id,
        "library_id": binding.library_id,
        "library_name": binding.library_name,
        "language": binding.language,
        "published_model_name": binding.published_model_name,
        "priority": binding.priority,
    }


def serialize_session(session: TestSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "profile_id": session.profile_id,
        "name": session.name,
        "device_context": parse_json_field(session.device_context_json, {}),
        "message_count": session.message_count,
        "last_message_at": session.last_message_at.isoformat() + "Z" if session.last_message_at else None,
        "created_at": session.created_at.isoformat() + "Z",
    }


def serialize_message(message: TestSessionMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "text": decrypt_text(message.text),
        "debug_trace": parse_json_field(message.debug_trace_json, None),
        "response_time_ms": message.response_time_ms,
        "created_at": message.created_at.isoformat() + "Z",
    }


def get_profile_or_404(session: Session, profile_id: str) -> DialogProfile:
    profile = session.get(DialogProfile, profile_id)
    if profile is None:
        raise ApiError(404, "PROFILE-404-NOT-FOUND", "目标对话方案不存在")
    return profile


def get_session_or_404(session: Session, session_id: str) -> TestSession:
    test_session = session.get(TestSession, session_id)
    if test_session is None:
        raise ApiError(404, "SESSION-404-NOT-FOUND", "测试会话不存在")
    return test_session


def get_published_profile(session: Session) -> DialogProfile:
    profile = session.execute(select(DialogProfile).where(DialogProfile.status == "published")).scalar_one_or_none()
    if profile is None:
        raise ApiError(409, "PROFILE-409-PUBLISHED", "当前没有可供设备调用的已发布方案")
    return profile


def ensure_payload_valid(payload: DialogProfilePayload):
    if not payload.name.strip():
        raise ApiError(422, "PROFILE-422-NAME", "方案名称不能为空")
    if payload.llm_model not in ALLOWED_MODELS:
        raise ApiError(422, "PROFILE-422-MODEL", "模型配置不合法")
    if payload.routing_strategy not in ALLOWED_ROUTING:
        raise ApiError(422, "PROFILE-422-ROUTING", "路由策略不合法")
    if not 0 <= payload.intent_threshold <= 1:
        raise ApiError(422, "PROFILE-422-THRESHOLD", "阈值必须在 0 到 1 之间")
    if not 1 <= payload.session_timeout_minutes <= 60:
        raise ApiError(422, "PROFILE-422-TIMEOUT", "会话超时必须在 1 到 60 分钟")


def load_bindings_snapshot(session: Session, library_ids: list[str]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for index, library_id in enumerate(library_ids, start=1):
        library = session.get(CommandLibrary, library_id)
        if library is None:
            raise ApiError(404, "PROFILE-404-LIBRARY", "指令库已失效，请重新选择")
        published_model = session.execute(
            select(LibraryModelVersion).where(
                LibraryModelVersion.library_id == library_id,
                LibraryModelVersion.is_published.is_(True),
            )
        ).scalar_one_or_none()
        snapshots.append(
            {
                "id": uuid.uuid4().hex,
                "library_id": library.id,
                "library_name": library.name,
                "language": library.language,
                "published_model_name": published_model.version_name if published_model else None,
                "priority": index,
            }
        )
    return snapshots


def replace_bindings(session: Session, profile: DialogProfile, library_ids: list[str]):
    existing = session.execute(
        select(DialogProfileLibraryBinding).where(DialogProfileLibraryBinding.profile_id == profile.id)
    ).scalars().all()
    for item in existing:
        session.delete(item)

    for snapshot in load_bindings_snapshot(session, library_ids):
        session.add(
            DialogProfileLibraryBinding(
                id=snapshot["id"],
                profile_id=profile.id,
                library_id=snapshot["library_id"],
                library_name=snapshot["library_name"],
                language=snapshot["language"],
                published_model_name=snapshot["published_model_name"],
                priority=snapshot["priority"],
            )
        )


def build_profile_summary(profiles: list[DialogProfile]) -> dict[str, int]:
    return {
        "total": len(profiles),
        "draft_count": sum(1 for item in profiles if item.status == "draft"),
        "published_count": sum(1 for item in profiles if item.status == "published"),
        "archived_count": sum(1 for item in profiles if item.status == "archived"),
    }


def build_publish_guard(profile: DialogProfile, bindings: list[DialogProfileLibraryBinding]) -> list[str]:
    guard_items: list[str] = []
    if not bindings:
        guard_items.append("未绑定任何指令库")
    for binding in bindings:
        if not binding.published_model_name:
            guard_items.append(f"指令库 {binding.library_name} 缺少已发布模型")
    if not profile.persona_prompt.strip():
        guard_items.append("人设描述未配置")
    if profile.intent_threshold <= 0:
        guard_items.append("阈值配置无效")
    return guard_items


def detect_language(text: str) -> tuple[str, bool]:
    has_zh = bool(CHINESE_CHAR_PATTERN.search(text))
    has_en = bool(ENGLISH_CHAR_PATTERN.search(text))
    if has_zh and has_en:
        return "zh", True
    if has_en:
        return "en", False
    return "zh", False


def binding_languages(bindings: list[DialogProfileLibraryBinding]) -> set[str]:
    return {item.language for item in bindings if item.language}


def resolve_route(
    text: str,
    device_context: dict[str, Any],
    *,
    language: str = "zh",
    mixed_input: bool = False,
    allow_intent: bool = True,
) -> tuple[str, str, dict[str, Any]]:
    slots: dict[str, Any] = {}
    temp_match = re.search(r"(\d+)\s*度", text)
    if temp_match is None and language == "en":
        temp_match = re.search(r"(\d+)\s*(?:degrees?|c)", text.lower())
    if temp_match:
        slots["temperature"] = int(temp_match.group(1))
    if device_context.get("cooking"):
        slots["cooking"] = True
    if device_context.get("device_id"):
        slots["device_id"] = device_context["device_id"]

    intent_tokens = ["开始", "设置", "温度", "暂停", "烹饪"]
    knowledge_tokens = ["多久", "怎么做", "食材", "知识"]
    lowered = text.lower()
    if language == "en":
        intent_tokens = ["start cooking", "set temperature", "set to", "pause cooking", "pause"]
        knowledge_tokens = ["how long", "what ingredients", "ingredients", "recipe", "knowledge"]
    elif mixed_input:
        intent_tokens = intent_tokens + ["start cooking", "set temperature", "set to", "pause cooking", "pause"]
        knowledge_tokens = knowledge_tokens + ["how long", "what ingredients", "ingredients", "recipe", "knowledge"]

    haystack = lowered if language == "en" or mixed_input else text
    if allow_intent and any(token in haystack for token in intent_tokens):
        return "intent", "device.control", slots
    if any(token in haystack for token in knowledge_tokens):
        intent = "knowledge.query"
        if ("多久" in text or "how long" in lowered) and device_context.get("cooking"):
            intent = "cooking.remaining_time"
        return "knowledge", intent, slots
    return "fallback", "fallback.chat", slots


def route_confidence_for(route: str) -> float:
    mapping = {
        "intent": 0.96,
        "knowledge": 0.91,
        "fallback": 0.68,
    }
    return mapping.get(route, 0.5)


def intent_confidence_for(intent: str) -> float:
    mapping = {
        "device.control": 0.94,
        "knowledge.query": 0.88,
        "cooking.remaining_time": 0.9,
        "fallback.chat": 0.67,
    }
    return mapping.get(intent, 0.5)


def render_assistant_reply(
    profile: DialogProfile,
    route: str,
    intent: str,
    text: str,
    device_context: dict[str, Any],
    *,
    language: str = "zh",
) -> str:
    prefix = f"{profile.persona_name}："
    if language == "en":
        prefix = "Kitchen Assistant:"
        if route == "intent":
            if "temperature" in text.lower():
                return f"{prefix} Temperature change received. I will handle it with the current profile."
            return f"{prefix} Command captured and executing via {intent}."
        if intent == "cooking.remaining_time" and device_context.get("cooking"):
            return f"{prefix} The device is cooking now. Please check the remaining time in the current context."
        if route == "knowledge":
            return f"{prefix} I searched the knowledge path and returned the most relevant answer."
        return f"{prefix} The current input did not match a clear command, so I will continue with fallback chat."
    if route == "intent":
        if "temperature" in text:
            return f"{prefix} 已收到设置请求，我会按当前方案处理温度调整。"
        return f"{prefix} 指令已记录，正在按 {intent} 执行。"
    if intent == "cooking.remaining_time" and device_context.get("cooking"):
        return f"{prefix} 当前设备处于烹饪中，请结合设备状态继续查看剩余时间。"
    if route == "knowledge":
        return f"{prefix} 我已按知识链路检索你的问题，并返回当前最相关结果。"
    return f"{prefix} 当前未命中明确指令，我会按闲聊兜底继续响应。"


def build_debug_trace(
    profile: DialogProfile,
    bindings: list[DialogProfileLibraryBinding],
    route: str,
    intent: str,
    slots: dict[str, Any],
    response_text: str,
    response_time_ms: int,
    device_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "route": {"type": route, "confidence": route_confidence_for(route)},
        "intent": {"name": intent, "confidence": intent_confidence_for(intent)},
        "slots": slots,
        "model": profile.llm_model,
        "threshold": profile.intent_threshold,
        "bindings": [
            {
                "library_id": item.library_id,
                "library_name": item.library_name,
                "published_model_name": item.published_model_name,
            }
            for item in bindings
        ],
        "response_text": response_text,
        "response_time_ms": response_time_ms,
        "device_context_snapshot": device_context,
    }


def process_dialog_turn(
    profile: DialogProfile,
    bindings: list[DialogProfileLibraryBinding],
    text: str,
    device_context: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    detected_language, mixed_input = detect_language(text)
    available_languages = binding_languages(bindings)
    allow_intent = detected_language in available_languages
    route, intent, slots = resolve_route(
        text,
        device_context,
        language=detected_language,
        mixed_input=mixed_input,
        allow_intent=allow_intent,
    )
    response_text = render_assistant_reply(
        profile,
        route,
        intent,
        text,
        device_context,
        language=detected_language,
    )
    response_time_ms = int((time.perf_counter() - started) * 1000)
    debug_trace = build_debug_trace(
        profile=profile,
        bindings=bindings,
        route=route,
        intent=intent,
        slots=slots,
        response_text=response_text,
        response_time_ms=response_time_ms,
        device_context=device_context,
    )
    return {
        "route": route,
        "intent": intent,
        "slots": slots,
        "response_text": response_text,
        "response_time_ms": response_time_ms,
        "debug_trace": debug_trace,
        "language": detected_language,
    }


def upsert_device_session(
    session: Session,
    *,
    device_id: str,
    profile: DialogProfile,
    device_context: dict[str, Any],
) -> DeviceSession:
    now = utc_now()
    current = session.execute(
        select(DeviceSession)
        .where(DeviceSession.device_id == device_id)
        .order_by(DeviceSession.created_at.desc())
    ).scalars().first()
    if current is not None and current.expires_at is not None:
        if current.profile_version == profile.publish_version and current.expires_at >= now:
            current.device_context_json = encrypt_json(device_context)
            current.last_message_at = now
            current.expires_at = now + timedelta(minutes=profile.session_timeout_minutes)
            return current

    created = DeviceSession(
        id=uuid.uuid4().hex,
        device_id=device_id,
        profile_id=profile.id,
        profile_version=profile.publish_version,
        device_context_json=encrypt_json(device_context),
    )
    session.add(created)
    session.flush()
    created.last_message_at = now
    created.expires_at = now + timedelta(minutes=profile.session_timeout_minutes)
    return created


def write_request_log(
    session: Session,
    *,
    request_id: str,
    device_id: str,
    session_id: str,
    profile_id: str,
    text: str,
    route: str,
    intent: str,
    latency_ms: int,
    device_context: dict[str, Any],
    debug_trace: dict[str, Any],
    profile_version: int,
):
    session.add(
        RequestLog(
            id=uuid.uuid4().hex,
            request_id=request_id,
            device_id=device_id,
            session_id=session_id,
            profile_id=profile_id,
            route_type=route,
            intent_name=intent,
            latency_ms=latency_ms,
            is_error=False,
            accuracy_hit=None,
            request_json=encrypt_json(
                {
                    "text": text,
                    "version": f"v{profile_version}.0.0",
                    "device_context": device_context,
                }
            ),
            response_json=encrypt_json(
                {
                    "route": debug_trace["route"],
                    "intent": debug_trace["intent"],
                    "slots": debug_trace["slots"],
                    "reply_text": debug_trace["response_text"],
                    "device_context_snapshot": debug_trace["device_context_snapshot"],
                }
            ),
        )
    )


@router.get("/dialog-profiles")
def list_dialog_profiles(
    request: Request,
    _: UserAccount = Depends(require_capability("profile_read")),
    session: Session = Depends(get_db),
):
    profiles = session.execute(select(DialogProfile).order_by(DialogProfile.created_at.asc())).scalars().all()
    current_published = next((item for item in profiles if item.status == "published"), None)
    return response_envelope(
        request,
        {
            "items": [serialize_profile(item) for item in profiles],
            "summary": build_profile_summary(profiles),
            "current_published_profile": serialize_profile(current_published) if current_published else None,
        },
    )


@router.post("/dialog-profiles")
def create_dialog_profile(
    payload: DialogProfilePayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("profile_write")),
    session: Session = Depends(get_db),
):
    ensure_payload_valid(payload)
    existing = session.execute(select(DialogProfile).where(DialogProfile.name == payload.name.strip())).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "PROFILE-409-NAME", "对话方案名称已存在")

    profile = DialogProfile(
        id=uuid.uuid4().hex,
        name=payload.name.strip(),
        status="draft",
        llm_model=payload.llm_model,
        routing_strategy=payload.routing_strategy,
        persona_name=payload.persona_name.strip(),
        persona_prompt=payload.persona_prompt.strip(),
        intent_threshold=payload.intent_threshold,
        session_timeout_minutes=payload.session_timeout_minutes,
        knowledge_base_id=payload.knowledge_base_id,
    )
    session.add(profile)
    session.flush()
    replace_bindings(session, profile, payload.library_ids)
    create_audit_log(session, actor.id, actor.id, "dialog_profile.create", {"profile_id": profile.id})
    session.commit()
    session.refresh(profile)
    return response_envelope(request, {"profile": serialize_profile(profile)})


@router.get("/dialog-profiles/{profile_id}")
def get_dialog_profile_detail(
    profile_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("profile_read")),
    session: Session = Depends(get_db),
):
    profile = get_profile_or_404(session, profile_id)
    bindings = session.execute(
        select(DialogProfileLibraryBinding)
        .where(DialogProfileLibraryBinding.profile_id == profile.id)
        .order_by(DialogProfileLibraryBinding.priority.asc())
    ).scalars().all()
    versions = session.execute(
        select(PublishedVersion)
        .where(PublishedVersion.entity_type == "dialog_profile", PublishedVersion.entity_id == profile.id)
        .order_by(PublishedVersion.created_at.desc())
    ).scalars().all()
    return response_envelope(
        request,
        {
            "profile": serialize_profile(profile),
            "bindings": [serialize_binding(item) for item in bindings],
            "published_versions": [
                {
                    "id": item.id,
                    "version": item.version,
                    "note": item.note,
                    "snapshot": parse_json_field(item.snapshot_json, {}),
                    "created_at": item.created_at.isoformat() + "Z",
                }
                for item in versions
            ],
        },
    )


@router.patch("/dialog-profiles/{profile_id}")
def update_dialog_profile(
    profile_id: str,
    payload: DialogProfilePayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("profile_write")),
    session: Session = Depends(get_db),
):
    ensure_payload_valid(payload)
    profile = get_profile_or_404(session, profile_id)
    existing = session.execute(
        select(DialogProfile).where(DialogProfile.name == payload.name.strip(), DialogProfile.id != profile.id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "PROFILE-409-NAME", "对话方案名称已存在")

    profile.name = payload.name.strip()
    profile.llm_model = payload.llm_model
    profile.routing_strategy = payload.routing_strategy
    profile.persona_name = payload.persona_name.strip()
    profile.persona_prompt = payload.persona_prompt.strip()
    profile.intent_threshold = payload.intent_threshold
    profile.session_timeout_minutes = payload.session_timeout_minutes
    profile.knowledge_base_id = payload.knowledge_base_id
    replace_bindings(session, profile, payload.library_ids)
    create_audit_log(session, actor.id, actor.id, "dialog_profile.update", {"profile_id": profile.id})
    session.commit()
    session.refresh(profile)
    return response_envelope(request, {"profile": serialize_profile(profile)})


@router.post("/dialog-profiles/{profile_id}/publish")
def publish_dialog_profile(
    profile_id: str,
    payload: PublishPayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("profile_publish")),
    session: Session = Depends(get_db),
):
    profile = get_profile_or_404(session, profile_id)
    bindings = session.execute(
        select(DialogProfileLibraryBinding)
        .where(DialogProfileLibraryBinding.profile_id == profile.id)
        .order_by(DialogProfileLibraryBinding.priority.asc())
    ).scalars().all()
    guard_items = build_publish_guard(profile, bindings)
    if guard_items:
        return response_envelope(
            request,
            {
                "profile": serialize_profile(profile),
                "guard_items": guard_items,
            },
            code="PROFILE-409-PUBLISH-GATE",
            message="当前方案未满足发布条件",
            status_code=409,
        )

    current_published = session.execute(
        select(DialogProfile).where(DialogProfile.status == "published", DialogProfile.id != profile.id)
    ).scalars().all()
    for item in current_published:
        item.status = "archived"

    profile.status = "published"
    profile.publish_version += 1
    session.add(
        PublishedVersion(
            id=uuid.uuid4().hex,
            entity_type="dialog_profile",
            entity_id=profile.id,
            version=profile.publish_version,
            snapshot_json=json.dumps(
                {
                    "profile": serialize_profile(profile),
                    "bindings": [serialize_binding(item) for item in bindings],
                },
                ensure_ascii=False,
            ),
            note=payload.note,
        )
    )
    create_audit_log(session, actor.id, actor.id, "dialog_profile.publish", {"profile_id": profile.id})
    session.commit()
    session.refresh(profile)
    return response_envelope(
        request,
        {
            "profile": serialize_profile(profile),
            "guard_items": [],
        },
    )


@router.post("/dialog-profiles/{profile_id}/test-sessions")
def create_test_session(
    profile_id: str,
    payload: CreateSessionPayload,
    request: Request,
    _: UserAccount = Depends(require_capability("profile_read")),
    session: Session = Depends(get_db),
):
    profile = get_profile_or_404(session, profile_id)
    test_session = TestSession(
        id=uuid.uuid4().hex,
        profile_id=profile.id,
        name=payload.name.strip() or "未命名会话",
        device_context_json=encrypt_json(payload.device_context),
        message_count=0,
    )
    session.add(test_session)
    session.commit()
    session.refresh(test_session)
    return response_envelope(request, {"session": serialize_session(test_session)})


@router.get("/test-sessions/{session_id}")
def get_test_session(
    session_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("profile_read")),
    session: Session = Depends(get_db),
):
    test_session = get_session_or_404(session, session_id)
    messages = session.execute(
        select(TestSessionMessage)
        .where(TestSessionMessage.session_id == test_session.id)
        .order_by(TestSessionMessage.created_at.asc())
    ).scalars().all()
    return response_envelope(
        request,
        {
            "session": serialize_session(test_session),
            "messages": [serialize_message(item) for item in messages],
        },
    )


@router.post("/test-sessions/{session_id}/messages")
def send_test_message(
    session_id: str,
    payload: SendMessagePayload,
    request: Request,
    _: UserAccount = Depends(require_capability("profile_read")),
    session: Session = Depends(get_db),
):
    if not payload.text.strip():
        raise ApiError(422, "SESSION-422-MESSAGE", "请输入测试内容")

    test_session = get_session_or_404(session, session_id)
    profile = get_profile_or_404(session, test_session.profile_id)
    bindings = session.execute(
        select(DialogProfileLibraryBinding)
        .where(DialogProfileLibraryBinding.profile_id == profile.id)
        .order_by(DialogProfileLibraryBinding.priority.asc())
    ).scalars().all()

    turn = process_dialog_turn(
        profile=profile,
        bindings=bindings,
        text=payload.text.strip(),
        device_context=payload.device_context,
    )

    user_message = TestSessionMessage(
        id=uuid.uuid4().hex,
        session_id=test_session.id,
        role="user",
        text=encrypt_text(payload.text.strip()),
        debug_trace_json=None,
        response_time_ms=None,
    )
    assistant_message = TestSessionMessage(
        id=uuid.uuid4().hex,
        session_id=test_session.id,
        role="assistant",
        text=encrypt_text(turn["response_text"]),
        debug_trace_json=encrypt_json(turn["debug_trace"]),
        response_time_ms=turn["response_time_ms"],
    )
    session.add_all([user_message, assistant_message])
    test_session.device_context_json = encrypt_json(payload.device_context)
    test_session.message_count += 2
    test_session.last_message_at = assistant_message.created_at
    session.commit()
    session.refresh(test_session)
    return response_envelope(
        request,
        {
            "session": serialize_session(test_session),
            "assistant_message": serialize_message(assistant_message),
            "debug_trace": turn["debug_trace"],
        },
    )
