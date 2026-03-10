#!/usr/bin/env python3
"""JointBERT PyTorch 模型导出为 ONNX 格式，支持可选 INT8 量化。

用法示例:
    python scripts/export_onnx.py --model-path models/jointbert --output-path models/jointbert.onnx
    python scripts/export_onnx.py --model-path models/jointbert --output-path models/jointbert.onnx --quantize
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoConfig, AutoTokenizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JointBERT 模型定义（与训练脚本 train_intent_model.py 保持一致）
# ---------------------------------------------------------------------------

class JointBERT(nn.Module):
    """联合意图分类 + 槽位序列标注模型。

    结构: BERT encoder → intent 分类头 + slot BIO 序列标注头
    """

    def __init__(
        self,
        model_name_or_path: str,
        num_intent_labels: int,
        num_slot_labels: int,
        dropout_rate: float = 0.1,
    ):
        super().__init__()
        from transformers import AutoModel

        self.bert = AutoModel.from_pretrained(model_name_or_path)
        hidden_size = self.bert.config.hidden_size

        self.intent_classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size, num_intent_labels),
        )
        self.slot_classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size, num_slot_labels),
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """前向推理，返回 (intent_logits, slot_logits)。"""
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        # [CLS] 向量用于意图分类
        cls_output = outputs.last_hidden_state[:, 0, :]
        intent_logits = self.intent_classifier(cls_output)

        # 全序列输出用于槽位标注
        sequence_output = outputs.last_hidden_state
        slot_logits = self.slot_classifier(sequence_output)

        return intent_logits, slot_logits


# ---------------------------------------------------------------------------
# 模型加载
# ---------------------------------------------------------------------------

def load_model(model_path: str) -> tuple[JointBERT, AutoTokenizer, dict]:
    """从训练产物目录加载 JointBERT 模型和分词器。

    期望目录结构:
        model_path/
        ├── config.json          # BERT 配置
        ├── pytorch_model.bin    # 或 model.safetensors
        ├── tokenizer_config.json
        ├── vocab.txt
        └── label_map.json       # {"intent_labels": [...], "slot_labels": [...]}
    """
    import json

    model_dir = Path(model_path)
    if not model_dir.exists():
        raise FileNotFoundError(f"模型目录不存在: {model_dir}")

    label_map_path = model_dir / "label_map.json"
    if not label_map_path.exists():
        raise FileNotFoundError(f"标签映射文件不存在: {label_map_path}")

    with open(label_map_path, encoding="utf-8") as f:
        label_map = json.load(f)

    intent_labels = label_map["intent_labels"]
    slot_labels = label_map["slot_labels"]

    logger.info(f"加载标签映射: {len(intent_labels)} 个意图, {len(slot_labels)} 个槽位标签")

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))

    config = AutoConfig.from_pretrained(str(model_dir))
    model = JointBERT(
        model_name_or_path=str(model_dir),
        num_intent_labels=len(intent_labels),
        num_slot_labels=len(slot_labels),
        dropout_rate=0.0,  # 推理时关闭 dropout
    )

    # 加载训练好的权重（兼容 pytorch_model.bin 和 model.safetensors）
    state_dict_path = model_dir / "pytorch_model.bin"
    safetensors_path = model_dir / "model.safetensors"

    if safetensors_path.exists():
        from safetensors.torch import load_file
        state_dict = load_file(str(safetensors_path))
        model.load_state_dict(state_dict, strict=False)
        logger.info(f"从 safetensors 加载权重: {safetensors_path}")
    elif state_dict_path.exists():
        state_dict = torch.load(str(state_dict_path), map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict, strict=False)
        logger.info(f"从 pytorch_model.bin 加载权重: {state_dict_path}")
    else:
        logger.warning("未找到独立权重文件，将使用预训练 BERT 基座权重")

    model.eval()
    return model, tokenizer, label_map


# ---------------------------------------------------------------------------
# ONNX 导出
# ---------------------------------------------------------------------------

def export_onnx(
    model: JointBERT,
    tokenizer: AutoTokenizer,
    output_path: str,
    max_seq_length: int = 128,
    opset_version: int = 14,
) -> Path:
    """将 JointBERT 模型导出为 ONNX 格式。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # 构造虚拟输入
    dummy_text = "帮我加热三分钟"
    encoded = tokenizer(
        dummy_text,
        max_length=max_seq_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )

    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]
    token_type_ids = encoded.get("token_type_ids", torch.zeros_like(input_ids))

    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "token_type_ids": {0: "batch_size", 1: "sequence_length"},
        "intent_logits": {0: "batch_size"},
        "slot_logits": {0: "batch_size", 1: "sequence_length"},
    }

    logger.info(f"开始导出 ONNX 模型到 {output} (opset={opset_version})")

    torch.onnx.export(
        model,
        (input_ids, attention_mask, token_type_ids),
        str(output),
        input_names=["input_ids", "attention_mask", "token_type_ids"],
        output_names=["intent_logits", "slot_logits"],
        dynamic_axes=dynamic_axes,
        opset_version=opset_version,
        do_constant_folding=True,
    )

    file_size_mb = output.stat().st_size / (1024 * 1024)
    logger.info(f"ONNX 模型已导出: {output} ({file_size_mb:.1f} MB)")
    return output


# ---------------------------------------------------------------------------
# INT8 量化
# ---------------------------------------------------------------------------

