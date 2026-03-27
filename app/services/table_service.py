from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

from app.core.config import settings
from app.db.database import get_main_connection, main_db_lock
from app.services.relay_service import relay_service

logger = logging.getLogger(__name__)

STATUS_IDLE = "idle"
STATUS_ACTIVE = "active"   # timed session running
STATUS_OPEN = "open"       # open (pay-per-hour) session running

MODE_TIMED = "timed"
MODE_OPEN = "open"


class TableService:
    """Business logic for pool table management."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_all_tables(self) -> list[dict]:
        with main_db_lock:
            conn = get_main_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM tables ORDER BY ch"
                ).fetchall()
                return [self._enrich(dict(r)) for r in rows]
            finally:
                conn.close()

    def get_table(self, ch: int) -> Optional[dict]:
        with main_db_lock:
            conn = get_main_connection()
            try:
                row = conn.execute(
                    "SELECT * FROM tables WHERE ch=?", (ch,)
                ).fetchone()
                if row is None:
                    return None
                return self._enrich(dict(row))
            finally:
                conn.close()

    def _enrich(self, row: dict) -> dict:
        """Attach computed fields (remaining_seconds, elapsed_seconds) to a table row."""
        now = int(time.time())
        status = row.get("status", STATUS_IDLE)

        if status == STATUS_ACTIVE:
            ends_at = row.get("ends_at", 0)
            remaining = max(0, ends_at - now)
            row["remaining_seconds"] = remaining
            row["elapsed_seconds"] = max(0, now - row.get("started_at", now))
        elif status == STATUS_OPEN:
            started = row.get("started_at", now)
            paused_secs = row.get("paused_secs", 0)
            paused_at = row.get("paused_at", 0)
            if paused_at:
                elapsed = (paused_at - started) - paused_secs
            else:
                elapsed = (now - started) - paused_secs
            row["elapsed_seconds"] = max(0, elapsed)
            rate = row.get("rate", 0.0)
            row["running_cost"] = round((elapsed / 3600) * rate, 2) if rate else 0.0
            row["remaining_seconds"] = 0
        else:
            row["remaining_seconds"] = 0
            row["elapsed_seconds"] = 0

        return row

    # ------------------------------------------------------------------
    # Timer / session management
    # ------------------------------------------------------------------

    def start_timer(
        self,
        ch: int,
        minutes: int,
        customer: str,
        actor: str = "",
    ) -> dict:
        """Start a timed session on table *ch*."""
        with self._lock:
            table = self._require_idle(ch)
            now = int(time.time())
            ends_at = now + minutes * 60

            ok = relay_service.turn_on(ch)
            if not ok and not relay_service.demo_mode:
                self._store_pending("ON", ch)

            with main_db_lock:
                conn = get_main_connection()
                try:
                    conn.execute(
                        """
                        UPDATE tables
                        SET status=?, mode=?, customer=?, started_at=?,
                            ends_at=?, rate=0, paused_at=0, paused_secs=0,
                            started_by=?
                        WHERE ch=?
                        """,
                        (STATUS_ACTIVE, MODE_TIMED, customer, now, ends_at, actor, ch),
                    )
                    conn.commit()
                finally:
                    conn.close()

            return self.get_table(ch)

    def open_table(
        self,
        ch: int,
        customer: str,
        rate: float = 0.0,
        actor: str = "",
    ) -> dict:
        """Start an open (pay-per-hour) session on table *ch*."""
        with self._lock:
            self._require_idle(ch)
            now = int(time.time())
            if rate <= 0:
                rate = settings.default_rate_per_hour

            ok = relay_service.turn_on(ch)
            if not ok and not relay_service.demo_mode:
                self._store_pending("ON", ch)

            with main_db_lock:
                conn = get_main_connection()
                try:
                    conn.execute(
                        """
                        UPDATE tables
                        SET status=?, mode=?, customer=?, started_at=?,
                            ends_at=0, rate=?, paused_at=0, paused_secs=0,
                            started_by=?
                        WHERE ch=?
                        """,
                        (STATUS_OPEN, MODE_OPEN, customer, now, rate, actor, ch),
                    )
                    conn.commit()
                finally:
                    conn.close()

            return self.get_table(ch)

    def add_time(self, ch: int, minutes: int, actor: str = "") -> dict:
        """Add minutes to an active timed session."""
        with self._lock:
            with main_db_lock:
                conn = get_main_connection()
                try:
                    row = conn.execute(
                        "SELECT status, ends_at FROM tables WHERE ch=?", (ch,)
                    ).fetchone()
                    if not row or row["status"] != STATUS_ACTIVE:
                        raise ValueError(f"Table {ch} is not in an active timed session")

                    new_ends_at = row["ends_at"] + minutes * 60
                    conn.execute(
                        "UPDATE tables SET ends_at=? WHERE ch=?",
                        (new_ends_at, ch),
                    )
                    conn.commit()
                finally:
                    conn.close()

            return self.get_table(ch)

    def finish_table(self, ch: int, actor: str = "") -> dict:
        """Finish an active or open session and write a history record."""
        with self._lock:
            with main_db_lock:
                conn = get_main_connection()
                try:
                    row = conn.execute(
                        "SELECT * FROM tables WHERE ch=?", (ch,)
                    ).fetchone()
                    if not row or row["status"] == STATUS_IDLE:
                        raise ValueError(f"Table {ch} is not in use")

                    now = int(time.time())
                    started_at = row["started_at"]
                    paused_secs = row["paused_secs"] or 0
                    mode = row["mode"]
                    customer = row["customer"]
                    rate = row["rate"] or 0.0
                    started_by = row.get("started_by") or ""

                    if mode == MODE_TIMED:
                        ends_at = row["ends_at"]
                        duration_s = max(0, ends_at - started_at)
                        total_cost = 0.0
                    else:
                        elapsed = (now - started_at) - paused_secs
                        duration_s = max(0, elapsed)
                        total_cost = round((duration_s / 3600) * rate, 2)

                    conn.execute(
                        """
                        INSERT INTO history
                            (ch, customer, mode, started_at, ended_at,
                             duration_s, total_cost, actor, started_by, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                        """,
                        (ch, customer, mode, started_at, now,
                         duration_s, total_cost, actor, started_by, now),
                    )

                    conn.execute(
                        """
                        UPDATE tables
                        SET status='idle', mode='timed', customer='',
                            started_at=0, ends_at=0, rate=0,
                            paused_at=0, paused_secs=0, started_by=''
                        WHERE ch=?
                        """,
                        (ch,),
                    )
                    conn.commit()
                finally:
                    conn.close()

            ok = relay_service.turn_off(ch)
            if not ok and not relay_service.demo_mode:
                self._store_pending("OFF", ch)

            return {"status": "finished", "ch": ch}

    def apply_outage_adjustment(
        self, ch: int, minutes: int, actor: str = ""
    ) -> dict:
        """Extend a timed session by *minutes* to compensate for an outage."""
        return self.add_time(ch, minutes, actor=actor)

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------

    def get_queue(self) -> list[dict]:
        with main_db_lock:
            conn = get_main_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM queue ORDER BY created_at ASC"
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def add_to_queue(
        self, customer: str, mode: str = MODE_TIMED, minutes: int = 0
    ) -> dict:
        now = int(time.time())
        with main_db_lock:
            conn = get_main_connection()
            try:
                cursor = conn.execute(
                    "INSERT INTO queue(customer, mode, minutes, created_at) VALUES(?,?,?,?)",
                    (customer, mode, minutes, now),
                )
                conn.commit()
                entry_id = cursor.lastrowid
                row = conn.execute(
                    "SELECT * FROM queue WHERE id=?", (entry_id,)
                ).fetchone()
                return dict(row)
            finally:
                conn.close()

    def remove_from_queue(self, queue_id: int) -> dict:
        with main_db_lock:
            conn = get_main_connection()
            try:
                conn.execute("DELETE FROM queue WHERE id=?", (queue_id,))
                conn.commit()
                return {"status": "removed", "queue_id": queue_id}
            finally:
                conn.close()

    def assign_queue_to_table(
        self, queue_id: int, table_ch: int, actor: str = ""
    ) -> dict:
        """Pull a queue entry and start it on a given table."""
        with main_db_lock:
            conn = get_main_connection()
            try:
                entry = conn.execute(
                    "SELECT * FROM queue WHERE id=?", (queue_id,)
                ).fetchone()
                if not entry:
                    raise ValueError(f"Queue entry {queue_id} not found")
                entry = dict(entry)

                conn.execute("DELETE FROM queue WHERE id=?", (queue_id,))
                conn.commit()
            finally:
                conn.close()

        if entry["mode"] == MODE_OPEN:
            return self.open_table(
                table_ch,
                customer=entry["customer"],
                rate=settings.default_rate_per_hour,
                actor=actor,
            )
        else:
            minutes = entry.get("minutes") or 60
            return self.start_timer(
                table_ch,
                minutes=minutes,
                customer=entry["customer"],
                actor=actor,
            )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_history(
        self,
        ch: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        with main_db_lock:
            conn = get_main_connection()
            try:
                if ch is not None:
                    rows = conn.execute(
                        "SELECT * FROM history WHERE ch=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (ch, limit, offset),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM history ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (limit, offset),
                    ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    # ------------------------------------------------------------------
    # Pending relay actions (retry when ESP32 comes back online)
    # ------------------------------------------------------------------

    def _store_pending(self, action: str, ch: int) -> None:
        now = int(time.time())
        with main_db_lock:
            conn = get_main_connection()
            try:
                conn.execute(
                    "INSERT INTO pending_actions(action, ch, created_at) VALUES(?,?,?)",
                    (action, ch, now),
                )
                conn.commit()
            finally:
                conn.close()

    def process_pending_actions(self) -> dict:
        """Retry stored relay actions. Call when ESP32 comes back online."""
        with main_db_lock:
            conn = get_main_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM pending_actions ORDER BY created_at ASC"
                ).fetchall()
            finally:
                conn.close()

        processed = []
        failed = []
        for row in rows:
            row = dict(row)
            action = row["action"]
            ch = row["ch"]
            if action == "ON":
                ok = relay_service.turn_on(ch)
            else:
                ok = relay_service.turn_off(ch)

            if ok:
                processed.append(row["id"])
            else:
                failed.append(row["id"])

        if processed:
            with main_db_lock:
                conn = get_main_connection()
                try:
                    placeholders = ",".join("?" * len(processed))
                    conn.execute(
                        f"DELETE FROM pending_actions WHERE id IN ({placeholders})",
                        processed,
                    )
                    conn.commit()
                finally:
                    conn.close()

        return {
            "processed": len(processed),
            "failed": len(failed),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_idle(self, ch: int) -> dict:
        with main_db_lock:
            conn = get_main_connection()
            try:
                row = conn.execute(
                    "SELECT * FROM tables WHERE ch=?", (ch,)
                ).fetchone()
                if row is None:
                    raise ValueError(f"Table {ch} does not exist")
                if row["status"] != STATUS_IDLE:
                    raise ValueError(f"Table {ch} is not idle (status={row['status']})")
                return dict(row)
            finally:
                conn.close()


table_service = TableService()
