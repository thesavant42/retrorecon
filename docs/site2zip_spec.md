# Site2Zip Feature Plan

This document describes the design for a new **Site2Zip** tool. The tool crawls a URL with a headless browser, collects all assets, generates a sitemap and packages everything in a ZIP for download. It combines screenshot capture, network logging and optional webpack source extraction.

## Goals
- Allow users to input a URL and retrieve a ZIP archive containing:
  - Rendered HTML and dynamic assets (scripts, styles, media, fonts).
  - A sitemap of discovered links.
  - HTTP request and response headers for every resource.
  - Screenshots of the initial page.
  - Unpacked sources when source maps reference inline or Base64 encoded bundles.
- Emulate a desktop browser by default with user agent options for Android or search engine bots.
- Support referrer spoofing via checkbox.
- Display a results table listing each capture with thumbnail preview, URL, timestamp and method. Clicking the thumbnail opens the full screenshot and provides a download link for the ZIP.

## Database Changes
Add a new `sitezips` table:
```sql
CREATE TABLE IF NOT EXISTS sitezips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    method TEXT DEFAULT 'GET',
    zip_path TEXT,
    screenshot_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
`ensure_schema()` should create this table when missing.

## Flask Routes
- `GET /site2zip` – serve the overlay with the capture form.
- `GET /tools/site2zip` – full-page version of the overlay for direct links.
- `POST /tools/site2zip` – launch the capture. Parameters:
  - `url` – target to fetch.
  - `agent` – optional user agent (`''`, `android`, `bot`).
  - `spoof_referrer` – `1` to spoof the referrer header.
- `GET /sitezips` – return JSON metadata for captured entries.
- `GET /download_sitezip/<int:id>` – download the ZIP archive.
- `POST /delete_sitezips` – remove captures by ID.

## UI Design
- Add **Site2Zip** to the Tools menu. Selecting it loads `site2zip.html` similar to `screenshotter.html`.
- The overlay contains a URL input, user agent dropdown and referrer spoof checkbox.
- A table below the form shows past captures with a delete checkbox per row, timestamp, URL, method, thumbnail and download link.
- Columns should be resizable as in other tables.

## Implementation Steps for Codex
1. Extend `db/schema.sql` and helper functions for the new `sitezips` table.
2. Implement capture logic using Playwright to fetch all resources, execute scripts and record network traffic. Save headers to text files and write files to a temporary directory before zipping.
3. When a source map references inline or Base64 encoded bundles, invoke the existing Webpack Exploder to unpack them into the ZIP.
4. Store the ZIP and screenshot under `static/sitezips/` and create DB entries via `save_sitezip_record()`.
5. Build the overlay template and accompanying JavaScript to call the new routes and update the results table.
6. Add unit tests covering capture, listing, download and deletion.
7. Document endpoints in `docs/api_routes.md`, update the README feature list and regenerate `retrorecon.postman.json`.

## Task Checklist for Codex
- [ ] Update database schema and helpers.
- [ ] Add capture functions and Flask routes.
- [ ] Create `site2zip.html`, styles and JavaScript for the overlay.
- [ ] Provide unit tests for the workflow and header logging.
- [ ] Update documentation (`README.md`, `docs/api_routes.md`, `docs/test_plan.md`).
- [ ] Regenerate `retrorecon.postman.json` with the new routes.
