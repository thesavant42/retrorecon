# init_db.py
import sqlite3

conn = sqlite3.connect("wabax.db")
c = conn.cursor()

# Drop old tables if they exist
c.execute("DROP TABLE IF EXISTS results")
c.execute("DROP TABLE IF EXISTS urls")
c.execute("DROP TABLE IF EXISTS jobs")

# Create the urls table
c.execute("""
    CREATE TABLE urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        domain TEXT,
        tags TEXT DEFAULT ''
    )
""")

# Create the jobs table
c.execute("""
    CREATE TABLE jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        domain TEXT,
        status TEXT,
        progress INTEGER,
        result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create the import_status table
c.execute("""
    CREATE TABLE IF NOT EXISTS import_status (
        id INTEGER PRIMARY KEY,
        status TEXT,
        detail TEXT,
        progress INTEGER,
        total INTEGER
    )
""");
conn.commit()
conn.close()
print("✅ WABAX database initialized with 'urls', 'jobs', and 'import_status' tables.")
