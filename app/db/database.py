from __future__ import annotations

import sqlite3
import threading

from app.core.config import settings

_main_lock = threading.Lock()
_auth_lock = threading.Lock()

# Expose locks so other modules can import them
main_db_lock = _main_lock
auth_db_lock = _auth_lock


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_main_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_auth_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.auth_db_path, check_same_thread=False)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_main_db() -> None:
    with _main_lock:
        conn = get_main_connection()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tables (
                    ch          INTEGER PRIMARY KEY,
                    status      TEXT    NOT NULL DEFAULT 'idle',
                    mode        TEXT    NOT NULL DEFAULT 'timed',
                    customer    TEXT    NOT NULL DEFAULT '',
                    started_at  INTEGER NOT NULL DEFAULT 0,
                    ends_at     INTEGER NOT NULL DEFAULT 0,
                    rate        REAL    NOT NULL DEFAULT 0,
                    paused_at   INTEGER NOT NULL DEFAULT 0,
                    paused_secs INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ch          INTEGER NOT NULL,
                    customer    TEXT    NOT NULL DEFAULT '',
                    mode        TEXT    NOT NULL DEFAULT 'timed',
                    started_at  INTEGER NOT NULL,
                    ended_at    INTEGER NOT NULL,
                    duration_s  INTEGER NOT NULL DEFAULT 0,
                    total_cost  REAL    NOT NULL DEFAULT 0,
                    actor       TEXT    NOT NULL DEFAULT '',
                    created_at  INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS queue (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer    TEXT    NOT NULL,
                    mode        TEXT    NOT NULL DEFAULT 'timed',
                    minutes     INTEGER NOT NULL DEFAULT 0,
                    created_at  INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pending_actions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    action      TEXT    NOT NULL,
                    ch          INTEGER NOT NULL,
                    created_at  INTEGER NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()


def init_auth_db() -> None:
    with _auth_lock:
        conn = get_auth_connection()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    role        TEXT    NOT NULL,
                    pin_hash    TEXT    NOT NULL,
                    created_at  INTEGER NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()


def seed_tables(num_tables: int) -> None:
    """Insert table rows for channels 1..num_tables if they don't exist."""
    with _main_lock:
        conn = get_main_connection()
        try:
            for ch in range(1, num_tables + 1):
                conn.execute(
                    "INSERT OR IGNORE INTO tables(ch) VALUES (?)",
                    (ch,),
                )
            conn.commit()
        finally:
            conn.close()


def init_databases() -> None:
    init_main_db()
    init_auth_db()
    seed_tables(settings.num_tables)
