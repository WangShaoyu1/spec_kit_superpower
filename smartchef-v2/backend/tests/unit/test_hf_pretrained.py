"""Tests for hf_pretrained.resolve_pretrained_for_model."""

import json
from pathlib import Path

import pytest


def test_resolve_local_dir_relative_to_pretrained(tmp_path, monkeypatch):
    from app.core import hf_pretrained as hp

    monkeypatch.setattr(hp, "_backend_root", lambda: tmp_path)
    pretrained = tmp_path / "data" / "models" / "pretrained" / "my-bert"
    pretrained.mkdir(parents=True)
    (pretrained / "config.json").write_text(json.dumps({"model_type": "bert"}), encoding="utf-8")

    from app.core.hf_pretrained import resolve_pretrained_for_model

    resolved, kw = resolve_pretrained_for_model("my-bert")
    assert Path(resolved) == pretrained
    assert kw.get("local_files_only") is True


def test_resolve_hub_id_respects_local_files_only(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("HF_LOCAL_FILES_ONLY", "true")
    try:
        from app.core.hf_pretrained import resolve_pretrained_for_model

        resolved, kw = resolve_pretrained_for_model("bert-base-chinese")
        assert resolved == "bert-base-chinese"
        assert kw.get("local_files_only") is True
    finally:
        get_settings.cache_clear()
        monkeypatch.delenv("HF_LOCAL_FILES_ONLY", raising=False)


def test_resolve_hub_id_default_allows_hub(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.delenv("HF_LOCAL_FILES_ONLY", raising=False)
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    try:
        from app.core.hf_pretrained import resolve_pretrained_for_model

        resolved, kw = resolve_pretrained_for_model("bert-base-chinese")
        assert resolved == "bert-base-chinese"
        assert kw.get("local_files_only") is not True
    finally:
        get_settings.cache_clear()
