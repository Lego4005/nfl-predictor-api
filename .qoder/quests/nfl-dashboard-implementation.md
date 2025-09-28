# NFL Dashboard Implementation Design Document

## 1. Overview

This document outlines the design for a professional NFL prediction dashboard that provides comprehensive analytics and betting insights for NFL games. The dashboard will feature a dark theme with accent colors, card-based layout, and responsive design to work across desktop and mobile devices.

### 1.1 Purpose

The dashboard aims to provide users with:

- Weekly game projections with Open, Current, and Model lines
- Deep-dive game detail pages for model projections and probabilities
- Model transparency via performance metrics
- Team and QB analytics
- Betting tools and calculators
- Responsive, accessible interface with dark theme

### 1.2 Scope

The dashboard will include:

- Main dashboard with game listings
- Game detail views
- Model performance tracking
- Team power rankings
- Player prop analysis
- Betting tools and calculators

### 1.3 Key Features

- **Expected Value Analysis**: Calculate and display EV for each game
- **Model Projections**: Show predicted outcomes based on the AI model
- **Win Probability**: Display both market and model win probabilities
- **Market Segmentation**: Show how different factors affect the spread
- **Player Matchup Stats**: Compare key players' projected performance
- **EPA Metrics**: Display expected points added for each team

## 2. Architecture

### 2.1 System Components

``mermaid
graph TD
    A[Frontend - React/Tailwind] --> B[API Layer]
    B --> C[Supabase Database]
    B --> D[External Data Sources]
    E[Mobile Clients] --> A
    F[Web Clients] --> A
    G[Admin Tools] --> B

    subgraph "Frontend Components"
        A --> H[NFL Dashboard]
        A --> I[Game List View]
        A --> J[Game Detail View]
        A --> K[Model Performance]
        A --> L[Power Rankings]
        A --> M[Player Props]
        A --> N[Betting Tools]
    end
    
    subgraph "Backend Services"
        B --> O[Game Data Service]
        B --> P[Prediction Service]
        B --> Q[Expert Analysis Service]
        B --> R[Betting Odds Service]
    end

```

### 2.2 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React with TypeScript, Tailwind CSS |
| UI Components | Radix UI, Framer Motion |
| State Management | React Hooks, Context API |
| Backend | Supabase, Python APIs |
| Data Sources | ESPN, NFL APIs, Sportsdata.io |
| Deployment | Docker, Render |

Based on the existing codebase analysis, the NFL dashboard will leverage:

- Existing `TeamLogo` component for team imagery
- Radix UI `Tabs` for navigation between dashboard sections
- Framer Motion for animations and transitions
- Supabase client for data fetching
- Existing CSS variables for theming

### 2.3 Data Flow

``mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Service
    participant S as Supabase
    participant E as External APIs

    U->>F: Navigate to dashboard
    F->>A: Request weekly games
    A->>S: Query games data
    S-->>A: Return games
    A->>E: Fetch current odds
    E-->>A: Return odds data
    A-->>F: Return combined data
    F->>U: Render dashboard
```

## 3. Component Architecture

### 3.1 Main Components

#### 3.1.1 NFL Dashboard (Root Component)

The main dashboard component that orchestrates all other components and manages global state. Based on the existing `NFEloDashboard` component, this will include:

- Week selection controls
- Tab-based navigation between sections
- Data fetching and state management
- Refresh functionality

#### 3.1.2 Game List View

Displays games in a card-based layout grouped by day with key metrics. Based on the existing `GameListView` component, each game row will include:

- Team logos and names
- Game time and venue
- Market spread vs model spread
- Expected value indicators
- Confidence meters
- Win probability displays

#### 3.1.3 Game Detail View

Provides in-depth analysis for individual games with model projections. Based on the requirements, this will include:

- Two-column layout for desktop
- Model projections and win probabilities
- QB matchup analysis
- Team matchup stats
- EPA summaries
- Market segmentation factors

#### 3.1.4 Model Performance

