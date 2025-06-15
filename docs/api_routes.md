# Retrorecon REST API

This document describes the HTTP endpoints exposed by the Flask application. All examples assume the server is running locally on `http://localhost:5000` and the `base_url` variable used by the Postman collection refers to that address.

## General Notes

- POST endpoints expect form data unless otherwise indicated.
- JSON responses are returned only from a few routes as noted.
- Successful POST requests typically redirect back to `/` with a flash message.

## Routes

### `GET /`
Render the main search page.

```
curl http://localhost:5000/
```

Optional query parameter `q` accepts plain text or expressions using the
`url:`, `timestamp:`, `http:` and `mime:` operators combined with Boolean
keywords (`AND`, `OR`, `NOT`).

Example:

```
curl -G --data-urlencode "q=url:example.com AND http:200" http://localhost:5000/
```

### `POST /fetch_cdx`
Fetch Wayback Machine CDX records for a domain and insert any new URLs into the loaded database.

Parameters:
- `domain` – domain name to query.

Example:
```
curl -X POST -d "domain=example.com" http://localhost:5000/fetch_cdx
```

### `POST /import_file` (`/import_json`)
Import URLs from a JSON file or load a database file. The route is accessible via both `/import_file` and `/import_json`.

Parameters depend on the uploaded file:
- `import_file` or `json_file` – JSON array/lines of records.
- `db_file` – SQLite `.db` file to load.

Example (JSON import):
```
curl -X POST -F "import_file=@records.json" http://localhost:5000/import_file
```

### `GET /import_progress`
Return JSON describing the current import status.

Example:
```
curl http://localhost:5000/import_progress
```
Response:
```json
{"status": "done", "progress": 10, "total": 10, "detail": "Imported 10 records."}
```

### `POST /add_tag`
Add a tag to a single URL entry.

Parameters:
- `entry_id` – ID of the entry.
- `new_tag` – tag text to add.

Example:
```
curl -X POST -d "entry_id=1" -d "new_tag=important" http://localhost:5000/add_tag
```

### `POST /bulk_action`
Apply a tag, remove a tag or delete many entries at once.

Parameters:
- `action` – `add_tag`, `remove_tag` or `delete`.
- `tag` – tag name used with add/remove actions.
- `selected_ids` – repeated form field of entry IDs.
- `select_all_matching` – when set to `true`, apply to all search results.

Example (add tag to two IDs):
```
curl -X POST \
  -F "action=add_tag" -F "tag=archive" \
  -F "selected_ids=3" -F "selected_ids=4" \
  http://localhost:5000/bulk_action
```

### `POST /set_theme`
Persist the chosen theme in the user session.

Parameter:
- `theme` – CSS filename from `static/themes/`.

```
curl -X POST -d "theme=nostalgia.css" http://localhost:5000/set_theme
```

### `POST /set_background`
Persist the selected background image.

Parameter:
- `background` – image filename from `static/img/`.

```
curl -X POST -d "background=stars.jpg" http://localhost:5000/set_background
```

### `POST /set_panel_opacity`
Update the UI panel opacity stored in the session.

Parameter:
- `opacity` – float between `0.1` and `1.0`.

```
curl -X POST -d "opacity=0.5" http://localhost:5000/set_panel_opacity
```

### `POST /set_font_size`
Adjust the base font size in the active theme.

Parameters:
- `size` – integer between `10` and `18`.
- `theme` – CSS theme filename (optional if already set).

```
curl -X POST -d "theme=nostalgia.css" -d "size=16" \
  http://localhost:5000/set_font_size
```

### `GET /saved_tags`
Return the list of saved tag searches.

```
curl http://localhost:5000/saved_tags
```

### `POST /saved_tags`
Add a new tag query to the saved list.

Parameter:
- `tag` – search expression to store.

```
curl -X POST -d "tag=#foo AND #bar" http://localhost:5000/saved_tags
```

### `POST /delete_saved_tag`
Remove a saved tag search.

Parameter:
- `tag` – query string to delete.

```
curl -X POST -d "tag=#foo AND #bar" http://localhost:5000/delete_saved_tag
```

### `POST /tools/webpack-zip`
Download sources referenced in a Webpack `.js.map` file as a ZIP archive.

Parameter:
- `map_url` – URL of the `.js.map` file.

```
curl -X POST -d "map_url=https://host/app.js.map" http://localhost:5000/tools/webpack-zip -o sources.zip
```

### `GET /text_tools`
Serve the Text Tools overlay used for encoding and decoding text.

```
curl http://localhost:5000/text_tools
```

### `POST /tools/base64_decode`
Decode Base64 text sent in the `text` field. Returns plain text.

```
curl -X POST -d "text=SGVsbG8h" http://localhost:5000/tools/base64_decode
```

### `POST /tools/base64_encode`
Encode posted text as Base64.

```
curl -X POST -d "text=Hello" http://localhost:5000/tools/base64_encode
```

### `POST /tools/url_decode`
Convert percent-encoded strings back to their ASCII form.

```
curl -X POST -d "text=This%20is%20fine%21" http://localhost:5000/tools/url_decode
```

### `POST /tools/url_encode`
Percent-encode a string so it is safe for use in URLs.

```
curl -X POST -d "text=This is fine!" http://localhost:5000/tools/url_encode
```

### `GET /jwt_tools`
Serve the JWT Tools overlay used for decoding and encoding JWTs.

```
curl http://localhost:5000/jwt_tools
```

### `POST /tools/jwt_decode`
Decode a JWT sent in the `token` field. Returns formatted JSON with readable timestamps.

```
curl -X POST -d "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:5000/tools/jwt_decode
```

### `POST /tools/jwt_encode`
Encode a JSON payload into a JWT. Accepts `payload` and optional `secret`.

```
curl -X POST -d "payload={\"sub\":1}" -d "secret=mykey" \
  http://localhost:5000/tools/jwt_encode
```

### `POST /new_db`
Create a new empty SQLite database.

Parameter:
- `db_name` – desired base name (optional, sanitized to `<name>.db`).

```
curl -X POST -d "db_name=project" http://localhost:5000/new_db
```

### `POST /load_db`
Upload and load a database file.

Parameter:
- `db_file` – uploaded `.db` file.

```
curl -X POST -F "db_file=@existing.db" http://localhost:5000/load_db
```

### `GET /save_db`
Download the currently loaded database. Use the optional `name` query parameter to specify the download filename.

```
curl -L "http://localhost:5000/save_db?name=backup.db" -o backup.db
```

### `POST /rename_db`
Rename the current database file.

Parameter:
- `new_name` – new base filename.

```
curl -X POST -d "new_name=renamed" http://localhost:5000/rename_db
```

### `GET /notes/<url_id>`
Return all notes for a URL in JSON form.

```
curl http://localhost:5000/notes/1
```

### `POST /notes`
Create a new note or update an existing one.

Parameters:
- `url_id` – ID of the related URL.
- `content` – note text.
- `note_id` – existing note ID when editing (optional).

```
curl -X POST -d "url_id=1" -d "content=hello" http://localhost:5000/notes
```

### `POST /delete_note`
Delete an individual note or, when `all=1`, remove all notes for a URL.

```
curl -X POST -d "note_id=3" http://localhost:5000/delete_note
```

### `GET /export_notes`
Download all notes as structured JSON.

```
curl http://localhost:5000/export_notes
```

## Generating a Postman Collection
Run the helper script to generate a Postman collection from the application's route map:

```
python scripts/generate_postman_collection.py > retrorecon.postman.json
```

Import the resulting `retrorecon.postman.json` file into Postman and set the `base_url` variable to your server address.

