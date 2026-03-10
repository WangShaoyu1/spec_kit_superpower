#!/usr/bin/env python3
"""从数据库导出标注训练数据（Intent + Slot + TrainingData）。

支持导出为 JSON Lines 或 CSV 格式，可按 profile_id 筛选。

用法示例:
    python scripts/export_training_data.py --output data/training.jsonl
    python scripts/export_training_data.py --output data/training.csv --format csv
    python scripts/export_training_data.py --output data/training.jsonl --profile-id <uuid>
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class ExportedSlotAnnotation:
    """导出的槽位标注。"""
    slot_key: str
    value: str
    start: int
    end: int


@dataclass
class ExportedSample:
    """导出的训练样本。"""
    id: str
    text: str
    intent_key: str
    intent_display_name: str
    category: str
    language: str
    slot_annotations: list[ExportedSlotAnnotation] = field(default_factory=list)
    bio_tags: list[str] = field(default_factory=list)
    is_auto_translated: bool = False
    created_at: str = ""


# ---------------------------------------------------------------------------
# BIO 标签生成
# ---------------------------------------------------------------------------

def build_bio_tags_char(text: str, annotations: list[ExportedSlotAnnotation]) -> list[str]:
    """根据字符级标注生成 BIO 标签（字符粒度，适合中文）。"""
    tags = ["O"] * len(text)
    sorted_anns = sorted(annotations, key=lambda a: a.start)

    for ann in sorted_anns:
        if ann.start < 0 or ann.end > len(text) or ann.start >= ann.end:
            continue
        for i in range(ann.start, ann.end):
            tags[i] = f"B-{ann.slot_key}" if i == ann.start else f"I-{ann.slot_key}"

    return tags


def build_bio_tags_token(text: str, annotations: list[ExportedSlotAnnotation]) -> list[str]:
    """根据标注生成 BIO 标签（空格分词 token 粒度，适合英文）。"""
    char_tags = build_bio_tags_char(text, annotations)
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
# 数据库读取
# ---------------------------------------------------------------------------

async def fetch_training_data(
    database_url: str,
    profile_id: str | None = None,
) -> list[ExportedSample]:
    """从数据库读取所有训练数据，联表查询 Intent + Slot + TrainingData。"""
    from sqlalchemy import text as sql_text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 查询训练数据 + 关联意图信息
    query = """
        SELECT
            td.id AS td_id,
            td.text,
            td.language,
            td.slot_annotations,
            td.is_auto_translated,
            td.created_at,
            i.intent_key,
            i.display_name AS intent_display_name,
            i.category
        FROM training_data td
        JOIN intents i ON td.intent_id = i.id
        WHERE i.is_active = true
    """

    params: dict = {}
    if profile_id:
        query += """
            AND i.id IN (
                SELECT DISTINCT td2.intent_id FROM training_data td2
                JOIN intents i2 ON td2.intent_id = i2.id
                WHERE i2.created_by = :profile_id
            )
        """
        params["profile_id"] = UUID(profile_id)

    query += " ORDER BY i.intent_key, td.language, td.created_at"

    # 查询槽位定义（用于 BIO 标签补充）
    slot_query = """
        SELECT
            s.intent_id,
            s.slot_key,
            s.display_name,
            s.entity_type,
            s.is_required
        FROM slots s
        JOIN intents i ON s.intent_id = i.id
        WHERE i.is_active = true
        ORDER BY s.intent_id, s.sort_order
    """

    samples: list[ExportedSample] = []

    async with session_factory() as session:
        # 获取训练数据
        result = await session.execute(sql_text(query), params)
        rows = result.fetchall()

        for row in rows:
            raw_annotations = row.slot_annotations or {}

            # slot_annotations 可以是 list[dict] 或 dict 格式
            annotation_list: list[dict] = []
            if isinstance(raw_annotations, list):
                annotation_list = raw_annotations
            elif isinstance(raw_annotations, dict) and "slots" in raw_annotations:
                annotation_list = raw_annotations["slots"]

            exported_anns = []
            for ann in annotation_list:
                exported_anns.append(ExportedSlotAnnotation(
                    slot_key=ann.get("slot_key", ""),
                    value=ann.get("value", ""),
                    start=ann.get("start", 0),
                    end=ann.get("end", 0),
                ))

            language = row.language or "zh"
            text = row.text

            if language == "zh":
                bio_tags = build_bio_tags_char(text, exported_anns)
            else:
                bio_tags = build_bio_tags_token(text, exported_anns)

            created_at = ""
            if row.created_at:
                created_at = row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at)

            samples.append(ExportedSample(
                id=str(row.td_id),
                text=text,
                intent_key=row.intent_key,
                intent_display_name=row.intent_display_name,
                category=row.category,
                language=language,
                slot_annotations=exported_anns,
                bio_tags=bio_tags,
                is_auto_translated=bool(row.is_auto_translated),
                created_at=created_at,
            ))

    await engine.dispose()

    logger.info(f"从数据库读取 {len(samples)} 条训练数据")
    return samples


# ---------------------------------------------------------------------------
# 导出格式写入
# ---------------------------------------------------------------------------

def export_jsonl(samples: list[ExportedSample], output_path: Path) -> None:
    """导出为 JSON Lines 格式。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for sample in samples:
            record = {
                "id": sample.id,
                "text": sample.text,
                "intent_label": sample.intent_key,
                "intent_display_name": sample.intent_display_name,
                "category": sample.category,
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
                "is_auto_translated": sample.is_auto_translated,
                "created_at": sample.created_at,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"JSONL 导出完成: {output_path}")


