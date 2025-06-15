# Notes Feature Implementation Plan

This document outlines the proposed design for adding per-URL notes to Retrorecon. Users will be able to store short text annotations on each URL result and manage them from the interface.

## Goals
- Add a "Notes" action to each result allowing users to create, edit and delete notes.
- Display an overlay with a text input and a history of notes for the selected URL.
- Persist notes in the SQLite database and expose them through JSON endpoints for export.
- Encode user input to mitigate cross-site scripting risks.

## Database Changes
Add a new `notes` table:
```sql
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY(url_id) REFERENCES urls(id)
);
```
`ensure_schema()` should create this table when missing so existing databases remain compatible.

## Flask Routes
- `GET /notes/<int:url_id>` – return all notes for the given URL as JSON.
- `POST /notes` – create or update a note. Parameters:
  - `url_id` – ID of the related URL.
  - `content` – note text.
  - optional `note_id` – when supplied, update the existing note.
- `POST /delete_note` – remove a note by ID or, when `all=1`, delete all notes for a URL.
- `GET /export_notes` – download all notes as a JSON document (`[{"url":...,"content":...}]`).

All input should be sanitized using `flask.escape` before storage.

## UI Updates
- Add a **+ Notes** button in the row tools section for each URL.
- Include a hidden overlay element in `index.html`:
  - Fixed position, full viewport width/height.
  - Top half: `<textarea>` for editing/adding a note.
  - Bottom half: list of existing notes with edit and delete controls.
- JavaScript should fetch `/notes/<url_id>` when the overlay opens and populate the list. Notes are updated via `fetch('/notes', {method:'POST', body: ...})`.
- Provide buttons to save the note, delete an individual entry and delete all notes.

## Export Format
Notes can be exported via `/export_notes` which returns JSON structured like:
```json
[
  {"url": "http://a.example/", "notes": ["first", "second"]},
  ...
]
```
This allows later reporting or integration with other tools.

## Implementation Steps
1. Update `db/schema.sql` with the `notes` table and ensure `init_db` and `ensure_schema` handle it.
2. Implement helper functions in `app.py` to query and modify notes.
3. Add the new Flask routes described above.
4. Update `templates/index.html`, `static/base.css` and associated scripts to present the overlay and note controls.
5. Escape note content using `flask.escape` before insert/update and render notes using Jinja's autoescape or by setting `textContent` in JavaScript.
6. Provide a JSON export route for all notes.
7. Write unit tests covering creation, update, deletion and export of notes.
8. Document the new endpoints in `docs/api_routes.md` and update the README features list.

## Task Checklist for Codex
- [ ] Extend `db/schema.sql` with the `notes` table and update schema helpers.
- [ ] Create helper functions in `app.py` for CRUD operations on notes.
- [ ] Implement the new Flask routes (`/notes`, `/notes/<id>`, `/delete_note`, `/export_notes`).
- [ ] Modify templates and JavaScript to show the notes overlay and interact with the API.
- [ ] Add CSS styles for the overlay, following `STYLE_GUIDE.md` scoping rules.
- [ ] Write unit tests exercising note creation, editing, deletion and export.
- [ ] Update documentation (`README.md`, `docs/api_routes.md`, `docs/test_plan.md`).
