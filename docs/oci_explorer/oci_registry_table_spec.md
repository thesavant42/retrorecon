# OCI Registry Table Explorer Design

This document outlines the plan for implementing the feature described in issue #582: **Table-formatted OCI Registry Explorer with Address Type Detection and Filesystem Browsing**.

## Summary
The current registry explorer returns raw JSON when a user fetches an image reference. To improve usability we will detect the registry type of any address, fetch its manifest, and present the contents in an interactive table. Each file in the virtual filesystem will have a direct download link and users can toggle between table and raw JSON views.

## Goals
- Accept an image or repository address from any major registry (Docker Hub, GCR, ECR, etc.).
- Determine the registry type automatically and adapt requests accordingly.
- Fetch the digest/manifest structure and build a browsable filesystem hierarchy.
- Render expandable tables showing metadata and files with download links.
- Provide a button to switch between JSON and table views.
- Indexed menus allow quick navigation through layers and metadata.

## Design Strategy
1. **Address Detection**
   - Parse the user supplied address and match common registry domains.
   - Branch logic for Docker Hub, Google Container Registry, Amazon ECR and generic OCI registries.
   - Normalize references so manifest requests use the proper base URL and credentials when needed.
2. **Manifest Retrieval**
   - Use existing async registry helpers (`fetch_token`, `fetch_index_or_manifest`, `fetch_blob`).
   - After fetching the manifest, inspect media type to decide if it is an index or single image.
   - For each layer, fetch file listings using `list_layer_files`.
3. **Filesystem Mapping**
   - Build an in-memory tree representing directories and files.
   - Each entry stores digest, size, permissions and path.
   - Generate download URLs referencing `/layers/<image>@<digest>/<path>` to reuse existing layer browsing routes.
4. **UI Rendering**
   - Extend `oci_explorer.js` to populate a new table layout.
   - Show a top level table summarizing manifest info with collapsible rows for each layer.
   - Nested tables or `<details>` elements display directory contents.
   - A “Raw JSON” toggle reveals the original manifest for advanced users.
5. **Performance Considerations**
   - Retrieve only necessary byte ranges for tar listings to avoid large downloads.
   - Cache layer information per session to speed up navigation.
6. **Testing and Documentation**
   - Add unit tests for address detection, manifest parsing and table generation.
   - Update `docs/api_routes.md` and README with the new explorer capabilities.

## Implementation Steps for Codex
1. **Route Enhancements**
   - Add detection logic in `retrorecon/routes/oci_explorer.py` before calling the existing helper functions.
   - Introduce optional credentials in configuration for private registries.
2. **Data Processing**
   - Expand `registry_explorer.py` with functions to map the manifest to a hierarchical table structure.
   - Provide JSON endpoints returning this structured data.
3. **Frontend Updates**
   - Update `static/oci_explorer.js` and templates to render expandable tables and a JSON toggle.
   - Include indexed menus for layer and file navigation.
4. **Testing**
   - Extend the PyTest suite to cover new routes and detection logic.
   - Regenerate Postman collection and run Stylelint checks for the new UI.
5. **Documentation**
   - Document the feature in this repository’s docs and add examples in the README.

## Task Checklist for Codex
- [ ] Implement registry address detection logic.
- [ ] Produce registry-specific manifest requests and parse results.
- [ ] Build a hierarchical table view with download links.
- [ ] Provide a JSON/table toggle in the UI.
- [ ] Add unit tests and update API documentation.

