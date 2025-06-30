# Getting Started with RetroRecon

This short guide walks through the typical workflow of exploring archived URLs.

1. **Fetch CDX data**
   ```bash
   curl -X POST http://localhost:5000/fetch_cdx -d "domain=example.com"
   # wildcard subdomains are also supported
   curl -X POST http://localhost:5000/fetch_cdx -d "domain=*.example.com"
   ```
   This pulls Wayback Machine records into the local SQLite database.

2. **Browse results**
   Visit `http://localhost:5000/` in your browser. Use the search box to filter
   URLs. Click a row to open the archived page.

3. **Tag or remove URLs**
   Select checkboxes and choose an action from the bulk menu to add tags or
   delete entries.

4. **Use built‑in tools**
   Open the **Tools** menu for helpers like Subdomonster or the Screenshotter.
   Each loads dynamically without leaving the page.

5. **Try the Demo panel**
   Under **Tools → Demo** you can preview modules in a single window. Choose a
   module from the dropdown to load it in place and click **Close** to return.
