# Desktop Regression Report - AI Experts Section

**Date**: 2025-10-06
**Tester**: Desktop Regression Tester
**Test Environment**: Playwright headless Chrome
**Application URL**: http://localhost:5173

---

## Executive Summary

**CRITICAL ISSUE IDENTIFIED**: The AI Experts section has mobile-first responsive classes that are **breaking the desktop layout**. While the grid is technically rendering, it contains `sm:flex sm:flex-nowrap` classes that should NOT be present on desktop viewports.

---

## Issue #1: Mobile Classes Polluting Desktop Layout

### Problem Description
The AI experts container has Tailwind classes for **all breakpoints** in the same class string, including mobile scroll behavior classes (`sm:flex`, `sm:flex-nowrap`, `sm:overflow-x-auto`) that persist in the DOM even on desktop viewports.

### Evidence

**Classes Found on Container**:
```
grid grid-cols-1 gap-6 max-w-4xl mx-auto
sm:flex sm:flex-nowrap sm:overflow-x-auto sm:snap-x sm:snap-mandatory sm:pb-4 sm:-mx-4 sm:px-4
md:grid md:grid-cols-3
lg:grid-cols-5
md:overflow-x-visible md:snap-none
experts-scroll
```

### Desktop Viewport Test Results (1440px)

**Test**: Desktop layout at 1440px
**Status**: ❌ FAILED

**Error**:
```
expect(containerClass).not.toContain('flex-nowrap');
Expected substring: not "flex-nowrap"
Received string: "grid grid-cols-1 gap-6 max-w-4xl mx-auto sm:flex sm:flex-nowrap..."
```

**Why This Matters**: While the computed style shows `display: grid` (because `lg:` overrides `sm:`), having mobile scroll classes in desktop markup indicates a **responsive design issue** where mobile-first classes aren't being properly scoped.

---

## Issue #2: Container Overflow on Desktop

### Problem Description
Even with grid layout active, the container is **overflowing horizontally** on desktop viewports.

### Evidence from 1440px Test

**Computed Styles**:
```json
{
  "display": "grid",
  "gridTemplateColumns": "153.594px 153.594px 153.609px 153.594px 153.609px",
  "gridAutoFlow": "row",
  "overflowX": "visible",
  "flexDirection": "row",
  "flexWrap": "nowrap",
  "gap": "24px",
  "width": "896px"
}
```

**Overflow Detection**:
- Scroll width: **1014px**
- Client width: **896px**
- **Is overflowing: true** ❌

### What's Wrong
The grid has 5 columns (5 × 153px = 765px) + gaps (4 × 24px = 96px) = **861px minimum width**, but the container is constrained to **896px** due to `max-w-4xl` (896px max-width).

However, the actual scroll width is **1014px**, which suggests:
1. Grid columns are being sized incorrectly
2. Additional padding/margins are adding to the total width
3. The `max-w-4xl` constraint is forcing overflow

---

## Issue #3: Inconsistent Grid Column Counts

### Problem Description
The grid column count doesn't scale properly across desktop breakpoints.

### Evidence from Breakpoint Tests

| Viewport | Breakpoint | Display | Grid Columns | Status |
|----------|------------|---------|--------------|--------|
| 1920px | xl | grid | 5 columns (153.5px each) | ⚠️ Should be more columns |
| 1440px | lg | grid | 5 columns (153.5px each) | ✅ Correct |
| 1024px | md | grid | 5 columns (124.8px each) | ⚠️ Should be 3 columns |
| 768px | sm | grid | 3 columns (224px each) | ⚠️ Should be horizontal scroll |

### Expected vs Actual

**Expected Behavior**:
- `1920px` (xl): 5-6 columns in grid
- `1440px` (lg): 5 columns in grid ✅
- `1024px` (md): 3 columns in grid
- `768px` (sm): Horizontal scroll (flex)

**Actual Behavior**:
- All desktop viewports showing 5 columns
- Column width adjusting but grid-cols staying at 5
- Mobile/tablet breakpoints not switching to proper layouts

---

## Root Cause Analysis

### Problematic Classes

**Current Implementation**:
```html
<div class="grid grid-cols-1 gap-6 max-w-4xl mx-auto
  sm:flex sm:flex-nowrap sm:overflow-x-auto sm:snap-x sm:snap-mandatory sm:pb-4 sm:-mx-4 sm:px-4
  md:grid md:grid-cols-3
  lg:grid-cols-5
  md:overflow-x-visible md:snap-none
  experts-scroll">
```

### Issues Identified

1. **Mobile-first classes not mobile-only**: `sm:` classes apply to ALL viewports ≥640px, including desktop
2. **Max-width constraint**: `max-w-4xl` (896px) is too narrow for 5 columns with proper spacing
3. **Missing xl breakpoint**: No `xl:grid-cols-6` or `2xl:grid-cols-7` for large screens
4. **md breakpoint confusion**: Shows `md:grid-cols-3` but computed shows 5 columns at 1024px

---

## Recommended Fixes

### Fix #1: Remove Mobile Scroll Classes from Desktop

