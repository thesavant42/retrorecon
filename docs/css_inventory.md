# Neon Theme CSS Inventory

This document categorizes the rules in `theme-neon.css` and its parent `base.css` as described in [issue #639](https://github.com/thesavant42/retrorecon/issues/639). Each section lists representative selectors and the color roles they use. The goal is to understand how the current styles map to layout, typography and other atomic groups before refactoring. See [Theme Style Guide](theme_style_guide.md) for the broader conventions used across all themes.

## Atomic Categories

| Category | Examples | Color Roles |
| -------- | -------- | ----------- |
| **Layout** | `.panel`, `.card`, `.navbar`, `.search-bar`, grid/flex helpers | background, border |
| **Typography** | `h1`, `h2`, `h3`, `p`, `.db-info` | text, link |
| **Controls & Forms** | `.btn`, `.dropbtn`, `input`, `select`, `.dropdown-content`, `.modal` | bg, text, outline, focus glow |
| **Tables & Lists** | `.url-table`, `.url-row-main`, `.tag-pill`, `.pagination` | stripe, highlight, text |
| **Accents & Icons** | `.accent`, `.badge`, `.icon`, `.tag-pill button` | accent, hover-accent |
| **States** | `:hover`, `:active`, `:disabled`, `.error` | hover, active, disabled, error |
| **Utility** | `.mt-1`, `.d-flex`, `.spinner`, `.hidden` | n/a |

## Layout
- `.panel`, `.card`, `.table-container` – panel backgrounds and borders using `--bg-panel` and `--border-color`.
- `.navbar`, `.controls`, `.menu-row` – flex and grid positioning utilities.
- `.search-bar`, `.search-history-box` – container blocks for forms and history pills.

## Typography
- `h1`, `h2`, `h3` – header colors pulled from `--font-accent`.
- `.db-info`, `.fw-bold` – bold text helpers.
- Base rule `* { color: #ffffff !important; font-size: 14px !important; }` in `base.css` sets universal text defaults.

## Controls & Forms
- `.btn`, `.btn--small`, `.bulk-action-btn` – button styles with border and background variables.
- Form elements `input`, `select`, `textarea` – share `background`, `color` and `border` from `--input-bg` and `--input-border`.
- `.dropdown`, `.dropdown-content`, `.dropbtn` – dropdown menus with focus and hover states.

## Tables & Lists
- `.url-table`, `.url-row-main` – table layout and zebra striping via border colors.
- `.tag-pill`, `.search-history .tag-pill` – pill-shaped list items with accent gradients.
- `.pagination` – numbered list with flex layout and hover transition.

## Accents & Icons
- `.accent` and links (`a`) – use `--font-accent` for highlight color.
- `.tag-pill button` – small delete icon inside pills.
- `.icon` classes in `base.css` for small inline images.

## States
- Hover effects on `.btn`, `.dropbtn`, `.tag-pill` and navigation items adjust `opacity` or background color.
- Active/disabled styles come from pseudo classes on buttons and inputs.

## Utility
- Margin and width helpers such as `.mt-1`, `.ml-05`, `.w-100`.
- `.spinner` animation and `.hidden` display control.

This inventory provides a baseline for future refactoring steps where colors will be normalized into variables and the theme engine will manage them dynamically.

