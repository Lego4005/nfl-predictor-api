import React from 'react'
import { Search, Settings, User, Menu } from 'lucide-react'

interface AppHeaderProps {
  currentPage: string
  onNavigate?: (pageId: string) => void
  user?: {
    name: string
    avatar?: string
  }
  onSearch?: (query: string) => void
  notifications?: number
  onToggleMobileMenu?: () => void
}

interface NavigationBreadcrumbProps {
  currentPage: string
  onNavigate?: (pageId: string) => void
}

interface UserActionsProps {
  user?: {
    name: string
    avatar?: string
  }
  notifications?: number
}

interface SearchInterfaceProps {
  onSearch?: (query: string) => void
  placeholder?: string
  suggestions?: string[]
}

// Navigation breadcrumb component
function NavigationBreadcrumb({ currentPage, onNavigate }: NavigationBreadcrumbProps) {
  const getPageTitle = (page: string) => {
    const titles: Record<string, string> = {
      'home': 'Home',
      'games': 'Games',
      'game-detail': 'Game Detail',
      'confidence-pool': 'Confidence Pool',
      'betting-card': 'Betting Card',
      'performance': 'Model Performance',
      'teams': 'Teams Directory',
      'team-detail': 'Team Detail',
      'rankings': 'Power Rankings',
      'tools': 'Tools & Utilities'
    }
    return titles[page] || 'Dashboard'
  }

  const getPageIcon = (page: string) => {
    const icons: Record<string, string> = {
      'home': '🏠',
      'games': '🏈',
      'game-detail': '🎯',
      'confidence-pool': '🎯',
      'betting-card': '🃏',
      'performance': '📊',
      'teams': '👥',
      'team-detail': '👥',
      'rankings': '🏆',
      'tools': '🔧'
    }
    return icons[page] || '📊'
  }

  const isDetailPage = currentPage.includes('detail')

  return (
    <div className="flex items-center gap-2">
      <span className="text-xl">{getPageIcon(currentPage)}</span>
      <div className="flex items-center gap-2">
        {isDetailPage && (
          <>
            <button
              onClick={() => onNavigate?.(currentPage.replace('-detail', ''))}
              className="text-primary hover:text-primary/80 transition-colors"
            >
              {currentPage.includes('game') ? 'Games' : 'Teams'}
            </button>
            <span className="text-muted-foreground">→</span>
          </>
        )}
        <h1 className="text-xl font-bold text-foreground">{getPageTitle(currentPage)}</h1>
      </div>
    </div>
  )
}

// User actions component
function UserActions({ user, notifications }: UserActionsProps) {
  return (
    <div className="flex items-center gap-3">
      {/* Notifications */}
      {notifications && notifications > 0 && (
        <button className="relative p-2 rounded-lg glass border border-border hover:border-primary/40 transition-colors">
          <span className="text-lg">🔔</span>
          <span className="absolute -top-1 -right-1 bg-destructive text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {notifications > 9 ? '9+' : notifications}
          </span>
        </button>
      )}

      {/* Settings */}
      <button className="p-2 rounded-lg glass border border-border hover:border-primary/40 transition-colors">
        <Settings className="w-5 h-5 text-muted-foreground" />
      </button>

      {/* User Profile */}
      <div className="flex items-center gap-2 p-2 rounded-lg glass border border-border hover:border-primary/40 transition-colors cursor-pointer">
        {user?.avatar ? (
          <img
            src={user.avatar}
            alt={user.name}
            className="w-6 h-6 rounded-full"
          />
        ) : (
          <User className="w-5 h-5 text-muted-foreground" />
        )}
        {user?.name && (
          <span className="text-sm text-foreground hidden md:block">{user.name}</span>
        )}
      </div>
    </div>
  )
}

// Search interface component
function SearchInterface({ onSearch, placeholder = "Search teams, games...", suggestions }: SearchInterfaceProps) {
  const [query, setQuery] = React.useState('')
  const [showSuggestions, setShowSuggestions] = React.useState(false)

  const handleSearch = (searchQuery: string) => {
    setQuery(searchQuery)
    onSearch?.(searchQuery)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSearch?.(query)
      setShowSuggestions(false)
    }
  }

  return (
    <div className="relative flex-1 max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onKeyPress={handleKeyPress}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          className="w-full pl-10 pr-4 py-2 rounded-lg glass border border-border focus:border-primary focus:outline-none text-sm placeholder-muted-foreground"
        />
      </div>

      {/* Search Suggestions */}
      {showSuggestions && suggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 glass border border-border rounded-lg shadow-lg z-50">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => {
                handleSearch(suggestion)
                setShowSuggestions(false)
              }}
              className="w-full text-left px-3 py-2 hover:bg-white/5 first:rounded-t-lg last:rounded-b-lg text-sm text-foreground"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Main AppHeader component
function AppHeader({ currentPage, onNavigate, user, onSearch, notifications }: AppHeaderProps) {
  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left: Navigation Breadcrumb */}
        <NavigationBreadcrumb currentPage={currentPage} onNavigate={onNavigate} />

        {/* Center: Search Interface (hidden on mobile) */}
        <div className="hidden md:block flex-1 max-w-md mx-6">
          <SearchInterface onSearch={onSearch} />
        </div>

        {/* Right: User Actions */}
        <UserActions user={user} notifications={notifications} />
      </div>

      {/* Mobile Search (shown on mobile only) */}
      <div className="md:hidden mt-3">
        <SearchInterface onSearch={onSearch} />
      </div>
    </header>
  )
}

export default AppHeader
export { NavigationBreadcrumb, UserActions, SearchInterface }