"""JointBERT 模型评估脚本：F1-Score、混淆矩阵、延迟基准。

评估内容:
  1. 意图分类: macro / micro / weighted F1-Score + 混淆矩阵热力图
  2. 槽位提取: entity-level Precision / Recall / F1
  3. 延迟基准: 单条推理时间 + 批量推理时间（含 P95 / P99）
  4. 综合报告输出（JSON 文件 + 控制台摘要）

用法:
  python -m scripts.evaluate_model \\
    --model-dir models/jointbert_v1 \\
    --test-file data/test_data.json \\
    --output-dir reports/eval_v1

测试数据 JSON 格式（与训练数据一致）:
  [
    {
      "text": "帮我设置温度到180度",
      "intent": "voice_cmd_set_cooking_temp",
      "slot_annotations": [{"slot": "number", "start": 8, "end": 11, "value": "180"}]
    },
    ...
  ]
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import AutoModel, AutoTokenizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evaluate_model")

DEFAULT_MAX_LEN = 128


# ── JointBERT 模型定义（与 train_intent_model.py 保持一致） ──────────


class JointBERT(nn.Module):
    """JointBERT: 共享 BERT 编码器 + 意图分类头 + 槽位序列标注头。"""

    def __init__(
        self,
        pretrained_model_name: str,
        num_intents: int,
        num_slot_labels: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.bert = AutoModel.from_pretrained(pretrained_model_name)
        hidden_size = self.bert.config.hidden_size

        self.intent_dropout = nn.Dropout(dropout)
        self.intent_classifier = nn.Linear(hidden_size, num_intents)

        self.slot_dropout = nn.Dropout(dropout)
        self.slot_classifier = nn.Linear(hidden_size, num_slot_labels)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        seq_output = outputs.last_hidden_state
        intent_logits = self.intent_classifier(
            self.intent_dropout(seq_output[:, 0, :])
        )
        slot_logits = self.slot_classifier(self.slot_dropout(seq_output))
        return intent_logits, slot_logits


# ── 模型加载 ──────────────────────────────────────────────────────────


def load_model(
    model_dir: str, device: torch.device
) -> tuple[JointBERT, AutoTokenizer, dict, dict]:
    """加载训练好的 JointBERT 模型、tokenizer 和标签映射。"""
    model_path = Path(model_dir)

    with open(model_path / "label_mapping.json", encoding="utf-8") as f:
        label_mapping = json.load(f)
    with open(model_path / "training_args.json", encoding="utf-8") as f:
        training_args = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(str(model_path))

    model = JointBERT(
        pretrained_model_name=str(model_path),
        num_intents=label_mapping["num_intents"],
        num_slot_labels=label_mapping["num_slot_labels"],
        dropout=training_args.get("dropout", 0.1),
    )
    state_dict = torch.load(
        model_path / "pytorch_model.bin", map_location=device, weights_only=True,
    )
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    logger.info(
        "模型已加载: %s (意图=%d, 槽位标签=%d)",
        model_dir, label_mapping["num_intents"], label_mapping["num_slot_labels"],
    )
    return model, tokenizer, label_mapping, training_args


def load_test_data(test_file: str) -> list[dict]:
    """加载测试数据 JSON。格式与训练数据一致。"""
    path = Path(test_file)
    if not path.exists():
        raise FileNotFoundError(f"测试数据文件不存在: {test_file}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── 推理 ──────────────────────────────────────────────────────────────


def predict_single(
    model: JointBERT,
    tokenizer: AutoTokenizer,
    text: str,
    label_mapping: dict,
    device: torch.device,
    max_len: int = DEFAULT_MAX_LEN,
) -> dict:
    """单条文本推理，返回意图和槽位预测。"""
    encoding = tokenizer(
        text,
        max_length=max_len,
        padding="max_length",
        truncation=True,
        return_offsets_mapping=True,
        return_tensors="pt",
    )

    input_ids = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)
    token_type_ids = encoding.get(
        "token_type_ids", torch.zeros_like(input_ids)
    ).to(device)
    offset_mapping = encoding["offset_mapping"].squeeze(0)

    with torch.no_grad():
        intent_logits, slot_logits = model(input_ids, attention_mask, token_type_ids)

    intent_probs = torch.softmax(intent_logits, dim=-1)
    intent_id = intent_logits.argmax(dim=-1).item()
    intent_key = label_mapping["id2intent"].get(str(intent_id), "unknown")
    intent_confidence = intent_probs[0, intent_id].item()

    slot_preds = slot_logits.argmax(dim=-1).squeeze(0)
    slots = _extract_entities_from_bio(
        text, slot_preds, offset_mapping, label_mapping["id2slot_label"],
    )

    return {
        "intent": intent_key,
        "intent_confidence": intent_confidence,
        "slots": slots,
    }


def predict_batch(
    model: JointBERT,
    tokenizer: AutoTokenizer,
    texts: list[str],
    label_mapping: dict,
    device: torch.device,
    max_len: int = DEFAULT_MAX_LEN,
    batch_size: int = 32,
) -> list[dict]:
    """批量推理。"""
    results: list[dict] = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        encoding = tokenizer(
            batch_texts,
            max_length=max_len,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)
        token_type_ids = encoding.get(
            "token_type_ids", torch.zeros_like(input_ids)
        ).to(device)
        offset_mappings = encoding["offset_mapping"]

        with torch.no_grad():
            intent_logits, slot_logits = model(
                input_ids, attention_mask, token_type_ids,
            )

        intent_ids = intent_logits.argmax(dim=-1)
        intent_probs = torch.softmax(intent_logits, dim=-1)
        slot_preds_batch = slot_logits.argmax(dim=-1)

        for j in range(len(batch_texts)):
            iid = intent_ids[j].item()
            intent_key = label_mapping["id2intent"].get(str(iid), "unknown")
            confidence = intent_probs[j, iid].item()

            slots = _extract_entities_from_bio(
                batch_texts[j],
                slot_preds_batch[j],
                offset_mappings[j],
                label_mapping["id2slot_label"],
            )
            results.append({
                "intent": intent_key,
                "intent_confidence": confidence,
                "slots": slots,
            })

    return results


def _extract_entities_from_bio(
    text: str,
    slot_preds: torch.Tensor,
    offset_mapping: torch.Tensor,
    id2slot_label: dict,
) -> list[dict]:
    """从 BIO 标签序列中提取实体 span。"""
    entities: list[dict] = []
    current: dict | None = None

    for idx in range(len(slot_preds)):
        start_char, end_char = offset_mapping[idx].tolist()

        if start_char == 0 and end_char == 0:
            if current:
                entities.append(current)
                current = None
            continue

        label = id2slot_label.get(str(slot_preds[idx].item()), "O")

        if label.startswith("B-"):
            if current:
                entities.append(current)
            slot_key = label[2:]
            current = {
                "slot": slot_key,
                "start": int(start_char),
                "end": int(end_char),
                "value": text[int(start_char) : int(end_char)],
            }
        elif label.startswith("I-") and current and label[2:] == current["slot"]:
            current["end"] = int(end_char)
            current["value"] = text[current["start"] : int(end_char)]
        else:
            if current:
                entities.append(current)
                current = None

    if current:
        entities.append(current)

    return entities


# ── 评估计算 ──────────────────────────────────────────────────────────


def evaluate_intent_classification(
    true_labels: list[str],
    pred_labels: list[str],
) -> dict:
    """意图分类评估：多种 F1、Precision、Recall、混淆矩阵。"""
    present_labels = sorted(set(true_labels) | set(pred_labels))

    accuracy = sum(
        t == p for t, p in zip(true_labels, pred_labels)
    ) / max(len(true_labels), 1)

    metrics = {
        "accuracy": accuracy,
        "f1_macro": f1_score(
            true_labels, pred_labels, average="macro", zero_division=0,
        ),
        "f1_micro": f1_score(
            true_labels, pred_labels, average="micro", zero_division=0,
        ),
        "f1_weighted": f1_score(
            true_labels, pred_labels, average="weighted", zero_division=0,
        ),
        "precision_macro": precision_score(
            true_labels, pred_labels, average="macro", zero_division=0,
        ),
        "recall_macro": recall_score(
            true_labels, pred_labels, average="macro", zero_division=0,
        ),
    }

    cm = confusion_matrix(true_labels, pred_labels, labels=present_labels)
    metrics["confusion_matrix"] = {
        "labels": present_labels,
        "matrix": cm.tolist(),
    }

    report = classification_report(
        true_labels, pred_labels,
        labels=present_labels,
        output_dict=True,
        zero_division=0,
    )
    metrics["per_class_report"] = {
        k: v for k, v in report.items()
        if k not in ("accuracy", "macro avg", "weighted avg")
    }

    return metrics


def evaluate_slot_extraction(
    true_slots_list: list[list[dict]],
    pred_slots_list: list[list[dict]],
) -> dict:
    """槽位提取 entity-level 评估：Precision / Recall / F1。

    匹配规则：(slot_key, value) 完全一致视为命中。
    """
    tp, fp, fn = 0, 0, 0

    for true_slots, pred_slots in zip(true_slots_list, pred_slots_list):
        true_set = {(s["slot"], s.get("value", "")) for s in true_slots}
        pred_set = {(s["slot"], s.get("value", "")) for s in pred_slots}

        tp += len(true_set & pred_set)
        fp += len(pred_set - true_set)
        fn += len(true_set - pred_set)

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    return {
        "slot_precision": precision,
        "slot_recall": recall,
        "slot_f1": f1,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def run_latency_benchmark(
    model: JointBERT,
    tokenizer: AutoTokenizer,
    texts: list[str],
    label_mapping: dict,
    device: torch.device,
    max_len: int = DEFAULT_MAX_LEN,
    warmup_runs: int = 10,
    benchmark_runs: int = 100,
    batch_size: int = 32,
) -> dict:
    """延迟基准测试：单条推理 + 批量推理。"""
    sample_text = texts[0] if texts else "设置温度到180度"

    # 预热，让 GPU / CPU 缓存就绪
    for _ in range(warmup_runs):
        predict_single(model, tokenizer, sample_text, label_mapping, device, max_len)

    # 单条推理延迟
    single_latencies = []
    for i in range(benchmark_runs):
        text = texts[i % len(texts)]
        t0 = time.perf_counter()
        predict_single(model, tokenizer, text, label_mapping, device, max_len)
        single_latencies.append((time.perf_counter() - t0) * 1000)

    arr_single = np.array(single_latencies)

    # 批量推理延迟
    batch_texts = [texts[i % len(texts)] for i in range(batch_size)]
    n_batch_runs = max(1, min(benchmark_runs // 5, 20))
    batch_latencies = []
    for _ in range(n_batch_runs):
        t0 = time.perf_counter()
        predict_batch(
            model, tokenizer, batch_texts, label_mapping, device, max_len, batch_size,
        )
        batch_latencies.append((time.perf_counter() - t0) * 1000)

    arr_batch = np.array(batch_latencies)

    return {
        "single_inference": {
            "runs": len(single_latencies),
            "mean_ms": float(np.mean(arr_single)),
            "median_ms": float(np.median(arr_single)),
            "p95_ms": float(np.percentile(arr_single, 95)),
            "p99_ms": float(np.percentile(arr_single, 99)),
            "min_ms": float(np.min(arr_single)),
            "max_ms": float(np.max(arr_single)),
        },
        "batch_inference": {
            "batch_size": batch_size,
            "runs": n_batch_runs,
            "mean_ms": float(np.mean(arr_batch)),
            "p95_ms": float(np.percentile(arr_batch, 95)),
            "per_sample_ms": float(np.mean(arr_batch) / max(batch_size, 1)),
        },
    }


# ── 报告输出 ──────────────────────────────────────────────────────────


def save_confusion_matrix_plot(
    cm_labels: list[str],
    cm_matrix: list[list[int]],
    output_path: Path,
) -> None:
    """保存混淆矩阵热力图为 PNG。"""
    matrix = np.array(cm_matrix)
    n = len(cm_labels)

    fig_size = max(8, n * 0.5)
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))

    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=cm_labels,
        yticklabels=cm_labels,
        ax=ax,
    )
    ax.set_xlabel("预测意图", fontsize=12)
    ax.set_ylabel("真实意图", fontsize=12)
    ax.set_title("意图分类混淆矩阵", fontsize=14)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("混淆矩阵热力图已保存: %s", output_path)


def save_evaluation_report(report: dict, output_dir: str) -> None:
    """保存评估报告（JSON）和混淆矩阵（JSON + PNG）。"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_file = output_path / "evaluation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info("评估报告已保存: %s", report_file)

    if "intent_classification" in report:
        cm_data = report["intent_classification"].get("confusion_matrix", {})
        cm_json = output_path / "confusion_matrix.json"
        with open(cm_json, "w", encoding="utf-8") as f:
            json.dump(cm_data, f, ensure_ascii=False, indent=2)
        logger.info("混淆矩阵数据已保存: %s", cm_json)

        if cm_data.get("labels") and cm_data.get("matrix"):
            save_confusion_matrix_plot(
                cm_data["labels"],
                cm_data["matrix"],
                output_path / "confusion_matrix.png",
            )


