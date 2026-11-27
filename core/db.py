import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "mdaais.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                temperature REAL,
                humidity REAL,
                soil_moisture REAL,
                light_lux REAL,
                soil_ph REAL,
                scenario TEXT
            );

            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                leaf_type TEXT,
                disease_name TEXT,
                disease_confidence REAL,
                weed_found INTEGER,
                weed_confidence REAL
            );

            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                action TEXT,
                composite_score REAL,
                details TEXT
            );

            CREATE TABLE IF NOT EXISTS model_weights (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                disease REAL,
                weed REAL,
                env REAL,
                temporal REAL,
                updated_at REAL
            );

            INSERT OR IGNORE INTO model_weights (id, disease, weed, env, temporal, updated_at)
            VALUES (1, 0.40, 0.20, 0.25, 0.15, strftime('%s', 'now'));
        """)

def log_telemetry(temp, hum, moisture, lux, ph, scenario="normal"):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO telemetry (timestamp, temperature, humidity, soil_moisture, light_lux, soil_ph, scenario)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), temp, hum, moisture, lux, ph, scenario)
        )

def get_recent_telemetry(limit=30):
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in reversed(cursor.fetchall())]

def log_action(action, score, details=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO actions (timestamp, action, composite_score, details) VALUES (?, ?, ?, ?)",
            (time.time(), action, score, details)
        )

def get_recent_actions(limit=10):
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM actions ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_weights():
    try:
        with get_conn() as conn:
            row = conn.execute("SELECT disease, weed, env, temporal FROM model_weights WHERE id = 1").fetchone()
            if row:
                return dict(row)
    except sqlite3.OperationalError:
        init_db()
    return {"disease": 0.40, "weed": 0.20, "env": 0.25, "temporal": 0.15}

def set_weights(disease, weed, env, temporal):
    total = disease + weed + env + temporal
    if total <= 0:
        return
    d, w, e, t = disease / total, weed / total, env / total, temporal / total
    with get_conn() as conn:
        conn.execute(
            """UPDATE model_weights 
               SET disease = ?, weed = ?, env = ?, temporal = ?, updated_at = ?
               WHERE id = 1""",
            (round(d, 3), round(w, 3), round(e, 3), round(t, 3), time.time())
        )
