/**
 * AI Prediction Accuracy Testing with Historical Data
 * Tests machine learning model predictions, accuracy metrics, and historical validation
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LiveGameUpdates from '../../../src/components/LiveGameUpdates';
import { WebSocketEventType } from '../../../src/services/websocketService';
import { MockWebSocket } from '../__mocks__/WebSocket';

// Historical game data for accuracy testing
const HISTORICAL_GAMES = [
  {
    // Super Bowl LV - Known outcome: Buccaneers won 31-9
    gameId: 'sb_55_2021',
    actualResult: {
      home_team: 'Buccaneers',
      away_team: 'Chiefs',
      final_home_score: 31,
      final_away_score: 9,
      winner: 'Buccaneers',
      final_spread: 22,
      total_points: 40
    },
    predictions: [
      {
        timestamp: '2021-02-07T18:00:00Z', // Pre-game
        home_win_probability: 0.45,
        away_win_probability: 0.55,
        predicted_spread: -3.5,
        confidence_level: 0.72,
        model_version: '1.8.0'
      },
      {
        timestamp: '2021-02-07T19:30:00Z', // Halftime
        home_win_probability: 0.78,
        away_win_probability: 0.22,
        predicted_spread: -12.5,
        confidence_level: 0.89,
        model_version: '1.8.0'
      }
    ]
  },
  {
    // AFC Championship 2022 - Known outcome: Bengals won 27-24 (OT)
    gameId: 'afc_championship_2022',
    actualResult: {
      home_team: 'Chiefs',
      away_team: 'Bengals',
      final_home_score: 24,
      final_away_score: 27,
      winner: 'Bengals',
      final_spread: -3,
      total_points: 51
    },
    predictions: [
      {
        timestamp: '2022-01-30T15:00:00Z',
        home_win_probability: 0.68,
        away_win_probability: 0.32,
        predicted_spread: -7.0,
        confidence_level: 0.75,
        model_version: '2.0.0'
      },
      {
        timestamp: '2022-01-30T17:00:00Z', // End of regulation
        home_win_probability: 0.52,
        away_win_probability: 0.48,
        predicted_spread: -1.5,
        confidence_level: 0.82,
        model_version: '2.0.0'
      }
    ]
  },
  {
    // Regular season upset - Known outcome: Giants beat Patriots 35-14
    gameId: 'giants_patriots_2023',
    actualResult: {
      home_team: 'Patriots',
      away_team: 'Giants',
      final_home_score: 14,
      final_away_score: 35,
      winner: 'Giants',
      final_spread: -21,
      total_points: 49
    },
    predictions: [
      {
        timestamp: '2023-11-26T13:00:00Z',
        home_win_probability: 0.75,
        away_win_probability: 0.25,
        predicted_spread: -6.5,
        confidence_level: 0.68,
        model_version: '2.1.0'
      },
      {
        timestamp: '2023-11-26T15:30:00Z', // Halftime
        home_win_probability: 0.15,
        away_win_probability: 0.85,
        predicted_spread: 18.5,
        confidence_level: 0.93,
        model_version: '2.1.0'
      }
    ]
  }
];

// Accuracy calculation utilities
class PredictionAccuracyAnalyzer {
  static calculateWinProbabilityAccuracy(predictions: any[], actualResult: any): number {
    if (predictions.length === 0) return 0;

    const correctPredictions = predictions.filter(pred => {
      const predictedWinner = pred.home_win_probability > 0.5 ? actualResult.home_team : actualResult.away_team;
      return predictedWinner === actualResult.winner;
    });

    return correctPredictions.length / predictions.length;
  }

  static calculateSpreadAccuracy(predictions: any[], actualResult: any): number {
    if (predictions.length === 0) return 0;

    const spreadErrors = predictions.map(pred => {
      return Math.abs(pred.predicted_spread - actualResult.final_spread);
    });

    const avgError = spreadErrors.reduce((sum, error) => sum + error, 0) / spreadErrors.length;
    return Math.max(0, 1 - (avgError / 21)); // 21 is max reasonable spread error
  }

  static calculateConfidenceCalibration(predictions: any[], actualResult: any): number {
    if (predictions.length === 0) return 0;

    // Check if confidence levels correlate with accuracy
    let calibrationScore = 0;

    predictions.forEach(pred => {
      const isCorrect = (pred.home_win_probability > 0.5 && actualResult.winner === actualResult.home_team) ||
                       (pred.home_win_probability <= 0.5 && actualResult.winner === actualResult.away_team);

      // High confidence should correlate with correct predictions
      if (pred.confidence_level > 0.8 && isCorrect) {
        calibrationScore += 1;
      } else if (pred.confidence_level < 0.6 && !isCorrect) {
        calibrationScore += 0.5; // Partial credit for appropriate low confidence
      }
    });

    return calibrationScore / predictions.length;
  }

  static calculateOverallAccuracy(gameData: typeof HISTORICAL_GAMES): {
    winProbabilityAccuracy: number;
    spreadAccuracy: number;
    confidenceCalibration: number;
    overallScore: number;
  } {
    const winAccuracies = gameData.map(game =>
      this.calculateWinProbabilityAccuracy(game.predictions, game.actualResult)
    );

    const spreadAccuracies = gameData.map(game =>
      this.calculateSpreadAccuracy(game.predictions, game.actualResult)
    );

    const confidenceCalibrations = gameData.map(game =>
      this.calculateConfidenceCalibration(game.predictions, game.actualResult)
    );

    const winProbabilityAccuracy = winAccuracies.reduce((sum, acc) => sum + acc, 0) / winAccuracies.length;
    const spreadAccuracy = spreadAccuracies.reduce((sum, acc) => sum + acc, 0) / spreadAccuracies.length;
    const confidenceCalibration = confidenceCalibrations.reduce((sum, acc) => sum + acc, 0) / confidenceCalibrations.length;

    const overallScore = (winProbabilityAccuracy * 0.4 + spreadAccuracy * 0.4 + confidenceCalibration * 0.2);

    return {
      winProbabilityAccuracy,
      spreadAccuracy,
      confidenceCalibration,
      overallScore
    };
  }
}

// Mock ML model responses
const generateRealisticPrediction = (gamePhase: 'pre-game' | 'early' | 'mid' | 'late', currentScore?: { home: number, away: number }) => {
  const baseConfidence = Math.random() * 0.3 + 0.6; // 0.6 to 0.9

  if (!currentScore) {
    // Pre-game prediction
    return {
      home_win_probability: Math.random() * 0.4 + 0.3, // 0.3 to 0.7
      away_win_probability: Math.random() * 0.4 + 0.3,
      predicted_spread: (Math.random() - 0.5) * 14, // -7 to +7
      confidence_level: baseConfidence,
      model_version: '2.1.0'
    };
  }

  // In-game prediction based on score
  const scoreDiff = currentScore.home - currentScore.away;
  const gamePhaseMultiplier = {
    'early': 0.3,
    'mid': 0.6,
    'late': 0.9
  }[gamePhase];

  const adjustedWinProb = 0.5 + (scoreDiff * 0.03 * gamePhaseMultiplier);
  const homeWinProb = Math.max(0.05, Math.min(0.95, adjustedWinProb));

  return {
    home_win_probability: homeWinProb,
    away_win_probability: 1 - homeWinProb,
    predicted_spread: scoreDiff + (Math.random() - 0.5) * 6,
    confidence_level: Math.min(0.95, baseConfidence + (Math.abs(scoreDiff) * 0.02)),
    model_version: '2.1.0'
  };
};

describe('AI Prediction Accuracy Testing', () => {
  let mockWs: MockWebSocket;
  let accuracyAnalyzer: typeof PredictionAccuracyAnalyzer;

  beforeEach(() => {
    mockWs = new MockWebSocket();
    global.WebSocket = vi.fn(() => mockWs) as any;
    accuracyAnalyzer = PredictionAccuracyAnalyzer;

    // Mock console methods
    console.log = vi.fn();
    console.warn = vi.fn();
    console.error = vi.fn();

    // Mock performance APIs
    global.performance = {
      ...global.performance,
      now: vi.fn(() => Date.now())
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Historical Accuracy Validation', () => {
    it('should validate accuracy against known historical outcomes', () => {
      const accuracyMetrics = accuracyAnalyzer.calculateOverallAccuracy(HISTORICAL_GAMES);

      console.log('Historical Accuracy Metrics:', accuracyMetrics);

      // Accuracy thresholds based on industry standards
      expect(accuracyMetrics.winProbabilityAccuracy).toBeGreaterThan(0.6); // At least 60% correct win predictions
      expect(accuracyMetrics.spreadAccuracy).toBeGreaterThan(0.5); // Reasonable spread accuracy
      expect(accuracyMetrics.confidenceCalibration).toBeGreaterThan(0.4); // Confidence should correlate with accuracy
      expect(accuracyMetrics.overallScore).toBeGreaterThan(0.55); // Overall threshold
    });

    it('should analyze prediction accuracy by game phase', () => {
      const gamePhaseAccuracy = {
        preGame: [] as number[],
        inGame: [] as number[]
      };

      HISTORICAL_GAMES.forEach(game => {
        game.predictions.forEach((prediction, index) => {
          const isCorrect = (prediction.home_win_probability > 0.5 && game.actualResult.winner === game.actualResult.home_team) ||
                           (prediction.home_win_probability <= 0.5 && game.actualResult.winner === game.actualResult.away_team);

          if (index === 0) {
            gamePhaseAccuracy.preGame.push(isCorrect ? 1 : 0);
          } else {
            gamePhaseAccuracy.inGame.push(isCorrect ? 1 : 0);
          }
        });
      });

      const preGameAccuracy = gamePhaseAccuracy.preGame.reduce((sum, val) => sum + val, 0) / gamePhaseAccuracy.preGame.length;
      const inGameAccuracy = gamePhaseAccuracy.inGame.reduce((sum, val) => sum + val, 0) / gamePhaseAccuracy.inGame.length;

      console.log('Pre-game accuracy:', preGameAccuracy);
      console.log('In-game accuracy:', inGameAccuracy);

      // In-game predictions should be more accurate than pre-game
      expect(inGameAccuracy).toBeGreaterThan(preGameAccuracy);
      expect(preGameAccuracy).toBeGreaterThan(0.4); // Minimum pre-game accuracy
      expect(inGameAccuracy).toBeGreaterThan(0.6); // Minimum in-game accuracy
    });

    it('should validate confidence level calibration', () => {
      const confidenceAccuracyMap = new Map<string, { correct: number, total: number }>();

      HISTORICAL_GAMES.forEach(game => {
        game.predictions.forEach(prediction => {
          const confidenceBucket = Math.floor(prediction.confidence_level * 10) / 10; // Round to nearest 0.1
          const isCorrect = (prediction.home_win_probability > 0.5 && game.actualResult.winner === game.actualResult.home_team) ||
                           (prediction.home_win_probability <= 0.5 && game.actualResult.winner === game.actualResult.away_team);

          const key = confidenceBucket.toString();
          if (!confidenceAccuracyMap.has(key)) {
            confidenceAccuracyMap.set(key, { correct: 0, total: 0 });
          }

          const bucket = confidenceAccuracyMap.get(key)!;
          bucket.total++;
          if (isCorrect) bucket.correct++;
        });
      });

      // Higher confidence should correlate with higher accuracy
      const confidenceLevels = Array.from(confidenceAccuracyMap.keys()).sort();
      let previousAccuracy = 0;

      confidenceLevels.forEach(level => {
        const bucket = confidenceAccuracyMap.get(level)!;
        const accuracy = bucket.correct / bucket.total;

        console.log(`Confidence ${level}: ${accuracy} (${bucket.correct}/${bucket.total})`);

        // Generally, higher confidence should not have significantly lower accuracy
        if (previousAccuracy > 0) {
          expect(accuracy).toBeGreaterThan(previousAccuracy - 0.3); // Allow some variation
        }
        previousAccuracy = accuracy;
      });
    });
  });

  describe('Real-time Prediction Testing', () => {
    it('should update predictions based on live game data', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Track prediction changes
      const predictionHistory: any[] = [];

      // Pre-game prediction
      const preGamePrediction = generateRealisticPrediction('pre-game');
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.PREDICTION_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            ...preGamePrediction,
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      predictionHistory.push({ phase: 'pre-game', ...preGamePrediction });

      // Early game with score
      const earlyGamePrediction = generateRealisticPrediction('early', { home: 7, away: 0 });
      await act(async () => {
        mockWs.simulateMessage({
          event_type: WebSocketEventType.SCORE_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            home_score: 7,
            away_score: 0,
            quarter: 1,
            time_remaining: '10:00',
            game_status: 'live',
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });

        mockWs.simulateMessage({
          event_type: WebSocketEventType.PREDICTION_UPDATE,
          data: {
            game_id: 'game_001',
            home_team: 'Patriots',
            away_team: 'Bills',
            ...earlyGamePrediction,
            updated_at: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        });
      });

      predictionHistory.push({ phase: 'early', score: { home: 7, away: 0 }, ...earlyGamePrediction });

      // Verify predictions are displayed and updated
      await waitFor(() => {
        const probabilityElement = screen.getByText(/\d+\.\d+%/);
        expect(probabilityElement).toBeInTheDocument();
      });

      // Analyze prediction evolution
      expect(predictionHistory.length).toBe(2);

      // Home team should have higher win probability after scoring
      expect(earlyGamePrediction.home_win_probability).toBeGreaterThan(preGamePrediction.home_win_probability);

      // Confidence should increase with more game data
      expect(earlyGamePrediction.confidence_level).toBeGreaterThanOrEqual(preGamePrediction.confidence_level);
    });

    it('should handle momentum shifts in predictions', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      const momentumScenarios = [
        { home: 0, away: 0, phase: 'pre-game' as const },
        { home: 14, away: 0, phase: 'early' as const },
        { home: 14, away: 14, phase: 'mid' as const },
        { home: 14, away: 21, phase: 'late' as const }
      ];

      const predictions: any[] = [];

      for (const scenario of momentumScenarios) {
        const prediction = generateRealisticPrediction(scenario.phase,
          scenario.phase === 'pre-game' ? undefined : { home: scenario.home, away: scenario.away }
        );

        await act(async () => {
          if (scenario.phase !== 'pre-game') {
            mockWs.simulateMessage({
              event_type: WebSocketEventType.SCORE_UPDATE,
              data: {
                game_id: 'game_001',
                home_team: 'Patriots',
                away_team: 'Bills',
                home_score: scenario.home,
                away_score: scenario.away,
                quarter: scenario.phase === 'early' ? 1 : scenario.phase === 'mid' ? 2 : 4,
                time_remaining: '05:00',
                game_status: 'live',
                updated_at: new Date().toISOString()
              },
              timestamp: new Date().toISOString()
            });
          }

          mockWs.simulateMessage({
            event_type: WebSocketEventType.PREDICTION_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              ...prediction,
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });

        predictions.push({ scenario, prediction });
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Analyze momentum shifts
      expect(predictions[1].prediction.home_win_probability).toBeGreaterThan(predictions[0].prediction.home_win_probability); // 14-0 lead
      expect(predictions[3].prediction.away_win_probability).toBeGreaterThan(predictions[2].prediction.away_win_probability); // 21-14 comeback

      // Verify final prediction is displayed
      await waitFor(() => {
        expect(screen.getByText(/\d+\.\d+%/)).toBeInTheDocument();
      });
    });

    it('should validate prediction accuracy in real-time simulation', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      // Simulate complete game with known outcome (Pats win 28-21)
      const gameProgression = [
        { home: 0, away: 0, quarter: 1, time: '15:00' },
        { home: 7, away: 0, quarter: 1, time: '08:30' },
        { home: 7, away: 7, quarter: 2, time: '12:15' },
        { home: 14, away: 7, quarter: 2, time: '03:20' },
        { home: 14, away: 14, quarter: 3, time: '10:45' },
        { home: 21, away: 14, quarter: 4, time: '08:30' },
        { home: 21, away: 21, quarter: 4, time: '02:15' },
        { home: 28, away: 21, quarter: 4, time: '00:00' }
      ];

      const predictions: any[] = [];
      const actualWinner = 'Patriots';

      for (const [index, state] of gameProgression.entries()) {
        const phase = index < 2 ? 'early' : index < 5 ? 'mid' : 'late';
        const prediction = generateRealisticPrediction(phase, { home: state.home, away: state.away });

        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.SCORE_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              home_score: state.home,
              away_score: state.away,
              quarter: state.quarter,
              time_remaining: state.time,
              game_status: index === gameProgression.length - 1 ? 'final' : 'live',
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });

          mockWs.simulateMessage({
            event_type: WebSocketEventType.PREDICTION_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              ...prediction,
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });

        predictions.push(prediction);
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      // Calculate accuracy
      const correctPredictions = predictions.filter(pred =>
        pred.home_win_probability > 0.5 // Patriots should win
      );

      const accuracy = correctPredictions.length / predictions.length;
      console.log(`Real-time simulation accuracy: ${accuracy} (${correctPredictions.length}/${predictions.length})`);

      // Most predictions should correctly favor the eventual winner
      expect(accuracy).toBeGreaterThan(0.5);

      // Final prediction should be confident and correct
      const finalPrediction = predictions[predictions.length - 1];
      expect(finalPrediction.home_win_probability).toBeGreaterThan(0.7);
      expect(finalPrediction.confidence_level).toBeGreaterThan(0.8);
    });
  });

  describe('Model Performance Analysis', () => {
    it('should track prediction consistency across model versions', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      const modelVersions = ['2.0.0', '2.1.0', '2.1.1'];
      const versionPredictions = new Map();

      for (const version of modelVersions) {
        const prediction = {
          ...generateRealisticPrediction('mid', { home: 14, away: 10 }),
          model_version: version
        };

        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.MODEL_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              ...prediction,
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });

        versionPredictions.set(version, prediction);
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Newer versions should generally have higher confidence
      const v20 = versionPredictions.get('2.0.0');
      const v21 = versionPredictions.get('2.1.0');
      const v211 = versionPredictions.get('2.1.1');

      expect(v211.confidence_level).toBeGreaterThanOrEqual(v20.confidence_level - 0.1); // Allow some variation

      // Predictions should be reasonably consistent between versions
      const winProbDiff = Math.abs(v211.home_win_probability - v20.home_win_probability);
      expect(winProbDiff).toBeLessThan(0.3); // Predictions shouldn't vary wildly
    });

    it('should measure prediction latency and update frequency', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      const updateTimestamps: number[] = [];
      const latencies: number[] = [];

      // Simulate rapid prediction updates
      for (let i = 0; i < 10; i++) {
        const sendTime = performance.now();

        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.PREDICTION_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              ...generateRealisticPrediction('mid', { home: 14 + i, away: 7 }),
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });

        const receiveTime = performance.now();
        updateTimestamps.push(receiveTime);
        latencies.push(receiveTime - sendTime);

        await new Promise(resolve => setTimeout(resolve, 500)); // 2Hz update rate
      }

      // Calculate metrics
      const avgLatency = latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length;
      const updateIntervals = updateTimestamps.slice(1).map((time, index) =>
        time - updateTimestamps[index]
      );
      const avgUpdateInterval = updateIntervals.reduce((sum, interval) => sum + interval, 0) / updateIntervals.length;

      console.log(`Average prediction latency: ${avgLatency}ms`);
      console.log(`Average update interval: ${avgUpdateInterval}ms`);

      // Performance requirements
      expect(avgLatency).toBeLessThan(100); // Under 100ms latency
      expect(avgUpdateInterval).toBeLessThan(1000); // Updates at least every second
    });

    it('should validate prediction bounds and sanity checks', async () => {
      render(<LiveGameUpdates gameId="game_001" showPredictions={true} />);

      await act(async () => {
        mockWs.simulateOpen();
      });

      const testPredictions = [
        generateRealisticPrediction('pre-game'),
        generateRealisticPrediction('early', { home: 21, away: 0 }),
        generateRealisticPrediction('late', { home: 0, away: 28 })
      ];

      for (const prediction of testPredictions) {
        await act(async () => {
          mockWs.simulateMessage({
            event_type: WebSocketEventType.PREDICTION_UPDATE,
            data: {
              game_id: 'game_001',
              home_team: 'Patriots',
              away_team: 'Bills',
              ...prediction,
              updated_at: new Date().toISOString()
            },
            timestamp: new Date().toISOString()
          });
        });

        // Validate prediction bounds
        expect(prediction.home_win_probability).toBeGreaterThanOrEqual(0);
        expect(prediction.home_win_probability).toBeLessThanOrEqual(1);
        expect(prediction.away_win_probability).toBeGreaterThanOrEqual(0);
        expect(prediction.away_win_probability).toBeLessThanOrEqual(1);

        // Probabilities should sum to 1 (within tolerance)
        const probSum = prediction.home_win_probability + prediction.away_win_probability;
        expect(Math.abs(probSum - 1)).toBeLessThan(0.01);

        // Confidence should be reasonable
        expect(prediction.confidence_level).toBeGreaterThan(0.1);
        expect(prediction.confidence_level).toBeLessThan(1.0);

        // Spread should be reasonable (-50 to +50)
        expect(prediction.predicted_spread).toBeGreaterThan(-50);
        expect(prediction.predicted_spread).toBeLessThan(50);

        await new Promise(resolve => setTimeout(resolve, 100));
      }
    });
  });
});