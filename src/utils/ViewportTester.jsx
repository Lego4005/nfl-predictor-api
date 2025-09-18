import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Smartphone, Tablet, Monitor, Maximize2, Minimize2 } from 'lucide-react';

/**
 * ViewportTester - A utility component for testing responsive design
 * Tests viewports from 320px to 768px and beyond
 */
const ViewportTester = ({ children, className = "" }) => {
  const [currentWidth, setCurrentWidth] = useState(window.innerWidth);
  const [currentHeight, setCurrentHeight] = useState(window.innerHeight);
  const [testMode, setTestMode] = useState(null);

  // Predefined test viewports
  const viewports = [
    { name: 'iPhone SE', width: 375, height: 667, icon: Smartphone },
    { name: 'iPhone 12', width: 390, height: 844, icon: Smartphone },
    { name: 'Samsung Galaxy', width: 412, height: 915, icon: Smartphone },
    { name: 'iPad Mini', width: 768, height: 1024, icon: Tablet },
    { name: 'iPad Pro', width: 1024, height: 1366, icon: Tablet },
    { name: 'Desktop', width: 1440, height: 900, icon: Monitor },
  ];

  // Track actual viewport changes
  useEffect(() => {
    const handleResize = () => {
      setCurrentWidth(window.innerWidth);
      setCurrentHeight(window.innerHeight);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Get current breakpoint info
  const getCurrentBreakpoint = () => {
    if (currentWidth < 640) return { name: 'Mobile', color: 'bg-red-500', range: '< 640px' };
    if (currentWidth < 768) return { name: 'Large Mobile', color: 'bg-orange-500', range: '640px - 767px' };
    if (currentWidth < 1024) return { name: 'Tablet', color: 'bg-yellow-500', range: '768px - 1023px' };
    if (currentWidth < 1280) return { name: 'Desktop', color: 'bg-green-500', range: '1024px - 1279px' };
    return { name: 'Large Desktop', color: 'bg-blue-500', range: '≥ 1280px' };
  };

  // Apply test viewport
  const applyTestViewport = (viewport) => {
    if (testMode?.name === viewport.name) {
      // Reset to natural size
      setTestMode(null);
      document.body.style.width = '';
      document.body.style.height = '';
      document.body.style.overflow = '';
    } else {
      setTestMode(viewport);
      document.body.style.width = `${viewport.width}px`;
      document.body.style.height = `${viewport.height}px`;
      document.body.style.overflow = 'auto';
    }
  };

  const breakpoint = getCurrentBreakpoint();

  if (process.env.NODE_ENV === 'production') {
    // Don't render in production
    return children;
  }

  return (
    <div className={className}>
      {/* Viewport Info Panel */}
      <Card className="fixed top-4 right-4 z-50 w-80 shadow-xl border-2 bg-background/95 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm">Viewport Tester</h3>
            <Badge className={`${breakpoint.color} text-white text-xs`}>
              {breakpoint.name}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Current Size Info */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Current Size:</span>
              <div className="font-mono">{currentWidth} × {currentHeight}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Range:</span>
              <div className="font-mono">{breakpoint.range}</div>
            </div>
          </div>

          {/* Test Mode Indicator */}
          {testMode && (
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-md">
              <div className="text-xs font-medium text-blue-700 dark:text-blue-300">
                Testing: {testMode.name} ({testMode.width}×{testMode.height})
              </div>
            </div>
          )}

          {/* Viewport Test Buttons */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-muted-foreground">Test Viewports:</div>
            <div className="grid grid-cols-2 gap-1">
              {viewports.map((viewport) => (
                <Button
                  key={viewport.name}
                  variant={testMode?.name === viewport.name ? "default" : "outline"}
                  size="sm"
                  onClick={() => applyTestViewport(viewport)}
                  className="justify-start text-xs h-8"
                >
                  <viewport.icon className="w-3 h-3 mr-1" />
                  {viewport.name}
                </Button>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setTestMode(null);
                document.body.style.width = '';
                document.body.style.height = '';
                document.body.style.overflow = '';
              }}
              className="flex-1 text-xs h-8"
            >
              <Maximize2 className="w-3 h-3 mr-1" />
              Reset
            </Button>
          </div>

          {/* Responsive Design Tips */}
          <div className="text-xs text-muted-foreground">
            <div className="font-medium mb-1">Touch Target Guidelines:</div>
            <ul className="space-y-0.5 text-[10px]">
              <li>• Min 44px for touch elements</li>
              <li>• Stack on mobile (&lt; 640px)</li>
              <li>• Horizontal scroll for tabs</li>
              <li>• Mobile-first grid layouts</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      {children}
    </div>
  );
};

// Hook for checking current breakpoint
export const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState('');

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      if (width < 640) setBreakpoint('mobile');
      else if (width < 768) setBreakpoint('sm');
      else if (width < 1024) setBreakpoint('md');
      else if (width < 1280) setBreakpoint('lg');
      else setBreakpoint('xl');
    };

    updateBreakpoint();
    window.addEventListener('resize', updateBreakpoint);
    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  return breakpoint;
};

// Utility for responsive testing
export const debugResponsive = () => {
  if (process.env.NODE_ENV === 'development') {
    console.log({
      viewport: `${window.innerWidth}×${window.innerHeight}`,
      breakpoint: window.innerWidth < 640 ? 'mobile' :
                  window.innerWidth < 768 ? 'sm' :
                  window.innerWidth < 1024 ? 'md' :
                  window.innerWidth < 1280 ? 'lg' : 'xl',
      devicePixelRatio: window.devicePixelRatio,
      orientation: window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
    });
  }
};

export default ViewportTester;