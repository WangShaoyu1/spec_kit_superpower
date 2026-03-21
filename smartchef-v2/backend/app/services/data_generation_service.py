"""LLM-based training / evaluation sample generation for intent libraries."""

from __future__ import annotations

import logging
import re
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.core.config import Settings, get_settings
from app.models.dataset import EvaluationDataset, TrainingDataset
from app.models.intent import Intent, SimilarQuestion
from app.services.intent_data_service import _update_dataset_counts

logger = logging.getLogger(__name__)

DEFAULT_TRAINING_TEMPLATE = """你是一个意图识别数据标注专家。请为以下意图生成 {count} 条不同的中文用户话语。
意图名称: {intent_name}
意图描述: {description}
已有示例: {examples}

要求:
1. 每行一条话语，不要编号
2. 话语要自然、多样，覆盖不同表述方式
3. 不要重复已有示例
"""

DEFAULT_EVAL_TEMPLATE = """你是一个对话系统测试专家。请为以下意图生成 {count} 条测试用例。
意图名称: {intent_name}
意图描述: {description}

要求:
1. 每行一条测试话语
2. 话语要尽量自然，模拟真实用户输入
3. 包含一些边界情况和容易混淆的表述
"""


def _parse_dataset_id(raw: object) -> UUID:
    if raw is None:
        raise BusinessException("E50501", "缺少 dataset_id")
    if isinstance(raw, UUID):
        return raw
    return UUID(str(raw))


def _clean_llm_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    line = re.sub(r"^\d+[\.\)、]\s*", "", line)
    line = line.lstrip("-*•").strip()
    return line


def _parse_response_lines(text: str) -> list[str]:
    if not text:
        return []
    out: list[str] = []
    for raw in text.splitlines():
        line = _clean_llm_line(raw)
        if line:
            out.append(line)
    return out


def _check_llm_config(settings: Settings) -> None:
    if not settings.ZENMUX_API_KEY:
        raise BusinessException(
            "E50601",
            "LLM 未配置: ZENMUX_API_KEY 为空，请在 .env 中设置 ZENMUX_API_KEY",
        )
    if not settings.ZENMUX_BASE_URL:
        raise BusinessException(
            "E50601",
            "LLM 未配置: ZENMUX_BASE_URL 为空，请在 .env 中设置",
        )


async def _call_llm(prompt: str, model_name: str, settings: Settings) -> list[str]:
    client = AsyncOpenAI(base_url=settings.ZENMUX_BASE_URL, api_key=settings.ZENMUX_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=60,
        )
        content = (resp.choices[0].message.content or "").strip()
        lines = _parse_response_lines(content)
        if not lines:
            logger.warning("LLM returned empty content (model=%s)", model_name)
        return lines
    except Exception as exc:
        logger.exception("LLM call failed (model=%s)", model_name)
        raise BusinessException("E50602", f"LLM 调用失败: {exc}") from exc


def _build_intent_list_lines(intents: list[Intent]) -> str:
    """多行意图列表，供 prompt 模板 {intent_list} 使用。"""
    return "\n".join(
        f"- {i.name_zh} ({i.intent_key}): {i.description or '(无)'}" for i in intents
    )


def _format_generation_prompt(
    template: str,
    *,
    intents: list[Intent],
    current: Intent,
    intent_examples: str,
    samples_per_intent: int,
) -> str:
    """填充 prompt；支持 PD 常用占位符，含 {intent_list}。"""
    desc = current.description or "(无)"
    intent_list = _build_intent_list_lines(intents)
    kwargs = {
        "count": samples_per_intent,
        "intent_name": current.name_zh,
        "description": desc,
        "examples": intent_examples,
        "intent_list": intent_list,
        "intent_key": current.intent_key,
    }
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise BusinessException(
            "E50603",
            f"提示词模板含未识别的占位符: {e}。支持: count, intent_name, description, examples, intent_list, intent_key",
        ) from e


async def _max_sq_sort_order(db: AsyncSession, intent_id: UUID) -> int:
    v = (
        await db.execute(
            select(func.coalesce(func.max(SimilarQuestion.sort_order), -1)).where(
                SimilarQuestion.intent_id == intent_id
            )
        )
    ).scalar()
    return int(v)


