import sqlite3

DB_PATH = "sample_data.db"

def init_sample_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Drop old table if exists (for a clean reset)
    cur.execute("DROP TABLE IF EXISTS scrap_logs")

    # Create table
    cur.execute("""
        CREATE TABLE scrap_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            machine TEXT NOT NULL,
            scrap_weight REAL NOT NULL,
            reason TEXT
        )
    """)

    # Insert sample data
    sample_data = [
        ("2025-09-30", "Press A", 120.5, "Misalignment"),
        ("2025-10-01", "Press B", 95.2, "Overheat"),
        ("2025-10-02", "Cutter C", 80.0, "Operator error"),
        ("2025-10-03", "Line D", 60.3, "Material defect"),
        ("2025-10-04", "Press A", 110.8, "Jammed sensor"),
        ("2025-10-04", "Cutter C", 75.6, "Operator error"),
    ]

    cur.executemany("""
        INSERT INTO scrap_logs (date, machine, scrap_weight, reason)
        VALUES (?, ?, ?, ?)
    """, sample_data)

    conn.commit()
    conn.close()
    print("✅ sample_data.db created successfully with sample logs!")

if __name__ == "__main__":
    init_sample_db()