Shows model accuracy metrics and historical performance. Based on the existing `ModelPerformance` component, this will include:

- Overall accuracy statistics
- Performance by category
- Recent predictions tracking
- Strengths and weaknesses analysis
- Historical performance charts

#### 3.1.5 Power Rankings

Displays team rankings with EPA metrics. Based on the existing `PowerRankings` component, this will include:

- Team rankings with movement indicators
- ELO ratings
- Offensive and defensive EPA metrics
- Strength of schedule metrics

#### 3.1.6 Player Props

Shows player prop bets with confidence indicators. This will include:

- High-confidence prop bets
- Player statistics
- Over/under recommendations
- Confidence levels

#### 3.1.7 Betting Tools

Collection of calculators and betting utilities. This will include:

- Odds converter
- Cover probability calculator
- Hedge calculator
- Parlay odds calculator

### 3.2 Component Hierarchy

``mermaid
graph TD
    A[NFLDashboard] --> B[WeeklyNavigation]
    A --> C[StatsOverview]
    A --> D[Tabs]
    D --> E[GameListView]
    D --> F[EVBettingCard]
    D --> G[ModelPerformance]
    D --> H[PowerRankings]

    E --> I[GameRow]
    I --> J[TeamLogo]
    I --> K[SpreadData]
    I --> L[ExpectedValue]
    I --> M[WinProbability]
    
    F --> N[EVGameCard]
    N --> J
    N --> O[BettingRecommendation]
    N --> P[GameContext]
    
    G --> Q[PerformanceMetrics]
    G --> R[CategoryPerformance]
    G --> S[RecentPicks]
    
    H --> T[TeamRanking]
    T --> J
    T --> U[TeamStats]

```

## 4. UI/UX Design

### 4.1 Visual Design

#### 4.1.1 Color Palette

- **Background**: #121212 (Dark)
- **Primary**: #FF0000 (Red)
- **Secondary**: #00A8E8 (Blue)
- **Accent**: #00FF00 (Green)
- **Text**: #E8EAED (Light Gray)
- **Muted Text**: #A3ABB6 (Gray)
- **Surface**: #14161A (Card Background)

Based on the existing CSS variables in the codebase, we'll extend the current theme system to support these colors while maintaining compatibility with existing components.

#### 4.1.2 Typography

- **Headers**: System UI, bold, 24-32px
- **Body**: System UI, regular, 14-16px
- **Captions**: System UI, light, 12-14px

#### 4.1.3 Spacing System

- **XS**: 4px
- **S**: 8px
- **M**: 16px
- **L**: 24px
- **XL**: 32px
- **XXL**: 48px

### 4.2 Layout Structure

#### 4.2.1 Desktop Layout

```

+-----------------------------------------------------+
| Header: Logo, Week Selector, Refresh                |
+-------------------+---------------------------------+
| Sidebar           | Main Content                    |
| - Navigation      | - Game List/Grid                |
| - Tools           | - Game Cards                    |
| - Ad Banner       | - Detailed Views                |
+-------------------+---------------------------------+
| Footer: Links, Disclosures                          |
+-----------------------------------------------------+

```

#### 4.2.2 Mobile Layout

```

+---------------------------------+
| Header: Logo, Menu, Refresh     |
+---------------------------------+
| Main Content                    |
| - Week Selector                 |
| - Game Cards (Stacked)          |
| - Detailed Views                |
+---------------------------------+
| Bottom Navigation               |
+---------------------------------+