def export_csv(samples: list[ExportedSample], output_path: Path) -> None:
    """导出为 CSV 格式。

    CSV 列: id, text, intent_label, intent_display_name, category, language,
            slot_annotations(JSON), bio_tags(空格分隔), is_auto_translated, created_at
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id", "text", "intent_label", "intent_display_name", "category",
        "language", "slot_annotations", "bio_tags", "is_auto_translated", "created_at",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for sample in samples:
            writer.writerow({
                "id": sample.id,
                "text": sample.text,
                "intent_label": sample.intent_key,
                "intent_display_name": sample.intent_display_name,
                "category": sample.category,
                "language": sample.language,
                "slot_annotations": json.dumps(
                    [{"slot_key": a.slot_key, "value": a.value, "start": a.start, "end": a.end}
                     for a in sample.slot_annotations],
                    ensure_ascii=False,
                ),
                "bio_tags": " ".join(sample.bio_tags),
                "is_auto_translated": sample.is_auto_translated,
                "created_at": sample.created_at,
            })

    logger.info(f"CSV 导出完成: {output_path}")


# ---------------------------------------------------------------------------
# 统计信息
# ---------------------------------------------------------------------------

def print_statistics(samples: list[ExportedSample]) -> None:
    """打印导出数据的统计信息。"""
    if not samples:
        logger.info("无数据")
        return

    intent_counts: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    with_slots = 0
    auto_translated = 0

    for s in samples:
        intent_counts[s.intent_key] = intent_counts.get(s.intent_key, 0) + 1
        language_counts[s.language] = language_counts.get(s.language, 0) + 1
        category_counts[s.category] = category_counts.get(s.category, 0) + 1
        if s.slot_annotations:
            with_slots += 1
        if s.is_auto_translated:
            auto_translated += 1

    logger.info("-" * 50)
    logger.info("数据统计:")
    logger.info(f"  总计: {len(samples)} 条")
    logger.info(f"  意图数: {len(intent_counts)}")
    logger.info(f"  含槽位标注: {with_slots} 条")
    logger.info(f"  自动翻译: {auto_translated} 条")

    logger.info("  语言分布:")
    for lang, count in sorted(language_counts.items()):
        logger.info(f"    {lang}: {count}")

    logger.info("  类别分布:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {cat}: {count}")

    logger.info("  意图分布 (前 15):")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1])[:15]:
        logger.info(f"    {intent}: {count}")

    logger.info("-" * 50)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从数据库导出标注训练数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导出为 JSONL
  python scripts/export_training_data.py --output data/training.jsonl

  # 导出为 CSV
  python scripts/export_training_data.py --output data/training.csv --format csv

  # 按创建者筛选
  python scripts/export_training_data.py --output data/training.jsonl --profile-id <user-uuid>

  # 指定数据库连接
  python scripts/export_training_data.py --output data/training.jsonl \\
      --database-url postgresql+asyncpg://user:pass@host:5432/smartchef

环境变量:
  DATABASE_URL  数据库连接字符串（也可通过 --database-url 参数传入）
        """,
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出文件路径",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv"],
        default="json",
        help="输出格式: json (JSONL) 或 csv（默认 json）",
    )
    parser.add_argument(
        "--profile-id",
        default=None,
        help="按创建者 UUID 筛选数据（可选）",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="数据库连接字符串（默认从环境变量 DATABASE_URL 或项目配置读取）",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        default=False,
        help="仅显示统计信息，不导出文件",
    )
    return parser.parse_args()


def _resolve_database_url(cli_url: str | None) -> str:
    """按优先级获取数据库连接字符串: CLI 参数 > 环境变量 > 项目配置。"""
    import os

    if cli_url:
        return cli_url

    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from app.core.config import get_settings
        return get_settings().DATABASE_URL
    except Exception:
        pass

    return "postgresql+asyncpg://postgres:postgres@localhost:5432/smartchef"


def main() -> int:
    args = parse_args()

    logger.info("=" * 60)
    logger.info("SmartChef 训练数据导出工具")
    logger.info("=" * 60)

    database_url = _resolve_database_url(args.database_url)
    logger.info(f"数据库: {database_url.split('@')[-1] if '@' in database_url else '(local)'}")

    # 从数据库查询
    samples = asyncio.run(fetch_training_data(
        database_url=database_url,
        profile_id=args.profile_id,
    ))

    if not samples:
        logger.warning("数据库中没有训练数据")
        return 0

    # 打印统计
    print_statistics(samples)

    if args.stats_only:
        logger.info("Stats-only 模式，跳过导出")
        return 0

    # 导出
    output_path = Path(args.output)

    if args.format == "csv":
        export_csv(samples, output_path)
    else:
        export_jsonl(samples, output_path)

    logger.info("=" * 60)
    logger.info(f"导出完成: {output_path} ({len(samples)} 条)")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
