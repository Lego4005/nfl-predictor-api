import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import NFEloDashboard from './NFEloDashboard';

// Mock child components
jest.mock('./GameListView', () => {
  return function MockGameListView() {
    return <div data-testid="game-list-view">Game List View</div>;
  };
});

jest.mock('./EVBettingCard', () => {
  return function MockEVBettingCard() {
    return <div data-testid="ev-betting-card">EV Betting Card</div>;
  };
});

jest.mock('./ModelPerformance', () => {
  return function MockModelPerformance() {
    return <div data-testid="model-performance">Model Performance</div>;
  };
});

jest.mock('./PowerRankings', () => {
  return function MockPowerRankings() {
    return <div data-testid="power-rankings">Power Rankings</div>;
  };
});

jest.mock('./WeeklyNavigation', () => {
  return function MockWeeklyNavigation({ currentWeek, onWeekChange }) {
    return (
      <div data-testid="weekly-navigation">
        Week {currentWeek}
        <button onClick={() => onWeekChange(currentWeek + 1)}>Next Week</button>
      </div>
    );
  };
});

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  }
}));

describe('NFEloDashboard', () => {
  test('renders without crashing', () => {
    render(<NFEloDashboard />);
    
    // Check if the main title is rendered
    expect(screen.getByText('NFElo-Style NFL Predictor')).toBeInTheDocument();
    
    // Check if the description is rendered
    expect(screen.getByText('Data-driven predictions with expected value analysis')).toBeInTheDocument();
    
    // Check if all tabs are rendered
    expect(screen.getByText('Games List')).toBeInTheDocument();
    expect(screen.getByText('EV Betting')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Power Rankings')).toBeInTheDocument();
    
    // Check if the game list view is rendered by default
    expect(screen.getByTestId('game-list-view')).toBeInTheDocument();
  });

  test('renders all components', () => {
    render(<NFEloDashboard />);
    
    // Check if all child components are rendered
    expect(screen.getByTestId('weekly-navigation')).toBeInTheDocument();
    expect(screen.getByTestId('game-list-view')).toBeInTheDocument();
    expect(screen.getByTestId('ev-betting-card')).toBeInTheDocument();
    expect(screen.getByTestId('model-performance')).toBeInTheDocument();
    expect(screen.getByTestId('power-rankings')).toBeInTheDocument();
  });

  test('displays stats overview', () => {
    render(<NFEloDashboard />);
    
    // Check if stats overview is rendered
    expect(screen.getByText('Games This Week')).toBeInTheDocument();
    expect(screen.getByText('High EV Plays')).toBeInTheDocument();
    expect(screen.getByText('Model Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Last Updated')).toBeInTheDocument();
  });
});