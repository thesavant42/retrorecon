🔎⏳📁 WABAX: Wayback Archive eXplorer 📁⏳🔎


Source of truth :https://github.com/thesavant42/wabax

A Flask-based tool for exploring, filtering, and tagging CDX data from the Internet Archive’s Wayback Machine.

---

## 🔧 Tech Stack

- **Backend**: Python 3 + Flask
- **Database**: SQLite (`cdx.db`)
- **Frontend**: Jinja2 templates + HTML/CSS + vanilla JS
- **Dynamic UI**: Pagination, theming, tag-based filtering

---

## 📦 Features

### 🔍 CDX Fetching
- Query the Wayback CDX API using a domain (e.g. `example.com`)
- Stores results into `cdx.db` under `entries` table
- Handles duplicates and bulk insertion cleanly

### 📥 NDJSON Import
- Upload Newline Delimeted* (NDJSON) `.json` file (in CDX format) < ok so it's ont really NDJSON, it's a bunch of single line json arrays?
- Data is inserted into the database

### 🧩 Filtering + Search
- Filter by:
  - **Query string** (`q`)
  - **Tags**, with support for inclusion/exclusion (`tag`, `-tag`)
- Filters persist through pagination

### 🏷️ Tag Management
- Tags displayed as clickable pills (COMING SOON)

### 🗑️ Bulk Deletion
- Select rows via checkbox
- Delete multiple entries at once

### 📄 Pagination
- "Previous" / "Next" navigation
- Page number shown

---

## 🗃 Directory Structure
```
.
├── app.py # Main Flask app
├── cdx.db # SQLite3 database
├── templates/
│ └── index.html # Jinja2 template
├── static/
│ └── fonts/matterhorn-regular.woff
│ └── foonts/...
│ └── wabax.css
│ └── init_db.py
│ └── schema.sql
```
---✅ Known Good State
cdx.db contains real archived URLs

index.html displays:

Import + fetch CDX forms

Search/filter inputs

Pagination both top and bottom

Tag pills and bulk operations

✏️ TODO (if desired)

Export filtered results

Integrate more CDX metadata (status codes, lengths)

💡 Attribution
Wayback Machine API: https://archive.org/help/wayback_api.php



## 🧪 Running Locall

```bash
pip install flask
python init_db.py
python app.py
```
Then visit: http://127.0.0.1:5000

## Known State:
Still needs project import/export.
