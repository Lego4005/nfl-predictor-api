# Mobile Responsiveness Test Plan
## NFL Predictor Platform - Comprehensive Mobile Testing Strategy

**Document Version:** 1.0.0
**Created:** 2025-10-06
**Test Scope:** Mobile responsiveness, viewport behavior, touch interactions, desktop preservation
**Testing Tools:** Playwright, Vitest, Manual QA

---

## Executive Summary

This test plan ensures the NFL Predictor platform delivers a consistent, high-quality experience across all devices while preserving existing desktop functionality. The plan covers viewport breakpoints from 320px (small mobile) to 2560px (ultrawide desktop), with specific focus on sidebar behavior, touch interactions, and layout integrity.

---

## 1. Testing Objectives

### Primary Goals
- Verify mobile responsiveness at all standard breakpoints
- Ensure desktop experience remains unchanged
- Validate touch interactions on mobile/tablet devices
- Prevent layout overflow and shifts
- Maintain accessibility across all viewports
- Ensure consistent behavior across browsers

### Success Criteria
- All viewport breakpoints render correctly
- No horizontal scrolling on mobile devices
- Touch targets meet minimum 44px × 44px requirement
- Desktop layout unchanged (1024px+)
- All automated tests pass
- Manual QA checklist 100% complete

---

## 2. Viewport Breakpoints & Test Targets

### Mobile Viewports
| Device Class | Width | Height | Device Examples | Priority |
|--------------|-------|--------|-----------------|----------|
| Small Mobile | 320px | 568px | iPhone SE, older devices | HIGH |
| Standard Mobile | 375px | 667px | iPhone 12 Mini, Pixel 5 | CRITICAL |
| Large Mobile | 414px | 896px | iPhone 12 Pro Max, Galaxy S21+ | HIGH |

### Tablet Viewports
| Device Class | Width | Height | Device Examples | Priority |
|--------------|-------|--------|-----------------|----------|
| Tablet Portrait | 768px | 1024px | iPad, iPad Air | HIGH |
| Tablet Landscape | 1024px | 768px | iPad horizontal | MEDIUM |
| Large Tablet | 1366px | 1024px | iPad Pro 12.9" | MEDIUM |

### Desktop Viewports (Regression Testing)
| Device Class | Width | Height | Use Case | Priority |
|--------------|-------|--------|----------|----------|
| Small Desktop | 1024px | 768px | Laptop minimum | CRITICAL |
| Standard Desktop | 1440px | 900px | Most common | CRITICAL |
| Large Desktop | 1920px | 1080px | HD displays | HIGH |
| Ultrawide | 2560px | 1440px | Ultrawide monitors | MEDIUM |

---

## 3. Component-Specific Test Cases

### 3.1 Sidebar Component

#### Desktop Behavior (1024px+)
**Expected:** Sidebar remains visible, no changes to existing behavior

**Test Cases:**
```typescript
✓ Sidebar visible by default on desktop
✓ Sidebar width remains 280px
✓ Sidebar navigation links accessible
✓ Hover states work correctly
✓ Active route highlighting functions
✓ Scroll behavior independent from main content
✓ Fixed position maintained
```

**Automated Test Location:** `tests/e2e/desktop-sidebar-preservation.spec.ts`

#### Mobile Behavior (< 1024px)
**Expected:** Sidebar hidden by default, accessible via menu toggle

**Test Cases:**
```typescript
✓ Sidebar hidden on initial load
✓ Menu toggle button visible (top-left or hamburger)
✓ Sidebar slides in from left on toggle
✓ Backdrop/overlay appears when sidebar open
✓ Sidebar dismisses on backdrop click
✓ Sidebar dismisses on navigation selection
✓ Touch swipe gesture closes sidebar
✓ Sidebar width optimized for mobile (280px max)
✓ Z-index prevents content overlap
✓ Animation smooth (< 300ms)
```

**Automated Test Location:** `tests/e2e/mobile-sidebar-behavior.spec.ts`

#### Tablet Behavior (768px - 1023px)
**Expected:** Hybrid behavior based on orientation

