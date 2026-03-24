# `backend/data` 目录

本目录存放**本地/运行时数据**，按需由程序创建。

| 目录 | 说明 |
|------|------|
| **`hf_cache/`** | Hugging Face Hub / Transformers 预训练模型与 tokenizer 缓存（`HF_HOME` 默认指向此处）。**同机多次训练复用**，体积大，**已在 `backend/.gitignore` 与仓库根 `.gitignore` 中忽略，勿提交。** |
| **`models/`** | 训练产出的 ONNX、`package.zip`、标签映射等（路径常写在 `artifact_uri` / `package_uri`）。 |
| **`models/pretrained/`** | （可选）手工放入的**完整**预训练模型目录，训练时 `base_model` 填子目录名或绝对路径；见仓库根 `README`「离线 / 预置预训练模型」。 |

**预下载（推荐训练前执行一次）**（在 `backend` 目录）：

**请使用本项目的虚拟环境 Python**（与 `pyproject.toml` 锁定的 `huggingface_hub` 一致；系统 Anaconda 全局 Python 可能报 `field() got an unexpected keyword argument 'alias'` 等错误）：

```bash
# Windows
.\.venv\Scripts\python.exe -m app.scripts.prefetch_hf_cache

# Linux / macOS
./.venv/bin/python -m app.scripts.prefetch_hf_cache
```

若本机用户目录 `~/.cache/huggingface` 里已有模型、希望**复制**到项目缓存（不删原目录）：

```bash
.\.venv\Scripts\python.exe -m app.scripts.prefetch_hf_cache --migrate-user-cache
```

脚本会拉取与前端下拉一致的 Hub 模型：`bert-base-chinese`、`distilbert-base-uncased`、`prajjwal1/bert-tiny`。

部署时可将 `hf_cache` 挂载为卷，或在镜像构建时执行上述命令。
