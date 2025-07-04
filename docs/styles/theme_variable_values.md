# Theme Variable Values

This table lists CSS custom properties defined in `static/base.css` and the theme files under `static/themes/` as of Step 1 in [issue #639](https://github.com/thesavant42/retrorecon/issues/639). Values are extracted via `scripts/generate_style_report.py`.



## base.css

| Variable | Value |
| -------- | ----- |
| `--color-base` | `#000000` |
| `--color-contrast` | `#ffffff` |
| `--color-accent` | `#8be9fd` |
| `--font-main` | `'Share Tech Mono', 'Consolas', monospace` |
| `--bg-color` | `var(--color-base)` |
| `--bg-rgb` | `0 0 0` |
| `--fg-color` | `var(--color-contrast)` |
| `--accent-color` | `var(--color-accent)` |
| `--panel-opacity` | `0.25` |
| `--radius` | `8px` |
| `--select-bg-color` | `var(--color-base)` |
| `--select-border-color` | `var(--color-contrast)` |
| `--background-color` | `var(--color-base)` |
| `--font-color` | `var(--color-contrast)` |
| `--primary-color` | `var(--color-accent)` |

## terminal-sans-dark.css

| Variable | Value |
| -------- | ----- |
| `--accent-color` | `var(--color-accent)` |
| `--bg-color` | `var(--color-base)` |
| `--bg-rgb` | `34 34 37` |
| `--color-accent` | `#62c4ff` |
| `--color-base` | `#222225` |
| `--color-contrast` | `#e8e9ed` |
| `--fg-color` | `var(--color-contrast)` |
| `--font-main` | `-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol` |
| `--panel-opacity` | `0.9` |
| `--select-bg-color` | `#3f3f44` |
| `--select-border-color` | `var(--color-contrast)` |


## theme-neon.css

| Variable | Value |
| -------- | ----- |
| `--accent-color` | `var(--font-accent)` |
| `--bg-color` | `rgba(0, 0, 0, 0.31)` |
| `--bg-rgb` | `0 0 0` |
| `--border-color` | `rgba(139, 233, 253, 0.4)` |
| `--fg-color` | `var(--font-main)` |
| `--font-accent` | `#8be9fd` |
| `--font-main` | `#fff` |
| `--input-border` | `#8be9fd` |
| `--panel-opacity` | `0.92` |


The above table was generated with `python scripts/generate_style_report.py`. Run that script whenever theme variables change to update both this document and `reports/style_report.html`.
