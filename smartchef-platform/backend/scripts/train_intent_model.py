"""JointBERT 训练脚本：基于 chinese-roberta-wwm-ext 的联合意图分类 + 槽位提取模型训练。

训练流程:
  1. 加载训练数据（JSON 文件或数据库导出）
  2. 构建标签映射（意图标签、BIO 槽位标签）
  3. Tokenize + 字符级 BIO 标签对齐到 token 级
  4. JointBERT 模型训练（联合损失 = 意图分类损失 + 槽位标注损失）
  5. 保存模型权重 + tokenizer + 标签映射

用法:
  python -m scripts.train_intent_model \\
    --data-file data/training_data.json \\
    --output-dir models/jointbert_v1 \\
    --epochs 10 --batch-size 32 --lr 5e-5

训练数据 JSON 格式:
  [
    {
      "text": "帮我设置温度到180度",
      "intent": "voice_cmd_set_cooking_temp",
      "language": "zh",
      "slot_annotations": [
        {"slot": "number", "start": 8, "end": 11, "value": "180"}
      ]
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

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset, random_split
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("train_intent_model")

DEFAULT_PRETRAINED = "hfl/chinese-roberta-wwm-ext"
DEFAULT_MAX_LEN = 128
SLOT_PAD_LABEL_ID = -100


# ── JointBERT 模型定义 ──────────────────────────────────────────────


class JointBERT(nn.Module):
    """JointBERT: 共享 BERT 编码器 + 意图分类头 + 槽位序列标注头。

    架构:
      BERT([CLS] t1 t2 ... [SEP])
        ├─ [CLS] hidden → Dropout → Linear → intent_logits  (num_intents)
        └─ token hidden → Dropout → Linear → slot_logits    (seq_len × num_slot_labels)

    联合训练使意图和槽位特征互相增强（research.md R3 决策）。
    """

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
        sequence_output = outputs.last_hidden_state  # (B, L, H)

        cls_output = sequence_output[:, 0, :]
        intent_logits = self.intent_classifier(self.intent_dropout(cls_output))

        slot_logits = self.slot_classifier(self.slot_dropout(sequence_output))

        return intent_logits, slot_logits


# ── 数据集 ────────────────────────────────────────────────────────────


class JointBERTDataset(Dataset):
    """JointBERT 训练数据集，负责 tokenize 和 BIO 标签对齐。"""

    def __init__(
        self,
        texts: list[str],
        intent_labels: list[int],
        char_bio_labels: list[list[int]],
        tokenizer,
        max_len: int = DEFAULT_MAX_LEN,
    ):
        self.texts = texts
        self.intent_labels = intent_labels
        self.char_bio_labels = char_bio_labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        text = self.texts[idx]
        intent_label = self.intent_labels[idx]
        char_labels = self.char_bio_labels[idx]

        encoding = self.tokenizer(
            text,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].squeeze(0)
        attention_mask = encoding["attention_mask"].squeeze(0)
        token_type_ids = encoding.get(
            "token_type_ids", torch.zeros_like(input_ids)
        ).squeeze(0)
        offset_mapping = encoding["offset_mapping"].squeeze(0)

        aligned_slot_labels = _align_slot_labels(
            char_labels, offset_mapping, self.max_len
        )

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
            "intent_label": torch.tensor(intent_label, dtype=torch.long),
            "slot_labels": torch.tensor(aligned_slot_labels, dtype=torch.long),
        }


# ── 数据处理工具 ──────────────────────────────────────────────────────


def _build_char_level_bio(
    text: str,
    slot_annotations: list[dict],
    slot_label2id: dict,
) -> list[int]:
    """将字符级 slot_annotations 转换为字符级 BIO 标签 ID 序列。

    slot_annotations 格式（与 data-model.md TrainingData.slot_annotations 一致）:
      [{"slot": "number", "start": 8, "end": 11, "value": "180"}]
    """
    o_id = slot_label2id["O"]
    labels = [o_id] * len(text)

    for ann in slot_annotations:
        slot_key = ann["slot"]
        start = ann["start"]
        end = ann["end"]

        b_label = f"B-{slot_key}"
        i_label = f"I-{slot_key}"
        if b_label not in slot_label2id:
            continue

        if start < len(text):
            labels[start] = slot_label2id[b_label]
        for i in range(start + 1, min(end, len(text))):
            labels[i] = slot_label2id[i_label]

    return labels


def _align_slot_labels(
    char_labels: list[int],
    offset_mapping: torch.Tensor,
    max_len: int,
) -> list[int]:
    """将字符级 BIO 标签对齐到 tokenizer 输出的 token 级别。

    特殊 token（[CLS], [SEP], [PAD]）的 offset 为 (0, 0)，标记为 -100 不参与损失。
    对于子词 token，取其首字符对应的标签。
    """
    aligned = []
    for i in range(max_len):
        if i >= len(offset_mapping):
            aligned.append(SLOT_PAD_LABEL_ID)
            continue

        start_char, end_char = offset_mapping[i].tolist()
        if start_char == 0 and end_char == 0:
            aligned.append(SLOT_PAD_LABEL_ID)
        elif int(start_char) < len(char_labels):
            aligned.append(char_labels[int(start_char)])
        else:
            aligned.append(SLOT_PAD_LABEL_ID)

    return aligned


def load_training_data(data_path: str) -> list[dict]:
    """加载训练数据 JSON 文件。"""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"训练数据文件不存在: {data_path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    logger.info("加载训练数据: %d 条", len(data))
    return data


def build_label_maps(
    data: list[dict],
) -> tuple[dict, dict, dict, dict]:
    """从训练数据构建标签映射。

    Returns:
        (intent2id, id2intent, slot_label2id, id2slot_label)
    """
    intent_keys = sorted({item["intent"] for item in data})
    intent2id = {k: i for i, k in enumerate(intent_keys)}
    id2intent = {i: k for k, i in intent2id.items()}

    slot_keys: set[str] = set()
    for item in data:
        for ann in item.get("slot_annotations", []):
            slot_keys.add(ann["slot"])

    bio_labels = ["O"]
    for sk in sorted(slot_keys):
        bio_labels.append(f"B-{sk}")
        bio_labels.append(f"I-{sk}")

    slot_label2id = {label: i for i, label in enumerate(bio_labels)}
    id2slot_label = {i: label for label, i in slot_label2id.items()}

    logger.info("意图数量: %d, 槽位标签数量: %d", len(intent2id), len(slot_label2id))
    return intent2id, id2intent, slot_label2id, id2slot_label


def prepare_dataset(
    data: list[dict],
    tokenizer,
    intent2id: dict,
    slot_label2id: dict,
    max_len: int = DEFAULT_MAX_LEN,
) -> JointBERTDataset:
    """将原始 JSON 数据转换为 JointBERTDataset。"""
    texts: list[str] = []
    intent_labels: list[int] = []
    char_bio_labels: list[list[int]] = []

    for item in data:
        text = item["text"]
        annotations = item.get("slot_annotations", [])

        texts.append(text)
        intent_labels.append(intent2id[item["intent"]])
        char_bio_labels.append(
            _build_char_level_bio(text, annotations, slot_label2id)
        )

    return JointBERTDataset(texts, intent_labels, char_bio_labels, tokenizer, max_len)


# ── 训练 / 验证循环 ──────────────────────────────────────────────────


def train_one_epoch(
    model: JointBERT,
    dataloader: DataLoader,
    optimizer: AdamW,
    scheduler,
    device: torch.device,
    intent_loss_fn: nn.Module,
    slot_loss_fn: nn.Module,
    slot_weight: float = 1.0,
) -> dict:
    """训练一个 epoch，返回平均损失。"""
    model.train()
    total_loss = 0.0
    total_intent_loss = 0.0
    total_slot_loss = 0.0
    n_steps = 0

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        token_type_ids = batch["token_type_ids"].to(device)
        intent_labels = batch["intent_label"].to(device)
        slot_labels = batch["slot_labels"].to(device)

        intent_logits, slot_logits = model(input_ids, attention_mask, token_type_ids)

        i_loss = intent_loss_fn(intent_logits, intent_labels)
        s_loss = slot_loss_fn(
            slot_logits.view(-1, slot_logits.size(-1)), slot_labels.view(-1)
        )
        loss = i_loss + slot_weight * s_loss

        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        total_intent_loss += i_loss.item()
        total_slot_loss += s_loss.item()
        n_steps += 1

    denom = max(n_steps, 1)
    return {
        "loss": total_loss / denom,
        "intent_loss": total_intent_loss / denom,
        "slot_loss": total_slot_loss / denom,
    }


def validate(
    model: JointBERT,
    dataloader: DataLoader,
    device: torch.device,
    intent_loss_fn: nn.Module,
    slot_loss_fn: nn.Module,
) -> dict:
    """在验证集上评估，返回损失和准确率。"""
    model.eval()
    total_loss = 0.0
    intent_correct = 0
    intent_total = 0
    slot_correct = 0
    slot_total = 0
    n_steps = 0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            token_type_ids = batch["token_type_ids"].to(device)
            intent_labels = batch["intent_label"].to(device)
            slot_labels = batch["slot_labels"].to(device)

            intent_logits, slot_logits = model(
                input_ids, attention_mask, token_type_ids
            )
            i_loss = intent_loss_fn(intent_logits, intent_labels)
            s_loss = slot_loss_fn(
                slot_logits.view(-1, slot_logits.size(-1)), slot_labels.view(-1)
            )
            total_loss += (i_loss + s_loss).item()

            preds = intent_logits.argmax(dim=-1)
            intent_correct += (preds == intent_labels).sum().item()
            intent_total += intent_labels.size(0)

            slot_preds = slot_logits.argmax(dim=-1)
            mask = slot_labels != SLOT_PAD_LABEL_ID
            slot_correct += (slot_preds[mask] == slot_labels[mask]).sum().item()
            slot_total += mask.sum().item()

            n_steps += 1

    return {
        "loss": total_loss / max(n_steps, 1),
        "intent_accuracy": intent_correct / max(intent_total, 1),
        "slot_accuracy": slot_correct / max(slot_total, 1),
    }


# ── 模型保存 ──────────────────────────────────────────────────────────


def save_model(
    model: JointBERT,
    tokenizer,
    output_dir: str,
    intent2id: dict,
    id2intent: dict,
    slot_label2id: dict,
    id2slot_label: dict,
    training_args: dict,
) -> None:
    """保存训练好的模型权重、tokenizer 和标签映射。

    输出目录结构:
      output_dir/
        pytorch_model.bin      — 模型权重
        config.json            — BERT 配置
        tokenizer_config.json  — tokenizer 配置
        vocab.txt              — 词表
        label_mapping.json     — 意图 / 槽位标签映射
        training_args.json     — 训练超参记录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), output_path / "pytorch_model.bin")
    tokenizer.save_pretrained(str(output_path))
    model.bert.config.save_pretrained(str(output_path))

    label_mapping = {
        "intent2id": intent2id,
        "id2intent": {str(k): v for k, v in id2intent.items()},
        "slot_label2id": slot_label2id,
        "id2slot_label": {str(k): v for k, v in id2slot_label.items()},
        "num_intents": len(intent2id),
        "num_slot_labels": len(slot_label2id),
    }
    with open(output_path / "label_mapping.json", "w", encoding="utf-8") as f:
        json.dump(label_mapping, f, ensure_ascii=False, indent=2)

    with open(output_path / "training_args.json", "w", encoding="utf-8") as f:
        json.dump(training_args, f, ensure_ascii=False, indent=2)

    logger.info("模型已保存至: %s", output_path)


