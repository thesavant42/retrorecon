# Retrorecon REST API

This document describes the HTTP endpoints exposed by the Flask application. All examples assume the server is running locally on `http://localhost:5000` and the `base_url` variable used by the Postman collection refers to that address.

The complete route map can also be browsed via the built-in Swagger UI at
`/swagger`. The underlying OpenAPI document is served as
`/static/openapi.yaml`.

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
Import URLs from a JSON file. The route is accessible via both `/import_file` and `/import_json`.

Parameters:
- `import_file` or `json_file` – JSON array or newline-delimited records.

Example:
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
Decode a JWT sent in the `token` field. Returns JSON containing the header,
payload and additional fields:
`exp_readable`, `expired`, `alg_warning` and `key_warning`.

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

### `GET /jwt_cookies`
Return the last 50 decoded JWT entries. Each object includes `issuer`, `alg`,
`claims`, `notes`, `token` and `created_at`.

```
curl http://localhost:5000/jwt_cookies
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

### `GET /text_notes`
Return all project-wide text notes.

```
curl http://localhost:5000/text_notes
```

### `POST /text_notes`
Create or update a text note.

Parameters:
- `content` – note text.
- `note_id` – existing note ID when editing (optional).

```
curl -X POST -d "content=demo" http://localhost:5000/text_notes
```

### `POST /delete_text_note`
Delete a text note by ID.

```
curl -X POST -d "note_id=1" http://localhost:5000/delete_text_note
```

### `GET /export_urls`
Export URL records in various formats.

Parameters:
- `format` – one of `txt`, `csv`, `md` or `json`.
- `q` – optional search query.
- `id` – repeatable ID filter when not using `select_all_matching`.
- `select_all_matching` – set to `true` to export all results for the query.

```
curl -L "http://localhost:5000/export_urls?format=csv&id=1&id=2"
```


### `GET /site2zip`
Serve the Site2Zip overlay for capturing a full page snapshot.

```
curl http://localhost:5000/site2zip
```

### `POST /tools/site2zip`
Launch a capture job and return JSON with the record ID.

Parameters:
- `url` – page to fetch.
- `agent` – optional user agent (`android`, `bot` or blank for desktop).
- `spoof_referrer` – set to `1` to spoof the referrer header.

```
curl -X POST -d "url=https://example.com" http://localhost:5000/tools/site2zip
```

### `GET /sitezips`
List previous Site2Zip captures as JSON.

```
curl http://localhost:5000/sitezips
```

### `GET /download_sitezip/<id>`
Download the ZIP archive for a capture.

```
curl -O http://localhost:5000/download_sitezip/1
```

### `POST /delete_sitezips`
Delete one or more captures by ID.

```
curl -X POST -d "ids=1,2" http://localhost:5000/delete_sitezips
```

### `GET /dag/repo/<name>`
List tags for a Docker repository.

```
curl http://localhost:5000/dag/repo/library/ubuntu
```

### `GET /dag/image/<ref>`
Return the manifest JSON for an image reference.

```
curl http://localhost:5000/dag/image/library/ubuntu:latest
```

### `GET /dag/fs/<digest>/<path>`
Extract a single file from a layer blob.

Query parameter:
- `image` – image reference containing the layer.

```
curl -O \
  "http://localhost:5000/dag/fs/sha256:1234/etc/os-release?image=library/ubuntu:latest"
