# init_db.py
import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).with_name("schema.sql")

conn = sqlite3.connect("wabax.db")
c = conn.cursor()

# Drop old tables if they exist
c.execute("DROP TABLE IF EXISTS results")
c.execute("DROP TABLE IF EXISTS urls")
c.execute("DROP TABLE IF EXISTS jobs")
c.execute("DROP TABLE IF EXISTS import_status")

# Load and execute the shared schema
with SCHEMA_FILE.open("r", encoding="utf-8") as f:
    conn.executescript(f.read())

conn.commit()
conn.close()
print("✅ WABAX database initialized using schema.sql")
