from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from .models import EarningRecord, Faucet, Task


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS faucets (
    faucet_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    paid_7d_usd TEXT NOT NULL DEFAULT '0',
    users_paid INTEGER NOT NULL DEFAULT 0,
    rating TEXT,
    health INTEGER,
    coins_json TEXT NOT NULL DEFAULT '[]',
    discovered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    faucet_id TEXT NOT NULL,
    name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    reward TEXT NOT NULL,
    estimated_seconds INTEGER NOT NULL,
    cooldown_seconds INTEGER NOT NULL,
    success_rate REAL NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (faucet_id)
        REFERENCES faucets(faucet_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faucet_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    currency TEXT NOT NULL,
    expected_amount TEXT NOT NULL,
    actual_amount TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    success INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    error TEXT,

    FOREIGN KEY (faucet_id)
        REFERENCES faucets(faucet_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_faucet
    ON tasks(faucet_id);

CREATE INDEX IF NOT EXISTS idx_earnings_faucet
    ON earnings(faucet_id);

CREATE INDEX IF NOT EXISTS idx_earnings_created_at
    ON earnings(created_at);
"""


class Database:
    """SQLite persistence layer for the recovery validation core."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        try:
            connection.executescript(SCHEMA)
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection():
            pass

    def upsert_faucet(self, faucet: Faucet) -> None:
        discovered_at = (
            faucet.discovered_at
            or datetime.now(timezone.utc)
        )

        with self.connection() as db:
            db.execute(
                """
                INSERT INTO faucets (
                    faucet_id,
                    name,
                    url,
                    description,
                    paid_7d_usd,
                    users_paid,
                    rating,
                    health,
                    coins_json,
                    discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(faucet_id) DO UPDATE SET
                    name = excluded.name,
                    url = excluded.url,
                    description = excluded.description,
                    paid_7d_usd = excluded.paid_7d_usd,
                    users_paid = excluded.users_paid,
                    rating = excluded.rating,
                    health = excluded.health,
                    coins_json = excluded.coins_json,
                    discovered_at = excluded.discovered_at
                """,
                (
                    faucet.faucet_id,
                    faucet.name,
                    faucet.url,
                    faucet.description,
                    str(faucet.paid_7d_usd),
                    faucet.users_paid,
                    (
                        str(faucet.rating)
                        if faucet.rating is not None
                        else None
                    ),
                    faucet.health,
                    json.dumps(faucet.coins),
                    discovered_at.isoformat(),
                ),
            )

    def upsert_task(self, task: Task) -> None:
        with self.connection() as db:
            db.execute(
                """
                INSERT INTO tasks (
                    task_id,
                    faucet_id,
                    name,
                    task_type,
                    reward,
                    estimated_seconds,
                    cooldown_seconds,
                    success_rate,
                    enabled
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)

                ON CONFLICT(task_id) DO UPDATE SET
                    faucet_id = excluded.faucet_id,
                    name = excluded.name,
                    task_type = excluded.task_type,
                    reward = excluded.reward,
                    estimated_seconds = excluded.estimated_seconds,
                    cooldown_seconds = excluded.cooldown_seconds,
                    success_rate = excluded.success_rate
                """,
                (
                    task.task_id,
                    task.faucet_id,
                    task.name,
                    task.task_type,
                    str(task.reward),
                    task.estimated_seconds,
                    task.cooldown_seconds,
                    task.success_rate,
                ),
            )

    def disable_task(self, task_id: str) -> None:
        with self.connection() as db:
            db.execute(
                """
                UPDATE tasks
                SET enabled = 0
                WHERE task_id = ?
                """,
                (task_id,),
            )

    def record_earning(
        self,
        record: EarningRecord,
    ) -> int:
        with self.connection() as db:
            cursor = db.execute(
                """
                INSERT INTO earnings (
                    faucet_id,
                    task_id,
                    task_type,
                    currency,
                    expected_amount,
                    actual_amount,
                    duration_seconds,
                    success,
                    created_at,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.faucet_id,
                    record.task_id,
                    record.task_type,
                    record.currency,
                    str(record.expected_amount),
                    str(record.actual_amount),
                    record.duration_seconds,
                    int(record.success),
                    record.created_at.isoformat(),
                    record.error,
                ),
            )

            return int(cursor.lastrowid)

    def get_faucet(
        self,
        faucet_id: str,
    ) -> sqlite3.Row | None:
        with self.connection() as db:
            return db.execute(
                """
                SELECT *
                FROM faucets
                WHERE faucet_id = ?
                """,
                (faucet_id,),
            ).fetchone()

    def list_faucets(self) -> list[sqlite3.Row]:
        with self.connection() as db:
            return list(
                db.execute(
                    """
                    SELECT *
                    FROM faucets
                    ORDER BY name ASC
                    """
                )
            )

    def list_tasks(
        self,
        enabled_only: bool = True,
    ) -> list[sqlite3.Row]:
        query = """
            SELECT *
            FROM tasks
        """

        if enabled_only:
            query += " WHERE enabled = 1"

        query += " ORDER BY reward DESC"

        with self.connection() as db:
            return list(db.execute(query))

    def recent_earnings(
        self,
        limit: int = 20,
    ) -> list[sqlite3.Row]:
        if limit <= 0:
            return []

        with self.connection() as db:
            return list(
                db.execute(
                    """
                    SELECT *
                    FROM earnings
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            )

    def totals(self) -> dict[str, Decimal]:
        with self.connection() as db:
            rows = db.execute(
                """
                SELECT
                    currency,
                    SUM(CAST(actual_amount AS REAL)) AS total
                FROM earnings
                WHERE success = 1
                GROUP BY currency
                ORDER BY currency
                """
            ).fetchall()

        return {
            row["currency"]: Decimal(
                str(row["total"] or 0)
            )
            for row in rows
        }

    def faucet_statistics(self) -> list[sqlite3.Row]:
        with self.connection() as db:
            return list(
                db.execute(
                    """
                    SELECT
                        f.faucet_id,
                        f.name,
                        COUNT(e.id) AS attempts,
                        COALESCE(
                            SUM(e.success),
                            0
                        ) AS successes,
                        COALESCE(
                            SUM(
                                CAST(
                                    e.actual_amount
                                    AS REAL
                                )
                            ),
                            0
                        ) AS earnings
                    FROM faucets f
                    LEFT JOIN earnings e
                        ON e.faucet_id = f.faucet_id
                    GROUP BY
                        f.faucet_id,
                        f.name
                    ORDER BY earnings DESC
                    """
                )
            )