**Test Cases:**
```typescript
✓ Portrait: Sidebar hidden by default
✓ Landscape: Sidebar visible (optional requirement)
✓ Consistent toggle behavior
✓ Orientation change handled gracefully
```

---

### 3.2 Navigation & Header

#### All Viewports
**Test Cases:**
```typescript
✓ Header remains sticky on scroll
✓ Logo/branding visible and correctly sized
✓ Navigation items accessible
✓ Dropdown menus work on mobile (touch)
✓ Search functionality (if present) responsive
✓ User menu/profile accessible
✓ Notification badges visible
```

**Mobile-Specific:**
```typescript
✓ Hamburger menu icon visible (< 1024px)
✓ Touch target minimum 44px × 44px
✓ Menu transition smooth
✓ Nested menus expand correctly
✓ Active state clearly indicated
```

---

### 3.3 Game Cards & Lists

#### Desktop (1024px+)
```typescript
✓ Grid layout: 3-4 cards per row
✓ Card spacing consistent
✓ Hover effects functional
✓ All data fields visible
✓ Card shadows/borders render correctly
```

#### Tablet (768px - 1023px)
```typescript
✓ Grid layout: 2-3 cards per row
✓ Cards resize proportionally
✓ Touch interactions replace hover
✓ Data remains readable
```

#### Mobile (< 768px)
```typescript
✓ Single column layout
✓ Cards full-width with margin
✓ Data condensed but readable
✓ Touch targets adequate size
✓ Swipe gestures for additional actions
✓ Vertical spacing prevents mis-taps
```

---

### 3.4 Live Game Updates

#### Real-time Updates
```typescript
✓ Score animations work on all devices
✓ Mobile animations optimized (shorter duration)
✓ WebSocket connections stable on mobile networks
✓ Offline indicator displays on disconnect
✓ Auto-refresh doesn't disrupt user interaction
✓ Battery-efficient on mobile (reduced polling)
```

#### Score Display
**Desktop:**
```typescript
✓ Large score display (font-size: 48px+)
✓ Team logos visible (60px × 60px)
✓ Game metadata (quarter, time) adjacent
```

**Mobile:**
```typescript
✓ Scaled score display (font-size: 32px+)
✓ Team logos visible (40px × 40px)
✓ Game metadata stacked vertically
✓ Minimum readable font: 14px
```

---

### 3.5 Data Tables & Charts

#### Responsive Tables
```typescript
✓ Desktop: Full table width, all columns visible
✓ Tablet: Horizontal scroll for wide tables
✓ Mobile: Card-based layout or priority columns only
✓ Sticky headers on scroll
✓ Sort functionality works on touch devices
✓ Filter controls accessible
```

#### Charts (Recharts/D3)
```typescript
✓ Charts resize to container width
✓ Mobile: Simplified chart legends
✓ Touch interactions for tooltips
✓ Axis labels remain readable (min 12px)
✓ Responsive aspect ratios
```

---

### 3.6 Modals & Overlays

#### All Viewports
```typescript
✓ Modal centers on screen
✓ Backdrop prevents background interaction
✓ Close button accessible (top-right)
✓ Escape key closes modal (desktop)
✓ Swipe-down closes modal (mobile)
```

#### Mobile-Specific
```typescript
✓ Modal max-width: 95vw
✓ Content scrollable if exceeds viewport
✓ Touch targets for actions: 48px × 48px
✓ Bottom sheet style for mobile (optional)
```

---

## 4. Touch Interaction Testing

### Touch Target Sizing
**WCAG 2.1 Level AAA Standard: 44px × 44px minimum**

**Test Matrix:**
| Element Type | Desktop Size | Mobile Size | Touch Area |
|--------------|--------------|-------------|------------|
| Primary Buttons | 40px height | 48px height | 48px × 48px |
| Icon Buttons | 32px × 32px | 44px × 44px | 48px × 48px |
| Navigation Links | 36px height | 44px height | Full width |
| Checkboxes/Radios | 20px × 20px | 24px × 24px | 44px × 44px |
| Toggle Switches | 40px × 24px | 48px × 28px | 56px × 44px |