```


### `POST /delete_jwt_cookies`
Delete stored JWT cookie entries.

Parameter:
- `ids` – comma-separated IDs.

```
curl -X POST -d "ids=1,2" http://localhost:5000/delete_jwt_cookies
```

### `POST /update_jwt_cookie`
Edit notes for a saved JWT record.

Parameters:
- `id` – record ID.
- `notes` – text notes.

```
curl -X POST -d "id=1" -d "notes=ok" http://localhost:5000/update_jwt_cookie
```

### `GET /export_jwt_cookies`
Export decoded JWT history as JSON.

```
curl http://localhost:5000/export_jwt_cookies
```


### `GET /screenshotter`
Serve the screenshot overlay.

```
curl http://localhost:5000/screenshotter
```

### `GET /tools/screenshotter`
Full-page screenshot overlay.

```
curl http://localhost:5000/tools/screenshotter
```

### `POST /tools/screenshot`
Capture a screenshot and return JSON with the ID.

Parameters:
- `url` – target URL.
- `user_agent` – optional agent string.
- `spoof_referrer` – `1` to spoof the referrer header.

```
curl -X POST -d "url=https://example.com" http://localhost:5000/tools/screenshot
```

### `GET /screenshots`
List captured screenshots as JSON.

```
curl http://localhost:5000/screenshots
```

### `POST /delete_screenshots`
Delete screenshots by ID.

```
curl -X POST -d "ids=1,2" http://localhost:5000/delete_screenshots
```


### `GET /subdomonster`
Serve the Subdomonster overlay with bulk-selection checkboxes.

```
curl http://localhost:5000/subdomonster
```

### `GET /tools/subdomonster`
Full-page subdomain overlay with the same bulk-selection features.

```
curl http://localhost:5000/tools/subdomonster
```

### `GET /subdomains`
List subdomains from the database.

Parameters (optional):
- `domain` – limit results to a root domain.
- `page` – return a specific page of results.
- `items` – number of subdomains per page.

```
curl "http://localhost:5000/subdomains?domain=example.com&page=1&items=50"
```

### `POST /subdomains`
Fetch subdomains from crt.sh, VirusTotal, or the local URL list.

Parameters:
- `domain` – target domain (optional when using the `local` source).
- `source` – `crtsh`, `virustotal`, or `local`.
- `api_key` – required for VirusTotal.

Use `source=local` to import subdomains discovered by scraping existing URLs.

```
curl -X POST -d "domain=example.com" -d "source=crtsh" http://localhost:5000/subdomains
curl -X POST -d "source=local" http://localhost:5000/subdomains
```

### `GET /export_subdomains`
Export subdomains for a domain.

```
curl "http://localhost:5000/export_subdomains?domain=example.com"
```

### `POST /mark_subdomain_cdx`
Mark a subdomain as indexed by CDX.

```
curl -X POST -d "subdomain=dev.example.com" http://localhost:5000/mark_subdomain_cdx
```

### `POST /scrape_subdomains`
Scrape discovered subdomains from existing URLs.

```
curl -X POST -d "domain=example.com" http://localhost:5000/scrape_subdomains
```

### `POST /delete_subdomain`
Delete a subdomain entry.

```
curl -X POST -d "domain=example.com" -d "subdomain=dev" http://localhost:5000/delete_subdomain
```


### `POST /load_saved_db`
Switch to a database file stored under `db/`.

```
curl -X POST -d "db_file=wabax.db" http://localhost:5000/load_saved_db
```

### `POST /set_items_per_page`
Change how many results display on the search page.

```
curl -X POST -d "count=20" http://localhost:5000/set_items_per_page
```

### `GET /docker_layers`
Return layer and manifest details for an image as JSON.

```
curl -G --data-urlencode "image=ubuntu:latest" http://localhost:5000/docker_layers
```
Pass `insecure=1` for registries with self-signed certificates.

### `GET /download_layer`
Download a compressed layer blob.

```
curl -L "http://localhost:5000/download_layer?image=ubuntu:latest&digest=sha256:1234" -o layer.tar.gz
```
Include `insecure=1` when downloading from insecure registries.

### `GET /oci_explorer`
Serve the OCI Explorer overlay.

```
curl http://localhost:5000/oci_explorer
```

### `GET /tools/oci_explorer`
Full-page OCI Explorer.

```
curl http://localhost:5000/tools/oci_explorer
```

### `GET /oci_explorer_api`
Query manifest information for an image.

```
curl -G --data-urlencode "image=ubuntu:latest" http://localhost:5000/oci_explorer_api
```

Pass `insecure=1` to disable TLS validation or when connecting to self-signed registries.

### `GET /registry_table`
Return manifest details as a hierarchical table structure.

```
curl -G --data-urlencode "image=ubuntu:latest" http://localhost:5000/registry_table
```
Add `insecure=1` to fetch manifests from registries with self-signed certificates.

### `GET /dag_explorer`
Serve the Dag Explorer overlay.

```
curl http://localhost:5000/dag_explorer
```

### `GET /tools/dag_explorer`
Full-page Dag Explorer overlay.

```
curl http://localhost:5000/tools/dag_explorer
```

### `GET /dag/layer/<image>@<digest>`
List files in a layer.

```
curl http://localhost:5000/dag/layer/library/ubuntu@sha256:abcd
```

### `GET /repo/<repo>`
View tags for a repository.

```
curl http://localhost:5000/repo/library/ubuntu
```

### `GET /image/<ref>`
Render manifest details for an image reference.

```
curl http://localhost:5000/image/library/ubuntu:latest
```

### `GET /image/<repo>@<digest>`
Render details for an image digest.

```
curl http://localhost:5000/image/library/ubuntu@sha256:abcd
```

### `GET /size/<repo>@<digest>`
Return the uncompressed size of a layer.

```
curl http://localhost:5000/size/library/ubuntu@sha256:abcd
```

### `GET /overview`
Render the project overview page summarizing domains and module counts.

```
curl http://localhost:5000/overview
```

### `GET /overview.json`
Return the same overview data as JSON.

```
curl http://localhost:5000/overview.json
```

