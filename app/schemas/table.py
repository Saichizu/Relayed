from __future__ import annotations

from pydantic import BaseModel, Field


class StartTimerRequest(BaseModel):
    minutes: int = Field(..., gt=0)
    customer: str = Field(..., min_length=1, max_length=64)
    actor: str = ""


class AddTimeRequest(BaseModel):
    minutes: int = Field(..., gt=0)
    actor: str = ""


class OpenTableRequest(BaseModel):
    customer: str = Field(..., min_length=1, max_length=64)
    rate: float = Field(default=0.0, ge=0)
    actor: str = ""


class FinishRequest(BaseModel):
    actor: str = ""


class QueueEntryRequest(BaseModel):
    customer: str = Field(..., min_length=1, max_length=64)
    mode: str = "timed"
    minutes: int = Field(default=0, ge=0)


class AssignQueueRequest(BaseModel):
    queue_id: int
    table_ch: int
    actor: str = ""


class OutageAdjustRequest(BaseModel):
    minutes: int = Field(..., gt=0)
    actor: str = ""