**Bad (Current)**:
```jsx
className="grid grid-cols-1 gap-6 max-w-4xl mx-auto
  sm:flex sm:flex-nowrap sm:overflow-x-auto..."
```

**Good (Should be)**:
```jsx
className="
  grid grid-cols-1 gap-6 max-w-4xl mx-auto
  sm:grid-cols-2 sm:max-w-2xl
  md:grid-cols-3 md:max-w-4xl
  lg:grid-cols-5 lg:max-w-7xl
  xl:grid-cols-6 xl:max-w-screen-xl
  experts-scroll
"
```

### Fix #2: Use Separate Component for Mobile Scroll

Create conditional rendering for mobile vs desktop:

```jsx
{/* Mobile: Horizontal Scroll */}
<div className="sm:hidden flex overflow-x-auto snap-x snap-mandatory pb-4 -mx-4 px-4">
  {experts.map(expert => <ExpertCard key={expert.id} expert={expert} />)}
</div>

{/* Desktop: Grid */}
<div className="hidden sm:grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 gap-6 max-w-7xl mx-auto">
  {experts.map(expert => <ExpertCard key={expert.id} expert={expert} />)}
</div>
```

### Fix #3: Adjust Max-Width for Desktop Grid

Remove or increase `max-w-4xl`:

| Columns | Recommended max-width |
|---------|-----------------------|
| 3 cols  | `max-w-4xl` (896px) |
| 5 cols  | `max-w-7xl` (1280px) |
| 6 cols  | `max-w-screen-xl` (1440px) |

### Fix #4: Add Proper Breakpoint Classes

```jsx
className="
  grid
  gap-6

  /* Mobile: 1 column */
  grid-cols-1 max-w-md

  /* Tablet: 2-3 columns */
  sm:grid-cols-2 sm:max-w-2xl
  md:grid-cols-3 md:max-w-4xl

  /* Desktop: 4-6 columns */
  lg:grid-cols-5 lg:max-w-7xl
  xl:grid-cols-6 xl:max-w-screen-xl

  /* Center container */
  mx-auto
"
```

---

## Screenshots

All screenshots saved to `/home/iris/code/experimental/nfl-predictor-api/tests/`:

1. `desktop-1920-full.png` - Full page at 1920px (xl breakpoint)
2. `desktop-1920.png` - Above-fold at 1920px
3. `desktop-1440.png` - Full page at 1440px (lg breakpoint) - **SHOWS ISSUE**
4. `desktop-1024.png` - Full page at 1024px (md breakpoint)
5. `desktop-768.png` - Full page at 768px (sm breakpoint)
6. `desktop-experts-section.png` - Close-up of AI experts section at 1440px

---

## Test Files

**Regression Test Suite**: `/home/iris/code/experimental/nfl-predictor-api/tests/desktop-regression.spec.ts`

**Run Tests**:
```bash
npx playwright test tests/desktop-regression.spec.ts
```

**Run with UI**:
```bash
npx playwright test tests/desktop-regression.spec.ts --ui
```

---

## Summary of Findings

| Issue | Severity | Impact | Fix Priority |
|-------|----------|--------|--------------|
| Mobile classes on desktop | 🔴 HIGH | Confusion, maintainability | 1 |
| Container overflow | 🟡 MEDIUM | Visual glitch, potential scroll | 2 |
| Inconsistent grid columns | 🟡 MEDIUM | Layout not responsive | 3 |
| Missing xl/2xl breakpoints | 🟢 LOW | Missed optimization for large screens | 4 |

---

## Next Steps

1. ✅ **DO NOT FIX** - Report complete (as requested)
2. ⏭️ Developer should review this report
3. ⏭️ Implement recommended fixes
4. ⏭️ Re-run regression tests to verify
5. ⏭️ Add visual regression tests with Percy/Chromatic

---

## Technical Details

**Browser**: Chromium (Playwright 1.48.x)
**Viewport Sizes Tested**: 768px, 1024px, 1440px, 1920px
**Test Framework**: Playwright
**Reporter**: Line reporter with console output
**Test Duration**: 10.0 seconds
**Tests Passed**: 4/5
**Tests Failed**: 1/5

**Failed Test**:
- `Desktop layout at 1440px` - Contains `flex-nowrap` class on desktop

**Passed Tests**:
- `AI Experts Grid on Desktop at 1920px` - Grid rendering correctly (but with extra classes)
- `Detailed AI Experts Layout Analysis` - Computed styles show overflow
- `Full Page Desktop Screenshot` - Screenshot captured
- `Check Responsive Breakpoints` - All breakpoints tested

---

## Conclusion

The desktop layout is **functional but polluted with mobile-first classes** that don't belong on desktop viewports. While the grid technically works due to Tailwind's responsive override system, the presence of `sm:flex sm:flex-nowrap sm:overflow-x-auto` classes indicates a **responsive design anti-pattern**.

**Recommended Approach**: Separate mobile scroll behavior into a mobile-only component, and use pure grid classes for desktop layouts without mobile class pollution.
