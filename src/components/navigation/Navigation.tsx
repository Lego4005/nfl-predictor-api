import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, Brain, Sword, BarChart3, 
  Settings, Menu, X, ChevronDown,
  Zap, Users, Target, TrendingUp
} from 'lucide-react';
import { Link, useNavigation, useBreadcrumbs } from './Router';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import type { Route } from './Router';

interface NavigationProps {
  routes: Route[];
  className?: string;
  showBreadcrumbs?: boolean;
}

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: React.ComponentType<any>;
  description?: string;
  badge?: string;
  children?: NavItem[];
}

const Navigation: React.FC<NavigationProps> = ({ 
  routes, 
  className = '', 
  showBreadcrumbs = true 
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const { currentRoute } = useNavigation();
  const breadcrumbs = useBreadcrumbs(routes);

  // Navigation structure
  const navItems: NavItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      path: '/',
      icon: Home,
      description: 'Main overview and live games'
    },
    {
      id: 'ai-council',
      label: 'AI Council',
      path: '/council',
      icon: Brain,
      description: 'Expert consensus and vote weights',
      children: [
        {
          id: 'council-overview',
          label: 'Council Overview',
          path: '/council',
          icon: Users,
          description: 'AI Council dashboard'
        },
        {
          id: 'vote-weights',
          label: 'Vote Weights',
          path: '/council/weights',
          icon: BarChart3,
          description: 'Detailed weight analysis'
        },
        {
          id: 'consensus-history',
          label: 'Consensus History',
          path: '/council/history',
          icon: TrendingUp,
          description: 'Historical decisions'
        }
      ]
    },
    {
      id: 'expert-battles',
      label: 'Expert Battles',
      path: '/battles',
      icon: Sword,
      description: 'Head-to-head expert comparisons',
      badge: 'New',
      children: [
        {
          id: 'battle-arena',
          label: 'Battle Arena',
          path: '/battles',
          icon: Sword,
          description: 'Expert head-to-head analysis'
        },
        {
          id: 'expert-rankings',
          label: 'Expert Rankings',
          path: '/battles/rankings',
          icon: Target,
          description: 'Performance leaderboard'
        }
      ]
    },
    {
      id: 'predictions',
      label: 'Predictions',
      path: '/predictions',
      icon: BarChart3,
      description: '27-category prediction analysis',
      children: [
        {
          id: 'all-categories',
          label: 'All Categories',
          path: '/predictions',
          icon: BarChart3,
          description: 'Complete prediction grid'
        },
        {
          id: 'game-outcome',
          label: 'Game Outcome',
          path: '/predictions/game-outcome',
          icon: Target,
          description: 'Winner and score predictions'
        },
        {
          id: 'betting-markets',
          label: 'Betting Markets',
          path: '/predictions/betting-markets',
          icon: TrendingUp,
          description: 'Spread and totals analysis'
        },
        {
          id: 'player-props',
          label: 'Player Props',
          path: '/predictions/player-props',
          icon: Users,
          description: 'Individual player predictions'
        }
      ]
    },
    {
      id: 'live-games',
      label: 'Live Games',
      path: '/live',
      icon: Zap,
      description: 'Real-time game tracking'
    }
  ];

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const isActiveRoute = (path: string): boolean => {
    if (path === '/') {
      return currentRoute === '/';
    }
    return currentRoute.startsWith(path);
  };

  const renderNavItem = (item: NavItem, depth: number = 0) => {
    const isActive = isActiveRoute(item.path);
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;
    const IconComponent = item.icon;

    return (
      <div key={item.id} className={`${depth > 0 ? 'ml-6' : ''}`}>
        <div className="relative">
          <Link
            to={item.path}
            className={`
              group flex items-center justify-between w-full px-3 py-2.5 rounded-lg
              text-sm font-medium transition-all duration-200
              ${isActive 
                ? 'bg-blue-100 text-blue-700 shadow-sm' 
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }
            `}
          >
            <div className="flex items-center gap-3">
              <IconComponent className={`
                h-4 w-4 transition-colors
                ${isActive ? 'text-blue-600' : 'text-gray-500 group-hover:text-gray-700'}
              `} />
              <span>{item.label}</span>
              {item.badge && (
                <Badge className="text-xs bg-orange-100 text-orange-700">
                  {item.badge}
                </Badge>
              )}
            </div>
            
            {hasChildren && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  toggleExpanded(item.id);
                }}
                className="p-1 rounded hover:bg-gray-200 transition-colors"
              >
                <ChevronDown className={`
                  h-3 w-3 transition-transform
                  ${isExpanded ? 'rotate-180' : ''}
                `} />
              </button>
            )}
          </Link>

          {/* Active indicator */}
          {isActive && (
            <motion.div
              layoutId="activeIndicator"
              className="absolute left-0 top-0 w-1 h-full bg-blue-600 rounded-r"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}
        </div>

        {/* Children */}
        <AnimatePresence>
          {hasChildren && isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden mt-1"
            >
              <div className="space-y-1">
                {item.children!.map(child => renderNavItem(child, depth + 1))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  return (
    <>
      {/* Desktop Navigation */}
      <nav className={`hidden lg:block ${className}`}>
        <Card className="h-full">
          <CardContent className="p-4">
            <div className="space-y-1">
              {navItems.map(item => renderNavItem(item))}
            </div>
          </CardContent>
        </Card>
      </nav>

      {/* Mobile Navigation */}
      <div className="lg:hidden">
        {/* Mobile Menu Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="fixed top-4 left-4 z-50 bg-white shadow-lg"
        >
          {isMobileMenuOpen ? (
            <X className="h-4 w-4" />
          ) : (
            <Menu className="h-4 w-4" />
          )}
        </Button>

        {/* Mobile Menu Overlay */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 z-40"
                onClick={() => setIsMobileMenuOpen(false)}
              />
              
              <motion.div
                initial={{ x: -300 }}
                animate={{ x: 0 }}
                exit={{ x: -300 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="fixed left-0 top-0 h-full w-80 bg-white shadow-xl z-50 overflow-y-auto"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Navigation</h2>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="space-y-1">
                    {navItems.map(item => renderNavItem(item))}
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>

      {/* Breadcrumbs */}
      {showBreadcrumbs && breadcrumbs.length > 1 && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b">
          <nav className="flex items-center space-x-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={index}>
                {index > 0 && (
                  <span className="text-gray-400">/</span>
                )}
                {crumb.path ? (
                  <Link
                    to={crumb.path}
                    params={crumb.params}
                    className="text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-gray-600 font-medium">
                    {crumb.label}
                  </span>
                )}
              </React.Fragment>
            ))}
          </nav>
        </div>
      )}
    </>
  );
};

export default Navigation;