# HTTPolaroid: Snapshot Capture System for RetroRecon

(formerly known as site2zip)

## 📘 User Story

As a security researcher, developer, or analyst,  
I want to take a single URL and create a full-fidelity capture of how a modern browser would load that page,  
so that I can preserve the rendered DOM, assets, scripts, screenshots, and navigation behavior  
into a downloadable `.zip` bundle for offline review or archival — without performing a full recursive crawl.

This process is referred to as taking a **"snap"**.

---

##  Core Requirements

### 1. ✅ Input Handling
- Accept a **single URL** from the user
- Support custom headers (optional), e.g.:
  - User-Agent override
  - Cookies or auth tokens
- Detect and follow any **HTTP or JavaScript redirects**, saving the redirect chain

---

### 2.  Browser Emulation
- Launch a **headless browser session** (Chromium or equivalent)
- Behave like a modern browser:
  - Execute JavaScript
  - Load iframes, scripts, images, fonts, and stylesheets
  - Trigger dynamic AJAX/XHR fetches
- Wait for **network idle**, or use a configurable timeout to determine when the page is “done loading”

---

### 3. 📸 Snap Capture
On successful load:
- Save **final DOM** as `index.html` (post-JS rendering)
- Capture a **full-page screenshot**
- Save a **HAR log or equivalent request/response trace**
- Detect and save any navigation or redirection to special pages like `logout.htm` (e.g., as `redirect-capture.html`)
- Save all loaded assets:
  - Images
  - JavaScript
  - CSS
  - Fonts
  - Favicon
  - XHR/Fetch JSON responses (optional, if possible to detect cleanly)

---

### 4.  Output Packaging
- Bundle all saved assets and metadata into a single `.zip` file
- Folder structure inside the zip should be logical:
```
/HTTPolaroid_snap/
├── index.html
├── screenshot.png
├── redirect-capture.html (if applicable)
├── harlog.json
├── assets/
│ ├── js/
│ ├── css/
│ ├── images/
│ └── fonts/
└── meta.json ← Includes final URL, status, timestamp
```
- Zip should be streamed to the client or saved to disk depending on usage context (CLI vs Flask)

---

## 🔎 Technical Considerations

### Current State (RetroRecon `site2zip`)
- ✅ Accepts a URL
- ✅ Uses a browser-like engine to load content (likely Puppeteer or Playwright)
- ✅ Saves HTML and screenshot
- ✅ Handles basic redirection and asset inclusion
- ✅ Creates a downloadable `.zip` file

### Recommendations (Compared to Current Implementation)
| Feature                        | Current | Recommendation |
|-------------------------------|---------|----------------|
| Headless browser              | ✅      | Retain; ensure Playwright is used for modern behavior |
| Full network trace / HAR      | ❌/⚠️     | Add HAR export or equivalent request log for forensics |
| Asset folder structure        | ⚠️ Flat or mixed | Structure into `/assets/js`, `/assets/css`, etc. |
| Screenshot capture            | ✅      | Retain; offer full-page by default |
| Redirect detection (logout)   | ⚠️ Maybe basic | Explicitly detect and label redirect captures |
| Custom headers/cookies        | ❌      | Add support for auth headers or cookie strings |
| Final metadata (JSON summary) | ❌      | Include `meta.json` with request info, timestamps, final URL |
| CLI + Flask mode support      | ⚠️ CLI-heavy | Expand Flask usage to allow web UI trigger |

---

## 🛠 Future Optional Features
(Out of scope unless requested)
- Screenshot diffs between multiple snaps
- JS console error capture
- CSP or security header audit
- Interactive `.html` viewer for exploring the bundle

---

## 🔗 Summary

HTTPolaroid creates a high-fidelity snapshot (“snap”) of a web page as loaded in a full browser context. It focuses on:
- Emulating full browser behavior (JS, assets, redirects)
- Capturing all visible and background-loaded content
- Packaging everything for forensic or research-grade analysis

It is not a crawler or archiver. It’s a **browser-grade single-request capture tool** that integrates seamlessly into RetroRecon as the `site2zip` module — now rebranded as HTTPolaroid.

