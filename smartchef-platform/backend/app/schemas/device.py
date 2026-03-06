from uuid import UUID
from pydantic import BaseModel, Field


class DeviceContext(BaseModel):
    cooking_status: str | None = None
    door_closed: bool | None = None
    current_temp: float | None = None
    current_page: str | None = None
    display_15: dict | None = None
    display_7: dict | None = None
    extra: dict | None = None


class DeviceDialogRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=128)
    text: str = Field(..., min_length=1)
    language: str = Field(default="zh", pattern="^(zh|en)$")
    device_context: DeviceContext | None = None


class DeviceDialogResponse(BaseModel):
    domain: str
    intent: str | None = None
    slots: dict = {}
    response_text: str
    needs_followup: bool = False
    session_id: str | None = None


class VersionInfo(BaseModel):
    version_tag: str
    profile_id: UUID
    description: str | None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}
