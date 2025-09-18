/**
 * Mock Service Worker Server Setup for API Mocking
 * Provides realistic API responses for frontend testing
 */

import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock data generators
const generateMockGame = (id: string) => ({
  game_id: id,
  home_team: {
    id: 'chiefs',
    name: 'Kansas City Chiefs',
    abbreviation: 'KC',
    city: 'Kansas City',
    logo_url: 'https://static.nfl.com/logos/teams/KC.png'
  },
  away_team: {
    id: 'ravens',
    name: 'Baltimore Ravens',
    abbreviation: 'BAL',
    city: 'Baltimore',
    logo_url: 'https://static.nfl.com/logos/teams/BAL.png'
  },
  start_time: '2024-09-05T20:20:00Z',
  game_status: 'scheduled',
  home_score: 0,
  away_score: 0,
  quarter: 1,
  time_remaining: '15:00',
  week: 1,
  season: 2024,
  weather: {
    temperature: 75,
    conditions: 'Clear',
    wind_speed: 5,
    wind_direction: 'W'
  }
});

const generateMockPrediction = (gameId: string) => ({
  game_id: gameId,
  model_version: 'v2.1.0',
  home_win_probability: 0.65,
  away_win_probability: 0.35,
  predicted_spread: -3.5,
  predicted_total: 48.5,
  confidence_level: 0.82,
  last_updated: new Date().toISOString()
});

const generateMockSystemHealth = () => ({
  timestamp: new Date().toISOString(),
  status: 'healthy',
  uptime_seconds: 86400,
  api: {
    status: 'healthy',
    response_time_ms: 125,
    requests_per_second: 450,
    error_rate: 0.1
  },
  database: {
    status: 'healthy',
    connections: 25,
    query_time_ms: 15,
    cpu_usage: 35.2,
    memory_usage: 68.5
  },
  websocket: {
    status: 'healthy',
    active_connections: 1250,
    messages_per_second: 85,
    connection_errors: 2
  },
  ml_models: {
    status: 'healthy',
    last_training: new Date(Date.now() - 3600000).toISOString(),
    accuracy: 0.672,
    predictions_per_hour: 850
  }
});

