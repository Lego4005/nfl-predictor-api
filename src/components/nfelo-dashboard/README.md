# NFElo-Style Dashboard

This directory contains the implementation of the NFElo-inspired interface for the NFL Predictor API system. The dashboard provides a professional, data-dense betting interface that leverages the current prediction infrastructure while providing users with comprehensive game analysis, model performance metrics, and expected value calculations.

## Components

### Main Dashboard (`NFEloDashboard.jsx`)
The main dashboard component that orchestrates all other components and manages the overall state.

### Game List View (`GameListView.jsx`)
Displays games in a horizontal row format with:
- Team information (logo, record, name)
- Spread data (market line, model line, movement)
- Expected value metrics
- Game context (time, weather, stadium)

### EV Betting Card (`EVBettingCard.jsx`)
Implements sophisticated expected value calculations and displays:
- Team matchup with visual representation
- Game details (venue, time, weather)
- Model recommendations with reasoning
- Value metrics (EV percentage, cover probability, unit recommendations)

### Model Performance (`ModelPerformance.jsx`)
Showcases model accuracy through multiple dimensions:
- Overall performance metrics
- Category-specific performance
- Historical analysis tables
- Strengths and weaknesses identification

### Power Rankings (`PowerRankings.jsx`)
Displays comprehensive team evaluation through:
- Core ratings (ELO-based power rankings)
- Offensive and defensive metrics
- Advanced analytics (EPA statistics)
- Team movement indicators

### Weekly Navigation (`WeeklyNavigation.jsx`)
Provides intuitive navigation between weeks with:
- Previous/next week buttons
- Current week display

## Data Integration

The dashboard integrates multiple data sources:
- **Prediction Engine**: Current model outputs for spread and total predictions
- **Market Data**: Real-time odds from configured sportsbooks
- **Historical Context**: Team performance metrics and head-to-head records
- **Environmental Factors**: Weather conditions and venue information

## Expected Value Calculation

The dashboard implements sophisticated expected value calculations:
- Model predictions vs. market odds comparison
- Cover probability analysis
- Unit return calculations
- Betting recommendations based on value

## Real-Time Data Integration

The interface leverages existing WebSocket infrastructure for:
- Game status changes (score updates, line movements, weather changes)
- Model recalculations based on new information
- Market data refresh from multiple sportsbooks
- Performance tracking during games

## Responsive Design

The layout adapts across device sizes:
- **Desktop**: Full data tables with comprehensive information
- **Tablet**: Condensed tables with key metrics prioritized
- **Mobile**: Card-based layout with swipe navigation

## Accessibility

The interface maintains accessibility standards:
- Color independence (information conveyed through multiple visual cues)
- Screen reader support (proper ARIA labels and semantic markup)
- Keyboard navigation (full functionality without mouse interaction)
- High contrast mode (alternative color schemes for visibility)

## Usage

To access the NFElo dashboard, navigate to `/nfelo` in the application.

## Development

To run tests for the dashboard components:
```bash
npm test nfelo-dashboard
```

## Future Enhancements

Planned improvements include:
- Integration with real API data
- Enhanced EPA visualization
- More detailed historical performance charts
- Additional filtering and sorting options
- Dark mode enhancements