async def generate_training_data(db: AsyncSession, library_id: UUID, config: dict) -> dict:
    settings = get_settings()
    _check_llm_config(settings)

    dataset_id = _parse_dataset_id(config.get("dataset_id"))
    model_name = config.get("model_name") or "gpt-4"
    samples_per_intent = int(config.get("samples_per_intent") or 20)
    prompt_template = config.get("prompt_template") or DEFAULT_TRAINING_TEMPLATE

    td = await db.get(TrainingDataset, dataset_id)
    if not td:
        raise BusinessException("E50501", "训练数据集不存在")
    if td.library_id != library_id:
        raise BusinessException("E50502", "训练数据集不属于该意图库")

    intents = (
        (await db.execute(select(Intent).where(Intent.dataset_id == dataset_id))).scalars().all()
    )
    if not intents:
        raise BusinessException(
            "E50503",
            "该数据集中没有意图，请先添加意图后再生成样本",
        )

    intent_count = len(intents)
    generated_count = 0
    errors: list[str] = []

    for intent in intents:
        example_rows = (
            (
                await db.execute(
                    select(SimilarQuestion.text).where(SimilarQuestion.intent_id == intent.id)
                )
            )
            .scalars()
            .all()
        )
        examples = "\n".join(example_rows) if example_rows else "(无)"
        prompt = _format_generation_prompt(
            prompt_template,
            intents=intents,
            current=intent,
            intent_examples=examples,
            samples_per_intent=samples_per_intent,
        )
        try:
            lines = await _call_llm(prompt, model_name, settings)
        except BusinessException as e:
            errors.append(f"意图 [{intent.name_zh}]: {e.error_msg}")
            continue

        if not lines:
            continue

        existing = {t.strip().lower() for t in example_rows}
        seen_batch: set[str] = set()
        base_order = await _max_sq_sort_order(db, intent.id)
        idx = 0
        for line in lines:
            if len(seen_batch) >= samples_per_intent:
                break
            key = line.strip().lower()
            if not key or key in existing or key in seen_batch:
                continue
            text = line[:512]
            sq = SimilarQuestion(
                intent_id=intent.id,
                text=text,
                slot_annotations={},
                source="llm",
                sort_order=base_order + idx + 1,
            )
            db.add(sq)
            seen_batch.add(key)
            idx += 1
            generated_count += 1

    await db.flush()
    await _update_dataset_counts(db, dataset_id)

    result = {
        "generated_count": generated_count,
        "intent_count": intent_count,
        "dataset_id": str(dataset_id),
    }
    if errors:
        result["errors"] = errors
        if generated_count == 0:
            raise BusinessException("E50602", f"LLM 生成全部失败: {'; '.join(errors)}")
    return result


async def generate_evaluation_data(db: AsyncSession, library_id: UUID, config: dict) -> dict:
    settings = get_settings()
    _check_llm_config(settings)

    eval_dataset_id = _parse_dataset_id(config.get("dataset_id"))
    model_name = config.get("model_name") or "gpt-4"
    samples_per_intent = int(config.get("samples_per_intent") or 10)
    prompt_template = config.get("prompt_template") or DEFAULT_EVAL_TEMPLATE

    ed = await db.get(EvaluationDataset, eval_dataset_id)
    if not ed:
        raise BusinessException("E50501", "评测数据集不存在")
    if ed.library_id != library_id:
        raise BusinessException("E50502", "评测数据集不属于该意图库")

    cfg = ed.config or {}
    raw_train = (
        config.get("training_dataset_id")
        or cfg.get("training_dataset_id")
        or cfg.get("train_dataset_id")
    )
    if not raw_train:
        raise BusinessException("E50503", "评测数据集未关联训练数据集，请在 config 中设置 training_dataset_id")

    training_dataset_id = _parse_dataset_id(raw_train)
    train_ds = await db.get(TrainingDataset, training_dataset_id)
    if not train_ds or train_ds.library_id != library_id:
        raise BusinessException("E50501", "训练数据集不存在")

    intents = (
        (await db.execute(select(Intent).where(Intent.dataset_id == training_dataset_id)))
        .scalars()
        .all()
    )
    if not intents:
        raise BusinessException(
            "E50503",
            "关联的训练数据集中没有意图，请先添加意图后再生成评测数据",
        )

    intent_count = len(intents)
    new_samples: list[dict] = []
    errors: list[str] = []
    existing_list = list(ed.samples or [])
    existing_utt = {
        (s.get("utterance") or s.get("text") or "").strip().lower()
        for s in existing_list
        if isinstance(s, dict)
    }

    for intent in intents:
        prompt = _format_generation_prompt(
            prompt_template,
            intents=intents,
            current=intent,
            intent_examples="(评测集生成不依赖相似问)",
            samples_per_intent=samples_per_intent,
        )
        try:
            lines = await _call_llm(prompt, model_name, settings)
        except BusinessException as e:
            errors.append(f"意图 [{intent.name_zh}]: {e.error_msg}")
            continue

        if not lines:
            continue

        added = 0
        for line in lines:
            if added >= samples_per_intent:
                break
            key = line.strip().lower()
            if not key or key in existing_utt:
                continue
            utt = line[:512]
            row = {"utterance": utt, "expected_result": intent.intent_key}
            new_samples.append(row)
            existing_utt.add(key)
            added += 1

    merged = existing_list + new_samples
    ed.samples = merged
    ed.sample_count = len(merged)
    await db.flush()

    result = {
        "generated_count": len(new_samples),
        "intent_count": intent_count,
        "dataset_id": str(eval_dataset_id),
    }
    if errors:
        result["errors"] = errors
        if not new_samples:
            raise BusinessException("E50602", f"LLM 生成全部失败: {'; '.join(errors)}")
    return result
