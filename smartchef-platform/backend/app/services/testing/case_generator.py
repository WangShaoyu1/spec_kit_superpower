"""测试用例自动生成器：基于意图配置和知识库生成覆盖性用例。"""
from dataclasses import dataclass
from uuid import UUID
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.batch_test import BatchTestJob, BatchTestCase
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent
from app.models.knowledge import KnowledgeDocument

__all__ = ["generate_test_cases", "CaseGeneratorStats"]


# 语气词/填充词，用于生成变体样本
FILLER_WORDS = ["嗯", "那个", "帮我", "请问", "能不能", "可以", "麻烦", "请"]
FILLER_SUFFIXES = ["吧", "呀", "啊", "呢", "哦"]


# 闲聊域预定义测试模板
CHITCHAT_TEMPLATES = [
    ("你好", "chitchat", None),
    ("嗨", "chitchat", None),
    ("在吗", "chitchat", None),
    ("你是谁", "chitchat", None),
    ("你能做什么", "chitchat", None),
    ("今天天气怎么样", "chitchat", None),
    ("讲个笑话", "chitchat", None),
    ("谢谢", "chitchat", None),
    ("再见", "chitchat", None),
    ("你好呀", "chitchat", None),
]


@dataclass
class CaseGeneratorStats:
    """用例生成统计。"""

    total: int
    intent_positive: int
    intent_variant: int
    intent_negative: int
    knowledge: int
    chitchat: int
    job_id: UUID


def _create_text_variants(text: str, max_variants: int = 2) -> list[str]:
    """生成简单文本变体（添加/删除语气词）。"""
    variants = []
    text = text.strip()
    if not text:
        return variants

    # 变体1：前加语气词
    for prefix in FILLER_WORDS[:3]:
        candidate = f"{prefix} {text}".replace("  ", " ")
        if candidate != text and candidate not in variants:
            variants.append(candidate)
            if len(variants) >= max_variants:
                return variants

    # 变体2：后加语气词
    for suffix in FILLER_SUFFIXES[:2]:
        candidate = f"{text}{suffix}"
        if candidate != text and candidate not in variants:
            variants.append(candidate)
            if len(variants) >= max_variants:
                return variants

    return variants[:max_variants]


def _extract_questions_from_document(doc: KnowledgeDocument) -> list[str]:
    """从知识文档标题/内容提取可生成的问题。"""
    questions = []
    title = (doc.title or "").strip()

    # 基于标题生成问题
    if title:
        # 若标题已是问句形式，直接使用
        if "?" in title or "？" in title or title.endswith(("吗", "呢", "什么", "怎么")):
            questions.append(title)
        else:
            # 常见问题模板
            templates = [
                f"{title}怎么做",
                f"{title}的做法",
                f"如何做{title}",
                f"{title}的步骤",
                f"怎么做{title}",
            ]
            questions.extend(templates[:2])  # 每个文档最多 2 个标题衍生问题

    # 从 content 提取简短句子作为问题（取前 200 字内的第一句）
    content = (doc.content or "").strip()
    if content and len(questions) < 3:
        # 取第一段或第一句
        first_part = content[:200]
        sentences = re.split(r"[。！？\n]+", first_part)
        for s in sentences:
            s = s.strip()
            if 5 <= len(s) <= 50 and s not in questions:
                questions.append(s)
                break

    return questions[:3]  # 每文档最多 3 个知识问题


async def _load_intents_for_profile(
    db: AsyncSession, profile: DialogProfile
) -> list[Intent]:
    """加载对话方案关联的意图及训练数据。"""
    query = (
        select(Intent)
        .options(
            selectinload(Intent.slots),
            selectinload(Intent.training_data),
        )
        .where(Intent.is_active == True)
    )
    if profile.intent_ids:
        query = query.where(Intent.id.in_(profile.intent_ids))
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def _load_knowledge_documents(
    db: AsyncSession, knowledge_base_ids: list[UUID]
) -> list[KnowledgeDocument]:
    """加载知识库文档。"""
    if not knowledge_base_ids:
        return []
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.knowledge_base_id.in_(knowledge_base_ids)
        )
    )
    return list(result.scalars().all())


