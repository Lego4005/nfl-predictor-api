import React, { useState, useMemo, lazy, Suspense } from 'react'
import './App.css'
import { GAMES, TEAMS } from '@/lib/nfl-data'
import { classNames } from '@/lib/nfl-utils'

// Layout Components
import AppHeader from '@/components/layout/AppHeader'
import AppSidebar from '@/components/layout/AppSidebar'

// Navigation Hook
import { useNavigation } from '@/hooks/navigation/useNavigation'

// Page Components - Direct imports for core pages
import HomePage from '@/pages/Home/HomePage'
import GamesPage from '@/pages/Games/GamesPage'
import TeamsPage from '@/pages/Teams/TeamsPage'

// Lazy loaded components for better performance
const RankingsPage = lazy(() => import('@/pages/Rankings/RankingsPage'))
const PerformancePage = lazy(() => import('@/pages/Performance/PerformancePage'))
const ConfidencePoolPage = lazy(() => import('@/pages/ConfidencePool/ConfidencePoolPage'))
const BettingCardPage = lazy(() => import('@/pages/BettingCard/BettingCardPage'))
const ToolsPage = lazy(() => import('@/pages/Tools/ToolsPage'))
const GameDetailPage = lazy(() => import('@/pages/Games/GameDetailPage'))
const TeamDetailPage = lazy(() => import('@/pages/Teams/TeamDetailPage'))

// Game interface for type safety
interface Game {
  id: string
  homeTeam: string
  awayTeam: string
  homeScore?: number
  awayScore?: number
  status: 'SCHEDULED' | 'LIVE' | 'FINAL'
  network: string
  venue: string
  time: string
  gameType?: string
  day: string
  spread: {
    open: string
    current: string
    model: string
  }
  homeSpread: string
  awaySpread: string
  pk?: string
}

// Mock games data (this would come from API in real implementation)
const mockGames: Game[] = [
  // Thursday Night Football
  {
    id: '1',
    homeTeam: 'DET',
    awayTeam: 'SF',
    homeScore: 27,
    awayScore: 20,
    status: 'FINAL',
    network: 'TNF',
    venue: "Levi's Stadium",
    time: '8:20 PM',
    day: 'Thursday Night',
    spread: { open: '+3', current: '+3.5', model: '+2' },
    homeSpread: '+3.5',
    awaySpread: '-3.5'
  },
  // Sunday Early Games
  {
    id: '2',
    homeTeam: 'KC',
    awayTeam: 'BUF',
    status: 'SCHEDULED',
    network: 'CBS',
    venue: 'GEHA Field at Arrowhead',
    time: '1:00 PM',
    day: 'Sunday Early',
    spread: { open: '+3', current: '+3.5', model: '+2' },
    homeSpread: '+3.5',
    awaySpread: '-3.5',
    pk: 'PK'
  },
  // Add more games as needed...
]

// Loading component
function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="glass rounded-xl p-6 text-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  )
}

// Error boundary component
function ErrorFallback({ error }: { error: Error }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="glass rounded-xl p-6 text-center border-destructive/20">
        <span className="text-destructive text-4xl mb-3 block">⚠️</span>
        <h3 className="text-lg font-medium text-white mb-2">Something went wrong</h3>
        <p className="text-sm text-muted-foreground mb-4">
          {error.message || 'An unexpected error occurred'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
        >
          Reload Page
        </button>
      </div>
    </div>
  )
}

function App() {
  // Navigation state management
  const navigation = useNavigation('home')

  // Layout state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Games page state
  const [currentWeek, setCurrentWeek] = useState(3)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [weekFilter, setWeekFilter] = useState('Week 3')
  const [viewDensity, setViewDensity] = useState('Compact')

  // Mock user data
  const user = {
    name: 'NFL Fan',
    avatar: undefined
  }

  // Filter games based on current filters
  const filteredGames = useMemo(() => {
    return mockGames.filter(game => {
      const matchesSearch = searchTerm === '' ||
        game.homeTeam.toLowerCase().includes(searchTerm.toLowerCase()) ||
        game.awayTeam.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesStatus = statusFilter === 'All' ||
        (statusFilter === 'Scheduled' && game.status === 'SCHEDULED') ||
        (statusFilter === 'Live' && game.status === 'LIVE') ||
        (statusFilter === 'Final' && game.status === 'FINAL')

      return matchesSearch && matchesStatus
    })
  }, [searchTerm, statusFilter])

  // Group games by day
  const gamesByDay = useMemo(() => {
    return filteredGames.reduce((acc, game) => {
      if (!acc[game.day]) {
        acc[game.day] = []
      }
      acc[game.day].push(game)
      return acc
    }, {} as Record<string, Game[]>)
  }, [filteredGames])

  // Handle search functionality
  const handleSearch = (query: string) => {
    setSearchTerm(query)
  }

  // Render page content based on current page
  const renderPageContent = () => {
    try {
      switch (navigation.currentPage) {
        case 'home':
          return <HomePage onNavigate={navigation.navigate} />

        case 'games':
          return (
            <GamesPage
              currentWeek={currentWeek}
              setCurrentWeek={setCurrentWeek}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              statusFilter={statusFilter}
              setStatusFilter={setStatusFilter}
              weekFilter={weekFilter}
              setWeekFilter={setWeekFilter}
              viewDensity={viewDensity}
              setViewDensity={setViewDensity}
              filteredGames={filteredGames}
              gamesByDay={gamesByDay}
              onGameClick={navigation.navigateToGame}
            />
          )

        case 'teams':
          return <TeamsPage onTeamClick={navigation.navigateToTeam} />

        case 'game-detail':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <GameDetailPage
                gameId={navigation.selectedGameId!}
                onBack={navigation.goBack}
              />
            </Suspense>
          )

        case 'team-detail':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <TeamDetailPage
                teamId={navigation.selectedTeamId!}
                onBack={navigation.goBack}
              />
            </Suspense>
          )

        case 'rankings':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <RankingsPage />
            </Suspense>
          )

        case 'performance':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <PerformancePage />
            </Suspense>
          )

        case 'confidence-pool':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <ConfidencePoolPage />
            </Suspense>
          )

        case 'betting-card':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <BettingCardPage />
            </Suspense>
          )

        case 'tools':
          return (
            <Suspense fallback={<LoadingSpinner />}>
              <ToolsPage />
            </Suspense>
          )

        default:
          return (
            <div className="glass rounded-xl p-8 text-center">
              <span className="text-warning text-4xl mb-3 block">🔍</span>
              <h3 className="text-lg font-medium text-white mb-2">Page Not Found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                The page you're looking for doesn't exist.
              </p>
              <button
                onClick={() => navigation.navigate('home')}
                className="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
              >
                Go Home
              </button>
            </div>
          )
      }
    } catch (error) {
      return <ErrorFallback error={error as Error} />
    }
  }

  return (
    <div className="h-screen bg-background flex overflow-hidden">
      {/* App Sidebar - Fixed Position */}
      <AppSidebar
        currentPage={navigation.currentPage}
        onNavigate={navigation.navigate}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* App Header */}
        <AppHeader
          currentPage={navigation.currentPage}
          onNavigate={navigation.navigate}
          user={user}
          onSearch={handleSearch}
          notifications={0}
        />

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-y-auto overflow-x-hidden">
          <div className="max-w-full mx-auto">
            {renderPageContent()}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App