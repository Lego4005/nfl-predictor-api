import React from 'react';
import { Home, Brain, Sword, BarChart3, Zap, Users, Target, TrendingUp, Trophy, Grid, Calculator } from 'lucide-react';
import type { Route } from '../components/navigation/Router';

// Lazy load components for better performance
const NFLDashboard = React.lazy(() => import('../components/NFLDashboard.current'));
const NFEloDashboard = React.lazy(() => import('../components/nfelo-dashboard/NFEloDashboard'));
const NFLDashboardPage = React.lazy(() => import('../pages/NFLDashboardPage'));
const PowerRankingsPage = React.lazy(() => import('../pages/PowerRankingsPage'));
const GameDetailPage = React.lazy(() => import('../pages/GameDetailPage'));
const OddsConverterPage = React.lazy(() => import('../pages/tools/OddsConverterPage'));
const CoverProbabilityPage = React.lazy(() => import('../pages/tools/CoverProbabilityPage'));
const HedgeCalculatorPage = React.lazy(() => import('../pages/tools/HedgeCalculatorPage'));
const AICouncilDashboard = React.lazy(() => import('../components/council/AICouncilDashboard'));
const ExpertBattleComparisons = React.lazy(() => import('../components/battles/ExpertBattleComparisons'));
const PredictionCategoriesGrid = React.lazy(() => import('../components/predictions/PredictionCategoriesGrid'));
const GameOutcomePanel = React.lazy(() => import('../components/predictions/GameOutcomePanel'));
const BettingMarketsPanel = React.lazy(() => import('../components/predictions/BettingMarketsPanel'));
const PlayerPropsPanel = React.lazy(() => import('../components/predictions/PlayerPropsPanel'));
const LiveScenariosPanel = React.lazy(() => import('../components/predictions/LiveScenariosPanel'));

// Loading component
const LoadingComponent = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

// Wrapper for lazy components
const withSuspense = (Component: React.LazyExoticComponent<React.ComponentType<any>>) => {
  return (props: any) => (
    <React.Suspense fallback={<LoadingComponent />}>
      <Component {...props} />
    </React.Suspense>
  );
};