def print_console_summary(report: dict) -> None:
    """打印控制台评估摘要。"""
    print("\n" + "=" * 70)
    print("  JointBERT 模型评估报告")
    print("=" * 70)

    if "intent_classification" in report:
        ic = report["intent_classification"]
        print("\n--- 意图分类 ---")
        print(f"  准确率 (Accuracy):   {ic['accuracy']:.4f}")
        print(f"  F1 (macro):          {ic['f1_macro']:.4f}")
        print(f"  F1 (micro):          {ic['f1_micro']:.4f}")
        print(f"  F1 (weighted):       {ic['f1_weighted']:.4f}")
        print(f"  精确率 (macro):      {ic['precision_macro']:.4f}")
        print(f"  召回率 (macro):      {ic['recall_macro']:.4f}")

    if "slot_extraction" in report:
        se = report["slot_extraction"]
        print("\n--- 槽位提取 (entity-level) ---")
        print(f"  Precision:  {se['slot_precision']:.4f}")
        print(f"  Recall:     {se['slot_recall']:.4f}")
        print(f"  F1:         {se['slot_f1']:.4f}")
        print(
            f"  TP={se['true_positives']}, "
            f"FP={se['false_positives']}, "
            f"FN={se['false_negatives']}"
        )

    if "latency_benchmark" in report:
        lb = report["latency_benchmark"]
        si = lb["single_inference"]
        bi = lb["batch_inference"]
        print("\n--- 延迟基准 ---")
        print(f"  单条推理 ({si['runs']} 次):")
        print(f"    平均:  {si['mean_ms']:.2f} ms")
        print(f"    中位:  {si['median_ms']:.2f} ms")
        print(f"    P95:   {si['p95_ms']:.2f} ms")
        print(f"    P99:   {si['p99_ms']:.2f} ms")
        print(f"  批量推理 (batch_size={bi['batch_size']}, {bi['runs']} 次):")
        print(f"    平均:  {bi['mean_ms']:.2f} ms")
        print(f"    单条:  {bi['per_sample_ms']:.2f} ms")

        p95 = si["p95_ms"]
        target = 200.0
        status = "PASS" if p95 < target else "FAIL"
        print(f"\n  >> P95 延迟 {p95:.2f}ms vs 目标 {target:.0f}ms → [{status}]")

    if "test_data_stats" in report:
        stats = report["test_data_stats"]
        print(f"\n--- 测试数据 ---")
        print(f"  样本数: {stats['total_samples']}")
        print(f"  意图数: {stats['num_intents']}")

    print("\n" + "=" * 70)


