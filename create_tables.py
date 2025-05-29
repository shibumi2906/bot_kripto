# create_tables.py

import sqlite3
from app.core.config import settings

# Собираем все DDL-запросы в одну строку.
SCHEMA = """
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
  telegram_id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  is_premium INTEGER DEFAULT 0,
  premium_expires_at TEXT
);

-- Таблица подписок
CREATE TABLE IF NOT EXISTS subscriptions (
  telegram_id INTEGER PRIMARY KEY,
  provider TEXT,
  status TEXT,
  started_at TEXT,
  expires_at TEXT
);

-- Таблица портфеля
CREATE TABLE IF NOT EXISTS portfolio (
  telegram_id INTEGER,
  asset TEXT,
  amount REAL,
  PRIMARY KEY (telegram_id, asset)
);

-- Таблица торговых сигналов
CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  signal_type TEXT,
  entry REAL,
  target REAL,
  stop_loss REAL,
  confidence REAL,
  explanation TEXT,
  created_at TEXT
);

-- Таблица сентимента соцсетей/новостей
CREATE TABLE IF NOT EXISTS social_sentiment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  timestamp TEXT,
  score REAL,
  mentions INTEGER
);

-- Таблица on-chain метрик
CREATE TABLE IF NOT EXISTS onchain_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  timestamp TEXT,
  active_addresses INTEGER,
  tx_volume REAL
);

-- Таблица новостей (если понадобится)
CREATE TABLE IF NOT EXISTS news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  timestamp TEXT,
  title TEXT,
  url TEXT,
  sentiment_score REAL
);
"""


def init_db(db_path: str = None):
    """
    Создаёт файл SQLite (по умолчанию settings.DB_PATH)
    и все таблицы, описанные в SCHEMA.
    """
    path = db_path or settings.DB_PATH
    conn = sqlite3.connect(path)
    try:
        # Выполняем сразу все команды из SCHEMA
        conn.executescript(SCHEMA)
        print(f"✅ Таблицы созданы или уже существуют в {path}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()



