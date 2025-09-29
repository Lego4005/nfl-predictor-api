import React from 'react'

interface HomePageProps {
  onNavigate?: (pageId: string) => void
}

function HomePage({ onNavigate }: HomePageProps) {
  return (
    <div className="space-y-6">
      <div className="text-center py-12">
        <h1 className="text-3xl font-bold text-foreground mb-4">🏠 Welcome to PickIQ</h1>
        <p className="text-gray-400 text-lg mb-8">Your ultimate NFL analytics and prediction dashboard</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <button
            onClick={() => onNavigate?.('games')}
            className="glass border border-border rounded-2xl p-6 hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:shadow-primary/10"
          >
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-3xl mb-3">🏈</span>
              <h3 className="text-lg font-semibold text-foreground mb-2">Games & Predictions</h3>
            </div>
            <p className="text-muted-foreground text-sm">Real-time game analysis and betting predictions</p>
          </button>

          <button
            onClick={() => onNavigate?.('rankings')}
            className="glass border border-border rounded-2xl p-6 hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:shadow-primary/10"
          >
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-3xl mb-3">🏆</span>
              <h3 className="text-lg font-semibold text-foreground mb-2">Team Rankings</h3>
            </div>
            <p className="text-muted-foreground text-sm">Power rankings and team performance metrics</p>
          </button>

          <button
            onClick={() => onNavigate?.('performance')}
            className="glass border border-border rounded-2xl p-6 hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:shadow-primary/10"
          >
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-3xl mb-3">📊</span>
              <h3 className="text-lg font-semibold text-foreground mb-2">Performance Analytics</h3>
            </div>
            <p className="text-muted-foreground text-sm">Model accuracy and prediction insights</p>
          </button>
        </div>
      </div>
    </div>
  )
}

export default HomePage