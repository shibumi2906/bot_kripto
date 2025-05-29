# app/core/db.py
import sqlite3
from typing import Any, List, Tuple

from app.core.config import settings

DB_PATH = settings.DB_PATH


def query(sql: str, params: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
    """
    Выполнить SELECT-запрос и вернуть все строки.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def execute(sql: str, params: Tuple[Any, ...] = ()) -> None:
    """
    Выполнить INSERT/UPDATE/DELETE-запрос.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

