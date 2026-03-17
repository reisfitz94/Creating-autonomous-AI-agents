import sqlite3
from typing import Dict


def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    return conn


def init_schema(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event TEXT,
        data TEXT
    )
    """
    )
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS strategy (
        symbol TEXT PRIMARY KEY,
        weight REAL
    )
    """
    )
    conn.commit()


def log_event(conn: sqlite3.Connection, event: str, data: str):
    c = conn.cursor()
    c.execute("INSERT INTO logs (event, data) VALUES (?, ?)", (event, data))
    conn.commit()


def save_strategy(conn: sqlite3.Connection, strategy: Dict[str, float]):
    """Persist a strategy dict to the database."""
    c = conn.cursor()
    for sym, weight in strategy.items():
        c.execute(
            "REPLACE INTO strategy (symbol, weight) VALUES (?, ?)",
            (sym, weight),
        )
    conn.commit()


def load_strategy(conn: sqlite3.Connection) -> Dict[str, float]:
    """Load persisted strategy weights."""
    c = conn.cursor()
    c.execute("SELECT symbol, weight FROM strategy")
    return {row[0]: row[1] for row in c.fetchall()}