// Define request handlers
export const handlers = [
  // Authentication endpoints
  rest.post('/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock_jwt_token_12345',
        refresh_token: 'mock_refresh_token_67890',
        token_type: 'bearer',
        expires_in: 3600
      })
    );
  }),

  rest.post('/api/auth/refresh', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'new_mock_jwt_token_12345',
        expires_in: 3600
      })
    );
  }),

  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Logged out successfully' })
    );
  }),

  // Games endpoints
  rest.get('/api/games', (req, res, ctx) => {
    const games = Array.from({ length: 16 }, (_, i) =>
      generateMockGame(`nfl_2024_week_1_game_${i + 1}`)
    );

    return res(
      ctx.status(200),
      ctx.json({
        games,
        total: games.length,
        page: 1,
        per_page: 16
      })
    );
  }),

  rest.get('/api/games/:gameId', (req, res, ctx) => {
    const { gameId } = req.params;
    return res(
      ctx.status(200),
      ctx.json(generateMockGame(gameId as string))
    );
  }),

  // Predictions endpoints
  rest.get('/api/predictions', (req, res, ctx) => {
    const predictions = Array.from({ length: 16 }, (_, i) =>
      generateMockPrediction(`nfl_2024_week_1_game_${i + 1}`)
    );

    return res(
      ctx.status(200),
      ctx.json({
        predictions,
        total: predictions.length
      })
    );
  }),

  rest.get('/api/predictions/:gameId', (req, res, ctx) => {
    const { gameId } = req.params;
    return res(
      ctx.status(200),
      ctx.json(generateMockPrediction(gameId as string))
    );
  }),

  // System health endpoint
  rest.get('/api/health', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(generateMockSystemHealth())
    );
  }),

  // Odds endpoints
  rest.get('/api/odds/:gameId', (req, res, ctx) => {
    const { gameId } = req.params;
    const odds = [
      {
        game_id: gameId,
        sportsbook: 'DraftKings',
        timestamp: new Date().toISOString(),
        spread: {
          home: -3.5,
          away: 3.5,
          home_odds: -110,
          away_odds: -110
        },
        moneyline: {
          home: -165,
          away: 140
        },
        total: {
          over: 48.5,
          under: 48.5,
          over_odds: -110,
          under_odds: -110
        }
      },
      {
        game_id: gameId,
        sportsbook: 'FanDuel',
        timestamp: new Date().toISOString(),
        spread: {
          home: -3.0,
          away: 3.0,
          home_odds: -105,
          away_odds: -115
        },
        moneyline: {
          home: -160,
          away: 135
        },
        total: {
          over: 49.0,
          under: 49.0,
          over_odds: -105,
          under_odds: -115
        }
      }
    ];

    return res(
      ctx.status(200),
      ctx.json({ odds })
    );
  }),

  // User endpoints
  rest.get('/api/user/profile', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        user_id: 'test_user_123',
        username: 'testuser',
        email: 'test@example.com',
        role: 'premium',
        preferences: {
          favorite_teams: ['KC', 'BAL'],
          notifications: {
            email: true,
            push: true
          }
        },
        statistics: {
          total_bets: 150,
          winning_bets: 85,
          total_wagered: 15000.00,
          total_winnings: 16750.00,
          current_streak: 3
        }
      })
    );
  }),

  // Analytics endpoints
  rest.get('/api/analytics/dashboard', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        daily_users: Array.from({ length: 30 }, (_, i) => ({
          date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          active_users: Math.floor(Math.random() * 1000) + 500,
          new_users: Math.floor(Math.random() * 50) + 10
        })),
        model_accuracy: Array.from({ length: 7 }, (_, i) => ({
          date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          accuracy: 0.55 + Math.random() * 0.15
        })),
        summary: {
          total_predictions_today: 156,
          accuracy_last_week: 0.672,
          active_users_today: 1248,
          revenue_today: 3250.00
        }
      })
    );
  }),

  // Betting endpoints
  rest.post('/api/betting/value-bets', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        value_bets: [
          {
            game_id: 'nfl_2024_week_1_chiefs_ravens',
            bet_type: 'moneyline',
            selection: 'away',
            sportsbook: 'DraftKings',
            odds: 140,
            model_probability: 0.45,
            implied_probability: 0.417,
            expected_value: 0.033,
            kelly_fraction: 0.024,
            recommended_bet: 24.50,
            confidence: 0.78
          }
        ]
      })
    );
  }),

  // WebSocket connection info (for connection testing)
  rest.get('/api/ws/info', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        websocket_url: 'ws://localhost:8080',
        supported_events: [
          'game_update',
          'prediction_update',
          'odds_update',
          'notification'
        ],
        heartbeat_interval: 30
      })
    );
  }),

  // Error simulation endpoints for testing error handling
  rest.get('/api/error/500', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        error: {
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Internal server error occurred',
          timestamp: new Date().toISOString()
        }
      })
    );
  }),

  rest.get('/api/error/429', (req, res, ctx) => {
    return res(
      ctx.status(429),
      ctx.json({
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Rate limit exceeded',
          retry_after: 60,
          timestamp: new Date().toISOString()
        }
      })
    );
  }),

  rest.get('/api/error/401', (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({
        error: {
          code: 'UNAUTHORIZED',
          message: 'Invalid or expired token',
          timestamp: new Date().toISOString()
        }
      })
    );
  }),

  // Catch-all handler for unmatched requests
  rest.get('*', (req, res, ctx) => {
    console.warn(`Unmatched GET request to ${req.url}`);
    return res(
      ctx.status(404),
      ctx.json({
        error: {
          code: 'NOT_FOUND',
          message: 'Endpoint not found',
          timestamp: new Date().toISOString()
        }
      })
    );
  }),

  rest.post('*', (req, res, ctx) => {
    console.warn(`Unmatched POST request to ${req.url}`);
    return res(
      ctx.status(404),
      ctx.json({
        error: {
          code: 'NOT_FOUND',
          message: 'Endpoint not found',
          timestamp: new Date().toISOString()
        }
      })
    );
  })
];

// Setup and export the server
export const server = setupServer(...handlers);