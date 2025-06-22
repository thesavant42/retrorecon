# Project Overview Design

This document outlines the new **Project Overview** feature. Each SQLite database represents a project. The overview page provides a quick summary of domains and related module data so users can navigate from a high level down to individual tools.

## Goals
- Treat every loaded `.db` file as its own project.
- Display counts for URLs, domains, screenshots, site zips, JWT cookies and notes.
- Group subdomains by root domain similar to the URL results table.
- Allow each subdomain to be sent to other Retrorecon tools.

## Routes
- `GET /overview` – Render the HTML overview with tables for each domain.
- `GET /overview.json` – Return the same data in JSON format.

## UI
The layout mirrors the search results page with a table for each domain. A summary line shows total counts for every module. Subdomain rows will include tool actions in future revisions.

## Database
No schema changes are required. Counts are derived from the existing `urls`, `domains`, `screenshots`, `sitezips`, `jwt_cookies` and `notes` tables.

## Implementation Notes
The Flask blueprint `overview.py` collects table counts and domain lists. It is registered in `app.py` so the page is accessible once a database is loaded.
