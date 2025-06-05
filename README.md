# 🔎⏳📁 WABAX - Wayback Archive Explorer 📁⏳🔎
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
- Upload Newline Delimeted (NDJSON) `.json` file (in CDX format)
- Data is inserted into the database

### 🧩 Filtering + Search
- Filter by:
  - **Query string** (`q`)
  - **Tags**, with support for inclusion/exclusion (`tag`, `-tag`)
- Filters persist through pagination

### 🏷️ Tag Management
- Tags displayed as clickable pills
- Add or delete tags via inline form
- Tags stored as comma-separated strings

### 🗑️ Bulk Deletion
- Select rows via checkbox
- Delete multiple entries at once

### 📄 Pagination
- Configurable number of results per page (default 25)
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
│ └── wabax..css
```
---✅ Known Good State
cdx.db contains real archived URLs

index.html displays:
Import + fetch CDX forms (Tools Dropdown)

Search/filter inputs

Pagination both top and bottom

Tag pills and bulk operations

✏️ TODO (if desired)
Export filtered results
Integrate more CDX metadata (status codes, lengths)

💡 Attribution
Color palettes from: https://www.shecodes.io/palettes
Wayback Machine API: https://archive.org/help/wayback_api.php



## 🧪 Running Locall

```bash
pip install flask
```
You will have to initialize the database the first time
```
python init_db.py
python app.py
```
Then visit: http://127.0.0.1:5000

## Known State:
Still needs bulk edit, bulk tag, project import/export.
