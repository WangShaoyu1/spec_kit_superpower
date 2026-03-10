#!/usr/bin/env python3
"""中文训练数据翻译为英文，通过 ZenMux（OpenAI 兼容）LLM API 调用。

BIO 槽位标注在翻译后会自动重新对齐。支持批量处理和速率限制。

用法示例:
    python scripts/translate_training_data.py --input data/train_zh.jsonl --output data/train_en.jsonl
    python scripts/translate_training_data.py --input data/train_zh.jsonl --output data/train_en.jsonl \\
        --batch-size 5 --rpm 30
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ZENMUX_BASE_URL = "https://zenmux.ai/api/v1"
DEFAULT_MODEL = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class SlotAnnotation:
    """单个槽位标注（文本片段级别）。"""
    slot_key: str
    value: str
    start: int
    end: int


@dataclass
class TrainingSample:
    """一条训练样本。"""
    text: str
    intent_label: str
    language: str = "zh"
    slot_annotations: list[SlotAnnotation] = field(default_factory=list)
    bio_tags: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 数据加载/保存
# ---------------------------------------------------------------------------

def load_training_data(input_path: str) -> list[TrainingSample]:
    """加载 JSONL 格式的训练数据。

    每行 JSON 格式:
    {
        "text": "帮我加热三分钟",
        "intent_label": "voice_cmd_heat",
        "language": "zh",
        "slot_annotations": [{"slot_key": "duration", "value": "三分钟", "start": 4, "end": 7}],
        "bio_tags": ["O", "O", "O", "O", "B-duration", "I-duration", "I-duration"]
    }
    """
    samples = []
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"输入文件不存在: {path}")

    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"第 {line_num} 行 JSON 解析失败: {e}")
                continue

            annotations = []
            for ann in data.get("slot_annotations", []) or []:
                annotations.append(SlotAnnotation(
                    slot_key=ann["slot_key"],
                    value=ann["value"],
                    start=ann.get("start", 0),
                    end=ann.get("end", 0),
                ))

            samples.append(TrainingSample(
                text=data["text"],
                intent_label=data["intent_label"],
                language=data.get("language", "zh"),
                slot_annotations=annotations,
                bio_tags=data.get("bio_tags", []),
                extra=data.get("extra", {}),
            ))

    logger.info(f"加载 {len(samples)} 条训练数据: {path}")
    return samples


def save_training_data(samples: list[TrainingSample], output_path: str) -> None:
    """保存为 JSONL 格式。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for sample in samples:
            record = {
                "text": sample.text,
                "intent_label": sample.intent_label,
                "language": sample.language,
                "slot_annotations": [
                    {
                        "slot_key": ann.slot_key,
                        "value": ann.value,
                        "start": ann.start,
                        "end": ann.end,
                    }
                    for ann in sample.slot_annotations
                ],
                "bio_tags": sample.bio_tags,
                "is_auto_translated": True,
            }
            record.update(sample.extra)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"保存 {len(samples)} 条翻译数据: {path}")


# ---------------------------------------------------------------------------
# 速率限制器
# ---------------------------------------------------------------------------

class RateLimiter:
    """简单的令牌桶速率限制器，按每分钟请求数(RPM)控制。"""

    def __init__(self, rpm: int):
        self.rpm = rpm
        self.interval = 60.0 / rpm
        self._last_call = 0.0

    async def acquire(self) -> None:
        now = time.monotonic()
        wait = self._last_call + self.interval - now
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call = time.monotonic()


# ---------------------------------------------------------------------------
# LLM 翻译
# ---------------------------------------------------------------------------