// Route definitions
export const routes: Route[] = [
  {
    path: '/',
    component: withSuspense(NFLDashboard),
    title: 'Dashboard',
    description: 'NFL Prediction Dashboard - Live games, expert predictions, and AI Council consensus',
    icon: Home
  },
  {
    path: '/nfelo',
    component: withSuspense(NFEloDashboard),
    title: 'NFElo Dashboard',
    description: 'NFElo-style interface with expected value analysis and power rankings',
    icon: Trophy
  },
  {
    path: '/nfl-dashboard',
    component: withSuspense(NFLDashboardPage),
    title: 'NFL Dashboard',
    description: 'Professional NFL prediction dashboard with comprehensive analytics and betting insights',
    icon: Grid
  },
  {
    path: '/power-rankings',
    component: withSuspense(PowerRankingsPage),
    title: 'Power Rankings',
    description: 'NFL team power rankings with EPA metrics and strength of schedule adjustments',
    icon: Trophy
  },
  {
    path: '/games/:gameId',
    component: withSuspense(GameDetailPage),
    title: 'Game Detail',
    description: 'Detailed analysis and predictions for individual NFL games',
    icon: Target
  },
  {
    path: '/tools/odds-converter',
    component: withSuspense(OddsConverterPage),
    title: 'Odds Converter',
    description: 'Convert between different odds formats and calculate implied probabilities',
    icon: Calculator
  },
  {
    path: '/tools/cover-probability',
    component: withSuspense(CoverProbabilityPage),
    title: 'Cover Probability',
    description: 'Calculate the probability of a team covering the spread based on EPA metrics',
    icon: Target
  },
  {
    path: '/tools/hedge-calculator',
    component: withSuspense(HedgeCalculatorPage),
    title: 'Hedge Calculator',
    description: 'Calculate optimal hedge amounts to minimize risk or maximize profit',
    icon: Calculator
  },
  {
    path: '/council',
    component: withSuspense(AICouncilDashboard),
    title: 'AI Council',
    description: 'AI Council Dashboard - Expert consensus and voting weight analysis',
    icon: Brain
  },
  {
    path: '/council/weights',
    component: () => {
      // Vote weights detail page - would be a specific component
      return (
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">Vote Weight Analysis</h1>
          <p className="text-gray-600">Detailed vote weight breakdown and historical analysis.</p>
        </div>
      );
    },
    title: 'Vote Weights',
    description: 'Detailed vote weight analysis and breakdown',
    icon: BarChart3
  },
  {
    path: '/council/history',
    component: () => {
      return (
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">Consensus History</h1>
          <p className="text-gray-600">Historical AI Council decisions and consensus tracking.</p>
        </div>
      );
    },
    title: 'Consensus History',
    description: 'Historical AI Council decisions and consensus evolution',
    icon: TrendingUp
  },
  {
    path: '/battles',
    component: (props) => {
      const expertIds = ['expert_1', 'expert_2', 'expert_3', 'expert_4'];
      return withSuspense(ExpertBattleComparisons)({
        ...props,
        expertIds,
        comparisonMetric: 'accuracy',
        timeRange: 'all_time'
      });
    },
    title: 'Expert Battles',
    description: 'Head-to-head expert performance comparisons and battle analysis',
    icon: Sword
  },
  {
    path: '/battles/rankings',
    component: () => {
      return (
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">Expert Rankings</h1>
          <p className="text-gray-600">Performance leaderboard and expert rankings across all categories.</p>
        </div>
      );
    },
    title: 'Expert Rankings',
    description: 'Expert performance leaderboard and rankings',
    icon: Target
  },
  {
    path: '/predictions',
    component: (props) => {
      const mockPredictions: any[] = [];
      const mockConsensus: any[] = [];
      return withSuspense(PredictionCategoriesGrid)({
        ...props,
        expertPredictions: mockPredictions,
        consensusResults: mockConsensus,
        activeCategoryFilter: 'all',
        onCategorySelect: (categoryId: string) => console.log('Selected:', categoryId),
        showConfidenceIndicators: true
      });
    },
    title: 'Predictions',
    description: '27-category prediction analysis across all expert models',
    icon: BarChart3
  },
  {
    path: '/predictions/game-outcome',
    component: (props) => {
      const mockPredictions: any[] = [];
      const mockConsensus: any[] = [];
      const categories = ['game_winner', 'final_score', 'margin_of_victory'];
      return withSuspense(GameOutcomePanel)({
        ...props,
        predictions: mockPredictions,
        consensus: mockConsensus,
        categories,
        onCategorySelect: (categoryId: string) => console.log('Selected:', categoryId),
        viewMode: 'grid'
      });
    },
    title: 'Game Outcome',
    description: 'Game winner, score, and margin predictions',
    icon: Target
  },
  {
    path: '/predictions/betting-markets',
    component: (props) => {
      const mockPredictions: any[] = [];
      const mockConsensus: any[] = [];
      const categories = ['point_spread', 'total_over_under', 'moneyline'];
      return withSuspense(BettingMarketsPanel)({
        ...props,
        predictions: mockPredictions,
        consensus: mockConsensus,
        categories,
        onCategorySelect: (categoryId: string) => console.log('Selected:', categoryId),
        viewMode: 'grid'
      });
    },
    title: 'Betting Markets',
    description: 'Point spreads, totals, and moneyline analysis',
    icon: TrendingUp
  },
  {
    path: '/predictions/player-props',
    component: (props) => {
      const mockPredictions: any[] = [];
      const mockConsensus: any[] = [];
      const categories = ['passing_yards', 'rushing_yards', 'receiving_yards'];
      return withSuspense(PlayerPropsPanel)({
        ...props,
        predictions: mockPredictions,
        consensus: mockConsensus,
        categories,
        onCategorySelect: (categoryId: string) => console.log('Selected:', categoryId),
        viewMode: 'grid'
      });
    },
    title: 'Player Props',
    description: 'Individual player performance predictions',
    icon: Users
  },
  {
    path: '/live',
    component: (props) => {
      const mockPredictions: any[] = [];
      const mockConsensus: any[] = [];
      const categories = ['next_score', 'momentum_shift', 'live_win_probability'];
      return withSuspense(LiveScenariosPanel)({
        ...props,
        predictions: mockPredictions,
        consensus: mockConsensus,
        categories,
        onCategorySelect: (categoryId: string) => console.log('Selected:', categoryId),
        viewMode: 'grid'
      });
    },
    title: 'Live Games',
    description: 'Real-time game tracking and live scenario analysis',
    icon: Zap
  },
  {
    path: '/expert/:expertId',
    component: (props) => {
      const { expertId } = props;
      return (
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">Expert Profile</h1>
          <p className="text-gray-600">Detailed analysis for expert: {expertId}</p>
        </div>
      );
    },
    title: 'Expert Profile',
    description: 'Individual expert analysis and performance history',
    icon: Users
  },
  {
    path: '/admin',
    component: () => {
      return (
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
          <p className="text-gray-600">Administrative interface for system management.</p>
        </div>
      );
    },
    title: 'Admin',
    description: 'Administrative interface for system management',
    requiresAuth: true
  }
];

export default routes;