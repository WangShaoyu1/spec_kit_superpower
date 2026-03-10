"""智能分析引擎：混淆矩阵、归因分析、优化建议。"""
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch_test import BatchTestJob, BatchTestCase

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6

__all__ = ["analyze_test_results", "generate_llm_suggestions", "AnalysisReport"]


# ── 数据结构 ──────────────────────────────────────────────────


@dataclass
class ConfusionPair:
    """混淆矩阵条目：预期意图 A 被错误识别为意图 B。"""

    expected: str
    actual: str
    count: int


@dataclass
class IntentMetrics:
    """单个意图的测试指标。"""

    intent_key: str
    total: int
    correct: int
    accuracy: float
    top_confusions: list[dict] = field(default_factory=list)


@dataclass
class Attribution:
    """失败归因类别。"""

    category: str
    description: str
    count: int
    percentage: float
    examples: list[dict] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """完整智能分析报告。"""

    job_id: UUID
    overall_accuracy: float
    intent_ranking: list[IntentMetrics]
    confusion_matrix: dict[str, dict[str, int]]
    top_confusions: list[ConfusionPair]
    attributions: list[Attribution]
    suggestions: list[str]

    def to_dict(self) -> dict:
        """转为可 JSON 序列化的字典，供 API 层直接返回。"""
        return {
            "job_id": str(self.job_id),
            "overall_accuracy": self.overall_accuracy,
            "intent_ranking": [
                {
                    "intent_key": m.intent_key,
                    "total": m.total,
                    "correct": m.correct,
                    "accuracy": m.accuracy,
                    "top_confusions": m.top_confusions,
                }
                for m in self.intent_ranking
            ],
            "confusion_matrix": self.confusion_matrix,
            "top_confusions": [
                {"expected": c.expected, "actual": c.actual, "count": c.count}
                for c in self.top_confusions
            ],
            "attributions": [
                {
                    "category": a.category,
                    "description": a.description,
                    "count": a.count,
                    "percentage": a.percentage,
                    "examples": a.examples,
                }
                for a in self.attributions
            ],
            "suggestions": self.suggestions,
        }


# ── 主入口 ────────────────────────────────────────────────────


async def analyze_test_results(
    db: AsyncSession,
    job_id: UUID,
    max_examples: int = 5,
) -> AnalysisReport:
    """
    对批量测试结果进行智能分析。

    分析维度：
    1. 混淆矩阵 — 实际意图 vs 预测意图的交叉统计
    2. 归因分析 — 将失败用例按根因分类（路由错误 / 意图混淆 / 低置信度等）
    3. 优化建议 — 基于分析结果给出可操作的改进建议
    """
    job = await _load_job(db, job_id)
    cases = await _load_cases(db, job_id)
    failed_cases = [c for c in cases if not c.passed]

    confusion = _build_confusion_matrix(cases)
    top_confusions = _extract_top_confusions(confusion)
    intent_ranking = _build_intent_ranking(cases, confusion)
    attributions = _build_attributions(failed_cases, max_examples)
    suggestions = _generate_suggestions(
        intent_ranking, top_confusions, attributions, job
    )

    return AnalysisReport(
        job_id=job_id,
        overall_accuracy=job.accuracy or 0.0,
        intent_ranking=intent_ranking,
        confusion_matrix=confusion,
        top_confusions=top_confusions,
        attributions=attributions,
        suggestions=suggestions,
    )


async def generate_llm_suggestions(
    report: AnalysisReport,
    llm_provider: str = "gpt-4o-mini",
) -> list[str]:
    """（可选）调用 LLM 对分析报告进行深度分析，生成高级优化建议。"""
    from app.services.chitchat.llm_adapter import chat_completion

    prompt = _build_llm_analysis_prompt(report)
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个 NLU 系统调优专家。请根据测试分析报告给出具体、"
                "可操作的优化建议，每条建议单独一行。"
            ),
        },
        {"role": "user", "content": prompt},
    ]
    response = await chat_completion(
        messages, model=llm_provider, temperature=0.3
    )
    return [line.strip() for line in response.strip().split("\n") if line.strip()]


# ── 数据加载 ──────────────────────────────────────────────────


