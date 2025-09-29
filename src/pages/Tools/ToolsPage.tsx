import React from 'react'

function ToolsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-2xl font-bold text-foreground">🔧 Tools & Utilities</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          {
            icon: '📊',
            title: 'Elo Calculator',
            description: 'Calculate team ratings and expected outcomes',
            delay: '0ms'
          },
          {
            icon: '🎯',
            title: 'Odds Converter',
            description: 'Convert between American, Decimal, and Fractional odds',
            delay: '100ms'
          },
          {
            icon: '💰',
            title: 'Bankroll Manager',
            description: 'Track your betting history and manage your bankroll',
            delay: '200ms'
          },
          {
            icon: '📈',
            title: 'Line Movement Tracker',
            description: 'Monitor betting line movements across sportsbooks',
            delay: '300ms'
          },
          {
            icon: '🔍',
            title: 'Value Bet Finder',
            description: 'Identify value betting opportunities',
            delay: '400ms'
          },
          {
            icon: '📋',
            title: 'Parlay Builder',
            description: 'Build and analyze multi-leg parlays',
            delay: '500ms'
          }
        ].map((tool, index) => (
          <div key={index} className={`glass border border-border rounded-2xl p-6 card-hover animate-card-in cursor-pointer [animation-delay:${tool.delay}]`}>
            <div className="text-3xl mb-3">{tool.icon}</div>
            <h3 className="text-lg font-semibold text-foreground mb-2">{tool.title}</h3>
            <p className="text-muted-foreground text-sm mb-4">{tool.description}</p>
            <button className="w-full px-4 py-2 bg-primary/20 text-primary border border-primary/30 rounded-lg hover:bg-primary/30 transition-colors">
              Launch Tool
            </button>
          </div>
        ))}
      </div>

      <div className="glass border border-border rounded-2xl p-6 animate-card-in [animation-delay:600ms]">
        <h3 className="text-lg font-semibold text-foreground mb-4">API Access</h3>
        <div className="space-y-3">
          <div className="p-4 glass-hover rounded-lg border border-border/50">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-foreground">REST API Endpoint</span>
              <span className="text-xs bg-success/20 text-success px-2 py-1 rounded-full border border-success/30">Active</span>
            </div>
            <code className="text-xs text-muted-foreground block font-mono">https://api.gridironelo.com/v1/</code>
          </div>
          <div className="p-4 glass-hover rounded-lg border border-border/50">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-foreground">WebSocket Feed</span>
              <span className="text-xs bg-success/20 text-success px-2 py-1 rounded-full border border-success/30">Connected</span>
            </div>
            <code className="text-xs text-muted-foreground block font-mono">wss://api.gridironelo.com/ws</code>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ToolsPage