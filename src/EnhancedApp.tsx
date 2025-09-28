import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { NavigationProvider, Router } from './components/navigation/Router';
import Navigation from './components/navigation/Navigation';
import LiveUpdateIndicator from './components/realtime/LiveUpdateIndicator';
import LiveUpdateNotifications from './components/realtime/LiveUpdateNotifications';
import { Toaster } from './components/ui/toaster';
import { Brain, Menu, Moon, Sun, Settings } from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import useLiveUpdates from './hooks/useLiveUpdates';
import routes from './config/routes';
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('App Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
          <Card className="max-w-lg w-full">
            <CardContent className="p-6 text-center">
              <div className="mb-4">
                <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-red-600 dark:text-red-400" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Something went wrong
                </h1>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                  The NFL Prediction Dashboard encountered an unexpected error.
                </p>
              </div>
              
              <div className="space-y-3">
                <Button 
                  onClick={() => window.location.reload()}
                  className="w-full"
                >
                  Reload Dashboard
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => this.setState({ hasError: false, error: null })}
                  className="w-full"
                >
                  Try Again
                </Button>
              </div>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500">
                    Error Details (Development)
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded overflow-auto">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Main App Component
const EnhancedApp: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('darkMode');
      if (saved !== null) {
        return JSON.parse(saved);
      }
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);

  // Live updates for real-time functionality
  const {
    isConnected,
    lastUpdate,
    latency,
    reconnectAttempts
  } = useLiveUpdates({
    enablePredictionUpdates: true,
    enableConsensusUpdates: true,
    enableExpertUpdates: true,
    enableGameUpdates: true,
    updateThrottleMs: 1000
  });

  // Dark mode effect
  useEffect(() => {
    const root = window.document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  // Admin mode check
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    setShowAdmin(urlParams.get('admin') === 'true');
  }, []);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const connectionState = {
    connected: isConnected,
    lastHeartbeat: new Date().toISOString(),
    reconnectAttempts,
    latency
  };

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <NavigationProvider>
          <div className={`dashboard-layout ${isDarkMode ? 'dark' : ''}`}>
            {/* Global Live Update Notifications */}
            <LiveUpdateNotifications
              updates={lastUpdate ? [lastUpdate] : []}
              maxNotifications={5}
              autoHideDelay={8000}
            />

            {/* Main Layout */}
            <div className="flex h-screen">
              {/* Sidebar Navigation */}
              <aside className={`
                dashboard-sidebar transition-all duration-300
                ${isSidebarCollapsed ? 'w-16' : 'w-64'}
              `}>
                <div className="h-full flex flex-col">
                  {/* Sidebar Header */}
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      {!isSidebarCollapsed && (
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                            <Brain className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <h1 className="font-bold text-gray-900 dark:text-white text-sm">
                              NFL Predictions
                            </h1>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              AI Dashboard
                            </p>
                          </div>
                        </div>
                      )}
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                        className="p-2"
                      >
                        <Menu className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Navigation */}
                  <div className="flex-1 overflow-y-auto scrollbar-thin">
                    <Navigation 
                      routes={routes} 
                      className="p-4"
                      showBreadcrumbs={false}
                    />
                  </div>

                  {/* Sidebar Footer */}
                  <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    {!isSidebarCollapsed && (
                      <div className="space-y-3">
                        {/* Connection Status */}
                        <LiveUpdateIndicator
                          connectionState={connectionState}
                          lastUpdate={lastUpdate}
                          showDetails={false}
                        />

                        {/* Controls */}
                        <div className="flex items-center justify-between">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={toggleDarkMode}
                            className="p-2"
                          >
                            {isDarkMode ? (
                              <Sun className="w-4 h-4" />
                            ) : (
                              <Moon className="w-4 h-4" />
                            )}
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowAdmin(!showAdmin)}
                            className="p-2"
                          >
                            <Settings className="w-4 h-4" />
                          </Button>

                          <Badge 
                            variant="outline" 
                            className={isConnected ? 'text-green-600' : 'text-red-600'}
                          >
                            {isConnected ? 'Live' : 'Offline'}
                          </Badge>
                        </div>
                      </div>
                    )}

                    {isSidebarCollapsed && (
                      <div className="flex flex-col items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={toggleDarkMode}
                          className="p-2"
                        >
                          {isDarkMode ? (
                            <Sun className="w-4 h-4" />
                          ) : (
                            <Moon className="w-4 h-4" />
                          )}
                        </Button>
                        
                        <div className={`w-2 h-2 rounded-full ${
                          isConnected ? 'bg-green-500' : 'bg-red-500'
                        } ${isConnected ? 'animate-pulse' : ''}`} />
                      </div>
                    )}
                  </div>
                </div>
              </aside>

              {/* Main Content Area */}
              <main className="dashboard-main">
                {/* Top Header */}
                <header className="dashboard-header">
                  <Navigation 
                    routes={routes}
                    showBreadcrumbs={true}
                  />
                </header>

                {/* Router Content */}
                <div className="p-6">
                  <Router 
                    routes={routes}
                    fallbackComponent={() => (
                      <div className="text-center py-12">
                        <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                          Page Not Found
                        </h2>
                        <p className="text-gray-600 dark:text-gray-300 mb-6">
                          The requested page could not be found.
                        </p>
                        <Button onClick={() => window.location.hash = '#/'}>
                          Return to Dashboard
                        </Button>
                      </div>
                    )}
                  />
                </div>
              </main>
            </div>

            {/* Toast Notifications */}
            <Toaster />
          </div>
        </NavigationProvider>

        {/* React Query DevTools (Development Only) */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default EnhancedApp;