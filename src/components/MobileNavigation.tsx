import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'

interface MobileNavigationProps {
  isOpen: boolean
  onClose: () => void
  activeTab: string
  onTabChange: (page: string) => void
}

interface NavigationItem {
  id: string
  label: string
  icon: string
  description: string
}

const MobileNavigation: React.FC<MobileNavigationProps> = ({
  isOpen,
  onClose,
  activeTab,
  onTabChange
}) => {
  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  // Handle ESC key to close
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  const navigationItems: NavigationItem[] = [
    {
      id: 'home',
      label: 'Home',
      icon: '🏠',
      description: 'Dashboard overview'
    },
    {
      id: 'games',
      label: 'Games',
      icon: '🏈',
      description: 'Game schedules & scores'
    },
    {
      id: 'teams',
      label: 'Teams',
      icon: '👥',
      description: 'Team information'
    },
    {
      id: 'rankings',
      label: 'Power Rankings',
      icon: '🏆',
      description: 'Team rankings'
    },
    {
      id: 'performance',
      label: 'Model Performance',
      icon: '📊',
      description: 'Prediction analytics'
    },
    {
      id: 'confidence-pool',
      label: 'Confidence Pool',
      icon: '🎯',
      description: 'Pick confidence games'
    },
    {
      id: 'betting-card',
      label: 'Betting Card',
      icon: '🃏',
      description: 'Betting insights'
    },
    {
      id: 'tools',
      label: 'Tools',
      icon: '🔧',
      description: 'Utilities & settings'
    }
  ]

  const handleItemClick = (tabId: string) => {
    onTabChange(tabId)
    onClose()
  }

  return (
    <>
      {/* Overlay - Only visible on mobile */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-40 lg:hidden"
            onClick={onClose}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      {/* Slide-out Drawer - Only visible on mobile */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'tween', duration: 0.3, ease: 'easeInOut' }}
            className="fixed left-0 top-0 bottom-0 w-80 max-w-[85vw] bg-card border-r border-border z-50 lg:hidden flex flex-col"
          >
            {/* Header */}
            <div className="p-6 border-b border-border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-foreground">Navigation</h2>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                  style={{ minWidth: '48px', minHeight: '48px' }}
                  aria-label="Close navigation menu"
                >
                  <X className="w-5 h-5 text-muted-foreground" />
                </button>
              </div>

              {/* App Title */}
              <div className="flex items-center gap-2">
                <span className="text-2xl">🏈</span>
                <span className="text-lg font-semibold text-foreground">NFL Predictor</span>
              </div>
            </div>

            {/* Navigation Items */}
            <div className="flex-1 p-4 space-y-2 overflow-y-auto">
              {navigationItems.map((item) => (
                <motion.button
                  key={item.id}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => handleItemClick(item.id)}
                  className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
                    activeTab === item.id
                      ? 'bg-primary/20 text-primary border-primary shadow-md'
                      : 'bg-card hover:bg-white/5 border-border hover:border-primary/40'
                  }`}
                  style={{ minHeight: '48px' }}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-md ${
                      activeTab === item.id
                        ? 'bg-primary/30'
                        : 'bg-white/5'
                    }`}>
                      <span className="text-xl">{item.icon}</span>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-foreground">{item.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {item.description}
                      </div>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-border">
              <div className="text-xs text-muted-foreground text-center">
                NFL Predictor v1.0
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default MobileNavigation
