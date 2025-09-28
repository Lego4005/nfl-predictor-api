import React, { createContext, useContext, useState, useEffect } from 'react';

// Route definitions
export interface Route {
  path: string;
  component: React.ComponentType<any>;
  title: string;
  description?: string;
  requiresAuth?: boolean;
  icon?: React.ComponentType<any>;
}

export interface RouteParams {
  [key: string]: string | undefined;
}

// Navigation context
interface NavigationContextType {
  currentRoute: string;
  params: RouteParams;
  navigate: (path: string, params?: RouteParams) => void;
  goBack: () => void;
  history: string[];
}

const NavigationContext = createContext<NavigationContextType | null>(null);

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
};

// Simple hash-based router implementation
export const NavigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentRoute, setCurrentRoute] = useState('/');
  const [params, setParams] = useState<RouteParams>({});
  const [history, setHistory] = useState<string[]>(['/']);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) || '/';
      const [path, queryString] = hash.split('?');
      
      // Parse query parameters
      const searchParams = new URLSearchParams(queryString);
      const newParams: RouteParams = {};
      searchParams.forEach((value, key) => {
        newParams[key] = value;
      });

      setCurrentRoute(path);
      setParams(newParams);
    };

    // Initialize with current hash
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (path: string, newParams?: RouteParams) => {
    let url = path;
    
    if (newParams && Object.keys(newParams).length > 0) {
      const searchParams = new URLSearchParams();
      Object.entries(newParams).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.set(key, value);
        }
      });
      url += `?${searchParams.toString()}`;
    }

    window.location.hash = url;
    setHistory(prev => [...prev, path]);
  };

  const goBack = () => {
    if (history.length > 1) {
      const newHistory = [...history];
      newHistory.pop(); // Remove current
      const previousRoute = newHistory[newHistory.length - 1];
      setHistory(newHistory);
      navigate(previousRoute);
    }
  };

  return (
    <NavigationContext.Provider value={{
      currentRoute,
      params,
      navigate,
      goBack,
      history
    }}>
      {children}
    </NavigationContext.Provider>
  );
};

// Route matching utilities
export const matchRoute = (pattern: string, path: string): { matches: boolean; params: RouteParams } => {
  const patternParts = pattern.split('/');
  const pathParts = path.split('/');

  if (patternParts.length !== pathParts.length) {
    return { matches: false, params: {} };
  }

  const params: RouteParams = {};
  
  for (let i = 0; i < patternParts.length; i++) {
    const patternPart = patternParts[i];
    const pathPart = pathParts[i];

    if (patternPart.startsWith(':')) {
      // Dynamic parameter
      const paramName = patternPart.slice(1);
      params[paramName] = pathPart;
    } else if (patternPart !== pathPart) {
      // Static part doesn't match
      return { matches: false, params: {} };
    }
  }

  return { matches: true, params };
};

// Router component
interface RouterProps {
  routes: Route[];
  fallbackComponent?: React.ComponentType;
}

export const Router: React.FC<RouterProps> = ({ routes, fallbackComponent: FallbackComponent }) => {
  const { currentRoute, params } = useNavigation();

  // Find matching route
  const matchedRoute = routes.find(route => {
    const match = matchRoute(route.path, currentRoute);
    return match.matches;
  });

  if (!matchedRoute) {
    if (FallbackComponent) {
      return <FallbackComponent />;
    }
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
          <p className="text-gray-600 mb-4">The requested route could not be found.</p>
          <button 
            onClick={() => window.location.hash = '#/'}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  // Extract route parameters
  const routeMatch = matchRoute(matchedRoute.path, currentRoute);
  const allParams = { ...params, ...routeMatch.params };

  const Component = matchedRoute.component;
  return <Component {...allParams} />;
};

// Link component for navigation
interface LinkProps {
  to: string;
  params?: RouteParams;
  children: React.ReactNode;
  className?: string;
  activeClassName?: string;
}

export const Link: React.FC<LinkProps> = ({ 
  to, 
  params, 
  children, 
  className = '', 
  activeClassName = 'active' 
}) => {
  const { currentRoute, navigate } = useNavigation();
  const isActive = currentRoute === to;

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate(to, params);
  };

  return (
    <a
      href={`#${to}`}
      onClick={handleClick}
      className={`${className} ${isActive ? activeClassName : ''}`}
    >
      {children}
    </a>
  );
};

// Navigation helpers
export const createRouteUrl = (path: string, params?: RouteParams): string => {
  let url = path;
  
  if (params && Object.keys(params).length > 0) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, value);
      }
    });
    url += `?${searchParams.toString()}`;
  }

  return `#${url}`;
};

// Route guards
export const withAuthGuard = <P extends object>(
  Component: React.ComponentType<P>,
  redirectTo: string = '/login'
) => {
  return (props: P) => {
    const { navigate } = useNavigation();
    // This would check authentication status
    const isAuthenticated = true; // Replace with actual auth check

    useEffect(() => {
      if (!isAuthenticated) {
        navigate(redirectTo);
      }
    }, [isAuthenticated, navigate]);

    if (!isAuthenticated) {
      return <div>Redirecting...</div>;
    }

    return <Component {...props} />;
  };
};

// Breadcrumb utilities
export interface BreadcrumbItem {
  label: string;
  path?: string;
  params?: RouteParams;
}

export const useBreadcrumbs = (routes: Route[]): BreadcrumbItem[] => {
  const { currentRoute, params } = useNavigation();

  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const pathParts = currentRoute.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', path: '/' }
    ];

    let currentPath = '';
    pathParts.forEach((part, index) => {
      currentPath += `/${part}`;
      
      const route = routes.find(r => {
        const match = matchRoute(r.path, currentPath);
        return match.matches;
      });

      if (route) {
        const isLast = index === pathParts.length - 1;
        breadcrumbs.push({
          label: route.title,
          path: isLast ? undefined : currentPath,
          params: isLast ? undefined : params
        });
      } else {
        // Generate label from path part
        const label = part.replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        breadcrumbs.push({
          label,
          path: undefined
        });
      }
    });

    return breadcrumbs;
  };

  return generateBreadcrumbs();
};