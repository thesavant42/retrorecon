# Retrorecon Themes Style Guide

This guide provides an overview of the CSS themes shipped with Retrorecon and explains how to make common style changes. The `neon` theme is used as the primary example.

## Theme Overview

Retrorecon's CSS is built around a small set of variables. The base file `static/base.css` defines the default palette:

```css
:root {
  --color-base: #000000;
  --color-contrast: #ffffff;
  --color-accent: #8be9fd;
  --font-main: 'Share Tech Mono', 'Consolas', monospace;

  --bg-color: var(--color-base);
  --bg-rgb: 0 0 0;
  --fg-color: var(--color-contrast);
  --accent-color: var(--color-accent);
  --panel-opacity: 0.25;
}
```

Headings are centered and bold. The main header size is defined around `1.6em`:

```css
.retrorecon-root h1{
  margin: 1.4em 0;
  text-align: center;
  font-size: 1.6em;
  letter-spacing: 0.04em;
  font-weight: bold;
}
```

The `neon` theme (`static/themes/theme-neon.css`) overrides these variables and sets its own font stack:

```css
:root {
  --bg-main: #00000000;
  --bg-panel: rgb(0 0 0 / 0%);
  --font-main: #ffffff;
  --font-accent: #8be9fd;
  --border-color: rgba(139, 233, 253, 0.4);
  --input-bg: rgb(34 39 50 / 0%);
  --input-border: #8be9fd;

  /* compatibility with base styles */
  --bg-color: rgba(0, 0, 0, 0.31);
  --bg-rgb: 0 0 0;
  --panel-opacity: 0.92;
  --fg-color: var(--font-main);
  --accent-color: var(--font-accent);
}

.retrorecon-root {
  background: linear-gradient(180deg, #00000000 0%, #00000000 100%);
  color: var(--font-main);
  font-family: 'Share Tech Mono', 'Consolas', monospace;
}
```

Table rows, buttons and form fields all inherit these colors:

```css
.retrorecon-root .url-row-main.url-result td {
  font-size: 1.2em;
  font-weight: bold;
  color: var(--accent-color);
}

.retrorecon-root input,
.retrorecon-root button,
.retrorecon-root select,
.retrorecon-root textarea {
  background: rgb(255 255 255 / 3%);
  color: var(--font-main);
  border: 1px solid var(--input-border);
  border-radius: 4px;
}
```

## Common Style Tasks

### Changing the Font
1. Open the desired theme file in `static/themes/` (e.g. `theme-neon.css`).
2. Locate the `.retrorecon-root` block and edit the `font-family` property.
3. Save the file and run `npm run lint` to ensure the stylesheet passes linting.

### Changing Font Colors
1. In the same theme file, adjust the CSS variables `--font-main` or `--font-accent` under `:root`.
2. Update any element-specific rules if needed (for example, table row colors).
3. Refresh the page after selecting the modified theme.

### Updating Background Images
1. Place a new image in `static/img/`.
2. Use the **Background** drop-down in the application to select it or POST to `/set_background`.
3. For best results, create images with a 16:9 aspect ratio (1920×1080 or larger). This minimizes tiling artifacts when the image is stretched to fill the viewport.

## Desktop Wallpaper Recommendations

Retrorecon uses `background-size: cover` to display wallpapers. To prevent visible tiling:

- Use a resolution of at least **1920×1080** (Full HD).
- Maintain a **16:9** aspect ratio so the browser can stretch the image without distortion.
- Larger 4K images (3840×2160) work well across multiple monitor sizes.

Place the finalized wallpaper file in `static/img/` and choose it from the menu.

---
This guide helps you understand the key theme variables, fonts and colors used by Retrorecon so you can quickly create or tweak themes.