async def _load_job(db: AsyncSession, job_id: UUID) -> BatchTestJob:
    result = await db.execute(
        select(BatchTestJob).where(BatchTestJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError(f"批量测试任务不存在: {job_id}")
    return job


async def _load_cases(db: AsyncSession, job_id: UUID) -> list[BatchTestCase]:
    result = await db.execute(
        select(BatchTestCase).where(BatchTestCase.job_id == job_id)
    )
    return list(result.scalars().all())


# ── 混淆矩阵 ──────────────────────────────────────────────────


def _build_confusion_matrix(
    cases: list[BatchTestCase],
) -> dict[str, dict[str, int]]:
    """
    生成混淆矩阵：matrix[expected][actual] = count。
    仅统计设置了 expected_intent 的用例。
    """
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for case in cases:
        expected = case.expected_intent or "unknown"
        actual = case.actual_intent or "none"
        matrix[expected][actual] += 1
    return {k: dict(v) for k, v in matrix.items()}


def _extract_top_confusions(
    matrix: dict[str, dict[str, int]],
    limit: int = 10,
) -> list[ConfusionPair]:
    """从混淆矩阵中提取最常见的错误分类对（排除正确匹配和 unknown）。"""
    pairs: list[ConfusionPair] = []
    for expected, actuals in matrix.items():
        if expected == "unknown":
            continue
        for actual, count in actuals.items():
            if expected != actual:
                pairs.append(
                    ConfusionPair(expected=expected, actual=actual, count=count)
                )
    pairs.sort(key=lambda p: p.count, reverse=True)
    return pairs[:limit]


# ── 意图准确率排名 ────────────────────────────────────────────


def _build_intent_ranking(
    cases: list[BatchTestCase],
    confusion: dict[str, dict[str, int]],
) -> list[IntentMetrics]:
    """按意图维度统计准确率，按准确率升序排列（最差排最前方便定位问题）。"""
    intent_groups: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "correct": 0}
    )
    for case in cases:
        key = case.expected_intent or "unknown"
        intent_groups[key]["total"] += 1
        if case.passed:
            intent_groups[key]["correct"] += 1

    ranking: list[IntentMetrics] = []
    for intent_key, stats in intent_groups.items():
        accuracy = (
            stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        )
        top_conf: list[dict] = []
        if intent_key in confusion:
            sorted_actuals = sorted(
                confusion[intent_key].items(), key=lambda x: -x[1]
            )
            for actual, count in sorted_actuals:
                if actual != intent_key:
                    top_conf.append({"misclassified_as": actual, "count": count})
        ranking.append(
            IntentMetrics(
                intent_key=intent_key,
                total=stats["total"],
                correct=stats["correct"],
                accuracy=accuracy,
                top_confusions=top_conf[:5],
            )
        )

    ranking.sort(key=lambda m: m.accuracy)
    return ranking


# ── 归因分析 ──────────────────────────────────────────────────

_ATTRIBUTION_CATEGORIES: dict[str, str] = {
    "route_mismatch": "路由域判断错误（预期域与实际域不一致）",
    "intent_mismatch": "意图分类错误（域正确但意图识别错误）",
    "low_confidence": f"低置信度识别（置信度低于 {CONFIDENCE_THRESHOLD}）",
    "no_intent_detected": "未检测到意图（Pipeline 返回空意图）",
    "other": "其他未归类错误",
}


def _build_attributions(
    failed_cases: list[BatchTestCase],
    max_examples: int,
) -> list[Attribution]:
    """将失败用例按根因分类，统计各类别数量并附带示例。"""
    buckets: dict[str, list[BatchTestCase]] = defaultdict(list)
    for case in failed_cases:
        category = _classify_failure(case)
        buckets[category].append(case)

    total_failures = len(failed_cases) or 1
    result: list[Attribution] = []
    for cat, cat_cases in sorted(buckets.items(), key=lambda x: -len(x[1])):
        examples = [
            {
                "input_text": c.input_text,
                "expected_intent": c.expected_intent,
                "actual_intent": c.actual_intent,
                "expected_domain": c.expected_domain,
                "actual_domain": c.actual_domain,
                "intent_confidence": c.intent_confidence,
            }
            for c in cat_cases[:max_examples]
        ]
        result.append(
            Attribution(
                category=cat,
                description=_ATTRIBUTION_CATEGORIES.get(cat, cat),
                count=len(cat_cases),
                percentage=round(len(cat_cases) / total_failures * 100, 1),
                examples=examples,
            )
        )
    return result


