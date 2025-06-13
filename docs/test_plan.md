# Test Plan for Database Workflow Updates

This document describes the tests required for the new database creation and rename features.

## Unit Tests (`tests/`)

1. **Create New DB with Name**
   - POST `/new_db` with `db_name=client1`.
   - Verify a file `client1.db` is created and `session['db_display_name']` equals `client1.db`.
   - Ensure tables exist by querying `urls`.

2. **Create New DB with Default Name**
   - POST `/new_db` with no name.
   - Expect file `waybax.db` and matching session value.

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
        run: npm install
      - name: Lint CSS
        run: npm run lint
```

This ensures database workflow tests are executed along with the existing suite and CSS linting on every commit.
