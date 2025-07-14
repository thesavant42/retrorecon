# Retrorecon Agents

This file documents the agent patterns and programmatic tasks commonly used in this project.  Agents can be called manually or referenced in Codex prompts to accomplish specific actions within the repository.

## 1. CDXFetcher
**Purpose**: Fetch Wayback Machine CDX entries for a domain and insert new URLs into the SQLite database.

**Input Schema**
```json
{
  "domain": "<string>"
}
```
**Example Call**
```python
client.post('/fetch_cdx', data={'domain': 'example.com'})
```
**Expected Output**
- Redirect response to `/` with a flash message like `Fetched CDX for example.com: inserted N new URLs.`

## 2. JSONImporter
**Purpose**: Import URLs from a JSON file or newline-delimited records in a background thread.

**Input Schema**
```json
{
  "file_content": "<bytes>"
}
```
**Example Call**
```python
threading.Thread(target=_background_import, args=(bytes_data,)).start()
```
**Expected Output**
- Progress stored in `import_progress.json`. Final status becomes `done` or `failed`.

## 3. ImportProgressTracker
**Purpose**: Query or update import progress.

**Input Schema**
```json
{
  "status": "<string>",
  "message": "<string>",
  "current": <int>,
  "total": <int>
}
```
**Example Call**
```python
set_import_progress('in_progress', 'working', 5, 10)
state = get_import_progress()
```
**Expected Output**
- JSON like `{ "status": "in_progress", "message": "working", "current": 5, "total": 10 }`.

## 4. TagManager
**Purpose**: Add or remove tags from URL entries.

**Input Schema (add_tag)**
```json
{
  "entry_id": "<int>",
  "new_tag": "<string>"
}
```
**Example Call**
```python
client.post('/add_tag', data={'entry_id': 1, 'new_tag': 'important'})
```
**Expected Output**
- Redirect with flash message indicating the tag was added.

## 5. BulkActionAgent
**Purpose**: Apply actions (add tag, remove tag, delete) to multiple URLs.

**Input Schema**
```json
{
  "action": "<add_tag|remove_tag|delete>",
  "tag": "<string>",
  "selected_ids": ["<id>", ...],
  "select_all_matching": "<bool>"
}
```
**Example Call**
```python
client.post('/bulk_action', data={'action': 'delete', 'selected_ids': ['3','4']})
```
**Expected Output**
- Redirect with a flash message summarizing the action.

## 6. ThemeManager
**Purpose**: Persist theme choice, background image, and panel opacity in the session.

**Input Schema (set_theme)**
```json
{
  "theme": "<filename.css>"
}
```
**Example Call**
```python
client.post('/set_theme', data={'theme': 'nostalgia.css'})
```
**Expected Output**
- Theme stored in the session and flash message confirming the change.

Similar patterns exist for `/set_background` (field `background`) and `/set_panel_opacity` (field `opacity`).

## 7. WebpackExploder
**Purpose**: Download a Webpack `.js.map` file and return a ZIP archive of the sources.

**Input Schema**
```json
{
  "map_url": "<string>"
}
```
**Example Call**
```python
client.post('/tools/webpack-zip', data={'map_url': 'https://host/app.js.map'})
```
**Expected Output**
- `application/zip` file download containing the source files referenced in the map.

## 8. DatabaseManager
**Purpose**: Create, load or save the SQLite database used by the application.

- `POST /new_db` – reset DB with demo entries.
- `POST /load_db` – upload a `.db` file.
- `GET /save_db?name=xyz` – download the current DB.

## 9. StyleLintAgent
**Purpose**: Run CSS linters.

**Usage**
```bash
npm --prefix frontend install
npm --prefix frontend run lint
```
**Expected Output**
- No lint errors reported. Checks both Stylelint rules and inline-style detection.

## 10. PyTestAgent
**Purpose**: Execute Python unit tests.

