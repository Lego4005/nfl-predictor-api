/**
 * Real-time Data Testing for Live Game Experience
 * Tests WebSocket data flow, game state updates, and data synchronization
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LiveGameUpdates from '../../../src/components/LiveGameUpdates';
import { WebSocketEventType } from '../../../src/services/websocketService';
import { MockWebSocket } from '../__mocks__/WebSocket';

// Mock real-time game data scenarios
const mockGameData = {
  preGame: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 0,
    away_score: 0,
    quarter: 0,
    time_remaining: '15:00',
    game_status: 'scheduled',
    updated_at: new Date().toISOString()
  },
  kickoff: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 0,
    away_score: 0,
    quarter: 1,
    time_remaining: '15:00',
    game_status: 'live',
    updated_at: new Date().toISOString()
  },
  touchdown: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 7,
    away_score: 0,
    quarter: 1,
    time_remaining: '12:34',
    game_status: 'live',
    updated_at: new Date().toISOString()
  },
  fieldGoal: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 7,
    away_score: 3,
    quarter: 2,
    time_remaining: '08:42',
    game_status: 'live',
    updated_at: new Date().toISOString()
  },
  redZone: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 14,
    away_score: 10,
    quarter: 3,
    time_remaining: '05:17',
    game_status: 'red_zone',
    updated_at: new Date().toISOString()
  },
  overtime: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 21,
    away_score: 21,
    quarter: 5,
    time_remaining: '10:00',
    game_status: 'overtime',
    updated_at: new Date().toISOString()
  },
  final: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_score: 28,
    away_score: 21,
    quarter: 5,
    time_remaining: '00:00',
    game_status: 'final',
    updated_at: new Date().toISOString()
  }
};

const mockPredictionData = {
  initial: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_win_probability: 0.52,
    away_win_probability: 0.48,
    predicted_spread: -2.5,
    confidence_level: 0.78,
    model_version: '2.1.0',
    updated_at: new Date().toISOString()
  },
  momentum_shift: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_win_probability: 0.68,
    away_win_probability: 0.32,
    predicted_spread: -7.5,
    confidence_level: 0.85,
    model_version: '2.1.0',
    updated_at: new Date().toISOString()
  },
  comeback: {
    game_id: 'game_001',
    home_team: 'Patriots',
    away_team: 'Bills',
    home_win_probability: 0.41,
    away_win_probability: 0.59,
    predicted_spread: 3.5,
    confidence_level: 0.82,
    model_version: '2.1.0',
    updated_at: new Date().toISOString()
  }
};

const mockOddsData = {
  draftkings: {
    game_id: 'game_001',
    sportsbook: 'DraftKings',
    home_team: 'Patriots',
    away_team: 'Bills',
    spread: -3.0,
    moneyline_home: -150,
    moneyline_away: +130,
    over_under: 47.5,
    updated_at: new Date().toISOString()
  },
  fanduel: {
    game_id: 'game_001',
    sportsbook: 'FanDuel',
    home_team: 'Patriots',
    away_team: 'Bills',
    spread: -2.5,
    moneyline_home: -145,
    moneyline_away: +125,
    over_under: 48.0,
    updated_at: new Date().toISOString()
  }
};

describe('Real-time Live Game Data Testing', () => {
  let mockWs: MockWebSocket;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';

    // Setup mock WebSocket
    mockWs = new MockWebSocket();
    global.WebSocket = vi.fn(() => mockWs) as any;

    // Mock performance APIs
    global.performance = {
      ...global.performance,
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByName: vi.fn(() => [])
    };

    // Mock IntersectionObserver
    global.IntersectionObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }));

    // Mock console methods
    console.log = vi.fn();
    console.warn = vi.fn();
    console.error = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  describe('WebSocket Connection and Data Flow', () => {
    it('should establish WebSocket connection and handle game data flow', async () => {
      const { container } = render(<LiveGameUpdates gameId="game_001" />);

      // Simulate WebSocket connection
      await act(async () => {
        mockWs.simulateOpen();
      });

      expect(screen.getByText(/Live/)).toBeInTheDocument();

      // Test pre-game state
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: mockGameData.preGame,
          timestamp: new Date().toISOString()
        });
      });

      expect(screen.getByText('SCHEDULED')).toBeInTheDocument();
      expect(screen.getByText('Patriots')).toBeInTheDocument();
      expect(screen.getByText('Bills')).toBeInTheDocument();

      // Test game start
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_STARTED,
          data: mockGameData.kickoff,
          timestamp: new Date().toISOString()
        });
      });

      expect(screen.getByText('LIVE')).toBeInTheDocument();
      expect(screen.getByText('1st - 15:00')).toBeInTheDocument();
    });

    it('should handle rapid score updates and maintain data consistency', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Rapid score updates
      const scoreUpdates = [
        { ...mockGameData.touchdown, home_score: 7 },
        { ...mockGameData.touchdown, home_score: 7, away_score: 3 },
        { ...mockGameData.touchdown, home_score: 14, away_score: 3 },
        { ...mockGameData.touchdown, home_score: 14, away_score: 10 }
      ];

      for (const update of scoreUpdates) {
        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: update,
            timestamp: new Date().toISOString()
          });
        });

        // Small delay to simulate real-time updates
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      await waitFor(() => {
        expect(screen.getByText('14')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
      });
    });

    it('should handle WebSocket disconnection and reconnection gracefully', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      // Initial connection
      await act(async () => {
        mockWs.simulateOpen();
      });

      expect(screen.getByText(/Live/)).toBeInTheDocument();

      // Simulate disconnection
      await act(async () => {
        mockWs.simulateClose();
      });

      await waitFor(() => {
        expect(screen.getByText(/Not connected/)).toBeInTheDocument();
        expect(screen.getByText(/Reconnecting/)).toBeInTheDocument();
      });

      // Simulate reconnection
      await act(async () => {
        mockWs.simulateOpen();
      });

      await waitFor(() => {
        expect(screen.getByText(/Live/)).toBeInTheDocument();
      });
    });
  });

  describe('Game State Transitions', () => {
    it('should handle complete game lifecycle from scheduled to final', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Game lifecycle sequence
      const gameStates = [
        mockGameData.preGame,
        mockGameData.kickoff,
        mockGameData.touchdown,
        mockGameData.fieldGoal,
        mockGameData.redZone,
        mockGameData.overtime,
        mockGameData.final
      ];

      for (const [index, state] of gameStates.entries()) {
        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.GAME_UPDATE,
            data: state,
            timestamp: new Date().toISOString()
          });
        });

        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify state-specific UI elements
        switch (index) {
          case 0: // Pre-game
            expect(screen.getByText('SCHEDULED')).toBeInTheDocument();
            break;
          case 1: // Kickoff
            expect(screen.getByText('LIVE')).toBeInTheDocument();
            break;
          case 4: // Red zone
            expect(screen.getByText('RED_ZONE')).toBeInTheDocument();
            break;
          case 5: // Overtime
            expect(screen.getByText('OVERTIME')).toBeInTheDocument();
            expect(screen.getByText('OT1 - 10:00')).toBeInTheDocument();
            break;
          case 6: // Final
            expect(screen.getByText('FINAL')).toBeInTheDocument();
            break;
        }
      }
    });

    it('should handle quarter transitions and time updates', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      const quarterUpdates = [
        { ...mockGameData.kickoff, quarter: 1, time_remaining: '15:00' },
        { ...mockGameData.kickoff, quarter: 1, time_remaining: '02:00' },
        { ...mockGameData.kickoff, quarter: 2, time_remaining: '15:00' },
        { ...mockGameData.kickoff, quarter: 3, time_remaining: '10:30' },
        { ...mockGameData.kickoff, quarter: 4, time_remaining: '02:00' }
      ];

      for (const update of quarterUpdates) {
        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.QUARTER_CHANGE,
            data: update,
            timestamp: new Date().toISOString()
          });
        });

        await waitFor(() => {
          const quarterText = `${update.quarter <= 4 ? ['1st', '2nd', '3rd', '4th'][update.quarter - 1] : `OT${update.quarter - 4}`} - ${update.time_remaining}`;
          expect(screen.getByText(quarterText)).toBeInTheDocument();
        });
      }
    });
  });

  describe('AI Prediction Updates', () => {
    it('should update predictions based on game momentum', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Initial prediction
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.PREDICTION_UPDATE,
          data: mockPredictionData.initial,
          timestamp: new Date().toISOString()
        });
      });

      expect(screen.getByText('52.0%')).toBeInTheDocument();
      expect(screen.getByText('48.0%')).toBeInTheDocument();

      // Momentum shift after touchdown
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.PREDICTION_UPDATE,
          data: mockPredictionData.momentum_shift,
          timestamp: new Date().toISOString()
        });
      });

      await waitFor(() => {
        expect(screen.getByText('68.0%')).toBeInTheDocument();
        expect(screen.getByText('32.0%')).toBeInTheDocument();
      });

      // Comeback scenario
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.PREDICTION_UPDATE,
          data: mockPredictionData.comeback,
          timestamp: new Date().toISOString()
        });
      });

      await waitFor(() => {
        expect(screen.getByText('41.0%')).toBeInTheDocument();
        expect(screen.getByText('59.0%')).toBeInTheDocument();
      });
    });

    it('should display confidence levels and model versions', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.PREDICTION_UPDATE,
          data: mockPredictionData.initial,
          timestamp: new Date().toISOString()
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Confidence: 78.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Live Odds Updates', () => {
    it('should handle multiple sportsbook odds updates', async () => {
      render(<LiveGameUpdates gameId="game_001" showOdds={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Add DraftKings odds
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.ODDS_UPDATE,
          data: mockOddsData.draftkings,
          timestamp: new Date().toISOString()
        });
      });

      expect(screen.getByText('DraftKings')).toBeInTheDocument();
      expect(screen.getByText('-3')).toBeInTheDocument();

      // Add FanDuel odds
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.ODDS_UPDATE,
          data: mockOddsData.fanduel,
          timestamp: new Date().toISOString()
        });
      });

      expect(screen.getByText('FanDuel')).toBeInTheDocument();
      expect(screen.getByText('-2.5')).toBeInTheDocument();

      // Update existing odds
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.ODDS_UPDATE,
          data: { ...mockOddsData.draftkings, spread: -4.0 },
          timestamp: new Date().toISOString()
        });
      });

      await waitFor(() => {
        expect(screen.getByText('-4')).toBeInTheDocument();
      });
    });

    it('should handle line movement notifications', async () => {
      render(<LiveGameUpdates gameId="game_001" showOdds={true} />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.ODDS_UPDATE,
          data: mockOddsData.draftkings,
          timestamp: new Date().toISOString()
        });
      });

      // Simulate line movement
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.LINE_MOVEMENT,
          data: {
            game_id: 'game_001',
            sportsbook: 'DraftKings',
            previous_spread: -3.0,
            new_spread: -4.5,
            movement: 'down',
            amount: 1.5
          },
          timestamp: new Date().toISOString()
        });
      });

      // Line movement should be reflected in updated odds
      await waitFor(() => {
        expect(screen.getByText('-4.5')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle malformed WebSocket messages gracefully', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Send malformed message
      await act(async () => {
        mockWs.simulateMessage('invalid json');
      });

      // Component should still be functional
      expect(screen.getByText(/Live/)).toBeInTheDocument();
    });

    it('should handle missing game data fields', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
        mockWs.simulateMessage({
          event_type: WebSocketEventType.GAME_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots'
            // Missing required fields
          },
          timestamp: new Date().toISOString()
        });
      });

      // Should display available data without crashing
      expect(screen.getByText('Patriots')).toBeInTheDocument();
    });

    it('should handle rapid message bursts without dropping data', async () => {
      render(<LiveGameUpdates gameId="game_001" />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Send burst of messages
      const messages = Array.from({ length: 50 }, (_, i) => ({
        event_type: WebSocketEventType.SCORE_UPDATE,
        data: { ...mockGameData.touchdown, home_score: i },
        timestamp: new Date().toISOString()
      }));

      await act(async () => {
        messages.forEach(msg => mockWs.simulateMessage(msg));
      });

      // Should display the final score
      await waitFor(() => {
        expect(screen.getByText('49')).toBeInTheDocument();
      });
    });
  });

  describe('Performance Under Load', () => {
    it('should maintain performance with multiple simultaneous games', async () => {
      render(<LiveGameUpdates />); // No specific gameId = all games

      await act(async () => {
        mockWs.simulateOpen();
      });

      const startTime = performance.now();

      // Simulate 10 simultaneous games with updates
      const gameIds = Array.from({ length: 10 }, (_, i) => `game_${i.toString().padStart(3, '0')}`);

      await act(async () => {
        gameIds.forEach((gameId, index) => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.GAME_UPDATE,
            data: {
              ...mockGameData.touchdown,
              game_id: gameId,
              home_team: `Team${index * 2}`,
              away_team: `Team${index * 2 + 1}`,
              home_score: Math.floor(Math.random() * 30),
              away_score: Math.floor(Math.random() * 30)
            },
            timestamp: new Date().toISOString()
          });
        });
      });

      const endTime = performance.now();
      const processingTime = endTime - startTime;

      // Should process all updates quickly (under 100ms)
      expect(processingTime).toBeLessThan(100);

      // All games should be displayed
      gameIds.forEach((_, index) => {
        expect(screen.getByText(`Team${index * 2}`)).toBeInTheDocument();
      });
    });
  });
});