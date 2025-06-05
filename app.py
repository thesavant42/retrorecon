# app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import json
from urllib.parse import urlparse

app = Flask(__name__)
DATABASE = 'wabax.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    domain = request.args.get('domain', '').strip()
    tag = request.args.get('tag', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    query = "SELECT * FROM urls WHERE 1=1"
    params = []

    if q:
        query += " AND (url LIKE ? OR domain LIKE ? OR tags LIKE ?)"
        params.extend([f'%{q}%'] * 3)
    if domain:
        query += " AND domain LIKE ?"
        params.append(f'%{domain}%')
    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%{tag}%')

    count_query = f"SELECT COUNT(*) FROM ({query})"
    conn = get_db_connection()
    total = conn.execute(count_query, params).fetchone()[0]

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    urls = conn.execute(query, params).fetchall()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'index.html',
        urls=urls,
        q=q,
        domain=domain,
        tag=tag,
        page=page,
        total_pages=total_pages
    )

@app.route('/bulk_action', methods=['POST'])
def bulk_action():
    action = request.form.get('action')
    ids = request.form.getlist('selected_ids')
    tag = request.form.get('tag', '').strip()

    if not ids:
        return redirect(url_for('index'))

    conn = get_db_connection()
    for url_id in ids:
        row = conn.execute("SELECT tags FROM urls WHERE id = ?", (url_id,)).fetchone()
        if not row:
            continue
        current_tags = set(row['tags'].split(', ')) if row['tags'] else set()

        if action == 'add_tag' and tag:
            current_tags.add(tag)
        elif action == 'remove_tag' and tag:
            current_tags.discard(tag)
        elif action == 'delete':
            conn.execute("DELETE FROM urls WHERE id = ?", (url_id,))
            continue

        updated_tags = ', '.join(sorted(t for t in current_tags if t))
        conn.execute("UPDATE urls SET tags = ? WHERE id = ?", (updated_tags, url_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/import_json', methods=['POST'])
def import_json():
    if 'json_file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['json_file']
    if file.filename == '':
        return redirect(url_for('index'))

    lines = file.read().decode('utf-8').splitlines()
    imported = 0

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        for line in lines:
            try:
                # Skip garbage
                line = line.strip().strip(',').strip('"')
                if not line or line in ['[', ']']:
                    continue

                # If line is a plain URL
                if line.startswith("http"):
                    url = line
                    domain = urlparse(url).netloc
                    c.execute("INSERT OR IGNORE INTO urls (url, domain, tags) VALUES (?, ?, '')", (url, domain))
                    imported += 1
                    continue

                # Try parsing as JSON
                entry = json.loads(line)
                url = entry.get('url', '').strip().strip('"')
                domain = entry.get('domain') or urlparse(url).netloc
                tags = entry.get('tags', [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',')]
                tags_str = ', '.join(tags)

                if url and domain:
                    c.execute("INSERT OR IGNORE INTO urls (url, domain, tags) VALUES (?, ?, ?)", (url, domain, tags_str))
                    imported += 1
            except Exception as e:
                print(f"⚠️ Failed to import: {line[:80]} — {e}")
        conn.commit()

    print(f"✅ Imported {imported} URLs")
    return redirect(url_for('index'))

@app.route('/fetch_cdx', methods=['POST'])
def fetch_cdx():
    # Placeholder CDX fetch route
    domain = request.form.get('domain')
    print(f"(CDX fetch requested for domain: {domain})")
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            conn.execute('''
                CREATE TABLE urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    domain TEXT,
                    tags TEXT
                )
            ''')
            conn.commit()
    app.run(debug=True)