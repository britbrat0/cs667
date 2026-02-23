import sqlite3
from app.config import settings

DB_PATH = settings.db_path


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trend_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            source TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            region TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_searched_at TIMESTAMP
        )
    """)

    # Migrate: add last_searched_at if it doesn't exist yet
    try:
        cursor.execute("ALTER TABLE keywords ADD COLUMN last_searched_at TIMESTAMP")
    except Exception:
        pass  # Column already exists

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trend_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            period_days INTEGER NOT NULL,
            volume_growth REAL,
            price_growth REAL,
            composite_score REAL,
            lifecycle_stage TEXT,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trend_data_keyword ON trend_data(keyword)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trend_data_recorded_at ON trend_data(recorded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trend_scores_keyword ON trend_scores(keyword)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_status ON keywords(status)")

    conn.commit()
    conn.close()