def _classify_failure(case: BatchTestCase) -> str:
    """判断单个失败用例的根因类别。"""
    if (
        case.expected_domain
        and case.actual_domain
        and case.expected_domain != case.actual_domain
    ):
        return "route_mismatch"
    if case.actual_intent is None:
        return "no_intent_detected"
    if (
        case.intent_confidence is not None
        and case.intent_confidence < CONFIDENCE_THRESHOLD
    ):
        return "low_confidence"
    if case.expected_intent and case.actual_intent != case.expected_intent:
        return "intent_mismatch"
    return "other"


# ── 优化建议 ──────────────────────────────────────────────────


def _generate_suggestions(
    ranking: list[IntentMetrics],
    top_confusions: list[ConfusionPair],
    attributions: list[Attribution],
    job: BatchTestJob,
) -> list[str]:
    """基于分析结果生成可操作的优化建议。"""
    suggestions: list[str] = []
    accuracy = job.accuracy or 0.0

    if accuracy < 0.9:
        suggestions.append(
            f"整体准确率 {accuracy:.1%} 低于 90%，"
            "建议全面审查训练数据覆盖度和路由策略配置。"
        )

    low_intents = [
        m for m in ranking if m.accuracy < 0.8 and m.intent_key != "unknown"
    ]
    for m in low_intents[:5]:
        suggestions.append(
            f"意图 [{m.intent_key}] 准确率仅 {m.accuracy:.1%}"
            f"（{m.correct}/{m.total}），建议补充更多多样化的训练表达。"
        )

    for pair in top_confusions[:3]:
        suggestions.append(
            f"意图 [{pair.expected}] 与 [{pair.actual}] 之间存在 "
            f"{pair.count} 次混淆，建议增加两者的差异化训练样本或调整意图边界。"
        )

    for attr in attributions:
        if attr.category == "route_mismatch" and attr.count > 3:
            suggestions.append(
                f"有 {attr.count} 条用例出现路由域判断错误，"
                "建议检查路由策略配置和域边界定义。"
            )
        if attr.category == "no_intent_detected" and attr.count > 2:
            suggestions.append(
                f"有 {attr.count} 条用例未检测到意图，"
                "可能是训练数据覆盖不足或表达方式差异过大。"
            )
        if attr.category == "low_confidence" and attr.count > 3:
            suggestions.append(
                f"有 {attr.count} 条用例识别置信度低于 {CONFIDENCE_THRESHOLD}，"
                "建议增加相关意图的训练数据量。"
            )

    avg_latency = job.avg_latency_ms or 0
    if avg_latency > 200:
        suggestions.append(
            f"平均响应延迟 {avg_latency:.0f}ms 超过 200ms 阈值，"
            "建议优化 Pipeline 性能或缩减知识库检索范围。"
        )

    if not suggestions:
        suggestions.append("所有指标表现良好，暂无优化建议。")

    return suggestions


# ── LLM 辅助分析 ──────────────────────────────────────────────


def _build_llm_analysis_prompt(report: AnalysisReport) -> str:
    """构建供 LLM 深度分析的提示词。"""
    lines = [
        "以下是 NLU 系统批量测试的分析报告：",
        f"- 整体准确率: {report.overall_accuracy:.1%}",
        "",
        "## 低准确率意图（按准确率升序）",
    ]
    for m in report.intent_ranking[:10]:
        lines.append(
            f"- {m.intent_key}: {m.accuracy:.1%} ({m.correct}/{m.total})"
        )

    lines.append("")
    lines.append("## 主要混淆对")
    for c in report.top_confusions[:5]:
        lines.append(
            f"- 预期 [{c.expected}] 被识别为 [{c.actual}]：{c.count} 次"
        )

    lines.append("")
    lines.append("## 失败归因分布")
    for a in report.attributions:
        lines.append(f"- {a.description}: {a.count} 条 ({a.percentage}%)")

    lines.append("")
    lines.append(
        "请针对以上数据，给出 3-5 条具体、可操作的优化建议，"
        "每条建议包含：问题描述、建议操作、预期效果。"
    )
    return "\n".join(lines)