```

### 4.3 Component Specifications

#### 4.3.1 Game Card

Each game card displays:

- Team logos and names
- Game time and date
- Current odds (Open, Current, Model)
- Model predictions
- Expected value (EV) indicator
- Win probability bars
- Confidence indicators

#### 4.3.2 Game Detail View

Two-column layout with:

- Left column: Model projections, win probability, quarterback matchup
- Right column: Proposition details, net line adjustment, market segmentation
- Detailed breakdown of team match-up stats
- EPA (Expected Points Added) metrics
- Value indicators for each player

## 5. Data Models

### 5.1 Game Data Model

Based on the existing types and the nfelo-style dashboard requirements:

``typescript
interface Game {
  id: string;
  homeTeam: string; // Team abbreviation
  awayTeam: string; // Team abbreviation
  startTime: string; // ISO timestamp
  status: 'scheduled' | 'live' | 'final';
  homeScore: number;
  awayScore: number;
  spread: number; // Market spread
  modelSpread: number; // Model predicted spread
  spreadMovement: number; // Change in spread
  overUnder: number; // Market total
  modelTotal: number; // Model predicted total
  homeWinProb: number; // Model win probability for home team
  awayWinProb: number; // Model win probability for away team
  ev: number; // Expected value
  confidence: number; // Model confidence
  weather?: WeatherConditions;
  venue?: string;
}

interface Team {
  id: string;
  name: string;
  city: string;
  abbreviation: string;
  logo: string;
  primaryColor: string;
  secondaryColor: string;
  record: TeamRecord;
  stats?: TeamStats;
  injuries?: InjuryReport[];
}

interface Prediction {
  gameId: string;
  homeTeamWinProbability: number;
  awayTeamWinProbability: number;
  predictedHomeScore: number;
  predictedAwayScore: number;
  confidence: PredictionConfidence;
  modelAccuracy: number;
  keyFactors: string[];
  lastUpdated: string;
}

```

### 5.2 Betting Data Model

Based on the existing types and nfelo-style requirements:

``typescript
interface BettingOdds {
  gameId: string;
  sportsbook: string;
  homeOdds: number;
  awayOdds: number;
  overUnder: number;
  spread: number;
  lastUpdated: string;
  homeSpreadOdds?: number;
  awaySpreadOdds?: number;
  overOdds?: number;
  underOdds?: number;
}

interface BettingInsight {
  gameId: string;
  recommendation: BettingRecommendation;
  confidence: number;
  expectedValue: number; // EV percentage
  reasoning: string[];
  riskLevel: RiskLevel;
  suggestedBetTypes?: BetType[];
}

// Enhanced game data for betting insights
interface GameWithBetting extends Game {
  openSpread?: number; // Opening line
  currentSpread?: number; // Current market line
  modelSpread: number; // Model prediction
  openTotal?: number; // Opening total
  currentTotal?: number; // Current market total
  modelTotal: number; // Model prediction
  ev: number; // Expected value
  confidence: number; // Model confidence
  bettingRecommendation?: string; // Strong Buy, Buy, Consider, Avoid
}

```

### 5.3 Performance Data Model

``typescript
interface ModelPerformance {
  week: string;
  accuracy: number;
  predictions: number;
  correct: number;
  averageConfidence: number;
  bestPredictions: string[];
  worstPredictions: string[];
}

interface Expert {
  id: string;
  name: string;
  type: ExpertType;
  specialization: string[];
  accuracy_metrics: {
    overall: number;
    by_category: Record<PredictionCategory, number>;
    by_prediction_type: Record<string, number>;
    recent_performance: number;
    season_performance: number;
  };
}

```

## 16. Data Integration and API Services

The dashboard will leverage existing API services and data models while incorporating the AI expert system.

### 16.1 NFL Prediction API Service

Based on the existing `nflAPI` service, the dashboard will use:

``typescript
class NFLPredictionAPIService {
  public readonly aiCouncil: AICouncilAPIService;
  public readonly expertPredictions: ExpertPredictionsAPIService;
  public readonly expertBattles: ExpertBattleAPIService;
  public readonly expertPerformance: ExpertPerformanceAPIService;
  public readonly systemHealth: SystemHealthAPIService;
  public readonly gameData: GameDataAPIService;
}

