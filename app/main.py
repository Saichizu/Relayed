from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import ensure_default_owner, router as auth_router
from app.api.routes.history import router as history_router
from app.api.routes.system import router as system_router
from app.api.routes.tables import router as tables_router
from app.core.config import settings
from app.db.database import init_databases

app = FastAPI(
    title="Relayed – Pool Table Control API",
    description="FastAPI backend for managing pool tables, timers, queue, history, and ESP32 relays.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_databases()
    ensure_default_owner()


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(tables_router)
app.include_router(history_router)
app.include_router(system_router)
