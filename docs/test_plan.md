# Test Plan for Database Workflow Updates

This document describes the tests required for the new database creation and rename features.

## Unit Tests (`tests/`)

1. **Create New DB with Name**
   - POST `/new_db` with `db_name=client1`.
   - Verify a file `db/client1.db` is created and `session['db_display_name']` equals `client1.db`.
   - Ensure tables exist by querying `urls`.

2. **Create New DB with Default Name**
   - POST `/new_db` with no name.
   - Expect file `db/waybax.db` and matching session value.

3. **Rename Database**
   - Start with a temporary database.
   - POST `/rename_db` with `new_name=renamed`.
   - Assert the old file no longer exists and `renamed.db` contains original data.

4. **Invalid Names**
   - Send names with illegal characters (`../bad` or `foo?bar`).
   - Assert response flashes an error and file is unchanged.

5. **Rename While Open**
   - Open a connection to the database.
   - Attempt `/rename_db` and expect an error message due to lock.

6. **List Existing Databases**
   - Create two databases in the `db/` folder.
   - `GET /list_dbs` should return JSON containing their filenames.
   - The unit test `test_list_dbs_and_load_saved` demonstrates this check.

7. **Load Saved Database**
   - POST `/load_saved_db` with one of the names returned from `/list_dbs`.
   - Verify `session['db_display_name']` updates and queries return the stored URL.

## GitHub Actions Workflow
Create `.github/workflows/ci.yml` running on pushes and pull requests:

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install Python deps
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest -q
      - name: Install Node deps
        run: |
          npm --prefix frontend install
      - name: Lint CSS
        run: |
          npm --prefix frontend run lint
```

This ensures database workflow tests are executed along with the existing suite and CSS linting on every commit.

## Notes Feature Tests

1. **Add and Retrieve Note**
   - Start with a database containing one URL.
   - POST `/notes` with `url_id=1` and `content=Test`.
   - GET `/notes/1` should return JSON with one note containing `Test`.

2. **Update Note**
   - POST `/notes` with `note_id=<id>` and `content=Updated`.
   - Confirm subsequent `GET /notes/1` shows the updated text.

3. **Delete Note**
   - POST `/delete_note` with `note_id=<id>`.
   - Ensure the note list for that URL is empty.

4. **Delete All Notes**
   - Create two notes, then POST `/delete_note` with `url_id=1` and `all=1`.
   - GET `/notes/1` should return an empty list.

5. **Export Notes**
   - Add notes for multiple URLs.
   - GET `/export_notes` and validate the JSON structure contains each URL and its notes.

## Text Tools Tests

1. **Menu Entry**
   - Click `Tools → Utilities → Text Tools` from the navbar.
   - Verify the overlay opens only when triggered by this menu option.

2. **URL Encode/Decode**
   - Enter `This is a sketchy string!?"` in the textarea.
   - Click **URL Encode**, then **URL Decode**.
   - The final text should match the original string exactly.

3. **Base64 Round Trip**
   - Input a multiline string using CRLF, LF and CR newlines.
   - Press **Base64 Encode** then **Base64 Decode**.
   - Text should return to the original form without errors.

## JWT Tools Tests

1. **Menu Entry**
   - Select `Tools → Utilities → JWT Tools` from the navbar.
   - Ensure the overlay opens only from this menu item and not during page load.

2. **Decode Demo Token**
   - Post a known demo token to `/tools/jwt_decode`.
   - Response should contain formatted JSON and a readable `exp` timestamp.
   - The JSON also includes `alg_warning` and `key_warning` flags.

3. **Edit and Encode**
   - Decode a token, modify the JSON payload and encode it again.
   - Decoding the result should reflect the edited fields.

4. **Sign with Secret**
   - Encode `{"sub":1}` with secret `secret123` and verify the signature using the same secret.

5. **Weak Algorithm Warning**
   - Decoding a token signed with `none` should return a warning flag in the response.

6. **Fixed Key Warning**
   - Provide a token signed with a known default key; decoding should highlight the weak key.

7. **Cookie Jar Entry**
   - After a successful decode, `/jwt_cookies` should list the new token with issuer, algorithm and notes.

## Site2Zip Tests

1. **Menu Entry**
   - Select `Tools → Active Recon → Site2Zip` from the navbar.
   - Verify the overlay only loads when triggered.

2. **Capture a Page**
   - POST `/tools/site2zip` with `url=https://example.com`.
   - Expect a JSON response with an ID and a screenshot file.
   - `GET /sitezips` should list the entry with a ZIP download link.

3. **User Agent Option**
   - Capture the same URL with `agent=android` and confirm the header log reflects the Android user agent.

4. **Referrer Spoofing**
   - Capture with `spoof_referrer=1` and verify the logged request headers contain a Referrer matching the target URL.

5. **Delete Capture**
   - POST `/delete_sitezips` with the capture ID and confirm it is removed from `/sitezips`.

## Project Overview Tests

1. **Overview Page Loads**
   - Create a database with URLs and subdomains.
   - GET `/overview` should return status 200 and list the domain name.

2. **JSON Data**
   - GET `/overview.json` should return counts for `urls` and `domains` reflecting the inserted records.

## API Spec Tests

1. **OpenAPI Generation**
   - Load `/swagger` and verify the UI shows all application routes.