async def generate_test_cases(
    db: AsyncSession,
    profile_id: UUID,
    job_name: str = "自动生成测试集",
    created_by: UUID | None = None,
) -> CaseGeneratorStats:
    """基于意图配置和知识库生成覆盖性测试用例，并存入 BatchTestCase 表。

    Args:
        db: 数据库会话
        profile_id: 对话方案 ID
        job_name: 测试任务名称
        created_by: 创建人 ID

    Returns:
        CaseGeneratorStats: 生成统计（各类用例数量、job_id）

    Raises:
        HTTPException: 对话方案不存在
    """
    result = await db.execute(
        select(DialogProfile).where(DialogProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话方案不存在",
        )

    # 创建待执行的批量测试任务
    job = BatchTestJob(
        name=job_name,
        profile_id=profile_id,
        status="pending",
        total_cases=0,
        created_by=created_by,
    )
    db.add(job)
    await db.flush()

    intents = await _load_intents_for_profile(db, profile)
    kb_ids = profile.knowledge_base_ids or []
    documents = await _load_knowledge_documents(db, kb_ids)

    # 收集所有意图的训练文本，用于负样本
    all_training_by_intent: dict[str, list[str]] = {}
    for intent in intents:
        texts = [td.text.strip() for td in (intent.training_data or []) if td.text]
        all_training_by_intent[intent.intent_key] = texts

    stats = CaseGeneratorStats(
        total=0,
        intent_positive=0,
        intent_variant=0,
        intent_negative=0,
        knowledge=0,
        chitchat=0,
        job_id=job.id,
    )

    # 已添加用例去重：(input_text, expected_intent) 只添加一次
    cases_added: set[tuple[str, str | None]] = set()

    def _add_case(text: str, domain: str, intent: str | None) -> bool:
        """添加用例，若已存在则跳过。返回是否实际添加。"""
        key = (text.strip(), intent)
        if key in cases_added:
            return False
        cases_added.add(key)
        case = BatchTestCase(
            job_id=job.id,
            input_text=text.strip(),
            expected_domain=domain,
            expected_intent=intent,
        )
        db.add(case)
        return True

    # 1. 意图域：正样本、变体样本、负样本
    for intent in intents:
        intent_key = intent.intent_key
        training_texts = all_training_by_intent.get(intent_key, [])

        # 正样本：直接使用训练数据
        for text in training_texts:
            if text and _add_case(text, "command", intent_key):
                stats.intent_positive += 1

        # 变体样本：每个训练样本最多 2 个变体
        for text in training_texts[:10]:  # 限制每个意图最多取 10 条做变体
            for variant in _create_text_variants(text, max_variants=2):
                if _add_case(variant, "command", intent_key):
                    stats.intent_variant += 1

        # 负样本：其他意图的训练数据，预期应正确匹配该其他意图（验证不会误分类）
        other_intent_keys = [i.intent_key for i in intents if i.intent_key != intent_key]
        for other_key in other_intent_keys:
            other_texts = all_training_by_intent.get(other_key, [])[:3]  # 每个其他意图取 3 条
            for text in other_texts:
                if text and _add_case(text, "command", other_key):
                    stats.intent_negative += 1

    # 2. 知识域：基于文档生成问题
    for doc in documents:
        for q in _extract_questions_from_document(doc):
            if q and _add_case(q, "knowledge", None):
                stats.knowledge += 1

    # 3. 闲聊域：预定义模板
    for text, domain, _ in CHITCHAT_TEMPLATES:
        if _add_case(text, domain, None):
            stats.chitchat += 1

    stats.total = (
        stats.intent_positive
        + stats.intent_variant
        + stats.intent_negative
        + stats.knowledge
        + stats.chitchat
    )
    job.total_cases = stats.total
    await db.flush()
    await db.refresh(job)

    return stats
