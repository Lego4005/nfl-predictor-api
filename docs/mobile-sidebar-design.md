# Mobile Sidebar Design Specification
## NFL Predictor API - Mobile-Friendly Navigation Solution

**Version:** 1.0
**Date:** 2025-10-06
**Designer:** Mobile Architecture Designer
**Status:** Design Specification (No Implementation)

---

## Executive Summary

This document specifies a mobile-friendly sidebar solution that preserves the existing desktop sidebar experience while providing an optimized navigation experience for mobile devices. The design employs a progressive enhancement strategy with strict isolation between mobile and desktop implementations.

---

## 1. Design Principles

### 1.1 Core Principles
- **Desktop Preservation:** Zero changes to desktop sidebar (min-width: 769px+)
- **Progressive Enhancement:** Mobile enhancements layer on top, not replace
- **Touch-First:** 44x44px minimum tap targets (iOS Human Interface Guidelines)
- **Performance:** Hardware-accelerated animations, minimal reflows
- **Accessibility:** ARIA landmarks, screen reader support, keyboard navigation

### 1.2 Breakpoint Strategy
```css
/* Desktop: No changes */
@media (min-width: 769px) {
  /* Existing desktop sidebar remains untouched */
}

/* Tablet: Hybrid approach */
@media (min-width: 641px) and (max-width: 768px) {
  /* Collapsible overlay drawer */
}

/* Mobile: Full mobile experience */
@media (max-width: 640px) {
  /* Slide-out drawer with hamburger menu */
}
```

---

## 2. Mobile Navigation Architecture

### 2.1 Recommended Approach: Slide-Out Drawer

**Rationale:**
- Preserves full navigation hierarchy (Platform, Predictions, Teams, Tools)
- Supports nested navigation with expandable sections
- Maintains brand consistency with desktop experience
- Proven pattern in sports apps (ESPN, The Athletic, Yahoo Sports)

**Alternative Considered (Bottom Navigation):**
- Rejected due to limited space for 10+ navigation items
- Would require significant navigation restructuring
- Less suitable for nested menus (AI Council children, Predictions children)

### 2.2 Mobile Sidebar Components

#### A. Hamburger Menu Button
```typescript
// Position: Fixed top-left (replaces collapsed toggle on mobile)
// Size: 44x44px tap target
// Icon: Lucide Menu icon (animated to X when open)
// Z-index: 60 (above overlay, below drawer)
```

#### B. Backdrop Overlay
```css
/* Semi-transparent overlay when drawer is open */
.mobile-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 50;
  opacity: 0;
  pointer-events: none;
  transition: opacity 300ms ease-out;
}

.mobile-sidebar-overlay.visible {
  opacity: 1;
  pointer-events: auto;
}
```

#### C. Slide-Out Drawer
```css
/* Drawer container */
.mobile-sidebar-drawer {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height for iOS */
  width: 280px; /* Slightly narrower than desktop 288px */
  max-width: 85vw; /* Ensure swipe-to-dismiss zone */
  background: hsl(var(--card));
  border-right: 1px solid hsl(var(--glass-border));
  z-index: 60;
  transform: translateX(-100%);
  transition: transform 300ms cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
}

.mobile-sidebar-drawer.visible {
  transform: translateX(0);
}
```

---

## 3. Component Structure

### 3.1 File Architecture (Modular Approach)

```
src/
├── components/
│   └── layout/
│       ├── AppSidebar.tsx           # Existing desktop sidebar (NO CHANGES)
│       ├── MobileSidebar.tsx        # NEW: Mobile-specific sidebar
│       ├── MobileHamburger.tsx      # NEW: Hamburger menu button
│       └── SidebarWrapper.tsx       # NEW: Responsive wrapper component
├── styles/
│   ├── index.css                    # Existing styles (minimal changes)
│   ├── mobile.css                   # Existing mobile utilities (enhance)
│   └── mobile-sidebar.css           # NEW: Mobile sidebar-specific styles
└── hooks/
    └── useMobileSidebar.ts          # NEW: Mobile sidebar state management
```

