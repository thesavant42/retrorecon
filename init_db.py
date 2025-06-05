# init_db.py
import sqlite3

conn = sqlite3.connect("wabax.db")
c = conn.cursor()

# Drop the old incorrect table
c.execute("DROP TABLE IF EXISTS results")

# Drop the correct table too, just in case
c.execute("DROP TABLE IF EXISTS urls")

# Create the correct table
c.execute("""
    CREATE TABLE urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        domain TEXT,
        tags TEXT DEFAULT ''
    )
""")

conn.commit()
conn.close()
print("✅ WABAX database initialized with 'urls' table.")