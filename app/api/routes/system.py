from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.system import DemoModeRequest
from app.services.relay_service import relay_service
from app.services.table_service import table_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/esp/status")
def esp_status() -> dict:
    status = relay_service.get_esp32_status()
    return {
        "reachable": relay_service.esp_is_reachable,
        "status": status,
        "last_status_ts": relay_service.last_status_ts,
        "demo_mode": relay_service.demo_mode,
    }


@router.post("/pending/process")
def process_pending() -> dict:
    return table_service.process_pending_actions()


@router.get("/demo-mode")
def get_demo_mode() -> dict:
    return {"enabled": relay_service.demo_mode}


@router.post("/demo-mode")
def set_demo_mode(payload: DemoModeRequest) -> dict:
    try:
        relay_service.set_demo_mode(payload.enabled)
        return {"enabled": relay_service.demo_mode}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
