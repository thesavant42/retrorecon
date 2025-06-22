# HTML Template Overview

This document catalogs the HTML templates currently present in the repository and notes what is unique about each one. The list helps identify overlap as we work toward a more unified single-page experience.

| Template | Purpose / Unique Features |
|---------|---------------------------|
| `_webpack_exploder_form.html` | Standalone form for entering a `.js.map` URL and either listing modules or downloading a ZIP of sources. Used inside the Webpack Exploder tool. |
| `dag_explorer.html` | Overlay for browsing OCI image manifests and layer contents. Provides example links and fetches tags or manifests on demand. |
| `fetching.html` | Simple progress page polling the server while CDX data is imported from the Wayback Machine. Redirects back to `/` when finished. |
| `index.html` | Main interface listing URLs. Includes search, pagination, menus and the Notes overlay. Loads other overlays like Text Tools and Screenshotter. |
| `overview.html` | Project Dashboard landing page with counts and subdomains grouped by domain. |
| `jwt_tools.html` | Overlay providing encode/decode operations for JWTs and a cookie jar for storing tokens. |
| `layerslayer.html` | Overlay that fetches a Docker image and lists each layer with filesystem stats using the layerslayer backend. |
| `oci_base.html` | Base layout for all OCI Explorer pages. Handles theming and provides the `.retrorecon-root` wrapper. |
| `oci_elf.html` | Extends `oci_base.html` to show extracted ELF metadata for a binary inside an image. |
| `oci_error.html` | Generic error page used by the OCI Explorer routes to display messages when an image or repository cannot be fetched. |
| `oci_fs.html` | Displays a filtered directory listing of a layer tarball with HTTP vs OCI metadata tabs. |
| `oci_hex.html` | Minimal page for rendering raw binary data in hex format. |
| `oci_image.html` | Shows the HTTP headers and OCI descriptor for an image along with a formatted manifest. Uses tabbed views. |
| `oci_index.html` | Default landing page for the OCI Explorer with basic instructions. |
| `oci_layer.html` | Presents metadata for a specific layer and includes a sorted file list from `crane blob`. |
| `oci_overlay.html` | Lists files extracted from an image using `crane export` and shows HTTP vs OCI views. |
| `oci_repo.html` | Renders repository details including child repos and tags with links to manifests. |
| `registry_explorer.html` | Overlay calling `/registry_explorer` to fetch image information via multiple methods (extension, layerslayer). |
| `screenshotter.html` | Overlay for capturing website screenshots with optional user agent and referrer spoofing. Displays existing shots in a table. |
| `site2zip.html` | Overlay similar to Screenshotter but crawls a URL and packages all assets into a downloadable ZIP. |
| `subdomonster.html` | Overlay that fetches subdomains from crt.sh or VirusTotal, supports tagging and export with pagination. |
| `swaggerui.html` | Embeds Swagger UI for browsing the REST API, applying Retrorecon theming. |
| `text_tools.html` | Overlay for encoding/decoding text using Base64 or URL transforms with copy/save actions. |

## Potential Refactors

Many of the overlays share very similar markup and JavaScript for handling tables, pagination and close buttons. A few refactoring ideas:

- **Create a shared overlay base template.** Extract the repeated `<div class="notes-overlay">` structure and button rows so individual tools only define their unique controls.
- **Consolidate JavaScript utilities.** Screenshotter, Site2Zip and Subdomonster each implement nearly identical functions for loading rows and handling selection. Moving these helpers into a common module will reduce duplication.
- **Reuse table components.** Registry and layerslayer overlays both build resizable tables. Using a single table component or Jinja macro would simplify markup and styling.
- **Progressively enhance index.html.** Loading overlays dynamically via fetch requests would pave the way for a single page application where tools can be swapped in without reloading.

These steps will help unify the experience and make the transition to a single page architecture smoother.
