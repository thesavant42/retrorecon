# retrorecon

A Flask web application for exploring Wayback Machine data. It fetches CDX records, stores them in SQLite, and provides a UI to search, tag and manage the results.

## Project Home
<https://github.com/thesavant42/retrorecon>

## Features
- **CDX import** from the Wayback Machine API
- **JSON import** of URL lists or records
- Background import with progress indicator
- Search and filter by text and tags
- Inline and bulk tag management
- Bulk actions with "select all visible" or "select all matching"
- Quick OSINT links for each URL (Wayback, Shodan, VirusTotal, Google, GitHub, crt.sh)
- Download, load or create databases from the menu, including naming your new
  database
- Rename the current database without leaving the application
- Remembers and reloads the most recently used database on launch
- Theme switching via Menu dropdown with optional background image toggle
- Optional theming via CSS files in `static/themes/`, including a dark OpenAI-inspired style and hundreds of Midnight City combinations (generated via `scripts/generate_midnight_themes.py`)
- Browser-side search history for quick queries
- Pagination with jump-to-page and total counts
- Webpack Exploder: input a `.js.map` URL and download a ZIP of the sources

## Installation
```bash
pip install -r requirements.txt
python scripts/init_db.py  # set up wabax.db with demo data
python app.py
# Optionally set RETRORECON_DB to open a specific database on launch
# RETRORECON_DB=dsprings.db python app.py
```
Then open <http://127.0.0.1:5000> in your browser.

## Usage
1. **Import from CDX**: enter a domain to fetch URLs from the Wayback API.
2. **Import from JSON**: upload a JSON file containing URLs or full CDX records.
3. Use the search box and tag filters to narrow results.
4. Add or remove tags individually or use the bulk actions.
5. Save the current database, load another or start a new one (and give it a
   name) using the menu. You can also rename the active database from the same
   dropdown.
6. When you relaunch the app, it automatically reloads the last database you used.

## License
MIT

## Attribution
- [Wayback Machine API](https://archive.org/help/wayback_api.php)
- [Webpack Exploder](https://spaceraccoon.github.io/webpack-exploder/)
- [Map Room visual inspiration](https://indianajones.fandom.com/wiki/Map_Room)
