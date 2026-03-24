"""LLM-based training / evaluation sample generation for intent libraries."""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any
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

# 控制台检索用统一前缀（uvicorn 默认会打出 app.services.data_generation_service 与消息）
LOG_TRAIN = "[generate-training]"
LOG_EVAL = "[generate-eval]"

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


def _check_llm_config(settings: Settings, *, log_prefix: str = "[llm-config]") -> None:
    if not settings.ZENMUX_API_KEY:
        logger.warning("%s 失败: ZENMUX_API_KEY 未设置", log_prefix)
        raise BusinessException(
            "E50601",
            "LLM 未配置: ZENMUX_API_KEY 为空，请在 .env 中设置 ZENMUX_API_KEY",
        )
    if not settings.ZENMUX_BASE_URL:
        logger.warning("%s 失败: ZENMUX_BASE_URL 未设置", log_prefix)
        raise BusinessException(
            "E50601",
            "LLM 未配置: ZENMUX_BASE_URL 为空，请在 .env 中设置",
        )
    logger.info("%s 通过（已检测到 API Key 与 Base URL）", log_prefix)


async def _call_llm(
    prompt: str,
    model_name: str,
    settings: Settings,
    *,
    stage: str = "llm",
) -> list[str]:
    """stage: 日志环节标识，便于在控制台搜索 ``[data_generation:xxx]``。"""
    log_tag = f"[data_generation:{stage}]"
    logger.info(
        "%s 步骤=OpenAI.chat.completions 开始 model=%s prompt_len=%d",
        log_tag,
        model_name,
        len(prompt),
    )
    client = AsyncOpenAI(base_url=settings.ZENMUX_BASE_URL, api_key=settings.ZENMUX_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=120,
        )
        choices = getattr(resp, "choices", None) or []
        if not choices:
            logger.warning(
                "%s 步骤=解析响应 失败: choices 为空 model=%s", log_tag, model_name
            )
            raise BusinessException(
                "E50602",
                "LLM 返回空 choices（可能为内容策略拦截或服务异常），请重试或更换模型",
            )
        msg = choices[0].message
        content = ((msg.content if msg else None) or "").strip()
        lines = _parse_response_lines(content)
        logger.info(
            "%s 步骤=解析响应 成功 raw_len=%d lines=%d",
            log_tag,
            len(content),
            len(lines),
        )
        if not lines:
            logger.warning("%s LLM 正文为空或无可解析行 model=%s", log_tag, model_name)
        return lines
    except BusinessException as be:
        logger.warning(
            "%s 步骤=OpenAI 业务异常 code=%s msg=%s",
            log_tag,
            getattr(be, "error_code", ""),
            getattr(be, "error_msg", str(be)),
        )
        raise
    except Exception as exc:
        logger.exception("%s 步骤=OpenAI 请求 未捕获异常 model=%s", log_tag, model_name)
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
    except ValueError as e:
        raise BusinessException(
            "E50603",
            f"提示词模板格式错误（花括号需成对，字面量请写成 {{ 与 }}）: {e}",
        ) from e


def _parse_samples_per_intent(raw: object, default: int = 20) -> int:
    if raw is None or raw == "":
        return default
    try:
        n = int(raw)
    except (TypeError, ValueError) as e:
        raise BusinessException("E50603", f"samples_per_intent 须为正整数: {raw!r}") from e
    if n < 1 or n > 500:
        raise BusinessException("E50603", "samples_per_intent 须在 1～500 之间")
    return n


def _append_per_intent_hint_if_needed(
    prompt_template: str,
    prompt: str,
    *,
    current: Intent,
    samples_per_intent: int,
) -> str:
    """仅含 {{intent_list}} 等列表类模板时，补充「当前针对哪一意图、生成几条」说明，避免多轮相同提示词无的放矢。"""
    if "{intent_name}" in prompt_template or "{intent_key}" in prompt_template:
        return prompt
    suffix = (
        f"\n\n【重要】请仅为当前意图「{current.name_zh}」（intent_key={current.intent_key}）"
        f" 生成恰好 {samples_per_intent} 条不同的中文用户口语化句子，每行一条，不要编号；"
        f"不要输出属于其他意图的句子。"
    )
    return prompt + suffix


async def _max_sq_sort_order(db: AsyncSession, intent_id: UUID) -> int:
    v = (
        await db.execute(
            select(func.coalesce(func.max(SimilarQuestion.sort_order), -1))
            .select_from(SimilarQuestion)
            .where(SimilarQuestion.intent_id == intent_id)
        )
    ).scalar()
    if v is None:
        return -1
    return int(v)