TRANSLATE_PROMPT = """\
你是一个专业翻译系统。请将以下中文文本翻译为英文。

要求:
1. 翻译要自然流畅
2. 保留原文的口语风格
3. 食物名称翻译为常用英文名（如：红烧肉 -> braised pork）
4. 如果文本包含标注的槽位值片段，翻译后请同时返回每个槽位值对应的英文翻译

输入格式:
- text: 要翻译的中文文本
- slots: 需要在译文中定位的槽位值列表 [{"slot_key": "xxx", "value_zh": "xxx"}]

请严格按 JSON 格式返回:
{
    "translated_text": "英文翻译结果",
    "slot_mappings": [{"slot_key": "xxx", "value_en": "xxx"}]
}

仅返回 JSON，不要添加其他内容。"""


async def translate_with_llm(
    client: "openai.AsyncOpenAI",
    model: str,
    sample: TrainingSample,
    rate_limiter: RateLimiter,
) -> TrainingSample | None:
    """通过 LLM 翻译单条训练数据并重新对齐槽位标注。"""
    await rate_limiter.acquire()

    slot_info = [
        {"slot_key": ann.slot_key, "value_zh": ann.value}
        for ann in sample.slot_annotations
    ]

    user_msg = json.dumps(
        {"text": sample.text, "slots": slot_info},
        ensure_ascii=False,
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": TRANSLATE_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=512,
        )
    except Exception as e:
        logger.error(f"LLM 调用失败: {e} | text='{sample.text[:30]}...'")
        return None

    raw = response.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(f"LLM 返回非法 JSON: {raw[:100]}")
        return None

    translated_text: str = result.get("translated_text", "")
    slot_mappings: list[dict] = result.get("slot_mappings", [])

    if not translated_text:
        logger.warning(f"LLM 返回空翻译: text='{sample.text[:30]}...'")
        return None

    # 重新对齐槽位标注
    new_annotations = _realign_slots(translated_text, sample.slot_annotations, slot_mappings)
    bio_tags = _build_bio_tags(translated_text, new_annotations)

    return TrainingSample(
        text=translated_text,
        intent_label=sample.intent_label,
        language="en",
        slot_annotations=new_annotations,
        bio_tags=bio_tags,
        extra=sample.extra,
    )


def _realign_slots(
    translated_text: str,
    original_annotations: list[SlotAnnotation],
    slot_mappings: list[dict],
) -> list[SlotAnnotation]:
    """根据 LLM 返回的槽位映射，在译文中定位槽位值。"""
    mapping_dict = {m["slot_key"]: m["value_en"] for m in slot_mappings if "value_en" in m}
    new_annotations = []

    for ann in original_annotations:
        en_value = mapping_dict.get(ann.slot_key)
        if not en_value:
            continue

        # 在译文中查找对应英文槽位值
        lower_text = translated_text.lower()
        lower_val = en_value.lower()
        idx = lower_text.find(lower_val)

        if idx >= 0:
            new_annotations.append(SlotAnnotation(
                slot_key=ann.slot_key,
                value=translated_text[idx: idx + len(en_value)],
                start=idx,
                end=idx + len(en_value),
            ))
        else:
            logger.debug(f"无法在译文中定位槽位 '{ann.slot_key}': '{en_value}'")

    return new_annotations


def _build_bio_tags(text: str, annotations: list[SlotAnnotation]) -> list[str]:
    """基于字符级槽位标注生成 BIO 标签序列（按空格分词的 token 级别）。"""
    char_tags = ["O"] * len(text)

    sorted_anns = sorted(annotations, key=lambda a: a.start)
    for ann in sorted_anns:
        if ann.start < 0 or ann.end > len(text):
            continue
        for i in range(ann.start, ann.end):
            char_tags[i] = f"B-{ann.slot_key}" if i == ann.start else f"I-{ann.slot_key}"

    # 按空格分词，取每个 token 首字符的标签
    tokens = text.split()
    bio_tags = []
    pos = 0
    for token in tokens:
        idx = text.find(token, pos)
        if idx >= 0:
            bio_tags.append(char_tags[idx])
            pos = idx + len(token)
        else:
            bio_tags.append("O")

    return bio_tags


# ---------------------------------------------------------------------------
# 批量翻译调度
# ---------------------------------------------------------------------------

