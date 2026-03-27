from __future__ import annotations

from pydantic import BaseModel, Field


class DemoModeRequest(BaseModel):
    enabled: bool


class RelayOverrideRequest(BaseModel):
    state: str = Field(..., pattern="^(on|off)$")
