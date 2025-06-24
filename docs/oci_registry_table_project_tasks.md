# OCI Registry Table Explorer Project Tasks

This document breaks down the design from `docs/oci_registry_table_spec.md` (issue #582) into actionable tasks for implementing the table-formatted OCI registry explorer.

## Implementation Steps for Codex
1. **Route Enhancements**
   - Add address type detection in `retrorecon/routes/registry.py` before invoking existing helper functions.
   - Provide optional registry credentials via configuration for private registries.
2. **Data Processing**
   - Extend `registry_explorer.py` with helpers that convert manifests into hierarchical table structures.
   - Expose JSON endpoints returning these structures for the frontend.
3. **Frontend Updates**
   - Modify `static/registry_explorer.js` and templates to display expandable tables and a toggle for raw JSON.
   - Include indexed menus so users can quickly jump between layers and files.
4. **Testing**
   - Expand the PyTest suite with new route and detection logic coverage.
   - Run Stylelint and regenerate the Postman collection for updated routes.
5. **Documentation**
   - Update `docs/api_routes.md` and the README with explorer details and usage examples.

## Task Checklist for Codex
- [ ] Implement registry address detection logic.
- [ ] Produce registry-specific manifest requests and parse results.
- [ ] Build a hierarchical table view with download links.
- [ ] Provide a JSON/table toggle in the UI.
- [ ] Add unit tests and update API documentation.