### Touch Gestures
```typescript
✓ Tap: Single selection/activation
✓ Double-tap: Zoom (disabled for app controls)
✓ Long-press: Context menu (cards)
✓ Swipe-left: Sidebar dismiss
✓ Swipe-right: Sidebar open (optional)
✓ Pinch-zoom: Disabled for UI, enabled for images
✓ Scroll: Smooth, no janky behavior
```

---

## 5. Layout Integrity Tests

### Overflow Prevention
```typescript
✓ No horizontal scroll on any viewport
✓ container max-width: 100vw
✓ Images constrain to parent width
✓ Long text wraps or truncates
✓ Tables scroll horizontally (contained)
✓ Modals fit within viewport
```

### Layout Shifts
**Target: Cumulative Layout Shift (CLS) < 0.1**

```typescript
✓ Images have width/height attributes
✓ Fonts preloaded to prevent FOUT
✓ Skeleton loaders prevent content jump
✓ Ads/dynamic content have reserved space
✓ Lazy-loaded content smooth transition
```

### Spacing & Alignment
```typescript
✓ Consistent padding: mobile (16px), desktop (24px)
✓ Vertical rhythm maintained (8px grid)
✓ Text alignment: left (mobile), varied (desktop)
✓ Card margins scale with viewport
✓ Section spacing proportional
```

---

## 6. Browser & Device Matrix

### Primary Test Targets

#### Desktop Browsers (1920×1080)
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

#### Mobile Browsers
- iOS Safari (iPhone 12, 14, 15)
- Chrome Mobile (Android 11, 12, 13)
- Firefox Mobile (Android)
- Samsung Internet (Galaxy devices)

#### Tablet Browsers
- Safari (iPad Pro, iPad Air)
- Chrome (Android tablets)

### Testing Priority
1. **CRITICAL:** Chrome Mobile (Android), Safari (iOS), Chrome Desktop
2. **HIGH:** Firefox Desktop, Safari Desktop, Edge Desktop
3. **MEDIUM:** Firefox Mobile, Samsung Internet
4. **LOW:** Legacy browsers (IE11 - degraded experience acceptable)

---

## 7. Automated Test Strategy

### 7.1 Playwright E2E Tests

**Test Suite Structure:**
```
tests/e2e/
├── mobile/
│   ├── sidebar-mobile.spec.ts
│   ├── navigation-mobile.spec.ts
│   ├── game-cards-mobile.spec.ts
│   ├── touch-interactions.spec.ts
│   └── layout-mobile.spec.ts
├── tablet/
│   ├── sidebar-tablet.spec.ts
│   └── orientation-changes.spec.ts
├── desktop/
│   ├── sidebar-desktop-preservation.spec.ts
│   ├── layout-desktop-regression.spec.ts
│   └── hover-interactions.spec.ts
├── responsive/
│   ├── viewport-breakpoints.spec.ts
│   ├── layout-integrity.spec.ts
│   └── overflow-prevention.spec.ts
└── cross-device/
    ├── consistency-tests.spec.ts
    └── touch-vs-mouse.spec.ts
```

**Example Test: Sidebar Mobile Behavior**
```typescript
// tests/e2e/mobile/sidebar-mobile.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Mobile Sidebar Behavior', () => {
  test.use({
    viewport: { width: 375, height: 667 },
    isMobile: true,
    hasTouch: true
  });

  test('sidebar hidden by default on mobile', async ({ page }) => {
    await page.goto('/');

    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).not.toBeVisible();
  });

  test('sidebar opens on menu toggle', async ({ page }) => {
    await page.goto('/');

    const menuToggle = page.locator('[data-testid="menu-toggle"]');
    await menuToggle.tap();

    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).toBeVisible();
  });

  test('sidebar closes on backdrop click', async ({ page }) => {
    await page.goto('/');

    // Open sidebar
    await page.locator('[data-testid="menu-toggle"]').tap();

    // Click backdrop
    const backdrop = page.locator('[data-testid="sidebar-backdrop"]');
    await backdrop.tap();

    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).not.toBeVisible();
  });

  test('touch target meets 44px minimum', async ({ page }) => {
    await page.goto('/');

    const menuToggle = page.locator('[data-testid="menu-toggle"]');
    const box = await menuToggle.boundingBox();

    expect(box!.width).toBeGreaterThanOrEqual(44);
    expect(box!.height).toBeGreaterThanOrEqual(44);
  });
});
```

