import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Menu, X, Home, Zap, BarChart3, Target, Users, DollarSign,
  Activity, Moon, Sun, Wifi, WifiOff, Settings
} from 'lucide-react';

const MobileNavigation = ({
  activeTab,
  onTabChange,
  darkMode,
  onToggleDarkMode,
  wsConnected,
  wideMode,
  onToggleWideMode
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Close menu when route changes
  useEffect(() => {
    setIsOpen(false);
  }, [activeTab]);

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const navigationItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: Home,
      description: 'Game highlights & insights'
    },
    {
      id: 'live',
      label: 'Live Games',
      icon: Zap,
      description: 'Real-time updates'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      description: 'Team performance data'
    },
    {
      id: 'predictions',
      label: 'Predictions',
      icon: Target,
      description: 'AI model insights'
    },
    {
      id: 'players',
      label: 'Players',
      icon: Users,
      description: 'Injuries & roster info'
    },
    {
      id: 'betting',
      label: 'Betting',
      icon: DollarSign,
      description: 'Odds & value bets'
    },
    {
      id: 'leaderboard',
      label: 'Leaderboard',
      icon: Users,
      description: 'Player & team rankings'
    },
    {
      id: 'health',
      label: 'System Health',
      icon: Activity,
      description: 'System status & monitoring'
    }
  ];

  const handleItemClick = (tabId) => {
    onTabChange(tabId);
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Hamburger Button */}
      <div className="lg:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          className={`touch-friendly hamburger ${isOpen ? 'hamburger-open' : ''}`}
          aria-label="Toggle navigation menu"
        >
          <div className="flex flex-col gap-1">
            <span className="hamburger-line" />
            <span className="hamburger-line" />
            <span className="hamburger-line" />
          </div>
        </Button>
      </div>

      {/* Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mobile-nav-overlay lg:hidden"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Mobile Navigation Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.3 }}
            className="mobile-nav-menu lg:hidden"
          >
            {/* Header */}
            <div className="p-4 border-b border-border">
              <div className="flex items-center justify-between mb-3">
                <h2 className="responsive-text-lg font-bold">NFL Dashboard</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                  className="touch-friendly"
                  aria-label="Close navigation menu"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Status Indicators */}
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant={wsConnected ? "default" : "secondary"} className="text-xs">
                  {wsConnected ? (
                    <><Wifi className="h-3 w-3 mr-1" />Live</>
                  ) : (
                    <><WifiOff className="h-3 w-3 mr-1" />Simulated</>
                  )}
                </Badge>
                <Badge variant="outline" className="text-xs bg-green-100 text-green-800 border-green-200">
                  2025 NFL Data
                </Badge>
              </div>
            </div>

            {/* Navigation Items */}
            <div className="flex-1 p-4 space-y-2 overflow-y-auto">
              {navigationItems.map((item) => (
                <motion.button
                  key={item.id}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleItemClick(item.id)}
                  className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                    activeTab === item.id
                      ? 'bg-primary text-primary-foreground border-primary shadow-md'
                      : 'bg-card hover:bg-accent border-border hover:border-accent-foreground/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-md ${
                      activeTab === item.id
                        ? 'bg-primary-foreground/20'
                        : 'bg-accent'
                    }`}>
                      <item.icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <div className="responsive-text-sm font-medium">{item.label}</div>
                      <div className={`responsive-text-xs opacity-70 ${
                        activeTab === item.id ? 'text-primary-foreground/70' : 'text-muted-foreground'
                      }`}>
                        {item.description}
                      </div>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>

            <Separator />

            {/* Settings & Controls */}
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4 text-muted-foreground" />
                  <span className="responsive-text-sm">Settings</span>
                </div>
              </div>

              <div className="space-y-3">
                {/* Dark Mode Toggle */}
                <div className="flex items-center justify-between">
                  <span className="responsive-text-sm">Dark Mode</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onToggleDarkMode}
                    className="touch-friendly"
                  >
                    {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                  </Button>
                </div>

                {/* Wide Mode Toggle (hidden on mobile) */}
                <div className="hidden sm:flex items-center justify-between">
                  <span className="responsive-text-sm">Wide Mode</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onToggleWideMode}
                    className="touch-friendly"
                  >
                    {wideMode ? 'Narrow' : 'Wide'}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default MobileNavigation;