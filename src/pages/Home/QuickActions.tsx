import React from 'react'

interface QuickActionsProps {
  onNavigate?: (pageId: string) => void
}

interface QuickActionCardProps {
  icon: string
  title: string
  description: string
  onClick: () => void
  delay?: string
}

function QuickActionCard({ icon, title, description, onClick, delay = '0ms' }: QuickActionCardProps) {
  return (
    <button
      onClick={onClick}
      className={`glass border border-border rounded-2xl p-6 hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:shadow-primary/10 animate-card-in cursor-pointer [animation-delay:${delay}] text-left w-full`}
    >
      <div className="flex items-start space-x-3">
        <span className="text-3xl flex-shrink-0">{icon}</span>
        <div>
          <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
          <p className="text-muted-foreground text-sm">{description}</p>
        </div>
      </div>
    </button>
  )
}

function QuickActions({ onNavigate }: QuickActionsProps) {
  const actions = [
    {
      icon: '🏈',
      title: 'View This Week\'s Games',
      description: 'See predictions and betting lines for upcoming games',
      onClick: () => onNavigate?.('games'),
      delay: '0ms'
    },
    {
      icon: '🎯',
      title: 'Join Confidence Pool',
      description: 'Make your weekly picks and compete with others',
      onClick: () => onNavigate?.('confidence-pool'),
      delay: '100ms'
    },
    {
      icon: '🃏',
      title: 'Check Betting Card',
      description: 'Find the best value bets with AI analysis',
      onClick: () => onNavigate?.('betting-card'),
      delay: '200ms'
    },
    {
      icon: '🏆',
      title: 'Power Rankings',
      description: 'See how teams stack up with Elo ratings',
      onClick: () => onNavigate?.('rankings'),
      delay: '300ms'
    },
    {
      icon: '📊',
      title: 'Model Performance',
      description: 'Track prediction accuracy and ROI',
      onClick: () => onNavigate?.('performance'),
      delay: '400ms'
    },
    {
      icon: '👥',
      title: 'Team Directory',
      description: 'Detailed stats and analysis for all teams',
      onClick: () => onNavigate?.('teams'),
      delay: '500ms'
    }
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-foreground">Quick Actions</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {actions.map((action, index) => (
          <QuickActionCard
            key={index}
            icon={action.icon}
            title={action.title}
            description={action.description}
            onClick={action.onClick}
            delay={action.delay}
          />
        ))}
      </div>
    </div>
  )
}

export default QuickActions