```

### 16.2 Data Fetching Strategy

#### 16.2.1 Dashboard Data
```typescript
// Combined dashboard data fetching
async getDashboardData(week: number, season: number) {
  try {
    const [games, experts, consensus] = await Promise.all([
      this.gameData.getGamesByWeek(week, season),
      this.aiCouncil.getCouncilMembers(),
      this.aiCouncil.getConsensusForWeek(week)
    ]);
    
    return {
      games,
      experts,
      consensus,
      lastUpdated: new Date().toISOString()
    };
  } catch (error) {
    throw new APIError('Failed to load dashboard data', 500);
  }
}
```

#### 16.2.2 Game Detail Data

``typescript
// Detailed game data with expert predictions
async getGameDetailData(gameId: string) {
  try {
    const [
      game,
      predictions,
      consensus,
      expertPredictions
    ] = await Promise.all([
      this.gameData.getGame(gameId),
      this.gameData.getGamePredictions(gameId),
      this.aiCouncil.getConsensusForGame(gameId),
      this.expertPredictions.getExpertPredictions(gameId)
    ]);

    return {
      game,
      predictions,
      consensus,
      expertPredictions,
      lastUpdated: new Date().toISOString()
    };
  } catch (error) {
    throw new APIError('Failed to load game detail data', 500);
  }
}

```

### 16.3 Data Transformation

#### 16.3.1 Game Data Transformation

Transform raw game data to match dashboard requirements:

``typescript
interface RawGame {
  game_id: string;
  home_team: string;
  away_team: string;
  game_time: string;
  status: string;
  week: number;
  season: number;
  // ... other fields
}

interface DashboardGame extends Game {
  // Enhanced with predictions and expert data
  predictions?: Prediction[];
  expertConsensus?: ConsensusResult[];
  expertPredictions?: ExpertPrediction[];
}

```

#### 16.3.2 Expert Data Transformation

Transform expert data for visualization:

``typescript
interface RawExpertPrediction {
  expert_id: string;
  game_id: string;
  predictions: any[];
  // ... other fields
}

interface TransformedExpertPrediction {
  expert: Expert;
  predictions: CategoryPrediction[];
  confidence: number;
  timestamp: string;
}

```

### 16.4 Caching Strategy

Implement caching to improve performance:

- **Game Data**: Cache for 5 minutes
- **Expert Data**: Cache for 10 minutes
- **Consensus Data**: Cache for 15 minutes
- **Performance Data**: Cache for 30 minutes

### 16.5 Error Handling

Robust error handling for data fetching:

``typescript
class DashboardDataService {
  async fetchData<T>(fetchFn: () => Promise<T>): Promise<{
    data: T | null;
    error: string | null;
    loading: boolean;
  }> {
    try {
      const data = await fetchFn();
      return { data, error: null, loading: false };
    } catch (error) {
      return {
        data: null,
        error: error instanceof APIError ? error.message : 'An unexpected error occurred',
        loading: false
      };
    }
  }
}
```

## 17. Theming and Styling

The dashboard will maintain a consistent dark theme with accent colors as specified in the requirements while leveraging the existing styling system.

### 17.1 CSS Variables Integration

Extend existing CSS variables to support the dashboard theme:

``css
:root {
  /*Existing variables */
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... other existing variables*/
  
  /*Dashboard-specific variables */
  --dashboard-bg: 12 12 12; /* #121212 */
  --dashboard-primary: 0 100% 50%; /* #FF0000 */
  --dashboard-secondary: 200 90% 47%; /* #00A8E8 */
  --dashboard-accent: 120 100% 50%; /* #00FF00 */
  --dashboard-surface: 14 16 1A; /* #14161A */
  --dashboard-text: 232 234 237; /* #E8EAED */
  --dashboard-muted: 163 171 182; /* #A3ABB6*/
}

.dark {
  /*Existing dark theme variables */
  --background: 0 0% 8%;
  --foreground: 0 0% 96%;
  /* ... other existing variables*/
  
  /*Dashboard-specific dark theme */
  --dashboard-bg: 12 12 12; /* #121212 */
  --dashboard-primary: 0 100% 50%; /* #FF0000 */
  --dashboard-secondary: 200 90% 47%; /* #00A8E8 */
  --dashboard-accent: 120 100% 50%; /* #00FF00 */
  --dashboard-surface: 14 16 1A; /* #14161A */
  --dashboard-text: 232 234 237; /* #E8EAED */
  --dashboard-muted: 163 171 182; /* #A3ABB6*/
}

```

