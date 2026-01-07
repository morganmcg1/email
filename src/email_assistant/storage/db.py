"""SQLite storage for rules and prioritization criteria."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class PrioritizationCriteria(BaseModel):
    """User's email prioritization criteria from interview."""

    vip_senders: list[str] = []
    vip_domains: list[str] = []
    high_priority_keywords: list[str] = []
    low_priority_types: list[str] = []
    custom_rules: list[str] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


DEFAULT_DB_PATH = Path.home() / ".email-assistant" / "email_assistant.db"


class Database:
    """SQLite database for email assistant data."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prioritization_criteria (
                    id INTEGER PRIMARY KEY,
                    criteria_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    natural_language TEXT,
                    conditions_json TEXT NOT NULL,
                    actions_json TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_cache (
                    email_id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    subject TEXT,
                    sender TEXT,
                    priority TEXT,
                    category TEXT,
                    needs_reply INTEGER,
                    cached_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_prioritization_criteria(self) -> Optional[PrioritizationCriteria]:
        """Get user's prioritization criteria."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT criteria_json FROM prioritization_criteria ORDER BY id DESC LIMIT 1"
            ).fetchone()

            if row:
                data = json.loads(row[0])
                return PrioritizationCriteria(**data)
            return None

    def has_prioritization_criteria(self) -> bool:
        """Check if prioritization criteria exist."""
        return self.get_prioritization_criteria() is not None

    def save_prioritization_criteria(self, criteria: PrioritizationCriteria) -> None:
        """Save user's prioritization criteria."""
        criteria.updated_at = datetime.now()
        criteria_json = criteria.model_dump_json()

        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM prioritization_criteria LIMIT 1"
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE prioritization_criteria
                    SET criteria_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (criteria_json, criteria.updated_at.isoformat(), existing[0]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO prioritization_criteria (criteria_json, created_at, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (criteria_json, criteria.created_at.isoformat(), criteria.updated_at.isoformat()),
                )
            conn.commit()

    def clear_prioritization_criteria(self) -> None:
        """Clear all prioritization criteria."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM prioritization_criteria")
            conn.commit()

    def save_rule(
        self,
        name: str,
        conditions: dict,
        actions: dict,
        natural_language: Optional[str] = None,
    ) -> int:
        """Save an automation rule."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO rules (name, natural_language, conditions_json, actions_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, natural_language, json.dumps(conditions), json.dumps(actions), now, now),
            )
            conn.commit()
            return cursor.lastrowid

    def get_rules(self, enabled_only: bool = True) -> list[dict]:
        """Get all automation rules."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT id, name, natural_language, conditions_json, actions_json, enabled FROM rules"
            if enabled_only:
                query += " WHERE enabled = 1"

            rows = conn.execute(query).fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "natural_language": row[2],
                    "conditions": json.loads(row[3]),
                    "actions": json.loads(row[4]),
                    "enabled": bool(row[5]),
                }
                for row in rows
            ]

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()
            return cursor.rowcount > 0

    def toggle_rule(self, rule_id: int, enabled: bool) -> bool:
        """Enable or disable a rule."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE rules SET enabled = ?, updated_at = ? WHERE id = ?",
                (int(enabled), datetime.now().isoformat(), rule_id),
            )
            conn.commit()
            return cursor.rowcount > 0
