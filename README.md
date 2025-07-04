# 🕶️⌛ RetroRecon
![Screenshot](docs/01-rr-text-logo.png)


A Flask web application for exploring Wayback Machine data. It fetches CDX records, stores them in SQLite, and provides a UI to search, tag and manage the results.


![Screenshot](docs/Screenshot-001.png)


**Timeline Analysis. OSINT Archeology.**  
RetroRecon digs through the internet’s attic to find forgotten, buried, or quietly updated web assets using the [Wayback Machine](https://archive.org/web/) and other archival data sources. It's built to help hackers, researchers, and digital historians reconstruct timelines, compare file changes, and extract secrets from the past.

---

## 🔦 What It Does (At a Glance)

- 🔍 **Crawls archived URLs** from the Wayback Machine (via CDX API)
- 🕶️ **Groups and filters results** by file type, timestamp, tags, or path
- 🧾 **Extracts & analyzes source maps** and JavaScript files for secrets
- 📁 **Saves everything locally** for offline inspection and auditing
- 🔍 **Flags suspicious patterns**, such as leaked API keys, environment files, and exposed `.map` files

---

## 🕵️ Use Cases

- **Security Research** – Discover forgotten `.env` files, exposed sourcemaps, or previously public endpoints
- **OSINT Investigations** – Build a historical snapshot of a domain or identify deleted content
- **Digital Forensics** – Trace changes in a site’s frontend or backend over time
- **Web Development Post-Mortems** – Compare JavaScript bundles, audit version regressions, and timeline UI changes

---

## 🔍 Features

| Feature                        | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| Wayback Archive Indexing      | Pulls structured snapshots via CDX API                                     |
| Local Source Map Extraction   | Finds and restores `.map` files for easier JS debugging                     |
| Suspicious Pattern Detection  | Scans downloaded files for API keys, JWTs, secrets, etc.                   |
| Filtering & Grouping          | Smart filters by type (e.g., `.js`, `.env`, `.php`, `.map`, etc.)          |
| HTML Report Output (WIP)      | Generate browsable summaries with tagged snapshots and visual comparisons  |
| Dynamic Rendering API         | Programmatically render pages from schemas with managed assets             |
| OCI Registry Table Explorer   | Browse container images as tables with direct download links |
| HTTPolaroid Snapshots         | Capture a single URL with full headers, screenshot and assets into a zip |
| Markdown Editor               | Edit and preview project docs with a resizable editor |
| Domain Sort (Subdomain View)  | Recursively group hosts by root domain |

---

## ⏱️ Quickstart

```bash
git clone https://github.com/thesavant42/retrorecon.git
cd retrorecon
pip install -r requirements.txt

# Start crawling a domain
python retrorecon.py --domain example.com
```

Use `--help` to view available options for filtering, exporting, and source map analysis.

## 🖥️ Running the Web Interface

Launch the Flask UI with the provided scripts. The optional `-l` flag sets the listening address (default `127.0.0.1`).

```bash
./launch_app.sh -l 0.0.0.0   # Linux/macOS
.\launch_app.bat -l 0.0.0.0  # Windows
```

These scripts export `RETRORECON_LISTEN` so `app.py` binds accordingly.
**Never expose the app publicly without proper hardening.**

### Vendored MCP SQLite Server

`launch_app.sh` and `launch_app.bat` previously started the vendored Model
Context Protocol server. This logic now lives inside the Flask application.
Whenever a database is loaded or switched RetroRecon launches
`mcp-server-sqlite` as a subprocess on port `12345` pointing at the active
database. The server is terminated automatically when the app shuts down.

LLMs can connect to MCP at `127.0.0.1:12345`. Include a line such as:

```
You have access to the currently loaded retrorecon SQLite database via MCP at
127.0.0.1:12345. Use this endpoint for SQL queries.
```

in your system prompt or tool configuration.

If dependency installation fails, delete the virtual environment directory and
rerun the launch script.

For a quick walkthrough of the common workflow see
[docs/new_user_guide.md](docs/new_user_guide.md).

### Capture a Snap

The **HTTPolaroid** tool can be triggered from the UI under `Tools → Active Recon`. It fetches a URL in a headless browser, follows redirects and saves the page, assets, headers and screenshot into a single zip file for download.

---

## 🕶️ Philosophy

RetroRecon isn’t just about scraping old URLs. It’s about **investigating time** — tracing the evolution of a site’s public footprint and finding what was exposed *when*. Think of it as a tool to:
> _"Reconstruct the past to understand the present. And maybe… exploit the future."_

---

## 🗃️ Project Layout

```
retrorecon/
├── retrorecon.py         # Main CLI interface
├── cdx.py                # Wayback CDX API logic
├── extract.py            # Source map and secrets extraction
├── utils/                # Helpers and formatters
├── static/               # CSS and JS for reports
└── templates/            # Jinja2 templates for report generation
```

---

## 🔍 Sample Output

Coming soon – screenshots of the report interface and extraction logs.

---

## ⏱️ Roadmap

- [ ] Full HTML reporting interface (Wayback snapshot explorer)
- [ ] Timeline diff view between asset versions
- [ ] Plugin system for custom extractors (e.g., Postman collections, GraphQL introspection)
- [ ] Integration with `jodskeys` and `darkwing_dox`

---

## 🕶️ Author

**savant42** – Veteran red teamer. Builder of weird tools.  
Reach me through [GitHub Discussions](https://github.com/thesavant42/retrorecon/discussions) or post an Issue.

---

## 📜 License

MIT License. Use it. Abuse it. Just don’t sell it back to me.