**Example Test: Desktop Preservation**
```typescript
// tests/e2e/desktop/sidebar-desktop-preservation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Desktop Sidebar Preservation', () => {
  test.use({ viewport: { width: 1920, height: 1080 } });

  test('sidebar visible by default on desktop', async ({ page }) => {
    await page.goto('/');

    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).toBeVisible();
  });

  test('sidebar maintains 280px width', async ({ page }) => {
    await page.goto('/');

    const sidebar = page.locator('[data-testid="sidebar"]');
    const box = await sidebar.boundingBox();

    expect(box!.width).toBe(280);
  });

  test('no menu toggle button on desktop', async ({ page }) => {
    await page.goto('/');

    const menuToggle = page.locator('[data-testid="menu-toggle"]');
    await expect(menuToggle).not.toBeVisible();
  });

  test('hover states work correctly', async ({ page }) => {
    await page.goto('/');

    const navLink = page.locator('[data-testid="nav-link"]').first();

    // Get initial background color
    const initialBg = await navLink.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    // Hover
    await navLink.hover();

    // Get hover background color
    const hoverBg = await navLink.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    expect(hoverBg).not.toBe(initialBg);
  });
});
```

**Example Test: Viewport Breakpoints**
```typescript
// tests/e2e/responsive/viewport-breakpoints.spec.ts
import { test, expect } from '@playwright/test';

const BREAKPOINTS = [
  { name: 'Small Mobile', width: 320, height: 568 },
  { name: 'Mobile', width: 375, height: 667 },
  { name: 'Large Mobile', width: 414, height: 896 },
  { name: 'Tablet Portrait', width: 768, height: 1024 },
  { name: 'Tablet Landscape', width: 1024, height: 768 },
  { name: 'Desktop', width: 1440, height: 900 },
  { name: 'Large Desktop', width: 1920, height: 1080 },
  { name: 'Ultrawide', width: 2560, height: 1440 },
];

BREAKPOINTS.forEach(({ name, width, height }) => {
  test(`${name} (${width}×${height}) - no horizontal overflow`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto('/');

    const body = page.locator('body');
    const scrollWidth = await body.evaluate(el => el.scrollWidth);

    // Allow 1px tolerance for rounding
    expect(scrollWidth).toBeLessThanOrEqual(width + 1);
  });

  test(`${name} (${width}×${height}) - readable font sizes`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto('/');

    const textElements = page.locator('p, span, div:not(:has(*))');
    const count = await textElements.count();

    if (count > 0) {
      for (let i = 0; i < Math.min(count, 10); i++) {
        const fontSize = await textElements.nth(i).evaluate(el => {
          const computed = window.getComputedStyle(el);
          return parseInt(computed.fontSize);
        });

        expect(fontSize).toBeGreaterThanOrEqual(14);
      }
    }
  });
});
```

### 7.2 Vitest Component Tests

**Test Focus:** Responsive rendering logic

```typescript
// tests/frontend/components/Sidebar.responsive.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Sidebar from '@/components/Sidebar';

describe('Sidebar Responsive Behavior', () => {
  it('renders mobile sidebar hidden by default', () => {
    // Mock window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(<Sidebar />);

    const sidebar = screen.getByTestId('sidebar');
    expect(sidebar).toHaveClass('hidden', 'md:block');
  });

  it('renders desktop sidebar visible', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1440,
    });

    render(<Sidebar />);

    const sidebar = screen.getByTestId('sidebar');
    expect(sidebar).not.toHaveClass('hidden');
  });
});
```

---

## 8. Manual QA Checklist

### Pre-Test Setup
- [ ] Clear browser cache and cookies
- [ ] Disable browser extensions
- [ ] Use incognito/private mode
- [ ] Test on physical devices (not just emulators)
- [ ] Charge devices to 80%+ battery

### 8.1 Mobile Testing (375×667 - iPhone 12)

#### Initial Load
- [ ] Page loads without errors
- [ ] No horizontal scrolling
- [ ] All images load correctly
- [ ] Fonts render clearly
- [ ] Loading indicators display

