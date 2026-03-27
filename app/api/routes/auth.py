from __future__ import annotations

import hashlib
import os
import time

from fastapi import APIRouter, HTTPException

from app.db.database import auth_db_lock, get_auth_connection
from app.schemas.auth import CreateUserRequest, LoginRequest, UpdateUserRequest

router = APIRouter(prefix="/auth", tags=["auth"])

ROLE_OWNER = "Owner"
ROLE_MANAGER = "Manager"
ROLE_EMPLOYEE = "Employee"
ALL_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_EMPLOYEE)

PBKDF2_ITERS = 100_000

# In-process session (single-server; replace with JWT / Redis for multi-worker)
_current_user: dict | None = None


# ------------------------------------------------------------------
# Password helpers
# ------------------------------------------------------------------


def _hash_password(password: str, salt_hex: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERS,
    )
    return f"{salt_hex}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, _ = stored.split("$", 1)
    except ValueError:
        return False
    return _hash_password(password, salt_hex) == stored


def _row_to_user(row: dict) -> dict:
    return {"id": int(row["id"]), "name": row["name"], "role": row["role"]}


# ------------------------------------------------------------------
# Startup helper
# ------------------------------------------------------------------


def ensure_default_owner(password: str = "", name: str = "") -> None:
    from app.core.config import settings

    if not password:
        password = settings.default_owner_password
    if not name:
        name = settings.default_owner_name

    with auth_db_lock:
        conn = get_auth_connection()
        try:
            count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
            if count and int(count["n"]) > 0:
                return
            salt_hex = os.urandom(16).hex()
            pw_hash = _hash_password(password, salt_hex)
            conn.execute(
                "INSERT INTO users(name, role, pin_hash, created_at) VALUES(?,?,?,?)",
                (name, ROLE_OWNER, pw_hash, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    global _current_user

    password = (payload.password or "").strip()
    if not password:
        raise HTTPException(status_code=400, detail="password is required")

    with auth_db_lock:
        conn = get_auth_connection()
        try:
            rows = conn.execute(
                "SELECT id, name, role, pin_hash FROM users"
            ).fetchall()
        finally:
            conn.close()

    for row in rows:
        if _verify_password(password, row["pin_hash"]):
            _current_user = _row_to_user(row)
            return {"user": _current_user}

    raise HTTPException(status_code=401, detail="invalid password")


@router.post("/logout")
def logout() -> dict:
    global _current_user
    _current_user = None
    return {"status": "logged_out"}


@router.get("/me")
def me() -> dict:
    return {"user": _current_user}


@router.get("/users")
def list_users() -> list[dict]:
    with auth_db_lock:
        conn = get_auth_connection()
        try:
            rows = conn.execute(
                "SELECT id, name, role FROM users ORDER BY role, name"
            ).fetchall()
            return [_row_to_user(r) for r in rows]
        finally:
            conn.close()


@router.post("/users")
def create_user(payload: CreateUserRequest) -> dict:
    if payload.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail="invalid role")

    salt_hex = os.urandom(16).hex()
    pw_hash = _hash_password(payload.password, salt_hex)

    with auth_db_lock:
        conn = get_auth_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO users(name, role, pin_hash, created_at) VALUES(?,?,?,?)",
                ((payload.name or "").strip() or "User", payload.role, pw_hash, int(time.time())),
            )
            conn.commit()
            user_id = cursor.lastrowid
            row = conn.execute("SELECT id, name, role FROM users WHERE id=?", (user_id,)).fetchone()
            return _row_to_user(row)
        finally:
            conn.close()


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UpdateUserRequest) -> dict:
    # Allowed column clauses — hardcoded to prevent SQL injection if logic ever changes
    ALLOWED_CLAUSES = {"name=?", "role=?", "pin_hash=?"}

    fields: list[str] = []
    values: list = []

    if payload.name is not None:
        fields.append("name=?")
        values.append((payload.name or "").strip() or "User")

    if payload.role is not None:
        if payload.role not in ALL_ROLES:
            raise HTTPException(status_code=400, detail="invalid role")
        fields.append("role=?")
        values.append(payload.role)

    if payload.password is not None:
        salt_hex = os.urandom(16).hex()
        fields.append("pin_hash=?")
        values.append(_hash_password(payload.password, salt_hex))

    if not fields:
        raise HTTPException(status_code=400, detail="no fields to update")

    # Guard: reject any clause not in the explicit whitelist
    if not all(f in ALLOWED_CLAUSES for f in fields):
        raise HTTPException(status_code=400, detail="invalid update fields")

    values.append(user_id)

    with auth_db_lock:
        conn = get_auth_connection()
        try:
            conn.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id=?",  # noqa: S608
                tuple(values),
            )
            conn.commit()
            row = conn.execute(
                "SELECT id, name, role FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="user not found")
            return _row_to_user(row)
        finally:
            conn.close()


@router.delete("/users/{user_id}")
def delete_user(user_id: int) -> dict:
    with auth_db_lock:
        conn = get_auth_connection()
        try:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            return {"status": "deleted", "user_id": user_id}
        finally:
            conn.close()
