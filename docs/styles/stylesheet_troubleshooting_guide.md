# RetroRecon Stylesheet Troubleshooting Guide

## Overview
This guide documents the major stylesheet issues encountered in RetroRecon and their solutions. Use this as a reference for diagnosing and fixing similar problems.

## Critical Issues Fixed

### Issue #1: Git Pull Commands in Launch Scripts
**Problem:** Launch scripts automatically pulled from git, potentially overwriting local changes.

**Symptoms:**
- Local modifications lost on app startup
- Unexpected code reversions
- Loss of agentic control over repository

**Files Affected:**
- `launch_app.bat` (line 14)
- `launch_app.sh` (line 5)

**Solution:**
```bash
# Before (problematic)
git pull

# After (safe)
# git pull - removed to prevent overwriting local changes
```

**Prevention:** Always comment out or remove automatic git operations in launch scripts.

---

### Issue #2: Broken Background Image CSS Selectors
**Problem:** Background images not displaying due to incorrect CSS selector scoping.

**Symptoms:**
- Background images not visible despite being selected
- Theme selection working but backgrounds not applying
- CSS rules targeting non-existent DOM structure

**Files Affected:**
- `static/base.css` (lines 1675-1684)

**Root Cause:**
```css
/* BROKEN - body is not a child of .retrorecon-root */
.retrorecon-root body.has-background-image {
  background-image: var(--background-image-url);
}
```

**Solution:**
```css
/* FIXED - body is a top-level element */
body.has-background-image {
  background-repeat: no-repeat;
  background-position: center center;
  background-attachment: fixed;
  background-size: cover;
  background-image: var(--background-image-url);
}

body.bg-hidden {
  background-image: none !important;
}
```

**Key Insight:** Background images are applied to the `body` element, which is never a child of `.retrorecon-root`. This requires an exception to the scoping rules.

---

### Issue #3: Massive CSS Duplications in Theme Files
**Problem:** Theme files contained complete copies of rules from base.css instead of just overrides.

**Symptoms:**
- Extremely large theme files
- Maintenance nightmares when changing base styles
- Inconsistent styling across themes
- Performance issues due to redundant CSS

**Files Affected:**
- `static/themes/theme-neon.css` (lines 150-325)

**Example Problem:**
```css
/* WRONG - Complete duplication from base.css */
.retrorecon-root .tag-pill {
  display: inline-block;        /* Duplicated layout rule */
  padding: 1px 4px;            /* Duplicated layout rule */
  background: var(--bg-color);  /* Theme-specific override */
  opacity: 1;                   /* Duplicated layout rule */
  border-radius: 10px;          /* Duplicated layout rule */
  /* ... 50+ more duplicated rules ... */
}
```

**Solution:**
```css
/* CORRECT - Only theme-specific overrides */
.retrorecon-root .search-history .tag-pill {
  background: linear-gradient(135deg, #ff2caf, #6a4cff);
  border-radius: 0;
}

.retrorecon-root .pagination {
  font-size: 15px;
  margin: 1em;
  gap: 0.6em;
}
```

**Result:** Reduced theme-neon.css from 342 lines to ~60 lines by removing 150+ lines of duplications.

---

### Issue #4: CSS Scoping Violations
**Problem:** Component CSS files used global selectors, breaking encapsulation.

**Symptoms:**
- CSS conflicts between components
- Styles bleeding outside intended scope
- Unpredictable styling behavior

**Files Affected:**
- `static/oci.css` (lines 2-4)

**Problem:**
```css
/* WRONG - Global scope breaks encapsulation */
:root {
  color-scheme: light dark;
}
```

**Solution:**
```css
/* CORRECT - Scoped to component */
.retrorecon-root {
  color-scheme: light dark;
  /* other component styles */
}
```

---

### Issue #5: Cached CSS File Pollution
**Problem:** Browser caching created duplicate CSS files in subdirectories.

**Symptoms:**
- Mysterious CSS conflicts
- Styles not updating after changes
- Duplicate files in `static/127.0.0.1%3A5000/` directories

**Files Affected:**
- `static/127.0.0.1%3A5000/static/base.css`
- `static/127.0.0.1%3A5000/static/themes/`

**Solution:**
```bash
# Windows
Remove-Item -Path "static\*%*" -Recurse -Force

# Linux/Mac  
rm -rf static/*%*
```