#### Navigation
- [ ] Sidebar hidden by default
- [ ] Menu toggle button visible and tappable
- [ ] Sidebar slides in smoothly
- [ ] Navigation links work
- [ ] Active route highlighted
- [ ] Sidebar closes on link tap
- [ ] Backdrop closes sidebar

#### Content
- [ ] Game cards display correctly
- [ ] Scores readable (min 24px)
- [ ] Team logos visible (40px)
- [ ] Touch targets ≥44px
- [ ] Buttons full-width or adequate size
- [ ] Forms usable with keyboard
- [ ] No overlapping elements

#### Interactions
- [ ] Tap responses immediate (<100ms)
- [ ] No double-tap zoom on controls
- [ ] Swipe gestures work
- [ ] Pull-to-refresh disabled (if not desired)
- [ ] Long-press context menus
- [ ] Scroll smooth, no lag

#### Orientation
- [ ] Portrait mode functional
- [ ] Landscape mode functional
- [ ] Orientation change smooth
- [ ] No content cut off
- [ ] Layout adapts correctly

#### Performance
- [ ] Page loads <3 seconds
- [ ] Animations smooth (60fps)
- [ ] No memory leaks
- [ ] Battery drain acceptable
- [ ] Network requests optimized

### 8.2 Tablet Testing (768×1024 - iPad)

#### Portrait Mode
- [ ] Sidebar behavior appropriate
- [ ] 2-column grid for game cards
- [ ] Touch targets adequate
- [ ] Text readable
- [ ] All features accessible

#### Landscape Mode
- [ ] Sidebar visible (or toggleable)
- [ ] 3-column grid for game cards
- [ ] Desktop-like experience
- [ ] Navigation intuitive

### 8.3 Desktop Testing (1920×1080)

#### Regression Tests
- [ ] Sidebar visible by default
- [ ] Sidebar width 280px
- [ ] No menu toggle button
- [ ] Hover states work
- [ ] Click interactions unchanged
- [ ] Layout matches previous version
- [ ] No visual regressions
- [ ] Performance unchanged
- [ ] All features functional
- [ ] Keyboard navigation works

#### Large Screens
- [ ] Content centered or full-width (as designed)
- [ ] Max-width containers prevent over-stretch
- [ ] Images don't pixelate
- [ ] Text remains readable

### 8.4 Cross-Browser Testing

#### Chrome Mobile (Android)
- [ ] All mobile tests pass
- [ ] Address bar auto-hide works
- [ ] Viewport units (vh/vw) correct

#### Safari Mobile (iOS)
- [ ] All mobile tests pass
- [ ] Safe area insets respected
- [ ] Bounce scroll disabled (if desired)
- [ ] Input zoom disabled (font-size ≥16px)

#### Chrome Desktop
- [ ] All desktop tests pass
- [ ] DevTools responsive mode accurate

#### Safari Desktop
- [ ] All desktop tests pass
- [ ] Webkit-specific styles work

#### Firefox Desktop
- [ ] All desktop tests pass
- [ ] Scrollbar styles consistent

### 8.5 Accessibility Testing

#### Screen Reader
- [ ] ARIA labels present
- [ ] Live regions announce updates
- [ ] Navigation keyboard accessible
- [ ] Focus indicators visible
- [ ] Headings properly nested

#### Contrast
- [ ] Text contrast ≥4.5:1 (WCAG AA)
- [ ] Important elements ≥7:1 (AAA)
- [ ] Focus indicators visible

#### Keyboard Navigation
- [ ] Tab order logical
- [ ] Skip links present
- [ ] All interactive elements focusable
- [ ] No keyboard traps

---

## 9. Test Data Requirements

### Mock Data Sets
```typescript
// Test data for consistent testing
export const mockGameData = {
  live_games: [
    {
      game_id: 'test_001',
      home_team: 'Patriots',
      away_team: 'Bills',
      home_score: 21,
      away_score: 14,
      quarter: 3,
      time_remaining: '08:42',
      game_status: 'live'
    },
    // ... more games
  ],
  predictions: [
    {
      matchup: 'BUF @ NE',
      su_pick: 'NE',
      su_confidence: 0.75,
      spread: -3.5,
      ats_pick: 'NE -3.5',
      ats_confidence: 0.68
    },
    // ... more predictions
  ]
};
```

