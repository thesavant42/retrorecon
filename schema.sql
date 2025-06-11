CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    domain TEXT,
    timestamp TEXT,
    status_code INTEGER,
    mime_type TEXT,
    tags TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    domain TEXT,
    status TEXT,
    progress INTEGER,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_status (
    id INTEGER PRIMARY KEY,
    status TEXT,
    detail TEXT,
    progress INTEGER,
    total INTEGER
);
