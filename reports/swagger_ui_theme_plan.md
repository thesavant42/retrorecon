# Swagger UI Theming Plan

This document outlines a future approach for integrating Swagger UI with the Retrorecon theme selector while keeping the interface readable.

## Goals

- Allow Swagger UI to inherit the same color scheme as the main application when a theme is chosen.
- Avoid overriding core Swagger UI styles that ensure readability.
- Provide a simple mechanism to opt-in or opt-out of theming.

## Proposed Approach

1. **Isolated Style Sheet**
   - Create a dedicated CSS file (e.g. `swagger-theme.css`) containing variable overrides for the standard Swagger UI classes.
   - Include this file only when a Retrorecon theme is active.

2. **Variable Mapping**
   - Map Retrorecon CSS variables (`--bg-color`, `--fg-color`, etc.) to Swagger UI elements using the `:root` selector inside `swagger-theme.css`.
   - Keep fonts and layout rules from the default Swagger UI bundle to preserve usability.

3. **Toggle Support**
   - Add a checkbox in the Preferences menu to enable or disable Swagger UI theming.
   - Store the preference in the user session similar to the existing theme choice.

4. **Testing**
   - Verify that dark and light themes render without losing contrast in form inputs and code blocks.
   - Manually check that disabling the theme falls back to the stock Swagger UI appearance.

This plan keeps the Swagger interface legible while making it visually consistent with the rest of Retrorecon.
