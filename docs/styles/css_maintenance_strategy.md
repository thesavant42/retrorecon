# CSS Maintenance Strategy for RetroRecon

## Overview
This document outlines the CSS maintenance strategy to prevent future stylesheet issues and maintain agentic control over the RetroRecon repository.

## CSS Architecture Rules

### 1. CSS Scoping Requirements
- **ALL** CSS rules MUST be scoped under `.retrorecon-root`
- **NEVER** use global `:root` selectors in theme or component CSS files
- **Exception:** `body` element styles for background images can be global but must be clearly documented

### 2. File Organization
```
static/
├── base.css                 # Core styles, foundational rules
├── themes/
│   └── theme-*.css         # Theme overrides ONLY, no duplicates
├── chat.css                # Component-specific styles
├── oci.css                 # OCI Explorer specific styles
└── tools.css               # Tools page specific styles
```

### 3. Theme File Rules
- Theme files should **ONLY** contain overrides and customizations
- **NEVER** duplicate entire rule blocks from base.css
- Use CSS custom properties (CSS variables) for theming
- Theme files should be minimal and focused

### 4. Background Image System
- Background images MUST use `body.has-background-image` selector (NOT `.retrorecon-root body.has-background-image`)
- Background image CSS variables should be defined in `:root`
- Background toggle functionality relies on proper selector structure

## Maintenance Procedures

### 1. Before Making CSS Changes
1. **Check current scoping** - Ensure all new rules are scoped under `.retrorecon-root`
2. **Verify no duplications** - Check if the rule already exists in base.css or other files
3. **Test background images** - Ensure changes don't break background functionality
4. **Check all themes** - Verify changes work with all available themes

### 2. Adding New CSS Rules
```css
/* ✅ CORRECT - Properly scoped */
.retrorecon-root .new-component {
  /* styles here */
}

/* ❌ INCORRECT - Global scope */
.new-component {
  /* styles here */
}

/* ❌ INCORRECT - :root in non-base files */
:root {
  --new-variable: value;
}
```

### 3. Theme Development
```css
/* ✅ CORRECT - Theme file with minimal overrides */
.retrorecon-root .component {
  background: var(--theme-bg);
  color: var(--theme-text);
}

/* ❌ INCORRECT - Duplicating entire rule blocks */
.retrorecon-root .component {
  display: flex;           /* Don't duplicate layout rules */
  flex-direction: column;  /* Don't duplicate layout rules */
  background: var(--theme-bg);
  color: var(--theme-text);
}
```

### 4. Regular Maintenance Tasks

#### Monthly Reviews
- [ ] Check for cached CSS files in `static/` subdirectories
- [ ] Audit theme files for unnecessary duplications
- [ ] Verify all CSS rules are properly scoped
- [ ] Test background image functionality

#### Before Releases
- [ ] Run CSS linting: `npm --prefix frontend run lint`
- [ ] Clear any cached CSS files
- [ ] Test all themes with background images
- [ ] Verify mobile responsiveness

### 5. Common Issue Prevention

#### Cached CSS Files
- **Problem:** Browser caching creates duplicate CSS files in subdirectories
- **Prevention:** Regular cleanup of `static/` subdirectories
- **Fix:** `Remove-Item -Path "static\*%*" -Recurse -Force`

#### Scoping Violations
- **Problem:** Global CSS rules break component isolation
- **Prevention:** Always start rules with `.retrorecon-root`
- **Detection:** Search for rules not starting with `.retrorecon-root`

#### Theme Duplications
- **Problem:** Theme files copy entire rule blocks instead of overriding
- **Prevention:** Theme files should only contain property overrides
- **Fix:** Remove duplicate rules, keep only unique theme properties

## Tools and Scripts

### CSS Auditing
```bash
# Check for unscoped selectors
npm --prefix frontend run lint

# Audit CSS coverage
python scripts/audit_css.py > reports/css_audit.json

# Check for inline styles (violations)
node frontend/scripts/check_inline_styles.js
```

### Automated Cleanup
```bash
# Remove cached CSS files (Windows)
Remove-Item -Path "static\*%*" -Recurse -Force

# Remove cached CSS files (Linux/Mac)  
rm -rf static/*%*
```

## Emergency Procedures

### If Background Images Stop Working
1. Check if `body.has-background-image` selector exists in base.css
2. Verify the selector is NOT scoped under `.retrorecon-root`
3. Test with browser dev tools by manually adding the class to body
4. Check if cached CSS files are overriding the rules

### If Themes Break
1. Check theme file for rule duplications
2. Verify CSS custom properties are defined in `:root`
3. Ensure theme files only contain overrides, not layout rules
4. Clear browser cache and cached CSS files

### If Scoping Issues Occur
1. Search for rules not starting with `.retrorecon-root`
2. Check for global `:root` selectors in component files
3. Verify component isolation is maintained

## Contact and Resources
- CSS Architecture Documentation: `STYLE_GUIDE.md`
- CSS Inventory: `docs/styles/css_inventory.md`
- Theme Guide: `docs/styles/theme_style_guide.md`
- Agent Patterns: `AGENTS.md` (StyleLintAgent, CSSAuditAgent)