### WebSocket Simulation
```typescript
// Simulate real-time updates
const simulateScoreUpdate = () => ({
  event_type: 'score_update',
  data: {
    game_id: 'test_001',
    home_score: 24,
    away_score: 14,
    timestamp: new Date().toISOString()
  }
});
```

---

## 10. Performance Benchmarks

### Target Metrics by Viewport

| Metric | Mobile | Tablet | Desktop |
|--------|--------|--------|---------|
| First Contentful Paint (FCP) | <1.8s | <1.5s | <1.2s |
| Largest Contentful Paint (LCP) | <2.5s | <2.0s | <1.5s |
| Time to Interactive (TTI) | <3.8s | <3.0s | <2.5s |
| Cumulative Layout Shift (CLS) | <0.1 | <0.1 | <0.1 |
| First Input Delay (FID) | <100ms | <100ms | <100ms |
| Total Blocking Time (TBT) | <300ms | <250ms | <200ms |

### Performance Testing Tools
- Lighthouse CI (mobile & desktop audits)
- WebPageTest (real device testing)
- Playwright performance metrics
- Chrome DevTools Performance panel
- React DevTools Profiler

---

## 11. Regression Testing Strategy

### Desktop Preservation Tests
**Critical:** Ensure no degradation of desktop experience

**Test Approach:**
1. **Visual Regression:** Screenshot comparison
   ```typescript
   test('desktop layout unchanged', async ({ page }) => {
     await page.goto('/');
     await expect(page).toHaveScreenshot('desktop-home.png', {
       fullPage: true,
       threshold: 0.1
     });
   });
   ```

2. **Functional Regression:** Behavior verification
   - All existing features work
   - No new bugs introduced
   - Performance maintained
   - Accessibility unchanged

3. **Automated Comparison:**
   - Run full desktop test suite before/after mobile changes
   - Compare test results
   - Flag any failures

### Continuous Integration
```yaml
# .github/workflows/responsive-tests.yml
name: Responsive Testing

on: [pull_request]

jobs:
  mobile-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:mobile

  desktop-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:desktop

  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:visual
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: visual-diff
          path: test-results/
```

---

## 12. Bug Reporting Template

### Title Format
`[MOBILE|TABLET|DESKTOP] [Component] - Brief description`

### Report Template
```markdown
**Environment:**
- Device: [iPhone 12 / iPad Pro / Desktop Chrome]
- Viewport: [375×667]
- Browser: [Safari 15.2]
- OS: [iOS 15.2]

**Steps to Reproduce:**
1. Navigate to /live-games
2. Tap on menu toggle
3. Observe sidebar behavior

**Expected Behavior:**
Sidebar should slide in from left with smooth animation

**Actual Behavior:**
Sidebar appears instantly without animation

**Screenshots/Video:**
[Attach screenshot or recording]

**Console Errors:**
[Paste any console errors]

**Severity:**
[Critical / High / Medium / Low]

**Reproducibility:**
[Always / Sometimes / Rare]

**Additional Notes:**
Issue only occurs on iOS Safari, not Chrome Mobile
```

---

## 13. Test Execution Schedule

### Phase 1: Automated Testing (Week 1)
- Day 1-2: Set up viewport tests
- Day 3-4: Component responsive tests
- Day 5: Performance benchmarks

### Phase 2: Manual QA (Week 2)
- Day 1-2: Mobile devices (iOS & Android)
- Day 3: Tablet devices
- Day 4: Desktop browsers
- Day 5: Bug fixing and retesting

### Phase 3: User Acceptance (Week 3)
- Day 1-3: Beta testing with real users
- Day 4-5: Feedback incorporation and final fixes

---

## 14. Test Environment Setup

### Local Development
```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install --with-deps

# Run responsive tests
npm run test:responsive

# Run with UI mode
npx playwright test --ui

# Run specific viewport
npx playwright test --project=mobile-chrome

# Visual regression baseline
npx playwright test --update-snapshots
```

