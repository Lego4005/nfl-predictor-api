import { useState, useCallback, useMemo } from 'react'

export interface NavigationState {
  currentPage: string
  selectedGameId: string | null
  selectedTeamId: string | null
  navigationHistory: string[]
  queryParams: Record<string, string>
}

export interface NavigationControls {
  navigate: (pageId: string, options?: NavigationOptions) => void
  navigateToGame: (gameId: string) => void
  navigateToTeam: (teamId: string) => void
  goBack: () => void
  canGoBack: boolean
  setQueryParam: (key: string, value: string) => void
  clearQueryParams: () => void
}

export interface NavigationOptions {
  gameId?: string
  teamId?: string
  queryParams?: Record<string, string>
  replace?: boolean
}

const DEFAULT_PAGE = 'home'

/**
 * Custom hook for managing application navigation state
 * Provides centralized navigation logic and state management
 */
export function useNavigation(initialPage: string = DEFAULT_PAGE): NavigationState & NavigationControls {
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null)
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null)
  const [navigationHistory, setNavigationHistory] = useState<string[]>([initialPage])
  const [queryParams, setQueryParams] = useState<Record<string, string>>({})

  // Navigate to a specific page with options
  const navigate = useCallback((pageId: string, options: NavigationOptions = {}) => {
    const { gameId, teamId, queryParams: newQueryParams, replace = false } = options

    // Update current page
    setCurrentPage(pageId)

    // Update selected IDs based on page and options
    if (pageId === 'game-detail' && gameId) {
      setSelectedGameId(gameId)
      setSelectedTeamId(null)
    } else if (pageId === 'team-detail' && teamId) {
      setSelectedTeamId(teamId)
      setSelectedGameId(null)
    } else if (!pageId.includes('detail')) {
      // Clear selections when navigating to non-detail pages
      setSelectedGameId(null)
      setSelectedTeamId(null)
    }

    // Update query parameters
    if (newQueryParams) {
      setQueryParams(prev => ({ ...prev, ...newQueryParams }))
    } else if (!pageId.includes('detail')) {
      // Clear query params when navigating to main pages
      setQueryParams({})
    }

    // Update navigation history
    setNavigationHistory(prev => {
      if (replace) {
        return [...prev.slice(0, -1), pageId]
      }
      // Avoid duplicate consecutive entries
      if (prev[prev.length - 1] !== pageId) {
        return [...prev, pageId]
      }
      return prev
    })
  }, [])

  // Navigate to a specific game detail page
  const navigateToGame = useCallback((gameId: string) => {
    navigate('game-detail', { gameId })
  }, [navigate])

  // Navigate to a specific team detail page
  const navigateToTeam = useCallback((teamId: string) => {
    navigate('team-detail', { teamId })
  }, [navigate])

  // Go back to the previous page
  const goBack = useCallback(() => {
    if (navigationHistory.length > 1) {
      const newHistory = navigationHistory.slice(0, -1)
      const previousPage = newHistory[newHistory.length - 1]
      
      setNavigationHistory(newHistory)
      setCurrentPage(previousPage)

      // Clear detail page selections when going back
      if (!previousPage.includes('detail')) {
        setSelectedGameId(null)
        setSelectedTeamId(null)
        setQueryParams({})
      }
    }
  }, [navigationHistory])

  // Check if we can go back
  const canGoBack = useMemo(() => {
    return navigationHistory.length > 1
  }, [navigationHistory])

  // Set a single query parameter
  const setQueryParam = useCallback((key: string, value: string) => {
    setQueryParams(prev => ({ ...prev, [key]: value }))
  }, [])

  // Clear all query parameters
  const clearQueryParams = useCallback(() => {
    setQueryParams({})
  }, [])

  return {
    // State
    currentPage,
    selectedGameId,
    selectedTeamId,
    navigationHistory,
    queryParams,
    
    // Controls
    navigate,
    navigateToGame,
    navigateToTeam,
    goBack,
    canGoBack,
    setQueryParam,
    clearQueryParams
  }
}

/**
 * Hook for managing URL synchronization with navigation state
 * This can be extended to work with React Router or other routing libraries
 */
export function useNavigationSync() {
  // This is a placeholder for URL synchronization logic
  // In a real application, this would integrate with:
  // - React Router for URL management
  // - Browser history API for back/forward buttons
  // - Deep linking support for bookmarkable URLs
  
  const syncToURL = useCallback((state: NavigationState) => {
    // Example implementation:
    // const url = new URL(window.location.href)
    // url.searchParams.set('page', state.currentPage)
    // if (state.selectedGameId) url.searchParams.set('gameId', state.selectedGameId)
    // if (state.selectedTeamId) url.searchParams.set('teamId', state.selectedTeamId)
    // Object.entries(state.queryParams).forEach(([key, value]) => {
    //   url.searchParams.set(key, value)
    // })
    // window.history.replaceState({}, '', url.toString())
  }, [])

  const syncFromURL = useCallback(() => {
    // Example implementation:
    // const url = new URL(window.location.href)
    // return {
    //   currentPage: url.searchParams.get('page') || 'home',
    //   selectedGameId: url.searchParams.get('gameId'),
    //   selectedTeamId: url.searchParams.get('teamId'),
    //   queryParams: Object.fromEntries(url.searchParams.entries())
    // }
    return null
  }, [])

  return {
    syncToURL,
    syncFromURL
  }
}

/**
 * Navigation configuration types and utilities
 */
export interface PageConfig {
  id: string
  title: string
  icon: string
  parent?: string
  requiresAuth?: boolean
  allowedRoles?: string[]
}

export const PAGE_CONFIGS: Record<string, PageConfig> = {
  'home': {
    id: 'home',
    title: 'Home',
    icon: '🏠'
  },
  'games': {
    id: 'games',
    title: 'Games',
    icon: '🏈'
  },
  'game-detail': {
    id: 'game-detail',
    title: 'Game Detail',
    icon: '🎯',
    parent: 'games'
  },
  'confidence-pool': {
    id: 'confidence-pool',
    title: 'Confidence Pool',
    icon: '🎯'
  },
  'betting-card': {
    id: 'betting-card',
    title: 'Betting Card',
    icon: '🃏'
  },
  'performance': {
    id: 'performance',
    title: 'Model Performance',
    icon: '📊'
  },
  'teams': {
    id: 'teams',
    title: 'Teams Directory',
    icon: '👥'
  },
  'team-detail': {
    id: 'team-detail',
    title: 'Team Detail',
    icon: '👥',
    parent: 'teams'
  },
  'rankings': {
    id: 'rankings',
    title: 'Power Rankings',
    icon: '🏆'
  },
  'tools': {
    id: 'tools',
    title: 'Tools & Utilities',
    icon: '🔧'
  }
}

/**
 * Get page configuration by ID
 */
export function getPageConfig(pageId: string): PageConfig | null {
  return PAGE_CONFIGS[pageId] || null
}

/**
 * Check if a page is a detail page
 */
export function isDetailPage(pageId: string): boolean {
  return pageId.includes('detail')
}

/**
 * Get parent page for a detail page
 */
export function getParentPage(pageId: string): string | null {
  const config = getPageConfig(pageId)
  return config?.parent || null
}