async def translate_batch(
    samples: list[TrainingSample],
    api_key: str,
    base_url: str,
    model: str,
    batch_size: int,
    rpm: int,
) -> list[TrainingSample]:
    """批量翻译训练数据，返回翻译成功的样本列表。"""
    import openai

    client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
    rate_limiter = RateLimiter(rpm)

    translated: list[TrainingSample] = []
    total = len(samples)
    failed = 0

    for batch_start in range(0, total, batch_size):
        batch = samples[batch_start: batch_start + batch_size]
        tasks = [
            translate_with_llm(client, model, sample, rate_limiter)
            for sample in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"翻译异常: {result}")
                failed += 1
            elif result is None:
                failed += 1
            else:
                translated.append(result)

        done = min(batch_start + batch_size, total)
        logger.info(f"进度: {done}/{total} (成功 {len(translated)}, 失败 {failed})")

    await client.close()
    return translated


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="中文训练数据翻译为英文（ZenMux LLM 调用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本翻译
  python scripts/translate_training_data.py --input data/train_zh.jsonl --output data/train_en.jsonl

  # 自定义批量大小和速率限制
  python scripts/translate_training_data.py --input data/train_zh.jsonl --output data/train_en.jsonl \\
      --batch-size 10 --rpm 60

  # 使用指定模型
  python scripts/translate_training_data.py --input data/train_zh.jsonl --output data/train_en.jsonl \\
      --model gpt-4o

环境变量:
  ZENMUX_API_KEY  ZenMux API 密钥（也可通过 --api-key 参数传入）
        """,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入中文训练数据文件 (JSONL 格式)",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出英文训练数据文件 (JSONL 格式)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="ZenMux API Key（默认从环境变量 ZENMUX_API_KEY 读取）",
    )
    parser.add_argument(
        "--base-url",
        default=ZENMUX_BASE_URL,
        help=f"API base URL（默认 {ZENMUX_BASE_URL}）",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"翻译用 LLM 模型名称（默认 {DEFAULT_MODEL}）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="并发翻译批次大小（默认 5）",
    )
    parser.add_argument(
        "--rpm",
        type=int,
        default=30,
        help="每分钟最大请求数（默认 30）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="仅加载数据并显示统计，不执行翻译",
    )
    return parser.parse_args()


def main() -> int:
    import os

    args = parse_args()

    logger.info("=" * 60)
    logger.info("SmartChef 训练数据翻译工具 (中→英)")
    logger.info("=" * 60)

    # 加载数据
    samples = load_training_data(args.input)

    # 筛选中文数据
    zh_samples = [s for s in samples if s.language == "zh"]
    logger.info(f"中文样本: {len(zh_samples)} / 总计 {len(samples)}")

    if not zh_samples:
        logger.warning("没有需要翻译的中文样本")
        return 0

    # 统计
    intent_counts: dict[str, int] = {}
    for s in zh_samples:
        intent_counts[s.intent_label] = intent_counts.get(s.intent_label, 0) + 1
    logger.info(f"涉及 {len(intent_counts)} 个意图:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1])[:10]:
        logger.info(f"  {intent}: {count} 条")

    if args.dry_run:
        logger.info("Dry run 模式，跳过翻译")
        return 0

    # API Key
    api_key = args.api_key or os.environ.get("ZENMUX_API_KEY", "")
    if not api_key:
        logger.error("未提供 API Key，请设置 ZENMUX_API_KEY 环境变量或使用 --api-key 参数")
        return 1

    # 执行翻译
    translated = asyncio.run(translate_batch(
        samples=zh_samples,
        api_key=api_key,
        base_url=args.base_url,
        model=args.model,
        batch_size=args.batch_size,
        rpm=args.rpm,
    ))

    logger.info(f"翻译完成: 成功 {len(translated)} / 总计 {len(zh_samples)}")

    if translated:
        save_training_data(translated, args.output)

    logger.info("=" * 60)
    logger.info("翻译任务完成!")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
