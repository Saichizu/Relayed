from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.table import (
    AddTimeRequest,
    AssignQueueRequest,
    FinishRequest,
    OpenTableRequest,
    OutageAdjustRequest,
    QueueEntryRequest,
    StartTimerRequest,
)
from app.services.table_service import table_service

router = APIRouter(prefix="/tables", tags=["tables"])


# -----------------------------------------------------------------------
# Table read
# -----------------------------------------------------------------------


@router.get("")
def list_tables() -> list[dict]:
    return table_service.get_all_tables()


@router.get("/{ch}")
def get_table(ch: int) -> dict:
    table = table_service.get_table(ch)
    if table is None:
        raise HTTPException(status_code=404, detail=f"Table {ch} not found")
    return table


# -----------------------------------------------------------------------
# Session control
# -----------------------------------------------------------------------


@router.post("/{ch}/start")
def start_timer(ch: int, payload: StartTimerRequest) -> dict:
    try:
        return table_service.start_timer(
            ch,
            minutes=payload.minutes,
            customer=payload.customer,
            actor=payload.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{ch}/open")
def open_table(ch: int, payload: OpenTableRequest) -> dict:
    try:
        return table_service.open_table(
            ch,
            customer=payload.customer,
            rate=payload.rate,
            actor=payload.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{ch}/add-time")
def add_time(ch: int, payload: AddTimeRequest) -> dict:
    try:
        return table_service.add_time(ch, minutes=payload.minutes, actor=payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{ch}/finish")
def finish_table(ch: int, payload: FinishRequest) -> dict:
    try:
        return table_service.finish_table(ch, actor=payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{ch}/outage-adjust")
def outage_adjust(ch: int, payload: OutageAdjustRequest) -> dict:
    try:
        return table_service.apply_outage_adjustment(
            ch, minutes=payload.minutes, actor=payload.actor
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------
# Queue
# -----------------------------------------------------------------------


@router.get("/queue/list")
def list_queue() -> list[dict]:
    return table_service.get_queue()


@router.post("/queue/add")
def add_to_queue(payload: QueueEntryRequest) -> dict:
    return table_service.add_to_queue(
        customer=payload.customer,
        mode=payload.mode,
        minutes=payload.minutes,
    )


@router.delete("/queue/{queue_id}")
def remove_from_queue(queue_id: int) -> dict:
    return table_service.remove_from_queue(queue_id)


@router.post("/queue/assign")
def assign_queue(payload: AssignQueueRequest) -> dict:
    try:
        return table_service.assign_queue_to_table(
            queue_id=payload.queue_id,
            table_ch=payload.table_ch,
            actor=payload.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
