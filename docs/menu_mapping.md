# Dynamic Page and Menu Mapping

This table lists each HTML template in the project alongside the dynamic pattern used to generate identical output. Pages without a custom pattern use the generic `static_html` schema which simply embeds the rendered template.

| Classic Template | Dynamic Schema / Lambda |
|------------------|------------------------|
| _webpack_exploder_form.html | static_html |
| dag_explorer.html | static_html |
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
| site2zip.html | static_html |
| subdomonster.html | subdomonster_page |
| swaggerui.html | static_html |
| text_tools.html | static_html |

## Menu Structure

The main navigation bar consists of five top‑level menus:

| Menu | Submenus |
|------|----------|
| File | New Database, Open SQLite Database, Rename Database, Load Saved DB, Import JSON Records, Import from Wayback API, Export (Plain Text / Markdown / CSV / JSON / SQLite) |
| Edit | Select All (page), Select All Matching, Delete Selected, Reset Tags, Add Tag |
| Preferences | Theme selector, Background selector, Toggle background image, Font size, Panel opacity |
| Tools | Webpack Exploder, Site2Zip, Text Tools, JWT Tools, ScreenShotter, Subdomonster, Demo, OCI Explorer, Swagger UI |
| Help | README, About |
