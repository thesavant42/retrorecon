# Dropdown Style Audit

This document enumerates the drop-down menus, navbar menu sections and other selection inputs found in the UI. It lists their key classes and indicates whether each style is explicitly defined in `static/themes/theme-neon.css`.

| Element | Selector | Theme Styles? |
|---------|----------|---------------|
| File menu | `.dropdown-content#file-menu` | uses base styles |
| Edit menu | `.dropdown-content#edit-menu` | uses base styles |
| Preferences menu | `.dropdown-content#prefs-menu` | uses base styles |
| Tools menu | `.dropdown-content#tools-menu` | **missing** |
| Results per page | `#results-per-page-select` | uses base styles |
| Theme selector | `#theme-select` | uses base styles |
| Background selector | `#background-select` | uses base styles |
| Row tool selector | `.tool-select` | uses base styles |
| Screenshot agent selector | `#screenshot-agent` | uses base styles |

The `theme-neon.css` file only overrides `.dropbtn` and navbar fonts. It lacks specific rules for `.dropdown-content` and menu buttons, causing inconsistent backgrounds in some menus.