**Usage**
```bash
pip install -r requirements.txt
pytest -q
```
**Expected Output**
- All tests pass (currently in `tests/`).

## 11. CSSAuditAgent
**Purpose**: Analyze HTML/CSS usage and detect unscoped selectors.

**Usage**
```bash
python scripts/audit_css.py > reports/report.json
```
**Expected Output**
- JSON summarizing element coverage and selectors not under `.retrorecon-root`.

When creating new CSS, follow `STYLE_GUIDE.md` which mandates that selectors be scoped under `.retrorecon-root` using BEM-style naming. Running `npm run lint` checks for inline styles and standard Stylelint rules.


## 12. FetchMCPAgent
**Purpose**: Dynamically fetch web content and convert it to markdown using the MCP (Model Context Protocol) fetch service.

**Configuration**: The `fetch` MCP is configured to register dynamically via Server-Sent Events (SSE) at `http://127.0.0.1:3000/sse` and supports lazy loading to optimize resource usage.

**Input Schema**
```json
{
  "url": "<string>",
  "options": {
    "user_agent": "<string>",
    "timeout": <int>
  }
}
```

**Example Usage**
```python
# Dynamic fetch requests can be made to any accessible URL
fetch_group = get_fetch_group()
if fetch_group:
    result = fetch_group.call_tool("fetch", {"url": "http://ifconfig.me"})
```

**Expected Output**
- Markdown-formatted content from the fetched URL
- Error handling for unreachable or invalid URLs
- Support for custom user agents and timeout configurations

**Architecture Notes**
- Integrates with LMStudio-Server for AI processing
- Uses SSE transport for real-time communication
- Supports dynamic target URLs without hardcoded endpoints

## 13. SQLiteMCPAgent  
**Purpose**: Provide embedded MCP server functionality for querying RetroRecon SQLite databases with natural language processing capabilities.

**Configuration**: The SQLite MCP server is embedded within RetroRecon and configured through environment variables and the `MCPConfig` class.

**Input Schema**
```json
{
  "query": "<string>",
  "database_path": "<string>",
  "row_limit": <int>
}
```

**Example Usage**
```python
# Query the RetroRecon database using the embedded MCP server
mcp_server = get_mcp_server()
if mcp_server:
    result = mcp_server.query_database("Find all URLs from example.com")
```

**Expected Output**
- Structured database query results
- Natural language processing of query intentions
- Respect for configured row limits and timeouts

**Architecture Notes**
- Embedded directly within RetroRecon application
- Interfaces with LMStudio-Server for query interpretation
- Supports multiple API bases for failover functionality
- Maintains database connection pooling for performance

## 14. ScreenshotAgent
**Purpose**: Capture website screenshots in a headless browser.

**Input Schema**
```json
{
  "url": "<string>",
  "user_agent": "<string>",
  "spoof_referrer": "<bool>"
}
```
**Example Call**
```python
client.post('/tools/screenshot', data={'url': 'https://example.com'})
```
**Expected Output**
- JSON like `{ "id": 1 }` representing the screenshot record.

## 15. SiteZipAgent
**Purpose**: Crawl a page and download all assets as a ZIP archive.

**Input Schema**
```json
{
  "url": "<string>",
  "agent": "<string>",
  "spoof_referrer": "<bool>"
}
```
**Example Call**
```python
client.post('/tools/site2zip', data={'url': 'https://example.com'})
```
**Expected Output**
- JSON like `{ "id": 5 }` with the capture ID.

## 16. SubdomainFetcher
**Purpose**: Retrieve subdomains for a domain from crt.sh or VirusTotal.

**Input Schema**
```json
{
  "domain": "<string>",
  "source": "<crtsh|virustotal>",
  "api_key": "<string>"
}
```
**Example Call**
```python
client.post('/subdomains', data={'domain': 'example.com', 'source': 'crtsh'})
```
**Expected Output**
- JSON list of discovered subdomain records.
