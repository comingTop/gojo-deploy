from __future__ import annotations

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo


class StateStore:
    def __init__(self, db_path: str = ":memory:", tz: str = "America/Sao_Paulo") -> None:
        self._tz = ZoneInfo(tz)
        self._db = sqlite3.connect(db_path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS gifts ("
            " day TEXT NOT NULL, user_id TEXT NOT NULL, username TEXT NOT NULL,"
            " coins INTEGER NOT NULL, at REAL NOT NULL)"
        )
        self._db.commit()

    def day_key(self, at: float) -> str:
        return datetime.fromtimestamp(at, self._tz).strftime("%Y-%m-%d")

    def record_gift(self, user_id: str, username: str, total_coins: int, at: float) -> None:
        self._db.execute(
            "INSERT INTO gifts(day, user_id, username, coins, at) VALUES(?,?,?,?,?)",
            (self.day_key(at), user_id, username, total_coins, at),
        )
        self._db.commit()

    def top_gifters(self, n: int, at: float) -> list[tuple[str, int]]:
        cur = self._db.execute(
            "SELECT username, SUM(coins) AS total FROM gifts"
            " WHERE day = ? GROUP BY user_id ORDER BY total DESC, MAX(at) ASC LIMIT ?",
            (self.day_key(at), n),
        )
        return [(row[0], int(row[1])) for row in cur.fetchall()]