### 17.2 Component Styling

#### 17.2.1 Card Components
Implement card-based layout with consistent styling:

``jsx
const DashboardCard = ({ children, className = '' }) => (
  <div className={`
    bg-[hsl(var(--dashboard-surface))] 
    rounded-xl 
    shadow-lg 
    border 
    border-gray-700 
    transition-all 
    duration-300
    ${className}
  `}>
    {children}
  </div>
);
```

#### 17.2.2 Color-coded Indicators

Use consistent color coding for different metrics:

``css
/*Expected Value indicators*/
.ev-positive {
  @apply text-green-400 bg-green-900/20;
}

.ev-negative {
  @apply text-red-400 bg-red-900/20;
}

/*Confidence indicators*/
.confidence-high {
  @apply text-blue-400;
}

.confidence-medium {
  @apply text-yellow-400;
}

.confidence-low {
  @apply text-gray-400;
}

/*Expert performance*/
.expert-top {
  @apply text-yellow-400;
}

.expert-good {
  @apply text-green-400;
}

.expert-average {
  @apply text-blue-400;
}

.expert-low {
  @apply text-red-400;
}

```

### 17.3 Responsive Design Implementation

#### 17.3.1 Breakpoint Definitions

``css
/*Mobile-first approach*/
.dashboard-container {
  @apply px-4 py-6;
}

/*Tablet*/
@media (min-width: 768px) {
  .dashboard-container {
    @apply px-6 py-8;
  }
  
  .game-grid {
    @apply grid-cols-2 gap-4;
  }
}

/*Desktop*/
@media (min-width: 1024px) {
  .dashboard-container {
    @apply px-8 py-10 max-w-7xl mx-auto;
  }
  
  .game-grid {
    @apply grid-cols-1 gap-4;
  }
  
  .dashboard-layout {
    @apply grid grid-cols-4 gap-6;
  }
  
  .sidebar {
    @apply col-span-1;
  }
  
  .main-content {
    @apply col-span-3;
  }
}

```

### 17.4 Animation and Transitions

Use Framer Motion for consistent animations:

``jsx
import { motion } from 'framer-motion';

const AnimatedCard = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
    className="card"
  >
    {children}
  </motion.div>
);

```

### 17.5 Accessibility Compliance

Ensure all components meet WCAG standards:

```jsx
const AccessibleButton = ({ onClick, children, ariaLabel }) => (
  <button
    onClick={onClick}
    aria-label={ariaLabel}
    className="focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    {children}
  </button>
);
```

## 18. Implementation Approach

The NFL dashboard implementation will leverage existing components and infrastructure while integrating the AI expert system to provide a comprehensive analytics platform.

### 18.1 Leveraging Existing Components

1. **UI Foundation**: Use existing `NFEloDashboard`, `GameListView`, `ModelPerformance`, and `PowerRankings` components as starting points
2. **Styling System**: Extend current Tailwind CSS configuration and CSS variables
3. **Data Components**: Utilize existing `TeamLogo` and other UI components
4. **API Services**: Build upon existing `nflAPI` service structure

### 18.2 AI Expert Integration

1. **Expert Visualization**: Create new components to display the 15 personality-based experts
2. **Consensus Display**: Implement consensus visualization for expert predictions
3. **Performance Tracking**: Integrate expert performance metrics alongside model performance
4. **Prediction Detail**: Enhance game detail views with expert reasoning and analysis

### 18.3 Data Integration

1. **API Layer**: Extend existing API services to fetch expert predictions and consensus
2. **Data Transformation**: Transform raw data to match dashboard requirements
3. **Caching Strategy**: Implement efficient caching for improved performance
4. **Error Handling**: Maintain consistent error handling across all data operations

### 18.4 Styling Consistency

