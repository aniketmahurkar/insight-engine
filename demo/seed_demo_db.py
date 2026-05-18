#!/usr/bin/env python3
"""Seeds a SQLite database with synthetic event data for demo purposes."""
import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "demo.db"
DAYS = 90
DAILY_EVENTS = 500
CATEGORIES = ["api", "web", "mobile", "batch"]
STATUSES = ["success", "error", "timeout"]


def seed():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE events (
        id INTEGER PRIMARY KEY, event_date TEXT, category TEXT,
        user_id INTEGER, duration_seconds INTEGER, status TEXT
    )""")

    cur.execute("""CREATE TABLE users (
        id INTEGER PRIMARY KEY, segment TEXT, created_date TEXT
    )""")

    cur.execute("""CREATE TABLE metrics (
        id INTEGER PRIMARY KEY, event_date TEXT, metric_name TEXT, value REAL
    )""")

    # Seed users
    for i in range(100):
        cur.execute("INSERT INTO users VALUES (?,?,?)",
            (i, random.choice(["free", "pro", "enterprise"]),
             (date.today() - timedelta(days=random.randint(30, 365))).isoformat()))

    # Seed events with anomaly in last 3 days
    event_id = 0
    start_date = date.today() - timedelta(days=DAYS)

    for day_offset in range(DAYS):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.isoformat()
        # Anomaly on the most recent day (yesterday relative to today)
        is_anomaly = day_offset == (DAYS - 1)

        daily_count = int(DAILY_EVENTS * 1.8) if is_anomaly else DAILY_EVENTS
        base_duration = 800 if is_anomaly else 350
        error_rate = 0.25 if is_anomaly else 0.05

        for _ in range(daily_count):
            event_id += 1
            duration = max(10, int(random.gauss(base_duration, 100)))
            status = "error" if random.random() < error_rate else random.choices(
                ["success", "timeout"], weights=[95, 5])[0]
            cur.execute("INSERT INTO events VALUES (?,?,?,?,?,?)",
                (event_id, date_str, random.choice(CATEGORIES),
                 random.randint(0, 99), duration, status))

    conn.commit()
    conn.close()
    print(f"Demo database created at {DB_PATH} ({event_id} events)")


if __name__ == "__main__":
    seed()
