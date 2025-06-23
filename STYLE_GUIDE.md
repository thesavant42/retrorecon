# Retrorecon Style Guide

This document defines CSS guidelines for the Retrorecon project. It has been peer-reviewed to promote consistency across contributions.

## 1. `.retrorecon-root` Container

Every Retrorecon page should wrap its content in a container element with the class `retrorecon-root`:

```html
<div class="retrorecon-root">
  ... page markup ...
</div>
```

All selectors in custom styles should start with `.retrorecon-root` to avoid conflicts when embedding Retrorecon into other sites or when applying multiple themes. Scoping rules this way keeps project styles self-contained.

Page-specific styles may override the `.retrorecon-root` layout when needed. For
example, the OCI Explorer disables the flex layout defined in `base.css` so that
tab labels render side by side. When adjusting the container's `display`
property, ensure that descendant selectors remain scoped under `.retrorecon-root`.

## 2. Selector Naming Conventions

Use a BEM‑style convention for class names. Base components have simple names (e.g. `.btn`, `.input`). Modifiers use a `--` suffix:

- `.btn--primary` – primary action button
- `.btn--secondary` – neutral button
- `.input--error` – input field displaying an error state

This pattern makes it clear which classes modify a base component and keeps selectors predictable.

## 3. Core Element Styles

Global variables define the base palette:

```css
:root {
  --bg-color: #f5f5ef;
  --fg-color: #23230a;
  --accent-color: #1b51a1;
}
```

Key element defaults derived from `static/base.css`:

- `body` uses the colors above, a system font stack, and `line-height: 1.5`.
- `h1` and `h2` are centered with top/bottom margins and bold weight.
- Anchor tags inherit `--accent-color` and show underlines on hover.
- Buttons have `cursor: pointer` and are styled using the `.btn` block with optional modifiers (`.btn--primary`, `.btn--danger`, etc.).
- Hidden elements reuse the `.hidden` utility (`display: none`).
- Spinners animate with a simple `@keyframes spin` rule.

Inputs, dropdowns, and other controls follow the same naming pattern (`.input`, `.dropdown`, `.dropdown--open`). Ensure every rule is scoped under `.retrorecon-root`.

Adhering to these conventions keeps Retrorecon styles clear, maintainable, and easy to extend with additional themes.

## 4. Visual Defaults

New templates should present a clean look by default. Avoid using glow effects
such as `box-shadow` or heavy `text-shadow` unless a design specifically
requires it. Common interface elements &mdash; including buttons, inputs and
table containers &mdash; should have slightly rounded corners using a
`border-radius` of around `4px` to `6px`.

Following these defaults ensures consistency between pages and keeps the
interface simple to theme.
