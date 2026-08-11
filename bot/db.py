import json
import sqlite3
import time
from contextlib import contextmanager

from .config import Config


class Database:
    def __init__(self, config: Config):
        self.path = config.db_path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._schema()

    def _schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS candles (
                symbol    TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                ts        INTEGER NOT NULL,
                open      REAL NOT NULL,
                high      REAL NOT NULL,
                low       REAL NOT NULL,
                close     REAL NOT NULL,
                volume    REAL NOT NULL,
                PRIMARY KEY (symbol, timeframe, ts)
            );
            CREATE TABLE IF NOT EXISTS signals (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        INTEGER NOT NULL,
                symbol    TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                strategy  TEXT NOT NULL,
                action    TEXT NOT NULL,
                price     REAL NOT NULL,
                reason    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          INTEGER NOT NULL,
                symbol      TEXT NOT NULL,
                side        TEXT NOT NULL,
                amount      REAL NOT NULL,
                price       REAL,
                status      TEXT NOT NULL,
                exchange_id TEXT
            );
            CREATE TABLE IF NOT EXISTS equity (
                ts     INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                value  REAL NOT NULL
            );
            """
        )
        self.conn.commit()

    @contextmanager
    def tx(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def insert_candles(self, symbol: str, timeframe: str, rows: list[list]) -> int:
        with self.tx() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (symbol, timeframe, int(r[0]), float(r[1]), float(r[2]), float(r[3]),
                     float(r[4]), float(r[5]))
                    for r in rows
                ],
            )
        return len(rows)

    def last_candle_ts(self, symbol: str, timeframe: str) -> int | None:
        row = self.conn.execute(
            "SELECT ts FROM candles WHERE symbol=? AND timeframe=? ORDER BY ts DESC LIMIT 1",
            (symbol, timeframe),
        ).fetchone()
        return row["ts"] if row else None

    def candles(self, symbol: str, timeframe: str, limit: int = 300) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM candles WHERE symbol=? AND timeframe=? ORDER BY ts DESC LIMIT ?",
            (symbol, timeframe, limit),
        ).fetchall()

    def insert_signal(self, signal: dict) -> None:
        with self.tx() as conn:
            conn.execute(
                "INSERT INTO signals (ts, symbol, timeframe, strategy, action, price, reason) "
                "VALUES (:ts, :symbol, :timeframe, :strategy, :action, :price, :reason)",
                signal,
            )

    def signals(self, limit: int = 100) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM signals ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()

    def insert_order(self, order: dict) -> int:
        with self.tx() as conn:
            cur = conn.execute(
                "INSERT INTO orders (ts, symbol, side, amount, price, status, exchange_id) "
                "VALUES (:ts, :symbol, :side, :amount, :price, :status, :exchange_id)",
                order,
            )
            return cur.lastrowid

    def orders(self, limit: int = 100) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM orders ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()

    def insert_equity(self, symbol: str, value: float) -> None:
        with self.tx() as conn:
            conn.execute(
                "INSERT INTO equity (ts, symbol, value) VALUES (?, ?, ?)",
                (int(time.time() * 1000), symbol, value),
            )

    def equity(self, limit: int = 500) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM equity ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()

    def set_status(self, payload: dict) -> None:
        with self.tx() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS status (id INTEGER PRIMARY KEY CHECK (id = 1), "
                "payload TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO status (id, payload) VALUES (1, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
                (json.dumps(payload),),
            )

    def get_status(self) -> dict | None:
        try:
            row = self.conn.execute("SELECT payload FROM status WHERE id = 1").fetchone()
        except sqlite3.OperationalError:
            return None
        return json.loads(row["payload"]) if row else None

    def close(self) -> None:
        self.conn.close()