def quantize_model(onnx_path: str, output_path: str | None = None) -> Path:
    """对 ONNX 模型进行 INT8 动态量化，减小模型体积并加速推理。"""
    from onnxruntime.quantization import QuantType, quantize_dynamic

    src = Path(onnx_path)
    if output_path is None:
        dst = src.with_stem(src.stem + "_int8")
    else:
        dst = Path(output_path)

    dst.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"开始 INT8 动态量化: {src} -> {dst}")

    quantize_dynamic(
        model_input=str(src),
        model_output=str(dst),
        weight_type=QuantType.QInt8,
        per_channel=True,
        reduce_range=True,
    )

    original_mb = src.stat().st_size / (1024 * 1024)
    quantized_mb = dst.stat().st_size / (1024 * 1024)
    ratio = (1 - quantized_mb / original_mb) * 100 if original_mb > 0 else 0

    logger.info(
        f"量化完成: {original_mb:.1f} MB -> {quantized_mb:.1f} MB (压缩 {ratio:.1f}%)"
    )
    return dst


# ---------------------------------------------------------------------------
# 验证导出正确性
# ---------------------------------------------------------------------------

def validate_onnx(
    pytorch_model: JointBERT,
    tokenizer: AutoTokenizer,
    onnx_path: str,
    max_seq_length: int = 128,
    atol: float = 1e-4,
) -> bool:
    """比较 PyTorch 和 ONNX 模型输出，验证导出正确性。"""
    import onnxruntime as ort

    test_texts = [
        "帮我加热三分钟",
        "今天天气怎么样",
        "红烧肉怎么做",
        "set temperature to 180 degrees",
    ]

    logger.info(f"验证 ONNX 模型: {onnx_path}")

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    all_pass = True

    for text in test_texts:
        encoded = tokenizer(
            text,
            max_length=max_seq_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        input_ids = encoded["input_ids"]
        attention_mask = encoded["attention_mask"]
        token_type_ids = encoded.get("token_type_ids", torch.zeros_like(input_ids))

        # PyTorch 推理
        with torch.no_grad():
            pt_intent, pt_slot = pytorch_model(input_ids, attention_mask, token_type_ids)

        # ONNX Runtime 推理
        ort_inputs = {
            "input_ids": input_ids.numpy(),
            "attention_mask": attention_mask.numpy(),
            "token_type_ids": token_type_ids.numpy(),
        }
        ort_intent, ort_slot = session.run(None, ort_inputs)

        # 比较输出差异
        intent_diff = np.max(np.abs(pt_intent.numpy() - ort_intent))
        slot_diff = np.max(np.abs(pt_slot.numpy() - ort_slot))

        passed = intent_diff < atol and slot_diff < atol
        status = "✓ 通过" if passed else "✗ 失败"

        logger.info(
            f"  {status} | '{text[:20]}...' "
            f"intent_diff={intent_diff:.6f} slot_diff={slot_diff:.6f}"
        )

        if not passed:
            all_pass = False

    if all_pass:
        logger.info("所有验证样本通过，ONNX 模型输出与 PyTorch 一致")
    else:
        logger.warning(f"部分验证失败 (atol={atol})，请检查导出参数")

    return all_pass


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JointBERT PyTorch 模型导出为 ONNX 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 仅导出 ONNX
  python scripts/export_onnx.py --model-path models/jointbert --output-path models/jointbert.onnx

  # 导出并量化
  python scripts/export_onnx.py --model-path models/jointbert --output-path models/jointbert.onnx --quantize

  # 指定量化输出路径
  python scripts/export_onnx.py --model-path models/jointbert --output-path models/jointbert.onnx \\
      --quantize --quantized-output models/jointbert_int8.onnx
        """,
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="训练好的 JointBERT 模型目录路径",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="ONNX 模型输出路径 (.onnx)",
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        default=False,
        help="是否进行 INT8 动态量化",
    )
    parser.add_argument(
        "--quantized-output",
        default=None,
        help="量化模型输出路径（默认在原文件名后追加 _int8）",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=128,
        help="最大序列长度（默认 128）",
    )
    parser.add_argument(
        "--opset-version",
        type=int,
        default=14,
        help="ONNX opset 版本（默认 14）",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        default=False,
        help="跳过导出后的正确性验证",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-4,
        help="验证时允许的最大绝对误差（默认 1e-4）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logger.info("=" * 60)
    logger.info("SmartChef JointBERT ONNX 导出工具")
    logger.info("=" * 60)

    # 1. 加载模型
    logger.info(f"[1/4] 加载模型: {args.model_path}")
    model, tokenizer, label_map = load_model(args.model_path)

    # 2. 导出 ONNX
    logger.info(f"[2/4] 导出 ONNX: {args.output_path}")
    onnx_path = export_onnx(
        model=model,
        tokenizer=tokenizer,
        output_path=args.output_path,
        max_seq_length=args.max_seq_length,
        opset_version=args.opset_version,
    )

    # 3. 验证
    if not args.skip_validation:
        logger.info("[3/4] 验证导出正确性")
        validate_onnx(
            pytorch_model=model,
            tokenizer=tokenizer,
            onnx_path=str(onnx_path),
            max_seq_length=args.max_seq_length,
            atol=args.atol,
        )
    else:
        logger.info("[3/4] 跳过验证")

    # 4. 可选量化
    if args.quantize:
        logger.info("[4/4] INT8 量化")
        quantized_path = quantize_model(
            onnx_path=str(onnx_path),
            output_path=args.quantized_output,
        )

        # 验证量化后模型
        if not args.skip_validation:
            logger.info("验证量化模型正确性（允许更大误差）")
            validate_onnx(
                pytorch_model=model,
                tokenizer=tokenizer,
                onnx_path=str(quantized_path),
                max_seq_length=args.max_seq_length,
                atol=0.1,  # 量化后允许更大误差
            )
    else:
        logger.info("[4/4] 跳过量化")

    logger.info("=" * 60)
    logger.info("导出完成!")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
