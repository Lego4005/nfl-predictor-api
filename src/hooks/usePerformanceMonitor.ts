/**
 * Performance monitoring hook for mobile optimization
 * Tracks frame rates, render times, and battery impact
 */

import { useCallback, useRef, useState, useEffect } from 'react';

interface PerformanceMetrics {
  frameRate: number;
  averageFrameTime: number;
  maxFrameTime: number;
  minFrameTime: number;
  renderCount: number;
  memoryUsage?: number;
  batteryLevel?: number;
  thermalState?: string;
}

interface PerformanceEntry {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    frameRate: 60,
    averageFrameTime: 16.67,
    maxFrameTime: 0,
    minFrameTime: Infinity,
    renderCount: 0
  });

  const performanceEntries = useRef<Map<string, PerformanceEntry>>(new Map());
  const frameTimeHistory = useRef<number[]>([]);
  const lastFrameTime = useRef<number>(performance.now());
  const animationFrame = useRef<number | null>(null);

  // Frame rate monitoring
  const measureFrameRate = useCallback(() => {
    const now = performance.now();
    const frameTime = now - lastFrameTime.current;

    frameTimeHistory.current.push(frameTime);

    // Keep only last 60 frames for rolling average
    if (frameTimeHistory.current.length > 60) {
      frameTimeHistory.current.shift();
    }

    const averageFrameTime = frameTimeHistory.current.reduce((sum, time) => sum + time, 0) / frameTimeHistory.current.length;
    const frameRate = 1000 / averageFrameTime;
    const maxFrameTime = Math.max(...frameTimeHistory.current);
    const minFrameTime = Math.min(...frameTimeHistory.current);

    setMetrics(prev => ({
      ...prev,
      frameRate: Math.round(frameRate),
      averageFrameTime: Math.round(averageFrameTime * 100) / 100,
      maxFrameTime: Math.round(maxFrameTime * 100) / 100,
      minFrameTime: Math.round(minFrameTime * 100) / 100,
      renderCount: prev.renderCount + 1
    }));

    lastFrameTime.current = now;
    animationFrame.current = requestAnimationFrame(measureFrameRate);
  }, []);

  // Start performance tracking for a specific operation
  const startTracking = useCallback((name: string) => {
    performanceEntries.current.set(name, {
      name,
      startTime: performance.now()
    });
  }, []);

  // Stop performance tracking and calculate duration
  const stopTracking = useCallback((name: string) => {
    const entry = performanceEntries.current.get(name);
    if (entry) {
      const endTime = performance.now();
      const duration = endTime - entry.startTime;

      performanceEntries.current.set(name, {
        ...entry,
        endTime,
        duration
      });

      // Log slow operations in development
      if (process.env.NODE_ENV === 'development' && duration > 16) {
        console.warn(`Slow operation detected: ${name} took ${duration.toFixed(2)}ms`);
      }
    }
  }, []);

  // Get performance metrics for a specific operation
  const getOperationMetrics = useCallback((name: string) => {
    return performanceEntries.current.get(name);
  }, []);

  // Get all current metrics
  const getMetrics = useCallback(() => {
    return metrics;
  }, [metrics]);

  // Get battery information (if available)
  const updateBatteryInfo = useCallback(async () => {
    if ('getBattery' in navigator) {
      try {
        const battery = await (navigator as any).getBattery();
        setMetrics(prev => ({
          ...prev,
          batteryLevel: Math.round(battery.level * 100)
        }));
      } catch (error) {
        // Battery API not available or permission denied
      }
    }
  }, []);

  // Get memory usage (if available)
  const updateMemoryInfo = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      setMetrics(prev => ({
        ...prev,
        memoryUsage: Math.round(memory.usedJSHeapSize / 1024 / 1024) // MB
      }));
    }
  }, []);

  // Get thermal state (if available on iOS)
  const updateThermalState = useCallback(() => {
    if ('webkitThermalState' in navigator) {
      const thermalState = (navigator as any).webkitThermalState;
      setMetrics(prev => ({
        ...prev,
        thermalState
      }));
    }
  }, []);

  // Performance optimization recommendations
  const getOptimizationRecommendations = useCallback(() => {
    const recommendations: string[] = [];

    if (metrics.frameRate < 30) {
      recommendations.push('Frame rate is critically low. Consider reducing animations or complexity.');
    } else if (metrics.frameRate < 45) {
      recommendations.push('Frame rate is below optimal. Consider performance optimizations.');
    }

    if (metrics.averageFrameTime > 33) {
      recommendations.push('Frame time is high. Consider debouncing updates or reducing DOM operations.');
    }

    if (metrics.memoryUsage && metrics.memoryUsage > 100) {
      recommendations.push('Memory usage is high. Consider memory optimization strategies.');
    }

    if (metrics.batteryLevel && metrics.batteryLevel < 20) {
      recommendations.push('Battery is low. Consider reducing animation frequency or visual effects.');
    }

    if (metrics.thermalState === 'critical') {
      recommendations.push('Device is overheating. Consider reducing performance-intensive operations.');
    }

    return recommendations;
  }, [metrics]);

  // Start monitoring when component mounts
  useEffect(() => {
    animationFrame.current = requestAnimationFrame(measureFrameRate);

    // Update battery and memory info periodically
    const interval = setInterval(() => {
      updateBatteryInfo();
      updateMemoryInfo();
      updateThermalState();
    }, 5000);

    return () => {
      if (animationFrame.current) {
        cancelAnimationFrame(animationFrame.current);
      }
      clearInterval(interval);
    };
  }, [measureFrameRate, updateBatteryInfo, updateMemoryInfo, updateThermalState]);

  return {
    metrics,
    startTracking,
    stopTracking,
    getOperationMetrics,
    getMetrics,
    getOptimizationRecommendations
  };
};