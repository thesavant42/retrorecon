# Dynamic Page and Menu Mapping

This table lists each HTML template in the project alongside the dynamic pattern used to generate identical output. Pages without a custom pattern use the generic `static_html` schema which simply embeds the rendered template.

| Classic Template | Dynamic Schema / Lambda |
|------------------|------------------------|
| _webpack_exploder_form.html | static_html |
| registry_explorer.html | static_html |
| demo.html | static_html |
| fetching.html | static_html |
| help_about.html | help_about_page |
| help_readme.html | static_html |
| index.html | lambda: index() |
| jwt_tools.html | static_html |
| layerslayer.html | static_html |
| oci_base.html | static_html |
| oci_elf.html | static_html |
| oci_error.html | static_html |
| oci_fs.html | static_html |
| oci_hex.html | static_html |
| oci_image.html | static_html |
| oci_index.html | static_html |
| oci_layer.html | static_html |
| oci_overlay.html | static_html |
| oci_repo.html | static_html |
| overview.html | static_html |
| registry_explorer.html | static_html |
| screenshotter.html | screenshotter_page |
| httpolaroid.html | static_html |
| subdomonster.html | subdomonster_page |
| swaggerui.html | static_html |
| text_tools.html | static_html |

## Menu Structure

The main navigation bar consists of four top‑level menus:

| Menu | Submenus |
|------|----------|
| File | New Project, Save Project, Save Project As…, Open Project, Export As (JSON / CSV / MD / XML / TXT), Backup SQL |
| Edit | Bulk Select (all matching / visible / none), Bulk Actions (delete tag / add tag / clear tags), Preferences (background selector, toggle, font options, color palette, opacity slider) |
| Tools | OSINT (Subdomonster, Hindsight, OCI Explorer), Active Recon (Screenshotter, Site2Zip), Utilities (Text Tools, JWT Tools, Webpack Exploder) |
| Help | GitHub Wiki, README, About |
