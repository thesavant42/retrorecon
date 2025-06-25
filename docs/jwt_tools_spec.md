# JWT Tools Feature Plan

This document specifies the design for a new **JWT Tools** window within Retrorecon. The tool lets users decode, edit and re-encode JSON Web Tokens without leaving the application.

## Goals
- Provide a menu entry under **Tools** labelled `JWT Tools`.
- Display a full-screen editor like the existing Text Tools overlay.
- Allow decoding of JWTs into formatted JSON with timestamp conversion.
- Allow encoding (and optional signing) of JWTs from edited JSON.
- Highlight weak algorithms and fixed keys.
- Offer quick copy and save actions.

## UI Design
- Selecting **Tools → JWT Tools** opens a modal overlay similar to `text_tools.html`.
- The top half contains `<textarea id="jwt-tool-input">` for the JWT or JSON payload.
- Beneath the textarea is a row of buttons:
  - **JWT Decode**
  - **JWT Encode**
  - **Save As** – downloads the current text
  - **Copy** – copies to the clipboard
  - **Close** – hides the overlay
- When decoding, the tool pretty prints the header and payload. Epoch values for `iat`, `nbf` and `exp` are translated to readable timestamps. Expired tokens show the `exp` value in black; valid tokens show it in green.
- A small text input allows supplying a `secret` used when encoding/signing.
- Algorithms considered weak (`none`, `HS256`, etc.) or tokens signed with a known fixed key should trigger a visible warning banner.

## API Routes
- `GET /jwt_tools` – serve the overlay HTML fragment.
- `POST /tools/jwt_decode` – accept a `token` field and return formatted JSON. Validation errors return status 400.
- `POST /tools/jwt_encode` – accept `payload` (JSON) and optional `secret`. Returns the encoded token.

## Defensive Considerations
- Limit request payloads to ~64 KB.
- Use Python's `jwt` library with explicit algorithms to avoid `none` spoofing.
- Catch decoding exceptions and return clear error messages.
- Sanitize any JSON inserted back into the DOM.

## Implementation Steps for Codex
1. Create `jwt_tools.html` template and accompanying JS in `static/jwt_tools.js`.
2. Implement the new Flask routes in `app.py` with robust error handling.
3. Update the navigation menu text (`Text Tools` entry renamed to `JWT Tools`).
4. Add CSS under `.retrorecon-root` in `tools.css` if additional styling is required.
5. Extend documentation and unit tests as outlined below.

## Task Checklist for Codex
- [ ] Build the HTML, CSS and JS for the JWT Tools overlay.
- [ ] Add the `/jwt_tools`, `/tools/jwt_decode` and `/tools/jwt_encode` routes.
- [ ] Support optional signing when a secret is provided.
- [ ] Display algorithm and key warnings when decoding.
- [ ] Update the navigation menu and ensure the overlay only opens from the menu.
- [ ] Create unit tests for decoding, encoding, signing and warnings.
- [ ] Update `README.md`, `docs/api_routes.md`, `docs/test_plan.md` and regenerate `tests/postman/retrorecon.postman.json`.
