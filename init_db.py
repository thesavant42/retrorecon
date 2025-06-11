"""Standalone script to initialize wabax.db using schema.sql."""
import app

if __name__ == "__main__":
    app.init_db()
    print(
        "✅ WABAX database initialized with 'urls', 'jobs', and 'import_status' tables."
    )
