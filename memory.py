"""
联系人独立记忆模块
使用 SQLite 持久化存储每个联系人的对话历史
"""

import sqlite3
import logging
from pathlib import Path
from threading import Lock

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "memory.db"


class ContactMemory:

    def __init__(self, db_path: str = None) -> None:
        self._db_path = db_path or str(DB_PATH)
        self._lock = Lock()
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contact ON messages(contact)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contact_time ON messages(contact, created_at)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contact_profiles (
                    contact TEXT PRIMARY KEY,
                    nickname TEXT,
                    notes TEXT DEFAULT '',
                    preferences TEXT DEFAULT '{}',
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            conn.close()
            log.info(f"记忆数据库初始化完成: {self._db_path}")

    def add_message(self, contact: str, role: str, content: str) -> None:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT INTO messages (contact, role, content) VALUES (?, ?, ?)",
                (contact, role, content)
            )
            conn.execute("""
                INSERT INTO contact_profiles (contact, last_seen, message_count)
                VALUES (?, CURRENT_TIMESTAMP, 1)
                ON CONFLICT(contact) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    message_count = message_count + 1
            """, (contact,))
            conn.commit()
            conn.close()

    def get_recent_messages(self, contact: str, limit: int = 20) -> list[dict]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute(
                "SELECT role, content, created_at FROM messages "
                "WHERE contact = ? ORDER BY id DESC LIMIT ?",
                (contact, limit)
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {"role": r[0], "content": r[1], "time": r[2]}
                for r in reversed(rows)
            ]

    def get_all_contacts(self) -> list[dict]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute("""
                SELECT contact, nickname, notes, first_seen, last_seen, message_count
                FROM contact_profiles ORDER BY last_seen DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "contact": r[0],
                    "nickname": r[1] or r[0],
                    "notes": r[2] or "",
                    "first_seen": r[3],
                    "last_seen": r[4],
                    "message_count": r[5]
                }
                for r in rows
            ]

    def update_notes(self, contact: str, notes: str) -> None:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                INSERT INTO contact_profiles (contact, notes)
                VALUES (?, ?)
                ON CONFLICT(contact) DO UPDATE SET notes = ?
            """, (contact, notes, notes))
            conn.commit()
            conn.close()

    def clear_contact(self, contact: str) -> None:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("DELETE FROM messages WHERE contact = ?", (contact,))
            conn.execute("DELETE FROM contact_profiles WHERE contact = ?", (contact,))
            conn.commit()
            conn.close()
            log.info(f"已清除 [{contact}] 的记忆")

    def get_stats(self) -> dict:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]
            cursor = conn.execute("SELECT COUNT(*) FROM contact_profiles")
            contacts = cursor.fetchone()[0]
            cursor = conn.execute(
                "SELECT contact, message_count FROM contact_profiles ORDER BY message_count DESC LIMIT 5"
            )
            top = [{"contact": r[0], "count": r[1]} for r in cursor.fetchall()]
            conn.close()
            return {
                "total_messages": total,
                "total_contacts": contacts,
                "top_contacts": top,
                "db_path": self._db_path,
                "db_size_kb": round(Path(self._db_path).stat().st_size / 1024, 1)
                    if Path(self._db_path).exists() else 0
            }