### 3.2 Responsive Wrapper Pattern

```typescript
// SidebarWrapper.tsx
import { useMediaQuery } from '@/hooks/useMediaQuery';
import AppSidebar from './AppSidebar';
import MobileSidebar from './MobileSidebar';

export function SidebarWrapper({ currentPage, onNavigate, ... }) {
  const isMobile = useMediaQuery('(max-width: 768px)');

  // Desktop: Use existing AppSidebar (unchanged)
  if (!isMobile) {
    return <AppSidebar {...props} />;
  }

  // Mobile: Use new MobileSidebar
  return <MobileSidebar {...props} />;
}
```

**Benefits:**
- Zero risk to desktop implementation
- Clean separation of concerns
- Easy A/B testing
- Independent mobile feature development

---

## 4. Mobile-Specific Features

### 4.1 Touch Interactions

#### Swipe Gestures
```typescript
// Swipe-to-open (from left edge)
onTouchStart: (e) => {
  if (e.touches[0].clientX < 20) {
    // Track swipe from edge
  }
}

// Swipe-to-close (from drawer)
onTouchMove: (e) => {
  if (swipeDistance > 50 && swipeVelocity > 0.3) {
    closeSidebar();
  }
}
```

#### Tap Target Optimization
```css
/* All interactive elements */
.mobile-nav-item {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
  touch-action: manipulation; /* Disable double-tap zoom */
}

/* Profile dropdown trigger */
.mobile-profile-button {
  min-height: 56px; /* Larger for important actions */
  padding: 12px;
}
```

### 4.2 Scroll Behavior

```css
/* Prevent body scroll when drawer open */
body.mobile-sidebar-open {
  overflow: hidden;
  position: fixed;
  width: 100%;
}

/* Smooth drawer scroll */
.mobile-sidebar-drawer {
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

/* Sticky header (logo + close button) */
.mobile-sidebar-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: hsl(var(--card));
  border-bottom: 1px solid hsl(var(--glass-border));
}
```

### 4.3 Navigation Sections (Collapsible)

```typescript
// Mobile navigation with collapsible sections
interface MobileNavigationSection {
  title: string;
  items: NavigationItem[];
  defaultExpanded: boolean; // Mobile-specific
  icon?: React.ComponentType; // Section icon for mobile
}

const mobileSections: MobileNavigationSection[] = [
  {
    title: 'Platform',
    defaultExpanded: true, // Always expanded on mobile
    items: [{ id: 'home', label: 'Home', icon: '🏠' }]
  },
  {
    title: 'Predictions',
    defaultExpanded: false, // Collapsed by default to save space
    icon: Gamepad2,
    items: [
      { id: 'games', label: 'Games', icon: '🏈' },
      { id: 'confidence-pool', label: 'Confidence Pool', icon: '🎯' },
      // ... more items
    ]
  }
];
```

---

## 5. Performance Optimizations

### 5.1 Hardware Acceleration

```css
/* Transform-based animations (GPU accelerated) */
.mobile-sidebar-drawer {
  transform: translateX(-100%);
  will-change: transform; /* Hint to browser */
  backface-visibility: hidden; /* Prevent flickering */
}

/* Avoid layout thrashing */
.mobile-sidebar-overlay {
  transform: translateZ(0); /* Force layer creation */
}
```

### 5.2 Lazy Component Loading

```typescript
// Only load mobile sidebar on mobile devices
const MobileSidebar = lazy(() =>
  import('./MobileSidebar').then(module => ({
    default: module.MobileSidebar
  }))
);

// Preload on hover/interaction (optional)
<button
  onMouseEnter={() => import('./MobileSidebar')}
  onTouchStart={() => import('./MobileSidebar')}
>
  Open Menu
</button>
```

### 5.3 Render Optimization

