import React, { useState, useRef, useEffect } from 'react'
import { getCurrentNFLWeek } from '../../utils/nflWeekCalculator'

interface WeekNavigationProps {
  currentWeek: number
  setCurrentWeek: (week: number) => void
}

function WeekNavigation({ currentWeek, setCurrentWeek }: WeekNavigationProps) {
  const [showWeekPicker, setShowWeekPicker] = useState(false)
  const [showQuickJump, setShowQuickJump] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const nflCurrentWeek = getCurrentNFLWeek(new Date('2025-09-29')).weekNumber

  // Get week status for styling
  const getWeekStatus = (week: number) => {
    if (week < nflCurrentWeek) return 'past'
    if (week === nflCurrentWeek) return 'current'
    return 'future'
  }

  const getWeekStatusLabel = (week: number) => {
    const status = getWeekStatus(week)
    switch (status) {
      case 'past': return 'Completed'
      case 'current': return 'Current Week'
      case 'future': return 'Upcoming'
      default: return ''
    }
  }

  const getWeekStatusColor = (week: number) => {
    const status = getWeekStatus(week)
    switch (status) {
      case 'past': return 'text-muted-foreground'
      case 'current': return 'text-primary'
      case 'future': return 'text-foreground'
      default: return 'text-foreground'
    }
  }

  const getWeekBorderColor = (week: number) => {
    const status = getWeekStatus(week)
    switch (status) {
      case 'past': return 'border-muted-foreground/30'
      case 'current': return 'border-primary'
      case 'future': return 'border-border'
      default: return 'border-border'
    }
  }

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowWeekPicker(false)
        setShowQuickJump(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Season progress calculation
  const seasonProgress = ((currentWeek - 1) / 17) * 100

  return (
    <div className="mb-6">
      {/* Progress Bar */}
      <div className="w-full max-w-2xl mx-auto mb-4">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
          <span>Week 1</span>
          <span className="text-primary font-medium">2025 NFL Season</span>
          <span>Week 18</span>
        </div>
        <div className="relative w-full h-2 bg-muted/30 rounded-full overflow-hidden">
          <div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary/80 to-primary transition-all duration-500 ease-out"
            style={{ width: `${seasonProgress}%` }}
          />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-primary border-2 border-background rounded-full shadow-sm transition-all duration-500 ease-out"
            style={{ left: `calc(${seasonProgress}% - 6px)` }}
          />
        </div>
      </div>

      {/* Main Navigation */}
      <div className="flex items-center justify-center gap-3 relative" ref={dropdownRef}>
        {/* Previous Week Button */}
        <button
          onClick={() => setCurrentWeek(Math.max(1, currentWeek - 1))}
          disabled={currentWeek <= 1}
          className="flex items-center justify-center w-10 h-10 rounded-lg glass border border-border hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-transparent group"
          title="Previous Week"
          aria-label="Go to previous week"
        >
          <span className="text-sm group-hover:text-primary transition-colors">‹</span>
        </button>

        {/* Quick Jump to Start */}
        <button
          onClick={() => setShowQuickJump(!showQuickJump)}
          className="px-3 py-2 text-xs font-medium rounded-lg glass border border-border hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 hidden sm:block"
          title="Quick Jump"
        >
          ⚡
        </button>

        {/* Current Week Display */}
        <div className="relative">
          <button
            onClick={() => setShowWeekPicker(!showWeekPicker)}
            className={`flex flex-col items-center px-8 py-4 glass border-2 rounded-xl hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 min-w-[160px] group shadow-sm ${getWeekBorderColor(currentWeek)}`}
            aria-expanded={showWeekPicker}
            aria-haspopup="listbox"
          >
            <div className="flex items-center space-x-3">
              <div className="relative">
                <span className="text-lg">🏈</span>
                {getWeekStatus(currentWeek) === 'current' && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full animate-pulse" />
                )}
              </div>
              <div className="text-center">
                <div className={`font-bold text-xl ${getWeekStatusColor(currentWeek)} leading-tight`}>
                  Week {currentWeek}
                </div>
                <div className={`text-xs font-medium ${getWeekStatusColor(currentWeek)} opacity-75 mt-0.5`}>
                  {getWeekStatusLabel(currentWeek)}
                </div>
              </div>
              <span className={`text-xs transition-transform duration-200 ${showWeekPicker ? 'rotate-180' : ''} ${getWeekStatusColor(currentWeek)} opacity-60`}>
                ▼
              </span>
            </div>
          </button>

          {/* Week Picker Dropdown */}
          {showWeekPicker && (
            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-80 glass border border-border rounded-xl p-4 z-50 shadow-2xl animate-in slide-in-from-top-2 duration-200">
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-foreground mb-2">Select Week</h3>
                <div className="grid grid-cols-6 gap-2 max-h-48 overflow-y-auto">
                  {Array.from({ length: 18 }, (_, i) => {
                    const week = i + 1
                    const status = getWeekStatus(week)
                    const isSelected = week === currentWeek

                    return (
                      <button
                        key={week}
                        onClick={() => {
                          setCurrentWeek(week)
                          setShowWeekPicker(false)
                        }}
                        className={`
                          relative px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95
                          ${isSelected
                            ? 'bg-primary text-primary-foreground shadow-md border-2 border-primary transform scale-105'
                            : status === 'past'
                              ? 'bg-muted/40 text-muted-foreground hover:bg-muted/60 border border-transparent hover:border-muted-foreground/20'
                              : status === 'current'
                                ? 'bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30 shadow-sm'
                                : 'bg-background/60 text-foreground hover:bg-background/80 border border-border hover:border-primary/30'
                          }
                        `}
                        title={`Week ${week} - ${getWeekStatusLabel(week)}`}
                        aria-label={`Select week ${week}, ${getWeekStatusLabel(week)}`}
                      >
                        <span className="relative z-10">{week}</span>
                        {status === 'current' && !isSelected && (
                          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-primary rounded-full animate-pulse" />
                        )}
                        {isSelected && (
                          <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary/40 rounded-lg" />
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Week Legend */}
              <div className="flex items-center justify-between text-xs pt-3 border-t border-border">
                <div className="flex items-center space-x-1.5">
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full" />
                  <span className="text-muted-foreground">Completed</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                  <span className="text-primary font-medium">Current</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <div className="w-2 h-2 bg-foreground/60 rounded-full" />
                  <span className="text-foreground">Upcoming</span>
                </div>
              </div>
            </div>
          )}

          {/* Quick Jump Dropdown */}
          {showQuickJump && (
            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-64 glass border border-border rounded-xl p-3 z-50 shadow-xl animate-in slide-in-from-top-2 duration-200">
              <h3 className="text-sm font-semibold text-foreground mb-2">Quick Jump</h3>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    setCurrentWeek(1)
                    setShowQuickJump(false)
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-primary/10 transition-colors text-sm"
                >
                  <span className="font-medium">Week 1</span>
                  <span className="text-muted-foreground ml-2">Season Start</span>
                </button>
                <button
                  onClick={() => {
                    setCurrentWeek(nflCurrentWeek)
                    setShowQuickJump(false)
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-primary/10 transition-colors text-sm"
                >
                  <span className="font-medium">Week {nflCurrentWeek}</span>
                  <span className="text-primary ml-2">Current Week</span>
                </button>
                <button
                  onClick={() => {
                    setCurrentWeek(18)
                    setShowQuickJump(false)
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-primary/10 transition-colors text-sm"
                >
                  <span className="font-medium">Week 18</span>
                  <span className="text-muted-foreground ml-2">Season End</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Next Week Button */}
        <button
          onClick={() => setCurrentWeek(Math.min(18, currentWeek + 1))}
          disabled={currentWeek >= 18}
          className="flex items-center justify-center w-10 h-10 rounded-lg glass border border-border hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-transparent group"
          title="Next Week"
          aria-label="Go to next week"
        >
          <span className="text-sm group-hover:text-primary transition-colors">›</span>
        </button>

        {/* Quick Jump to Current Week */}
        {currentWeek !== nflCurrentWeek && (
          <div className="relative">
            <button
              onClick={() => setCurrentWeek(nflCurrentWeek)}
              className="px-4 py-2.5 bg-primary/15 text-primary text-sm font-medium rounded-lg hover:bg-primary/25 hover:scale-105 transition-all duration-200 border border-primary/30 shadow-sm group"
              title={`Jump to Current Week (${nflCurrentWeek})`}
            >
              <span className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                <span>Live</span>
              </span>
            </button>
          </div>
        )}
      </div>

      {/* Mobile Week Indicators */}
      <div className="flex justify-center mt-3 sm:hidden">
        <div className="flex items-center space-x-1">
          {Array.from({ length: Math.min(5, 18) }, (_, i) => {
            const week = Math.max(1, Math.min(18, currentWeek - 2 + i))
            const isActive = week === currentWeek
            const status = getWeekStatus(week)

            return (
              <button
                key={week}
                onClick={() => setCurrentWeek(week)}
                className={`
                  w-8 h-8 rounded-lg text-xs font-medium transition-all duration-200
                  ${isActive
                    ? 'bg-primary text-primary-foreground scale-110 shadow-md'
                    : status === 'current'
                      ? 'bg-primary/20 text-primary'
                      : 'bg-muted/40 text-muted-foreground hover:bg-muted/60'
                  }
                `}
              >
                {week}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default WeekNavigation