**Prevention:** Regular cleanup of static directory subdirectories with encoded characters.

## Diagnostic Procedures

### Background Images Not Working
1. **Check CSS Selector:**
   ```css
   /* Should be this (global) */
   body.has-background-image { ... }
   
   /* NOT this (scoped) */
   .retrorecon-root body.has-background-image { ... }
   ```

2. **Verify HTML Structure:**
   - Check if `has-background-image` class is added to `<body>`
   - Verify `--background-image-url` CSS variable is set

3. **Browser Dev Tools:**
   ```javascript
   // Check if background image is loaded
   console.log(document.body.classList);
   console.log(getComputedStyle(document.body).backgroundImage);
   ```

### Theme Issues
1. **Check for Duplications:**
   - Theme files should be small (< 100 lines typically)
   - Look for complete rule blocks copied from base.css
   - Verify only color/font/spacing overrides exist

2. **Verify CSS Variables:**
   ```css
   /* Variables should be in :root */
   :root {
     --theme-bg: #000;
     --theme-text: #fff;
   }
   ```

3. **Test Theme Switching:**
   - Load different themes
   - Check if styles change appropriately
   - Verify no layout shifts occur

### Scoping Issues
1. **Search for Unscoped Rules:**
   ```bash
   # Find rules not starting with .retrorecon-root
   grep -n "^[^.].*{" static/*.css
   ```

2. **Check for Global Selectors:**
   ```bash
   # Find :root selectors in non-base files
   grep -n ":root" static/themes/*.css static/tools.css static/chat.css
   ```

### Performance Issues
1. **Check File Sizes:**
   ```bash
   # Large theme files indicate duplications
   ls -la static/themes/
   ls -la static/*.css
   ```

2. **Audit CSS Loading:**
   - Check network tab in dev tools
   - Look for duplicate CSS requests
   - Verify caching is working correctly

## Testing Procedures

### Complete CSS Health Check
```bash
# 1. Clear cached files
Remove-Item -Path "static\*%*" -Recurse -Force

# 2. Run linting
npm --prefix frontend run lint

# 3. Audit CSS
python scripts/audit_css.py > reports/css_audit.json

# 4. Check inline styles
node frontend/scripts/check_inline_styles.js
```

### Background Image Test
1. Start application
2. Open Edit menu → Preferences
3. Try different backgrounds from dropdown
4. Verify images change immediately
5. Test "Show background image" checkbox toggle

### Theme Test
1. Switch between available themes
2. Check all major UI components render correctly
3. Verify no layout shifts occur
4. Test background images with each theme

### Scoping Test
1. Inspect elements in browser dev tools
2. Verify all styles are scoped under `.retrorecon-root`
3. Check no global styles are interfering
4. Test component isolation

## Emergency Recovery

### If All Backgrounds Disappear
1. Check `static/base.css` for `body.has-background-image` selector
2. Verify it's NOT scoped under `.retrorecon-root`
3. Clear browser cache completely
4. Remove any cached CSS files
5. Restart application

### If Themes Break Completely
1. Check theme files are loading (network tab)
2. Verify CSS custom properties are defined
3. Temporarily disable themes to test base styles
4. Check for JavaScript errors in console

### If Layout Completely Breaks
1. Check for global CSS conflicts
2. Verify `.retrorecon-root` scoping
3. Disable theme loading temporarily
4. Check for malformed CSS syntax errors

## Monitoring and Prevention

### Regular Maintenance Checklist
- [ ] Monthly: Clear cached CSS files
- [ ] Before releases: Run full CSS health check
- [ ] After theme changes: Test all backgrounds
- [ ] After base.css changes: Test all themes

### Code Review Checklist
- [ ] New CSS rules are scoped under `.retrorecon-root`
- [ ] Theme files only contain overrides, not duplications
- [ ] No global selectors in component files
- [ ] Background image selectors target `body` correctly

### Automated Monitoring
```bash
# Add to CI/CD pipeline
npm --prefix frontend run lint || exit 1
node frontend/scripts/check_inline_styles.js || exit 1
```

## Resources
- [CSS Maintenance Strategy](css_maintenance_strategy.md)
- [Style Guide](../STYLE_GUIDE.md)
- [CSS Inventory](css_inventory.md)
- [Theme Development Guide](theme_style_guide.md)