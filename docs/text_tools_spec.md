# Text Tools Feature Plan

This document defines the specification for the new **Text Tools** interface that replaces the existing Base64 Tool. The goal is to provide common text encoding and decoding actions directly within Retrorecon.

## Goals
- Add a menu option under **Tools** labelled `Text Tools`.
- Provide a full-screen editor styled like the Notes overlay.
- Support Base64 and URL encoding/decoding with inline updates.
- Allow quick copying of the text and closing the tool.
- Expose REST endpoints for each operation to enable API use and Postman tests.
- Apply defensive coding practices to sanitize input and handle errors gracefully.

## UI Design
- When the user selects **Tools → Text Tools**, a full screen modal appears.
- The modal mirrors the layout of the Notes overlay:
  - Large `<textarea id="text-tool-input">` spans the top portion.
  - Beneath the textarea is a row of buttons:
    - **Base64 Decode**
    - **Base64 Encode**
    - **URL Decode**
    - **URL Encode**
    - **Copy** (copies the textarea contents using the Clipboard API)
    - **Close** (hides the overlay)
- All styles reuse the `.notes-overlay` rules from `static/base.css` with minimal additions under `.retrorecon-root`.
- Each button triggers a fetch call to its matching API route. The returned text replaces the current textarea contents so chained operations are possible.

## API Routes
Four POST endpoints operate on a `text` field and return plain text results:
- `POST /tools/base64_decode`
- `POST /tools/base64_encode`
- `POST /tools/url_decode`
- `POST /tools/url_encode`

Additionally `GET /text_tools` serves the overlay HTML/JS fragment for use in the SPA.

Each route validates input, performs the transformation and returns a 200 response with `text/plain` content. Invalid Base64 data should return a 400 status with an error message.

## Defensive Considerations
- Limit request payload size (e.g. 64 KB) to avoid memory issues.
- Use `base64.b64decode(..., validate=True)` so malformed input raises an error.
- Reject decoding requests containing non-text bytes after decoding.
- Escape output where it is inserted back into the DOM to prevent XSS.

## Implementation Steps for Codex
1. Create `text_tools.html` template containing the overlay markup and JavaScript to call the new routes and copy to clipboard.
2. Add the `/text_tools` and `/tools/*` Flask routes in `app.py`.
3. Update the `Tools` dropdown in `templates/index.html` to open the new overlay (rename old "Base64 Tool" link).
4. Add styles in `static/tools.css` scoped under `.retrorecon-root` if needed.
5. Register the new routes in the Postman collection using `scripts/generate_postman_collection.py`.
6. Write unit tests covering:
   - Menu opens the overlay only when triggered.
   - Round‑trip URL encode/decode of `This is a sketchy string!?"`.
   - Base64 encode/decode of a multiline string with various newline characters.
7. Document the endpoints in `docs/api_routes.md` and update the README feature list.

## Task Checklist for Codex
- [ ] Implement HTML, CSS and JS for the Text Tools overlay.
- [ ] Create the five Flask routes with validation and tests.
- [ ] Update navigation link text and behaviour.
- [ ] Extend documentation (`README.md`, `docs/api_routes.md`, `docs/test_plan.md`).
- [ ] Regenerate `retrorecon.postman.json` and commit it.