### Test Scripts (package.json)
```json
{
  "scripts": {
    "test:mobile": "playwright test --project=mobile-chrome --project=mobile-safari",
    "test:tablet": "playwright test --project=tablet-chrome",
    "test:desktop": "playwright test --project=chromium-desktop --project=firefox-desktop",
    "test:responsive": "playwright test tests/e2e/responsive/",
    "test:visual": "playwright test --grep @visual",
    "test:all": "playwright test",
    "test:component": "vitest run tests/frontend/",
    "test:coverage": "vitest run --coverage"
  }
}
```

---

## 15. Success Metrics & KPIs

### Test Coverage
- [ ] 100% of viewport breakpoints tested
- [ ] 100% of interactive components tested
- [ ] 90%+ code coverage for responsive logic
- [ ] 100% of browsers in matrix tested

### Quality Metrics
- [ ] Zero critical bugs
- [ ] <5 medium bugs
- [ ] All automated tests passing
- [ ] Lighthouse score >90 (mobile)
- [ ] Lighthouse score >95 (desktop)

### User Experience
- [ ] <2% bounce rate increase
- [ ] >95% mobile usability (Google)
- [ ] <0.5s interaction delay
- [ ] Zero horizontal scroll complaints

---

## 16. Maintenance & Updates

### Ongoing Testing
- Run responsive tests on every PR
- Visual regression on weekly basis
- Manual QA for major releases
- Real device testing quarterly

### Test Updates
- Update breakpoints as device trends change
- Add new devices to test matrix annually
- Review touch target sizes (WCAG updates)
- Performance budget adjustments

### Documentation
- Update test plan for new features
- Document new test cases
- Maintain test data sets
- Archive test results

---

## 17. Tools & Resources

### Testing Tools
- **Playwright** - E2E testing with device emulation
- **Vitest** - Component unit testing
- **Lighthouse CI** - Performance & accessibility audits
- **Percy/Chromatic** - Visual regression testing
- **BrowserStack** - Real device testing
- **Responsively** - Multi-viewport preview tool

### Design Tools
- **Figma/Sketch** - Design reference
- **Chrome DevTools** - Device emulation
- **Responsively App** - Multi-device preview
- **viewport-resizer** - Browser extension

### Documentation
- [Playwright Docs](https://playwright.dev/docs/intro)
- [Vitest Docs](https://vitest.dev/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Responsive Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)

---

## 18. Appendix

### A. CSS Breakpoint Reference
```css
/* Mobile First Approach */
/* Base: 0-639px (mobile) */

/* Small mobile */
@media (max-width: 374px) { }

/* Tablet */
@media (min-width: 640px) { }
@media (min-width: 768px) { }

/* Desktop */
@media (min-width: 1024px) { }
@media (min-width: 1280px) { }
@media (min-width: 1536px) { }
```

### B. Touch Target Sizing Guide
```css
/* Minimum touch targets */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  /* Add padding for visual size vs. touch area */
  padding: 12px 16px;
}

/* Ensure adequate spacing */
.touch-list-item {
  margin-bottom: 8px; /* Prevent mis-taps */
}
```

### C. Common Responsive Patterns

**Sidebar Pattern:**
```tsx
// Hidden on mobile, visible on desktop
<aside className="hidden lg:block lg:w-280 ...">

// Mobile toggle
<button className="lg:hidden" onClick={toggleSidebar}>
```

**Grid Pattern:**
```tsx
// 1 column mobile, 2 tablet, 3 desktop
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
```

**Typography Pattern:**
```tsx
// Responsive font sizes
<h1 className="text-2xl sm:text-3xl lg:text-4xl">
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-06 | Mobile Testing Specialist | Initial test plan creation |

---

## Sign-off

**Prepared by:** Mobile Testing Specialist
**Reviewed by:** [QA Lead]
**Approved by:** [Tech Lead]
**Date:** 2025-10-06

---

**Next Steps:**
1. Review and approve test plan
2. Set up automated test infrastructure
3. Begin Phase 1: Automated testing
4. Schedule manual QA sessions
5. Coordinate with development team for fixes
