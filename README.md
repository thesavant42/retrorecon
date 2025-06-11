# retrorecon


## Source of Truth
Source of truth: https://github.com/thesavant42/retrorecon



A Flask-based tool for exploring, filtering, and tagging CDX data from the Internet Archive’s Wayback Machine.


---

## 🔧 Tech Stack

- **Backend**: Python 3 + Flask
- **Database**: SQLite (`wabax.db`)
- **Frontend**: Jinja2 templates + HTML/CSS + vanilla JS
- **Dynamic UI**: Pagination, theming, tag-based filtering


## 📦 Features

### 🔍 CDX Fetching
- Query the Wayback CDX API using a domain (e.g. `example.com`)
- Stores results into `wabax.db` under `urls` table
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

### 🗑️ Bulk Deletion : FIX ME!
- Select rows via checkbox
- Delete multiple entries at once

### 📄 Pagination
- TODO: Configurable number of results per page (default 25)
- "Previous" / "Next" navigation
- Page number shown
- Input Box to jump to page

---

Known Bugs, fix me first:
Bulk Select - "Select all matching"
  - and delete rows..
  - and delete tag(s)

✏️ TODO 
Add sorting (by file or host)
Tag pills and bulk operations
Export filtered results
Still needs bulk edit, bulk tag, project import/export.
Integrate more CDX metadata (status codes, lengths): https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md



✅ Known Good State


index.html displays:
Import + fetch CDX forms
Search/filter inputs
Select all visible checks all results on the page
Clear button unchecks all buttons and empties search and tag boxes
Pagination both top and bottom


## 🧪 Running Local

```bash
pip install flask
python init_db.py
python app.py
```
Then visit: http://127.0.0.1:5000

Both the application and `init_db.py` read the database schema from `schema.sql`.


💡 Attribution

- Wayback Machine API:   https://archive.org/help/wayback_api.php
- Webpack Exploder:      https://spaceraccoon.github.io/webpack-exploder/
- Visual Inspiration:    https://indianajones.fandom.com/wiki/Map_Room