```typescript
// Memoize navigation items
const navigationItems = useMemo(
  () => sections.map(section => ({ ...section, items: [...] })),
  [sections]
);

// Virtual scrolling for large lists (optional)
import { FixedSizeList } from 'react-window';
```

---

## 6. CSS Architecture

### 6.1 Isolation Strategy

```css
/* mobile-sidebar.css - Mobile-only styles */
@media (max-width: 768px) {
  /* Scope all mobile sidebar styles */
  .mobile-sidebar-container { ... }
  .mobile-sidebar-drawer { ... }
  .mobile-sidebar-overlay { ... }

  /* Hide desktop sidebar */
  .app-sidebar-desktop {
    display: none !important;
  }
}

/* Desktop protection */
@media (min-width: 769px) {
  /* Ensure mobile components never render */
  .mobile-sidebar-container,
  .mobile-hamburger-button {
    display: none !important;
  }
}
```

### 6.2 Utility Classes (Extend mobile.css)

```css
/* Add to src/styles/mobile.css */

/* Touch-friendly spacing */
.mobile-nav-spacing {
  padding: 8px 16px;
  gap: 12px;
}

/* Safe area insets (iOS notch/island) */
.mobile-sidebar-safe {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
}

/* Prevent text selection on tap */
.mobile-no-select {
  -webkit-user-select: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
```

---

## 7. Accessibility Considerations

### 7.1 ARIA Landmarks

```jsx
<nav
  aria-label="Mobile navigation"
  role="navigation"
  aria-hidden={!isOpen}
>
  <button
    aria-label="Close navigation menu"
    aria-expanded={isOpen}
    onClick={closeSidebar}
  >
    <X />
  </button>
</nav>
```

### 7.2 Focus Management

```typescript
// Trap focus within drawer when open
useEffect(() => {
  if (isOpen) {
    const drawer = drawerRef.current;
    const focusableElements = drawer.querySelectorAll(
      'a, button, input, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus first element when opened
    firstElement?.focus();

    // Trap focus within drawer
    const handleTab = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    drawer.addEventListener('keydown', handleTab);
    return () => drawer.removeEventListener('keydown', handleTab);
  }
}, [isOpen]);
```

### 7.3 Keyboard Navigation

```typescript
// Escape key to close drawer
useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && isOpen) {
      closeSidebar();
    }
  };

  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [isOpen]);
```

---

## 8. State Management

### 8.1 Custom Hook Pattern

```typescript
// useMobileSidebar.ts
import { useState, useCallback, useEffect } from 'react';

interface UseMobileSidebarReturn {
  isOpen: boolean;
  openSidebar: () => void;
  closeSidebar: () => void;
  toggleSidebar: () => void;
}

export function useMobileSidebar(): UseMobileSidebarReturn {
  const [isOpen, setIsOpen] = useState(false);

  const openSidebar = useCallback(() => {
    setIsOpen(true);
    // Prevent body scroll
    document.body.classList.add('mobile-sidebar-open');
  }, []);

  const closeSidebar = useCallback(() => {
    setIsOpen(false);
    // Restore body scroll
    document.body.classList.remove('mobile-sidebar-open');
  }, []);

  const toggleSidebar = useCallback(() => {
    isOpen ? closeSidebar() : openSidebar();
  }, [isOpen, openSidebar, closeSidebar]);

  // Close on route change (optional)
  useEffect(() => {
    return () => {
      if (isOpen) closeSidebar();
    };
  }, [location.pathname]);

  return { isOpen, openSidebar, closeSidebar, toggleSidebar };
}
```

### 8.2 Context Provider (Alternative)

```typescript
// MobileSidebarContext.tsx
const MobileSidebarContext = createContext<UseMobileSidebarReturn | null>(null);

export function MobileSidebarProvider({ children }: { children: ReactNode }) {
  const sidebar = useMobileSidebar();

  return (
    <MobileSidebarContext.Provider value={sidebar}>
      {children}
    </MobileSidebarContext.Provider>
  );
}

export function useMobileSidebarContext() {
  const context = useContext(MobileSidebarContext);
  if (!context) {
    throw new Error('useMobileSidebarContext must be used within MobileSidebarProvider');
  }
  return context;
}
```

