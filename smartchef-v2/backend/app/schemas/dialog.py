"""Pydantic schemas for the device-facing dialog API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DialogRequest(BaseModel):
    profile_id: str
    text: str = Field(..., min_length=1, max_length=2048)
    session_id: str | None = None
    device_id: str | None = None


class DialogResponse(BaseModel):
    session_id: str
    domain: str
    intent: str | None = None
    slots: dict = {}
    confidence: float = 0.0
    response_text: str
    debug: dict = {}
