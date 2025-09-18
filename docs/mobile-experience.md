# Mobile Live Game Experience

## Overview

The Mobile Live Game Experience provides a touch-first, immersive interface for viewing NFL games on mobile devices. It features swipe gestures, progressive disclosure UI patterns, and performance optimizations specifically designed for mobile constraints.

## Key Features

### 🏈 Immersive Game Cards
- Full-width cards that feel like mini TVs
- Gradient backgrounds with team colors
- Real-time score updates with haptic feedback
- Auto-switching between live games

### 👆 Touch-First Interactions
- **Swipe Left/Right**: Navigate between stats layers
- **Swipe Up**: Reveal additional details
- **Tap**: Interact with expandable sections
- **Long Press**: Access contextual options
- **Haptic Feedback**: Tactile responses for actions

### 📊 Progressive Disclosure UI
- **Layer 1**: Game Overview (scores, status, time)
- **Layer 2**: AI Predictions (win probability, spread)
- **Layer 3**: Live Odds (multiple sportsbooks)
- **Layer 4**: Field Visualizer (ball position, down/distance)

### ⚡ Performance Optimizations
- Frame rate monitoring (target: 60fps)
- Battery usage optimization
- Memory management
- Thermal state awareness
- Efficient rendering pipeline

## Components

### MobileLiveGameExperience
Main container component that orchestrates the mobile experience.

**Features:**
- Auto-detects mobile devices
- Manages swipe gestures
- Handles live data updates
- Performance monitoring

### TouchOptimizedButton
Enhanced button component with mobile-first design.

**Features:**
- 44px minimum touch targets (iOS guidelines)
- Haptic feedback support
- Long press detection
- Ripple animations
- Accessibility support

### ProgressiveFieldVisualizer
Interactive football field visualization.

**Features:**
- Responsive SVG rendering
- Ball position tracking
- Down and distance indicators
- Team-specific styling
- Mobile-optimized dimensions

### MobileStatsLayer
Progressive disclosure interface for statistics.

**Features:**
- Expandable sections
- Touch-optimized layouts
- Animated transitions
- Data visualization

### SwipeIndicator
Visual cues for available swipe gestures.

**Features:**
- Directional arrows
- Fade-in animations
- Context-aware visibility

## Performance Features

### Frame Rate Monitoring
```typescript
const { metrics, getOptimizationRecommendations } = usePerformanceMonitor();
// Target: 60fps (16.67ms per frame)
// Warning: <45fps
// Critical: <30fps
```

### Battery Optimization
- Reduces animation frequency when battery < 20%
- Thermal throttling when device overheats
- Efficient memory usage patterns
- Smart background processing

### Touch Gestures
```typescript
const { swipeHandlers } = useSwipeGestures({
  onSwipeLeft: () => nextLayer(),
  onSwipeRight: () => prevLayer(),
  threshold: 50, // pixels
  velocity: 0.3  // px/ms
});
```

## Usage

### Basic Integration
```tsx
import MobileLiveGameExperience from './components/MobileLiveGameExperience';

function App() {
  return (
    <MobileLiveGameExperience
      gameId="optional-specific-game"
      className="custom-styles"
    />
  );
}
```

### Auto-Detection
The component automatically detects mobile devices and switches modes:
```typescript
// In App.tsx
useEffect(() => {
  const isMobile = window.innerWidth <= 768 ||
    /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  if (isMobile && mode === 'live') {
    setMode('mobile');
  }
}, []);
```

## Customization

### Themes
```css
/* Custom team colors */
.mobile-card {
  background: linear-gradient(135deg, var(--team-primary), var(--team-secondary));
}

/* Dark mode optimization */
@media (prefers-color-scheme: dark) {
  .mobile-card {
    background: rgba(17, 24, 39, 0.8);
  }
}
```

### Gesture Sensitivity
```typescript
const customSwipeConfig = {
  threshold: 75,    // Higher = less sensitive
  velocity: 0.5,    // Higher = faster swipe required
  preventDefaultScroll: true
};
```

## Accessibility

### Touch Targets
- Minimum 44px x 44px (iOS guideline)
- Visual feedback for all interactions
- High contrast mode support

### Reduced Motion
- Respects `prefers-reduced-motion`
- Fallback static layouts
- Essential animations only

### Screen Readers
- Semantic HTML structure
- ARIA labels and roles
- Live region updates

## Browser Support

### iOS Safari
- Touch events
- Haptic feedback
- Battery API
- Thermal state detection

### Android Chrome
- Touch events
- Vibration API
- Memory API
- Performance monitoring

### Progressive Enhancement
- Fallback for unsupported features
- Graceful degradation
- Core functionality always available

## Performance Metrics

### Target Benchmarks
- **Frame Rate**: 60fps sustained
- **Memory Usage**: <100MB
- **Battery Impact**: <5% per hour
- **Touch Response**: <16ms
- **Animation Smoothness**: 95%+ frames

### Monitoring
```typescript
// Real-time performance tracking
const recommendations = getOptimizationRecommendations();
// Returns array of specific optimization suggestions
```

## Development

### Testing on Mobile
```bash
# Start development server
npm run dev

# Test on device via network
# Access via http://[local-ip]:5173
```

### Performance Profiling
```typescript
// Enable performance monitoring in development
const { startTracking, stopTracking } = usePerformanceMonitor();

startTracking('expensive-operation');
// ... perform operation
stopTracking('expensive-operation');
```

### Debug Mode
```tsx
<MobileLiveGameExperience
  gameId="test-game"
  debugMode={true} // Shows performance metrics
/>
```

## Best Practices

### Animation Guidelines
- Use `transform` and `opacity` for animations
- Avoid animating layout properties
- Prefer 60fps over complex effects
- Implement animation budgets

### Memory Management
- Clean up event listeners
- Debounce frequent updates
- Lazy load non-critical components
- Monitor memory usage

### Touch Interactions
- Provide immediate visual feedback
- Use appropriate touch targets
- Support multi-touch gestures
- Handle edge cases gracefully

## Troubleshooting

### Performance Issues
1. Check frame rate in debug mode
2. Review memory usage
3. Reduce animation complexity
4. Enable thermal throttling

### Touch Problems
1. Verify touch target sizes
2. Check for event conflicts
3. Test on actual devices
4. Review gesture thresholds

### Data Issues
1. Verify WebSocket connection
2. Check network conditions
3. Implement offline fallbacks
4. Monitor data freshness