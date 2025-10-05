import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sample_data.db")

def get_db_connection():
    """Return an SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sample_data():
    """Create sample tables and data if not already present."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create a simple scrap_logs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scrap_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            machine TEXT,
            scrap_weight REAL,
            reason TEXT
        )
    """)

    # Check if data already exists
    cur.execute("SELECT COUNT(*) FROM scrap_logs")
    count = cur.fetchone()[0]

    if count == 0:
        cur.executemany("""
            INSERT INTO scrap_logs (date, machine, scrap_weight, reason)
            VALUES (?, ?, ?, ?)
        """, [
            ("2025-09-30", "Press A", 120.5, "Misalignment"),
            ("2025-10-01", "Press B", 95.2, "Overheat"),
            ("2025-10-02", "Cutter C", 80.0, "Operator error"),
            ("2025-10-03", "Line D", 60.3, "Material defect"),
        ])
        print("✅ Sample data inserted into scrap_logs table.")

    conn.commit()
    conn.close()
