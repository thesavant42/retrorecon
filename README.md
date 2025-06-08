# retroRecon:


## Source of Truth
Source of truth: https://github.com/thesavant42/wabax

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

### 📥 Multiline JSON Import
- Upload JSON file (in CDX format)
```
[
  "http://example.com:80/",
  "https://www.example.com/%22",
  "https://www.example.com/%22%22",
  "https://www.example.com/%22,",
]
```
- Data is inserted into the database

### 🧩 Filtering + Search
- Filter by:
  - **Query string** (`q`)
  - **File extension** (`ext`)
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
- TODO: Configurable number of results per page (default 25)
- "Previous" / "Next" navigation
- Page number shown
- Input Box to jump to page

---

---✅ Known Good State
cdx.db contains real archived URLs

index.html displays:

Import + fetch CDX forms
Search/filter inputs
Select all visible checks all results on the page
Clear button unchecks all buttons and empties searh and tab boxes
Pagination both top and bottom


✏️ TODO (if desired)
Add sorting (by file or host)
Tag pills and bulk operations
Export filtered results

Integrate more CDX metadata (status codes, lengths)

💡 Attribution
Wayback Machine API: https://archive.org/help/wayback_api.php
Webpack Exploder: https://spaceraccoon.github.io/webpack-exploder/
Inspiration: https://indianajones.fandom.com/wiki/Map_Room


## 🧪 Running Local

```bash
pip install flask
pythin init_db.py
python app.py
```
Then visit: http://127.0.0.1:5000

## Known State:
Still needs bulk edit, bulk tag, project import/export.
