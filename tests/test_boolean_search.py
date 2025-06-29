import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrorecon.search_utils import build_search_sql


def test_and_not_url_only():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, timestamp TEXT, status_code INTEGER, mime_type TEXT, tags TEXT)"
    )
    # url contains 'config', tags contain '.js'
    conn.execute(
        "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES ('https://demo.com/config', '20210101', 200, 'text/html', 'script.js')"
    )
    # url has '.js'
    conn.execute(
        "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES ('https://demo.com/config.js', '20210101', 200, 'application/javascript', '')"
    )

    sql, params = build_search_sql('config AND NOT .js')
    rows = conn.execute(f'SELECT url FROM urls WHERE {sql}', params).fetchall()
    assert [r['url'] for r in rows] == ['https://demo.com/config']