# ── CLI 入口 ──────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JointBERT 训练脚本：联合意图分类 + 槽位提取",
    )
    parser.add_argument(
        "--data-file", type=str, required=True,
        help="训练数据 JSON 文件路径",
    )
    parser.add_argument(
        "--output-dir", type=str, default="models/jointbert_v1",
        help="模型输出目录（默认 models/jointbert_v1）",
    )
    parser.add_argument(
        "--pretrained-model", type=str, default=DEFAULT_PRETRAINED,
        help=f"预训练基座模型（默认 {DEFAULT_PRETRAINED}）",
    )
    parser.add_argument(
        "--max-len", type=int, default=DEFAULT_MAX_LEN,
        help="最大序列长度（默认 128）",
    )
    parser.add_argument("--epochs", type=int, default=10, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=32, help="批次大小")
    parser.add_argument("--lr", type=float, default=5e-5, help="学习率")
    parser.add_argument("--warmup-steps", type=int, default=100, help="预热步数")
    parser.add_argument("--weight-decay", type=float, default=0.01, help="权重衰减")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout 比率")
    parser.add_argument(
        "--slot-loss-weight", type=float, default=1.0,
        help="槽位损失权重（联合损失 = intent_loss + weight * slot_loss）",
    )
    parser.add_argument("--val-split", type=float, default=0.1, help="验证集比例")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument(
        "--device", type=str, default="auto",
        help="训练设备（auto / cpu / cuda）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 随机种子
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    # 设备
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    logger.info("训练设备: %s", device)

    # ── 数据加载 ──
    data = load_training_data(args.data_file)
    intent2id, id2intent, slot_label2id, id2slot_label = build_label_maps(data)

    logger.info("加载预训练模型: %s", args.pretrained_model)
    tokenizer = AutoTokenizer.from_pretrained(args.pretrained_model)

    dataset = prepare_dataset(data, tokenizer, intent2id, slot_label2id, args.max_len)

    # 训练 / 验证集划分
    val_size = max(1, int(len(dataset) * args.val_split))
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(args.seed),
    )
    logger.info("数据集划分: 训练 %d / 验证 %d", train_size, val_size)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    # ── 模型构建 ──
    model = JointBERT(
        pretrained_model_name=args.pretrained_model,
        num_intents=len(intent2id),
        num_slot_labels=len(slot_label2id),
        dropout=args.dropout,
    ).to(device)

    intent_loss_fn = nn.CrossEntropyLoss()
    slot_loss_fn = nn.CrossEntropyLoss(ignore_index=SLOT_PAD_LABEL_ID)

    # BERT 层和分类头使用不同的 weight_decay
    no_decay = ("bias", "LayerNorm.weight")
    param_groups = [
        {
            "params": [
                p for n, p in model.named_parameters()
                if not any(nd in n for nd in no_decay)
            ],
            "weight_decay": args.weight_decay,
        },
        {
            "params": [
                p for n, p in model.named_parameters()
                if any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.0,
        },
    ]
    optimizer = AdamW(param_groups, lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=args.warmup_steps,
        num_training_steps=total_steps,
    )

    # ── 训练循环 ──
    logger.info("=" * 60)
    logger.info("开始训练")
    logger.info("  总轮数:   %d", args.epochs)
    logger.info("  批次大小: %d", args.batch_size)
    logger.info("  学习率:   %s", args.lr)
    logger.info("  总步数:   %d", total_steps)
    logger.info("  预热步数: %d", args.warmup_steps)
    logger.info("=" * 60)

    best_val_loss = float("inf")
    wall_start = time.time()

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_m = train_one_epoch(
            model, train_loader, optimizer, scheduler, device,
            intent_loss_fn, slot_loss_fn, args.slot_loss_weight,
        )
        val_m = validate(model, val_loader, device, intent_loss_fn, slot_loss_fn)

        elapsed = time.time() - t0
        logger.info(
            "Epoch %d/%d (%.1fs) | "
            "Train loss: %.4f (intent: %.4f, slot: %.4f) | "
            "Val loss: %.4f, Intent acc: %.4f, Slot acc: %.4f",
            epoch, args.epochs, elapsed,
            train_m["loss"], train_m["intent_loss"], train_m["slot_loss"],
            val_m["loss"], val_m["intent_accuracy"], val_m["slot_accuracy"],
        )

        if val_m["loss"] < best_val_loss:
            best_val_loss = val_m["loss"]
            save_model(
                model, tokenizer, args.output_dir,
                intent2id, id2intent, slot_label2id, id2slot_label,
                training_args={
                    "pretrained_model": args.pretrained_model,
                    "max_len": args.max_len,
                    "epochs": args.epochs,
                    "batch_size": args.batch_size,
                    "learning_rate": args.lr,
                    "warmup_steps": args.warmup_steps,
                    "weight_decay": args.weight_decay,
                    "dropout": args.dropout,
                    "slot_loss_weight": args.slot_loss_weight,
                    "best_val_loss": best_val_loss,
                    "best_epoch": epoch,
                    "seed": args.seed,
                },
            )
            logger.info("  -> 最优模型已保存 (val_loss=%.4f)", best_val_loss)

    wall_total = time.time() - wall_start
    logger.info("=" * 60)
    logger.info(
        "训练完成! 总时长: %.1fs, 最优 val_loss: %.4f", wall_total, best_val_loss,
    )
    logger.info("模型保存在: %s", args.output_dir)


if __name__ == "__main__":
    main()
