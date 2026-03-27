from __future__ import annotations

from pydantic import BaseModel


class DemoModeRequest(BaseModel):
    enabled: bool
