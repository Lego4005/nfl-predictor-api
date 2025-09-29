import React, { useState, useMemo, lazy, Suspense } from 'react'
import './App.css'
import { TEAMS } from '@/lib/nfl-data'
import { classNames } from '@/lib/nfl-utils'
import { getCurrentNFLWeek } from '@/utils/nflWeekCalculator.js'
import { useGames } from '@/hooks/useAPI'
import { useCurrentWeekESPNGames } from '@/hooks/useESPNData'

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
  gameTime?: Date
  gameType?: string
  day: string
  timeSlot: string
  dayOrder: number
  spread: {
    open: string
    current: string
    model: string
  }
  homeSpread: string
  awaySpread: string
  pk?: string
}

function App() {
  // Navigation state management
  const navigation = useNavigation('home')

  // Layout state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Get current NFL week
  const currentNFLWeek = getCurrentNFLWeek(new Date('2025-09-29')) // Current date

  // Games page state - initialize with Week 1 to show complete progression
  const [currentWeek, setCurrentWeek] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [weekFilter, setWeekFilter] = useState('Week 1')
  const [viewDensity, setViewDensity] = useState('Compact')

  // Fetch all games for the 2025 season for better filtering UX
  const { data: gamesData, isLoading: gamesLoading, error: gamesError } = useGames()

  // Mock user data
  const user = {
    name: 'NFL Fan',
    avatar: undefined
  }

  // Transform API data to expected format and organize by NFL schedule days
  const transformedGames = useMemo(() => {
    if (!gamesData || !Array.isArray(gamesData)) return []

    console.log(`🎮 Total games fetched: ${gamesData.length}`)
    console.log(`📊 Sample raw game:`, gamesData[0])
    console.log(`📊 Game weeks distribution:`, gamesData.reduce((acc: any, game: any) => {
      acc[game.week] = (acc[game.week] || 0) + 1
      return acc
    }, {}))

    const transformed = gamesData.map((game: any) => {
      // Parse game time and ensure it's in Eastern Time
      const gameDate = new Date(game.game_time || game.date)

      // Get Eastern Time hour for proper day classification
      const easternHour = parseInt(gameDate.toLocaleString('en-US', {
        timeZone: 'America/New_York',
        hour: '2-digit',
        hour12: false
      }))

      const easternMinutes = parseInt(gameDate.toLocaleString('en-US', {
        timeZone: 'America/New_York',
        minute: '2-digit'
      }))

      // Get the day of week in Eastern Time
      const easternDateString = gameDate.toLocaleDateString('en-US', {
        timeZone: 'America/New_York',
        weekday: 'long'
      })

      let dayOfWeek = 0
      switch (easternDateString) {
        case 'Sunday': dayOfWeek = 0; break
        case 'Monday': dayOfWeek = 1; break
        case 'Tuesday': dayOfWeek = 2; break
        case 'Wednesday': dayOfWeek = 3; break
        case 'Thursday': dayOfWeek = 4; break
        case 'Friday': dayOfWeek = 5; break
        case 'Saturday': dayOfWeek = 6; break
      }

      // Create dynamic day slot based on actual kickoff time in Eastern Time
      let daySlot = ''
      let timeSlot = ''
      let sortOrder = 0
      let network = game.network || 'TBD'

      // Determine day and time slot based on actual kickoff time in Eastern Time
      // NFL week flow: Thursday → Saturday (rare) → Sunday → Monday (then other special days)
      if (dayOfWeek === 4) { // Thursday
        daySlot = 'Thursday Night'
        timeSlot = 'Prime Time'
        sortOrder = 1
        network = network === 'CBS/FOX' ? 'TNF' : (network || 'TNF')
      } else if (dayOfWeek === 6) { // Saturday (playoffs, late season, college off weeks)
        daySlot = 'Saturday'
        if (easternHour >= 20) {
          timeSlot = 'Night'
          sortOrder = 1.8
        } else if (easternHour >= 16) {
          timeSlot = 'Afternoon'
          sortOrder = 1.7
        } else {
          timeSlot = 'Early'
          sortOrder = 1.6
        }
        network = network === 'CBS/FOX' ? 'ESPN' : (network || 'ESPN')
      } else if (dayOfWeek === 0) { // Sunday - ALL games go in single "Sunday" column
        daySlot = 'Sunday'
        sortOrder = 2
        if (easternHour >= 20 || (easternHour === 19 && easternMinutes >= 30)) { // 8:00 PM or later (7:30 PM for some games)
          timeSlot = 'Night'
          network = network === 'CBS/FOX' ? 'NBC' : (network || 'NBC')
        } else if (easternHour >= 16 || (easternHour === 15 && easternMinutes >= 30)) { // 4:00 PM or later (3:30 PM for some games)
          timeSlot = 'Late'
          network = network === 'CBS/FOX' ? 'FOX' : (network || 'FOX')
        } else { // Before 4:00 PM
          timeSlot = 'Early'
          network = network === 'CBS/FOX' ? 'CBS' : (network || 'CBS')
        }
      } else if (dayOfWeek === 1) { // Monday
        daySlot = 'Monday Night'
        timeSlot = 'Prime Time'
        sortOrder = 3
        network = network === 'CBS/FOX' ? 'ESPN' : (network || 'ESPN')
      } else if (dayOfWeek === 2) { // Tuesday (makeup games, international)
        daySlot = 'Tuesday Night'
        timeSlot = 'Prime Time'
        sortOrder = 4
      } else if (dayOfWeek === 3) { // Wednesday (makeup games, international)
        daySlot = 'Wednesday Night'
        timeSlot = 'Prime Time'
        sortOrder = 5
      } else {
        // Handle other days (Friday is extremely rare)
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        const dayName = dayNames[dayOfWeek]
        daySlot = `${dayName}`
        timeSlot = easternHour >= 17 ? 'Night' : easternHour >= 12 ? 'Afternoon' : 'Morning'
        sortOrder = dayOfWeek === 0 ? 10 : dayOfWeek + (easternHour / 24)
      }

      return {
        id: game.id,
        week: game.week,
        season: game.season,
        homeTeam: game.home_team,
        awayTeam: game.away_team,
        homeScore: game.home_score,
        awayScore: game.away_score,
        status: game.status?.toUpperCase() as 'SCHEDULED' | 'LIVE' | 'FINAL',
        network: network,
        venue: game.venue || 'TBD',
        time: gameDate.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          timeZone: 'America/New_York' // Always display in Eastern Time
        }),
        gameTime: gameDate, // Keep original date for sorting and display
        day: daySlot,
        timeSlot: timeSlot, // Time slot within the day (Early, Late, Night, etc.)
        dayOrder: sortOrder, // For sorting days in correct NFL order
        spread: {
          open: '+3',
          current: '+3.5',
          model: '+2'
        },
        homeSpread: '+3.5',
        awaySpread: '-3.5'
      }
    })

    console.log(`🎯 Sample transformed game:`, transformed[0])
    return transformed
  }, [gamesData])

  // Filter games based on current filters
  // Handle week filter changes - ensure proper synchronization
  const handleWeekChange = (week: number) => {
    setCurrentWeek(week)
    setWeekFilter(`Week ${week}`)
  }

  const filteredGames = useMemo(() => {
    console.log(`🔍 Filtering ${transformedGames.length} games...`)
    console.log(`📋 Current filters: Week=${weekFilter}, Status=${statusFilter}, Search='${searchTerm}'`)

    const filtered = transformedGames.filter((game: any) => {
      const matchesSearch = searchTerm === '' ||
        game.homeTeam.toLowerCase().includes(searchTerm.toLowerCase()) ||
        game.awayTeam.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesStatus = statusFilter === 'All' ||
        (statusFilter === 'Scheduled' && (game.status === 'SCHEDULED' || game.status === 'scheduled')) ||
        (statusFilter === 'Live' && (game.status === 'LIVE' || game.status === 'live')) ||
        (statusFilter === 'Final' && (game.status === 'FINAL' || game.status === 'final' || game.status === 'Final'))

      // Filter by week - extract week number from weekFilter (e.g., "Week 4" -> 4)
      const selectedWeek = parseInt(weekFilter.replace('Week ', ''))
      const matchesWeek = game.week === selectedWeek

      return matchesSearch && matchesStatus && matchesWeek
    })

    console.log(`✅ Filtered to ${filtered.length} games for ${weekFilter} with status '${statusFilter}'`)
    if (filtered.length > 0) {
      console.log(`🎮 Sample filtered games:`, filtered.slice(0, 3).map(g => `${g.awayTeam} @ ${g.homeTeam} (Week ${g.week}, ${g.status})`));
    }
    return filtered
  }, [transformedGames, searchTerm, statusFilter, weekFilter])

  // Group games by day with proper ordering
  const gamesByDay = useMemo(() => {
    const grouped = filteredGames.reduce((acc: Record<string, any[]>, game: any) => {
      if (!acc[game.day]) {
        acc[game.day] = []
      }
      acc[game.day].push(game)
      return acc
    }, {} as Record<string, Game[]>)

    // Sort games within each day by time slot and actual game time
    Object.keys(grouped).forEach(day => {
      grouped[day].sort((a, b) => {
        // For Sunday, sort by time slots first: Early < Late < Night
        if (day === 'Sunday') {
          const timeSlotOrder = { 'Early': 1, 'Late': 2, 'Night': 3 }
          const aTimeOrder = timeSlotOrder[a.timeSlot as keyof typeof timeSlotOrder] || 999
          const bTimeOrder = timeSlotOrder[b.timeSlot as keyof typeof timeSlotOrder] || 999
          if (aTimeOrder !== bTimeOrder) {
            return aTimeOrder - bTimeOrder
          }
        }
        // Then sort by actual game time within the time slot
        const timeA = new Date(a.gameTime || a.time)
        const timeB = new Date(b.gameTime || b.time)
        return timeA.getTime() - timeB.getTime()
      })
    })

    // Create ordered object based on dayOrder
    const orderedGrouped: Record<string, any[]> = {}
    const dayEntries = Object.entries(grouped)
      .map(([dayName, games]) => ({
        dayName,
        games,
        order: games[0]?.dayOrder || 999
      }))
      .sort((a, b) => a.order - b.order)

    dayEntries.forEach(({ dayName, games }) => {
      orderedGrouped[dayName] = games
    })

    return orderedGrouped
  }, [filteredGames])

  // Loading component
  const LoadingSpinner = () => (
    <div className="flex items-center justify-center p-8">
      <div className="glass rounded-xl p-6 text-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  )

  // Error fallback component
  const ErrorFallback = ({ error }: { error: Error }) => (
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
          if (gamesLoading) {
            return <LoadingSpinner />
          }
          if (gamesError) {
            return <ErrorFallback error={gamesError as Error} />
          }
          return (
            <GamesPage
              currentWeek={currentWeek}
              setCurrentWeek={handleWeekChange}
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