async def generate_training_data(
    db: AsyncSession,
    library_id: UUID,
    config: dict,
    *,
    progress_callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> dict:
    settings = get_settings()
    logger.info(
        "%s 开始 library_id=%s config_keys=%s",
        LOG_TRAIN,
        library_id,
        sorted((config or {}).keys()),
    )
    _check_llm_config(settings, log_prefix=f"{LOG_TRAIN} [llm-config]")

    dataset_id = _parse_dataset_id(config.get("dataset_id"))
    model_name = config.get("model_name") or "gpt-4"
    samples_per_intent = _parse_samples_per_intent(config.get("samples_per_intent"), 20)
    prompt_template = config.get("prompt_template") or DEFAULT_TRAINING_TEMPLATE
    logger.info(
        "%s 步骤=参数 dataset_id=%s model=%s samples_per_intent=%d template_len=%d",
        LOG_TRAIN,
        dataset_id,
        model_name,
        samples_per_intent,
        len(prompt_template or ""),
    )

    td = await db.get(TrainingDataset, dataset_id)
    if not td:
        logger.warning("%s 步骤=加载训练集 失败: 记录不存在 dataset_id=%s", LOG_TRAIN, dataset_id)
        raise BusinessException("E50501", "训练数据集不存在")
    if td.library_id != library_id:
        logger.warning(
            "%s 步骤=校验归属 失败: dataset.library_id=%s != library_id=%s",
            LOG_TRAIN,
            td.library_id,
            library_id,
        )
        raise BusinessException("E50502", "训练数据集不属于该意图库")
    logger.info("%s 步骤=加载训练集 成功 name=%s", LOG_TRAIN, getattr(td, "name", ""))

    intents = (
        (await db.execute(select(Intent).where(Intent.dataset_id == dataset_id))).scalars().all()
    )
    if not intents:
        logger.warning("%s 步骤=加载意图列表 失败: 0 条", LOG_TRAIN)
        raise BusinessException(
            "E50503",
            "该数据集中没有意图，请先添加意图后再生成样本",
        )
    logger.info("%s 步骤=加载意图列表 成功 count=%d", LOG_TRAIN, len(intents))

    intent_count = len(intents)
    generated_count = 0
    errors: list[str] = []

    if progress_callback:
        await progress_callback(
            {
                "intent_total": intent_count,
                "intent_index": 0,
                "generated_count": 0,
                "errors": [],
                "current_intent_key": None,
                "current_intent_name": None,
            }
        )

    for idx_intent, intent in enumerate(intents):
        logger.info(
            "%s 步骤=意图循环 [%d/%d] intent_key=%s name=%s id=%s",
            LOG_TRAIN,
            idx_intent + 1,
            intent_count,
            intent.intent_key,
            intent.name_zh,
            intent.id,
        )
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
        try:
            prompt = _format_generation_prompt(
                prompt_template,
                intents=intents,
                current=intent,
                intent_examples=examples,
                samples_per_intent=samples_per_intent,
            )
        except BusinessException as e:
            logger.warning(
                "%s 步骤=填充提示词模板 失败 intent=%s code=%s %s",
                LOG_TRAIN,
                intent.intent_key,
                e.error_code,
                e.error_msg,
            )
            raise
        prompt = _append_per_intent_hint_if_needed(
            prompt_template, prompt, current=intent, samples_per_intent=samples_per_intent
        )
        logger.info(
            "%s 步骤=提示词就绪 intent=%s final_prompt_len=%d",
            LOG_TRAIN,
            intent.intent_key,
            len(prompt),
        )
        lines: list[str] = []
        try:
            lines = await _call_llm(
                prompt,
                model_name,
                settings,
                stage=f"train/{intent.intent_key}",
            )
        except BusinessException as e:
            logger.warning(
                "%s 步骤=LLM 调用 失败 intent=%s code=%s msg=%s",
                LOG_TRAIN,
                intent.intent_key,
                e.error_code,
                e.error_msg,
            )
            errors.append(f"意图 [{intent.name_zh}]: {e.error_msg}")

        if not lines:
            logger.warning(
                "%s 步骤=写入相似问 跳过: 无解析行 intent=%s", LOG_TRAIN, intent.intent_key
            )
        else:
            existing = {t.strip().lower() for t in example_rows}
            seen_batch: set[str] = set()
            base_order = await _max_sq_sort_order(db, intent.id)
            logger.info(
                "%s 步骤=写入相似问 开始 intent=%s base_sort_order=%d",
                LOG_TRAIN,
                intent.intent_key,
                base_order,
            )
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
            logger.info(
                "%s 步骤=意图循环 本意图新增 intent=%s added=%d",
                LOG_TRAIN,
                intent.intent_key,
                idx,
            )

        if progress_callback:
            await db.flush()
            await _update_dataset_counts(db, dataset_id)
            await progress_callback(
                {
                    "intent_index": idx_intent + 1,
                    "intent_total": intent_count,
                    "current_intent_key": intent.intent_key,
                    "current_intent_name": intent.name_zh,
                    "generated_count": generated_count,
                    "errors": list(errors),
                }
            )
            await db.commit()

    if not progress_callback:
        logger.info("%s 步骤=flush+更新统计 dataset_id=%s", LOG_TRAIN, dataset_id)
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
            logger.warning(
                "%s 结束 失败: 全部意图均未生成成功 errors=%s", LOG_TRAIN, errors
            )
            raise BusinessException("E50602", f"LLM 生成全部失败: {'; '.join(errors)}")
    logger.info(
        "%s 结束 成功 generated=%d intent_count=%d errors=%d",
        LOG_TRAIN,
        generated_count,
        intent_count,
        len(errors),
    )
    return result


async def generate_evaluation_data(db: AsyncSession, library_id: UUID, config: dict) -> dict:
    settings = get_settings()
    logger.info(
        "%s 开始 library_id=%s config_keys=%s",
        LOG_EVAL,
        library_id,
        sorted((config or {}).keys()),
    )
    _check_llm_config(settings, log_prefix=f"{LOG_EVAL} [llm-config]")

    eval_dataset_id = _parse_dataset_id(config.get("dataset_id"))
    model_name = config.get("model_name") or "gpt-4"
    samples_per_intent = _parse_samples_per_intent(config.get("samples_per_intent"), 10)
    prompt_template = config.get("prompt_template") or DEFAULT_EVAL_TEMPLATE

    ed = await db.get(EvaluationDataset, eval_dataset_id)
    if not ed:
        logger.warning("%s 步骤=加载评测集 失败: 不存在 id=%s", LOG_EVAL, eval_dataset_id)
        raise BusinessException("E50501", "评测数据集不存在")
    if ed.library_id != library_id:
        logger.warning(
            "%s 步骤=校验评测集归属 失败 eval.library_id=%s != library_id=%s",
            LOG_EVAL,
            ed.library_id,
            library_id,
        )
        raise BusinessException("E50502", "评测数据集不属于该意图库")

    cfg = ed.config or {}
    raw_train = (
        config.get("training_dataset_id")
        or cfg.get("training_dataset_id")
        or cfg.get("train_dataset_id")
    )
    if not raw_train:
        logger.warning("%s 步骤=解析关联训练集 失败: config 中无 training_dataset_id", LOG_EVAL)
        raise BusinessException("E50503", "评测数据集未关联训练数据集，请在 config 中设置 training_dataset_id")

    training_dataset_id = _parse_dataset_id(raw_train)
    train_ds = await db.get(TrainingDataset, training_dataset_id)
    if not train_ds or train_ds.library_id != library_id:
        logger.warning(
            "%s 步骤=加载关联训练集 失败 train_id=%s", LOG_EVAL, training_dataset_id
        )
        raise BusinessException("E50501", "训练数据集不存在")
    logger.info(
        "%s 步骤=关联训练集 training_dataset_id=%s", LOG_EVAL, training_dataset_id
    )

    intents = (
        (await db.execute(select(Intent).where(Intent.dataset_id == training_dataset_id)))
        .scalars()
        .all()
    )
    if not intents:
        logger.warning("%s 步骤=加载意图 失败: 训练集中无意图", LOG_EVAL)
        raise BusinessException(
            "E50503",
            "关联的训练数据集中没有意图，请先添加意图后再生成评测数据",
        )
    logger.info("%s 步骤=加载意图 count=%d", LOG_EVAL, len(intents))

    intent_count = len(intents)
    new_samples: list[dict] = []
    errors: list[str] = []
    existing_list = list(ed.samples or [])
    existing_utt = {
        (s.get("utterance") or s.get("text") or "").strip().lower()
        for s in existing_list
        if isinstance(s, dict)
    }

    for ie, intent in enumerate(intents):
        logger.info(
            "%s 步骤=意图循环 [%d/%d] intent_key=%s",
            LOG_EVAL,
            ie + 1,
            intent_count,
            intent.intent_key,
        )
        prompt = _format_generation_prompt(
            prompt_template,
            intents=intents,
            current=intent,
            intent_examples="(评测集生成不依赖相似问)",
            samples_per_intent=samples_per_intent,
        )
        try:
            lines = await _call_llm(
                prompt,
                model_name,
                settings,
                stage=f"eval/{intent.intent_key}",
            )
        except BusinessException as e:
            logger.warning(
                "%s 步骤=LLM 失败 intent=%s code=%s %s",
                LOG_EVAL,
                intent.intent_key,
                e.error_code,
                e.error_msg,
            )
            errors.append(f"意图 [{intent.name_zh}]: {e.error_msg}")
            continue

        if not lines:
            logger.warning("%s 步骤=无解析行 intent=%s", LOG_EVAL, intent.intent_key)
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
    logger.info("%s 步骤=写入评测样本 flush eval_id=%s new=%d", LOG_EVAL, eval_dataset_id, len(new_samples))
    await db.flush()

    result = {
        "generated_count": len(new_samples),
        "intent_count": intent_count,
        "dataset_id": str(eval_dataset_id),
    }
    if errors:
        result["errors"] = errors
        if not new_samples:
            logger.warning("%s 结束 失败: 无新增样本 errors=%s", LOG_EVAL, errors)
            raise BusinessException("E50602", f"LLM 生成全部失败: {'; '.join(errors)}")
    logger.info(
        "%s 结束 成功 new_samples=%d errors=%d",
        LOG_EVAL,
        len(new_samples),
        len(errors),
    )
    return result