1. **Dark Theme**: Implement consistent dark theme with specified accent colors
2. **Card-based Layout**: Use card components for all major content areas
3. **Responsive Design**: Ensure consistent experience across all device sizes
4. **Accessibility**: Maintain WCAG compliance for all components

### 18.5 Development Phases

1. **Phase 1**: Core dashboard structure with existing components
2. **Phase 2**: AI expert integration and visualization
3. **Phase 3**: Enhanced data display and filtering
4. **Phase 4**: Performance optimization and testing
5. **Phase 5**: Final styling and accessibility review

This approach ensures we maintain consistency with the existing look and feel while implementing our unique data and AI expert system.

## 19. PRD Alignment and Enhancements

Based on the detailed PRD and Engineering Appendix, the implementation will be enhanced to match the nfelo-style dashboard paradigm.

### 19.1 Information Architecture & Routing

The dashboard will implement a route-based navigation structure rather than tab-based:

- **Routes**:
  - `/` (Overview)
  - `/games` (Weekly game projections)
  - `/games/[slug]` (Game detail pages)
  - `/games/nfl-model-performance` (Model performance metrics)
  - `/ev-bets` (Expected value betting opportunities)
  - `/power-ratings` (Team power ratings)
  - `/qb-rankings` (Quarterback rankings)
  - `/receiving-leaders` (Top receivers)
  - `/tools/*` (Betting tools and calculators)
  - `/about`, `/analysis`, `/disclosure` (Static pages)

- **Sidebar Navigation**:
  - Persistent left sidebar with sections:
    - Predictions: Games, Confidence Picks, Betting Card, Model Performance
    - Teams: Power Ratings, EPA Tiers, Tendencies, Strength of Schedule, Win Totals
    - QBs: QB Rankings, Era Adjusted
    - Tools & More: Odds, Cover Prob, Hold, Hedge, Parlay, Passer Rating, HFA Tracker
    - About/Analysis

### 19.2 Power Ratings Page Specification

The power ratings page will be implemented as a dense, sortable table matching nfelo's design:

#### 19.2.1 Visual Design

