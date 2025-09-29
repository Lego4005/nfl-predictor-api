import React from 'react'

interface WeekNavigationProps {
  currentWeek: number
  setCurrentWeek: (week: number) => void
}

function WeekNavigation({ currentWeek, setCurrentWeek }: WeekNavigationProps) {
  return (
    <div className="flex items-center justify-center space-x-4 mb-4">
      <button
        onClick={() => setCurrentWeek(Math.max(1, currentWeek - 1))}
        disabled={currentWeek <= 1}
        className="p-2 rounded-lg glass border border-border hover:border-primary/40 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        ←
      </button>
      
      <div className="flex items-center space-x-2 px-4 py-2 glass border border-border rounded-lg">
        <span className="text-sm">📅</span>
        <span className="font-medium text-foreground">Week {currentWeek}</span>
      </div>
      
      <button
        onClick={() => setCurrentWeek(Math.min(18, currentWeek + 1))}
        disabled={currentWeek >= 18}
        className="p-2 rounded-lg glass border border-border hover:border-primary/40 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        →
      </button>
    </div>
  )
}

export default WeekNavigation