---

## 9. Animation Specifications

### 9.1 Drawer Slide Animation

```css
/* Drawer entrance */
@keyframes slideInFromLeft {
  from {
    transform: translateX(-100%);
    opacity: 0.8;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.mobile-sidebar-drawer.entering {
  animation: slideInFromLeft 300ms cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* Drawer exit */
@keyframes slideOutToLeft {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(-100%);
    opacity: 0.8;
  }
}

.mobile-sidebar-drawer.exiting {
  animation: slideOutToLeft 250ms cubic-bezier(0.4, 0, 1, 1) forwards;
}
```

### 9.2 Overlay Fade

```css
.mobile-sidebar-overlay {
  transition: opacity 300ms ease-out;
}

.mobile-sidebar-overlay.visible {
  opacity: 1;
}
```

### 9.3 Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  .mobile-sidebar-drawer,
  .mobile-sidebar-overlay {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
```

---

## 10. Component Specifications

### 10.1 MobileHamburger Component

```typescript
interface MobileHamburgerProps {
  isOpen: boolean;
  onToggle: () => void;
  className?: string;
}

export function MobileHamburger({ isOpen, onToggle, className }: MobileHamburgerProps) {
  return (
    <button
      type="button"
      className={classNames(
        'mobile-hamburger-button',
        'fixed top-4 left-4 z-60',
        'w-11 h-11', // 44px tap target
        'bg-card border border-glass-border',
        'rounded-xl shadow-lg',
        'flex items-center justify-center',
        'transition-all duration-200',
        'hover:bg-muted active:scale-95',
        className
      )}
      onClick={onToggle}
      aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
      aria-expanded={isOpen}
    >
      {isOpen ? (
        <X className="w-5 h-5 text-foreground" />
      ) : (
        <Menu className="w-5 h-5 text-foreground" />
      )}
    </button>
  );
}
```

### 10.2 MobileSidebar Component Structure

```typescript
interface MobileSidebarProps {
  currentPage: string;
  onNavigate: (pageId: string) => void;
  sections: NavigationSection[];
}

export function MobileSidebar({ currentPage, onNavigate, sections }: MobileSidebarProps) {
  const { isOpen, closeSidebar } = useMobileSidebar();
  const drawerRef = useRef<HTMLDivElement>(null);

  return (
    <div className="mobile-sidebar-container">
      {/* Overlay */}
      <div
        className={classNames(
          'mobile-sidebar-overlay',
          isOpen && 'visible'
        )}
        onClick={closeSidebar}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        ref={drawerRef}
        className={classNames(
          'mobile-sidebar-drawer',
          isOpen && 'visible'
        )}
        aria-hidden={!isOpen}
      >
        {/* Sticky Header */}
        <div className="mobile-sidebar-header">
          <div className="flex items-center justify-between p-4">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary/20 rounded-lg">
                <span className="text-primary">🏈</span>
              </div>
              <div>
                <h1 className="font-bold text-sm">PickIQ</h1>
                <p className="text-xs text-muted-foreground">NFL Analytics</p>
              </div>
            </div>

            {/* Close button */}
            <button
              onClick={closeSidebar}
              className="w-11 h-11 rounded-xl hover:bg-muted"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Content */}
        <div className="p-4 space-y-4">
          {sections.map((section, idx) => (
            <MobileNavigationSection
              key={idx}
              section={section}
              currentPage={currentPage}
              onNavigate={(pageId) => {
                onNavigate(pageId);
                closeSidebar(); // Auto-close on navigation
              }}
            />
          ))}
        </div>

        {/* Sticky Footer (Profile) */}
        <div className="sticky bottom-0 p-4 border-t border-glass-border bg-card">
          <SidebarProfile isCollapsed={false} />
        </div>
      </aside>
    </div>
  );
}
```

---

## 11. Testing Recommendations

### 11.1 Device Testing Matrix

| Device Category | Screen Size | Test Scenarios |
|-----------------|-------------|----------------|
| iPhone SE       | 375x667     | Small screen, swipe gestures, safe area |
| iPhone 14 Pro   | 393x852     | Dynamic Island, notch, safe area insets |
| iPhone 14 Pro Max | 430x932   | Large screen, one-handed use |
| iPad Mini       | 744x1133    | Tablet breakpoint (641-768px) |
| Android (Pixel) | 412x915     | Material Design patterns |
| Android (Galaxy) | 360x740    | Compact Android device |

### 11.2 Interaction Testing

```typescript
// Test cases for mobile sidebar
describe('MobileSidebar', () => {
  it('opens on hamburger button click', () => {
    // Test click handler
  });

  it('closes on overlay click', () => {
    // Test overlay dismiss
  });

  it('closes on escape key press', () => {
    // Test keyboard interaction
  });

  it('supports swipe-to-open from left edge', () => {
    // Test touch gesture
  });

  it('supports swipe-to-close', () => {
    // Test drag gesture
  });

  it('traps focus within drawer when open', () => {
    // Test accessibility
  });

  it('prevents body scroll when open', () => {
    // Test scroll lock
  });

  it('auto-closes on navigation', () => {
    // Test navigation behavior
  });
});
```

### 11.3 Performance Testing

```typescript
// Performance benchmarks
const performanceTests = {
  drawerOpenTime: '< 300ms',
  drawerCloseTime: '< 250ms',
  overlayFadeTime: '< 300ms',
  firstPaint: '< 100ms',
  interactionReady: '< 500ms',
  fps: '> 55 fps' // Target 60fps
};
```

---

## 12. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `useMobileSidebar` hook
- [ ] Create `useMediaQuery` hook (if not exists)
- [ ] Set up `mobile-sidebar.css` stylesheet
- [ ] Create `SidebarWrapper` component

### Phase 2: Mobile Components (Week 1-2)
- [ ] Build `MobileHamburger` component
- [ ] Build `MobileSidebar` drawer component
- [ ] Build `MobileNavigationSection` component
- [ ] Implement overlay and animations

### Phase 3: Interactions (Week 2)
- [ ] Add swipe gesture support
- [ ] Implement focus trap
- [ ] Add keyboard navigation (Escape, Tab)
- [ ] Test scroll lock behavior

### Phase 4: Polish & Testing (Week 2-3)
- [ ] Test on real devices (iOS, Android)
- [ ] Optimize animations (60fps target)
- [ ] Add reduced motion support
- [ ] Screen reader testing
- [ ] Performance profiling

### Phase 5: Integration (Week 3)
- [ ] Integrate into `PickIQApp.tsx`
- [ ] Update layout to use `SidebarWrapper`
- [ ] Cross-browser testing
- [ ] User acceptance testing

---

## 13. Edge Cases & Considerations

### 13.1 Orientation Changes
```typescript
// Handle orientation change
useEffect(() => {
  const handleOrientationChange = () => {
    if (isOpen && window.innerWidth > 768) {
      closeSidebar(); // Close if rotated to desktop size
    }
  };

  window.addEventListener('orientationchange', handleOrientationChange);
  return () => window.removeEventListener('orientationchange', handleOrientationChange);
}, [isOpen]);
```

### 13.2 iOS Safari Bounce
```css
/* Prevent iOS Safari bounce on drawer */
.mobile-sidebar-drawer {
  overscroll-behavior: contain;
}

