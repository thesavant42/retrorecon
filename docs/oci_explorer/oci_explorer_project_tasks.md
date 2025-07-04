# OCI Explorer Project Tasks

This document breaks down the user story from issue #560 into actionable tasks for implementing the OCI Explorer in Retrorecon.

## Implementation Steps for Codex
1. **Registry Access and Authentication**
   - Allow browsing of public registries without credentials by handling anonymous authentication automatically.
   - Support optional credentials for private registries and store them securely for the session.
2. **Manifest and Metadata Retrieval**
   - Add routes to fetch manifests and layer details using HTTP range requests so entire images are not downloaded.
   - Display manifest data in collapsible tables with digests and sizes.
3. **Virtual Filesystem Browser**
   - Implement `/fs/<digest>/<path>` to list directories and files as if running `ls -al`.
   - Show permissions, owner, timestamps and size in columns with hyperlinks for deeper navigation.
   - Provide a safe text or hex viewer with a download button for each file.
4. **Search and Indexing**
   - Index file and directory names plus user tags for fast keyword searches.
   - Expose a search box that filters the virtual filesystem view.
5. **Bookmarks and Tagging**
   - Enable bookmarking of registries, images and tags using existing annotation modules.
   - Allow saved bookmarks to be recalled from the interface.
6. **Layer and File Downloads**
   - Offer buttons to download entire layers or individual files via ranged reads with a lookback window.
7. **Performance and Caching**
   - Cache partial tar data so repeated navigation is fast and comparable to https://oci.dag.dev/.
8. **UI Integration**
   - Extend the current `oci_explorer` overlay or create new templates as needed.
   - Ensure metadata tables can be collapsed and progress indicators show during fetches.
9. **Documentation and Testing**
   - Document new routes in `docs/api_routes.md` and update the README feature list.
   - Add unit tests for manifest retrieval, filesystem browsing and downloads.
   - Regenerate the Postman collection when routes are finalized.

## Task Checklist for Codex
- [ ] Implement registry authentication handling.
- [ ] Create manifest and layer retrieval routes with HTTP range support.
- [ ] Build `/fs/<digest>/<path>` browsing with `ls -al` style output.
- [ ] Provide safe viewers and download buttons for files.
- [ ] Index file names and tags for keyword search.
- [ ] Add bookmarking capabilities tied into existing annotations.
- [ ] Support partial and full layer downloads.
- [ ] Cache partial tar data for quick navigation.
- [ ] Update templates and overlays for the new UI elements.
- [ ] Write unit tests and regenerate API documentation.