# ── CLI 入口 ──────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JointBERT 模型评估脚本：F1-Score、混淆矩阵、延迟基准",
    )
    parser.add_argument(
        "--model-dir", type=str, required=True,
        help="训练好的模型目录（包含 pytorch_model.bin 和 label_mapping.json）",
    )
    parser.add_argument(
        "--test-file", type=str, required=True,
        help="测试数据 JSON 文件路径",
    )
    parser.add_argument(
        "--output-dir", type=str, default="reports/eval",
        help="评估报告输出目录（默认 reports/eval）",
    )
    parser.add_argument(
        "--max-len", type=int, default=DEFAULT_MAX_LEN,
        help="最大序列长度（默认 128）",
    )
    parser.add_argument(
        "--batch-size", type=int, default=32,
        help="批量推理批次大小",
    )
    parser.add_argument(
        "--warmup-runs", type=int, default=10,
        help="延迟测试预热次数",
    )
    parser.add_argument(
        "--benchmark-runs", type=int, default=100,
        help="延迟测试运行次数",
    )
    parser.add_argument(
        "--device", type=str, default="auto",
        help="推理设备（auto / cpu / cuda）",
    )
    parser.add_argument(
        "--skip-latency", action="store_true",
        help="跳过延迟基准测试",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 设备选择
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    logger.info("评估设备: %s", device)

    # 加载模型
    model, tokenizer, label_mapping, training_args = load_model(
        args.model_dir, device,
    )

    # 加载测试数据
    test_data = load_test_data(args.test_file)
    logger.info("测试样本数: %d", len(test_data))

    texts = [item["text"] for item in test_data]
    true_intents = [item["intent"] for item in test_data]
    true_slots_list = [item.get("slot_annotations", []) for item in test_data]

    # ── 批量推理 ──
    logger.info("执行批量推理...")
    predictions = predict_batch(
        model, tokenizer, texts, label_mapping, device, args.max_len, args.batch_size,
    )
    pred_intents = [p["intent"] for p in predictions]
    pred_slots_list = [p["slots"] for p in predictions]

    # ── 意图分类评估 ──
    intent_metrics = evaluate_intent_classification(true_intents, pred_intents)
    logger.info("意图分类 F1 (macro): %.4f", intent_metrics["f1_macro"])

    # ── 槽位提取评估 ──
    slot_metrics = evaluate_slot_extraction(true_slots_list, pred_slots_list)
    logger.info("槽位提取 F1: %.4f", slot_metrics["slot_f1"])

    # ── 延迟基准 ──
    latency_metrics: dict = {}
    if not args.skip_latency:
        logger.info("运行延迟基准测试...")
        latency_metrics = run_latency_benchmark(
            model, tokenizer, texts, label_mapping, device,
            args.max_len, args.warmup_runs, args.benchmark_runs, args.batch_size,
        )
        logger.info(
            "单条推理 P95: %.2f ms",
            latency_metrics["single_inference"]["p95_ms"],
        )

    # ── 汇总报告 ──
    report = {
        "model_dir": args.model_dir,
        "test_file": args.test_file,
        "device": str(device),
        "test_data_stats": {
            "total_samples": len(test_data),
            "num_intents": len(set(true_intents)),
            "intent_distribution": {
                k: true_intents.count(k) for k in sorted(set(true_intents))
            },
        },
        "intent_classification": intent_metrics,
        "slot_extraction": slot_metrics,
        "training_args": training_args,
    }
    if latency_metrics:
        report["latency_benchmark"] = latency_metrics

    save_evaluation_report(report, args.output_dir)
    print_console_summary(report)


if __name__ == "__main__":
    main()