- **Theme**: Dark background (#121212), surface (#14161A), text (#E8EAED)
- **Accents**: Brand (#00A8E8), Positive (#00FF00), Negative (#FF4D4F)
- **Layout**: Compact table with one row per team

#### 19.2.2 Table Columns

- **Team Identity**: Logo, team code, record
- **nfelo Metrics**: Elo rating, QB adjustment, WoW change, YTD value
- **Offensive EPA**: Play, Pass, Rush splits
- **Defensive EPA**: Play, Pass, Rush splits
- **Points/Game**: For, Against, Net difference
- **Wins**: Actual, Pythagorean, Elo, Film

#### 19.2.3 Behaviors

- **Sortable Columns**: Click headers to sort by any metric
- **Signed Number Formatting**: Color-coded positive/negative values
- **Movement Indicators**: Arrows and color pills for ranking changes
- **Responsive Design**: Hide less-critical columns on smaller screens

### 19.3 Component and Data Contracts

#### 19.3.1 TeamPowerRow Component

```typescript
interface TeamPowerRowProps {
  logo: string;
  name: string;
  code: string;
  record: string;
  nfelo: number;
  qbAdj: number;
  wowChange: number;
  ytdValue: number;
  offEPA: { play: number; pass: number; rush: number };
  defEPA: { play: number; pass: number; rush: number };
  pointsFor: number;
  pointsAgainst: number;
  net: number;
  wins: number;
  pythag: number;
  eloWins: number;
  filmWins: number;
  movement: 'up' | 'down' | null;
  isBiggestRise: boolean;
  isBiggestFall: boolean;
}
```

#### 19.3.2 Game Data Contracts

``typescript
interface GameRowData {
  id: string;
  slug: string;
  kickoff: string;
  bucket: 'thu' | 'sun_early' | 'sun_late' | 'mon';
  teams: { home: TeamRef; away: TeamRef };
  markets: {
    open: MarketSnapshot;
    current: MarketSnapshot;
    model: ModelProjection;
  };
  ev?: { side: 'home' | 'away' | null; value: number };
  tags?: string[];
}

interface GameDetailData extends GameRowData {
  matchupStats: {
    offEpa: { home: number; away: number };
    defEpa: { home: number; away: number };
    recentForm?: { home: number; away: number };
  };
  qb: {
    home: { name: string; rating: number; epa?: number };
    away: { name: string; rating: number; epa?: number };
  };
  marketFactors?: {
    injuries?: string[];
    weather?: string;
    travel?: string;
    rest?: string;
  };
}

```

### 19.4 Theme Tokens Integration

Extend CSS variables to match the specified color palette:

```css
:root {
  --bg: #0E0F12;
  --surface: #14161A;
  --surface-2: #1B1F24;
  --text: #E8EAED;
  --muted: #A3ABB6;
  --divider: #2A2F36;
  --brand: #00A8E8;
  --ev-pos: #00FF88;
  --ev-neg: #FF5A5F;
  --shadow-1: 0 1px 2px rgba(0,0,0,0.3);
}

html, body {
  background: var(--bg);
  color: var(--text);
}
```

### 19.5 Reusable DataTable Component

Implement a reusable DataTable component for consistent table rendering:

``typescript
type Column = {
  key: string;
  label: string;
  align?: 'left'|'right'|'center';
  width?: number;
  responsive?: { hideBelow?: 'sm'|'md'|'lg' };
  format?: 'number'|'percent'|'signed'|'text';
};

type ColumnGroup = { label: string; columns: Column[]; };

export type DataTableProps = {
  groups: ColumnGroup[];
  rows: Record<string, any>[];
  rowKey: (row: any, idx: number) => string;
  minWidth?: number;
};

```

### 19.6 Performance Optimization

1. **Caching Strategy**: 
   - Power ratings: Cache for 15-60 minutes
   - Game data: Cache for 5-15 minutes
   - Revalidate more frequently on game days

2. **Server-Side Precomputation**:
   - Format signed numbers and percentages server-side
   - Precompute derived metrics

3. **Responsive Table Handling**:
   - Horizontal scroll for wide tables on mobile
   - Column hiding based on screen size

### 19.7 Accessibility Compliance

1. **Table Semantics**:
   - Proper `<thead>`, `<tbody>`, `<th>` with scope attributes
   - ARIA labels for sortable headers
   - Keyboard navigation support

2. **Visual Design**:
   - Sufficient color contrast ratios
   - Focus rings for interactive elements
   - Right-aligned numeric cells with tabular numerals

### 19.8 Development Milestones

1. **M1**: Sidebar, routes, theme tokens, disclosures
2. **M2**: `/games` list with compact rows; EV badge
3. **M3**: Game Detail shell (Model/Market/Projection Detail/QB/Matchups)
4. **M4**: `/power-ratings` using DataTable; sorting, signed colors
5. **M5**: Model Performance page: KPI strip + cumulative units + season table
6. **M6**: `/qb-rankings` and `/receiving-leaders` using DataTable
7. **M7**: Tools pages (odds, cover prob, hold, hedge, parlay, passer rating)
8. **M8**: QA, accessibility, performance passes

This approach ensures we maintain consistency with the existing look and feel while implementing our unique data and AI expert system, aligned with the nfelo-style dashboard paradigm.

## 20. Betting Utilities and Tools

The dashboard will include a comprehensive suite of betting tools and calculators as specified in the PRD.

### 20.1 Odds Conversion Utilities

Implement core odds conversion functions:

``typescript
// utils/odds.ts
export const americanToImplied = (odds: number): number =>
  odds > 0 ? 100 / (odds + 100) : -odds / (-odds + 100);

export const impliedToAmerican = (p: number): number => {
  if (p <= 0 || p >= 1) return Infinity;
  return p >= 0.5 ? Math.round((-p * 100) / (1 - p)) : Math.round(((1 - p) * 100) / p);
};

export const decimalToAmerican = (odds: number): number =>
  odds >= 2.0 ? Math.round((odds - 1) * 100) : Math.round(-100 / (odds - 1));

export const americanToDecimal = (odds: number): number =>
  odds > 0 ? odds / 100 + 1 : 100 / Math.abs(odds) + 1;
```

### 20.2 Expected Value Calculation

Implement expected value functions for betting analysis:

``typescript
export const expectedValue = (p: number, odds: number, stake = 1): number => {
  const imp = americanToImplied(odds);
  const payout = odds > 0 ? (odds / 100) *stake : (100 / -odds)* stake;
  const gain = payout;        // profit when win
  const loss = stake;         // loss when lose
  return p *gain - (1 - p)* loss;
};

export const isPositiveEv = (p: number, odds: number, min = 0.02): boolean =>
  expectedValue(p, odds) > min;

export const spreadDelta = (modelLine: number, marketLine: number): number =>
  modelLine - marketLine; // positive means model likes home more

```

### 20.3 Betting Tools Components

#### 20.3.1 Odds Converter Tool
``typescript
interface OddsConverterProps {
  initialValue?: number;
  initialFormat?: 'american' | 'decimal' | 'fractional';
  onConvert?: (converted: Record<string, number>) => void;
}

const OddsConverter: React.FC<OddsConverterProps> = ({ 
  initialValue = -110, 
  initialFormat = 'american',
  onConvert 
}) => {
  // Implementation for converting between odds formats
};
```

#### 20.3.2 Cover Probability Calculator

``typescript
interface CoverProbabilityCalculatorProps {
  spread: number;
  teamEPA: number;
  opponentEPA: number;
  homeFieldAdvantage?: number;
  onCalculate?: (result: CoverProbabilityResult) => void;
}

interface CoverProbabilityResult {
  coverProbability: number;
  expectedMargin: number;
  ev: number;
}

```

#### 20.3.3 Sportsbook Hold Calculator
```typescript
interface HoldCalculatorProps {
  odds: number[]; // Array of odds for all possible outcomes
  onCalculate?: (hold: number) => void;
}
```

#### 20.3.4 Hedge Calculator

``typescript
interface HedgeCalculatorProps {
  originalBet: {
    odds: number;
    stake: number;
  };
  hedgeOdds: number;
  strategies: Array<'no_hedge' | 'break_even' | 'equal_profit'>;
  onCalculate?: (results: HedgeStrategyResult[]) => void;
}

interface HedgeStrategyResult {
  strategy: 'no_hedge' | 'break_even' | 'equal_profit';
  hedgeStake: number;
  profitIfOriginalWins: number;
  profitIfHedgeWins: number;
}

```

#### 20.3.5 Parlay Odds Calculator
``typescript
interface ParlayCalculatorProps {
  legs: Array<{ odds: number }>;
  stake?: number;
  onCalculate?: (result: ParlayResult) => void;
}

interface ParlayResult {
  payout: number;
  profit: number;
  impliedProbability: number;
}
```

### 20.4 Tools Routing Structure

The tools will be organized under the `/tools` route with individual pages:

- `/tools/nfl-odds-calculator`
- `/tools/nfl-cover-probability-calculator`
- `/tools/sportsbook-hold-calculator`
- `/tools/hedge-calculator`
- `/tools/parlay-odds-calculator`
- `/tools/qb-passer-rating-calculator`
- `/tools/nfl-home-field-advantage-hfa-tracker`

Each tool page will include:

- Input controls for relevant parameters
- Real-time calculation results
- Explanatory content about the metric
- Links to related tools and resources

### 20.5 Tool Integration with AI Experts

The betting tools will integrate with the AI expert system:

- **Expert Recommendations**: Show how different experts would use each tool
- **Historical Performance**: Display expert accuracy with similar calculations
- **Consensus Views**: Aggregate expert opinions on optimal strategies
- **Risk Assessment**: Incorporate expert risk tolerance models

This integration ensures that the tools provide not just mechanical calculations but also strategic insights from the AI expert system.