/* Lock body scroll */
body.mobile-sidebar-open {
  position: fixed;
  overflow: hidden;
  width: 100%;
}
```

### 13.3 Android Navigation Bar
```css
/* Account for Android navigation bar */
.mobile-sidebar-drawer {
  padding-bottom: env(safe-area-inset-bottom);
}
```

### 13.4 Slow Network
```typescript
// Show loading state for lazy-loaded sidebar
<Suspense fallback={<MobileSidebarSkeleton />}>
  <MobileSidebar {...props} />
</Suspense>
```

---

## 14. Metrics & Success Criteria

### 14.1 Performance Metrics
- **Time to Interactive:** < 500ms
- **Drawer Open Animation:** 300ms (60fps)
- **Drawer Close Animation:** 250ms (60fps)
- **JavaScript Bundle Size:** < 15KB (gzipped)
- **CSS Bundle Size:** < 5KB (gzipped)

### 14.2 User Experience Metrics
- **Tap Target Success Rate:** > 95%
- **Swipe Gesture Success Rate:** > 85%
- **Navigation Completion Rate:** > 90%
- **Error Rate:** < 2%

### 14.3 Accessibility Metrics
- **Lighthouse Accessibility Score:** > 95
- **WCAG 2.1 Level AA:** 100% compliance
- **Screen Reader Compatibility:** NVDA, JAWS, VoiceOver

---

## 15. Future Enhancements

### 15.1 Advanced Features (Post-MVP)
- **Search in sidebar:** Quick navigation to pages
- **Recent pages:** Show last 3 visited pages at top
- **Favorites/Pins:** Pin frequently used pages
- **Swipe velocity:** Faster swipe = faster close
- **Drawer width customization:** User preference (narrow/wide)

### 15.2 Experimental Features
- **Bottom sheet variant:** Alternative to side drawer
- **Floating action button:** Quick access to primary actions
- **Gesture hints:** Teach users swipe gestures
- **Haptic feedback:** Vibration on open/close (iOS/Android)

---

## 16. References & Resources

### 16.1 Design Patterns
- [Material Design Navigation Drawer](https://m3.material.io/components/navigation-drawer/overview)
- [iOS Human Interface Guidelines - Navigation](https://developer.apple.com/design/human-interface-guidelines/navigation)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### 16.2 Code Examples
- [Radix UI Dialog](https://www.radix-ui.com/primitives/docs/components/dialog) - Accessible modal patterns
- [Headless UI Transition](https://headlessui.com/react/transition) - Animation utilities
- [React Spring](https://www.react-spring.dev/) - Advanced animations

### 16.3 Performance Tools
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [WebPageTest](https://www.webpagetest.org/)
- [React DevTools Profiler](https://react.dev/learn/react-developer-tools)

---

## 17. Approval & Sign-Off

**Design Reviewed By:** [Implementation Team]
**Approved By:** [Product Owner]
**Implementation Start Date:** [TBD]
**Target Completion Date:** [TBD]

---

## Appendix A: Component Props API

### MobileSidebar Props
```typescript
interface MobileSidebarProps {
  currentPage: string;           // Current active page ID
  onNavigate: (pageId: string) => void; // Navigation callback
  sections: NavigationSection[]; // Navigation sections
  className?: string;            // Optional custom classes
  onOpen?: () => void;           // Open callback
  onClose?: () => void;          // Close callback
}
```

### MobileHamburger Props
```typescript
interface MobileHamburgerProps {
  isOpen: boolean;               // Drawer open state
  onToggle: () => void;          // Toggle callback
  className?: string;            // Optional custom classes
  variant?: 'default' | 'ghost'; // Style variant
}
```

### useMobileSidebar Return Type
```typescript
interface UseMobileSidebarReturn {
  isOpen: boolean;               // Current open state
  openSidebar: () => void;       // Open drawer
  closeSidebar: () => void;      // Close drawer
  toggleSidebar: () => void;     // Toggle drawer
}
```

---

## Appendix B: CSS Custom Properties

```css
/* Mobile sidebar theme variables */
:root {
  --mobile-sidebar-width: 280px;
  --mobile-sidebar-max-width: 85vw;
  --mobile-sidebar-z-index: 60;
  --mobile-overlay-z-index: 50;
  --mobile-hamburger-z-index: 60;
  --mobile-sidebar-transition: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --mobile-overlay-transition: 300ms ease-out;
}
```

---

**End of Design Specification**
