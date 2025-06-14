# Database Workflow Enhancement Plan

This document outlines the steps required to implement the updated database workflow supporting named creation and in-app renaming.

## Goals
- Allow users to specify a name when creating a new SQLite database.
- Display the chosen name in the UI (`loaded> example.db`).
- Provide a "Rename Database" action that safely renames the current database file.
- Validate file names and report errors for invalid input.

## Proposed Changes

### 1. Update `create_new_db`
- Modify `create_new_db(name: str)` in `app.py` to accept an optional filename.
- When `name` is provided, sanitize it:
  - Allow alphanumeric characters, dashes and underscores.
  - Reject names longer than 64 characters or containing path separators.
  - Append `.db` if missing.
  - Remove the existing database (if any) and initialize using the current schema without demo entries.
- Store the name in `session['db_display_name']` and update `app.config['DATABASE']` to point to the new file.

### 2. Add `rename_database`
- New Flask route `/rename_db` accepting `POST` with `new_name`.
- Close the current SQLite connection via `close_connection(None)`.
- Perform the same validation as in new DB creation.
- Use `os.rename` to rename the current file. Handle `OSError` if the target exists or if a lock prevents renaming.
- On success, update `app.config['DATABASE']` and `session['db_display_name']`.
- Flash success or error messages to the user.

### 3. UI Updates
- In `templates/index.html` add:
  - A text input for the new DB name when selecting "New DB".
  - A new "Rename DB" button triggering a small form or modal requesting the new name.
- Ensure the "loaded>" indicator reflects `db_name` from the session after each operation.

### 4. Validation and Error Handling
- Reject blank names or names containing characters other than `[A-Za-z0-9_-]`.
- If validation fails, flash an error and keep the existing database loaded.
- If renaming fails due to file locks, flash a descriptive error message.

## Migration Considerations
- Existing databases remain compatible; only new workflow for creating/renaming is added.
- Update any deployment scripts to pass a desired name to `/new_db` if needed.

