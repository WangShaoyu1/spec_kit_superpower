# 可选：本机预置预训练模型（离线）

将 Hugging Face 格式的完整模型目录放在本目录下，例如：

`bert-base-chinese/config.json`、`tokenizer.json` 等。

训练时「基础模型」填写 **`bert-base-chinese`**（文件夹名）或绝对路径。

若希望完全禁止联网，在 `backend/.env` 中设置：

```env
HF_LOCAL_FILES_ONLY=true
```

并确保 `HF_HOME`（默认 `backend/data/hf_cache`）中已有 Hub 缓存，或本目录已放置完整模型。
