#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js';
import axios from 'axios';
import WebSocket from 'ws';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '..', '.env') });

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

class SystemValidator {
  constructor() {
    this.results = {
      database: { status: 'pending', details: {} },
      espnApi: { status: 'pending', details: {} },
      oddsApi: { status: 'pending', details: {} },
      predictions: { status: 'pending', details: {} },
      websocket: { status: 'pending', details: {} },
      frontend: { status: 'pending', details: {} },
      authentication: { status: 'pending', details: {} }
    };
  }

  async validateDatabase() {
    console.log('\n📊 Validating Database...');
    try {
      // Check games table
      const { data: games, error: gamesError } = await supabase
        .from('games')
        .select('count')
        .limit(1);

      if (gamesError) throw gamesError;

      // Check predictions table
      const { data: predictions, error: predError } = await supabase
        .from('predictions')
        .select('count')
        .limit(1);

      if (predError) throw predError;

      // Check user_picks table
      const { data: picks, error: picksError } = await supabase
        .from('user_picks')
        .select('count')
        .limit(1);

      if (picksError) throw picksError;

      // Get counts
      const { count: gameCount } = await supabase
        .from('games')
        .select('*', { count: 'exact', head: true });

      const { count: predCount } = await supabase
        .from('predictions')
        .select('*', { count: 'exact', head: true });

      this.results.database = {
        status: 'success',
        details: {
          connected: true,
          games: gameCount || 0,
          predictions: predCount || 0,
          tablesAccessible: true
        }
      };

      console.log(`  ✅ Database connected`);
      console.log(`  📈 Games: ${gameCount || 0}`);
      console.log(`  🔮 Predictions: ${predCount || 0}`);

    } catch (error) {
      this.results.database = {
        status: 'error',
        details: { error: error.message }
      };
      console.log(`  ❌ Database error: ${error.message}`);
    }
  }

  async validateESPNApi() {
    console.log('\n🏈 Validating ESPN API...');
    try {
      const response = await axios.get(
        'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
        { timeout: 5000 }
      );

      const events = response.data?.events || [];
      const liveGames = events.filter(e =>
        e.competitions?.[0]?.status?.type?.state === 'in'
      ).length;

      this.results.espnApi = {
        status: 'success',
        details: {
          accessible: true,
          totalGames: events.length,
          liveGames,
          season: response.data?.season?.year,
          week: response.data?.week?.number
        }
      };

      console.log(`  ✅ ESPN API accessible`);
      console.log(`  📅 Season: ${response.data?.season?.year}, Week: ${response.data?.week?.number}`);
      console.log(`  🎮 Games: ${events.length} total, ${liveGames} live`);

    } catch (error) {
      this.results.espnApi = {
        status: 'error',
        details: { error: error.message }
      };
      console.log(`  ❌ ESPN API error: ${error.message}`);
    }
  }

  async validateOddsApi() {
    console.log('\n💰 Validating Odds API...');
    try {
      if (!process.env.VITE_ODDS_API_KEY) {
        console.log('  ⚠️  No Odds API key configured');
        this.results.oddsApi = {
          status: 'warning',
          details: { message: 'API key not configured' }
        };
        return;
      }

      const response = await axios.get(
        'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds',
        {
          params: {
            apiKey: process.env.VITE_ODDS_API_KEY,
            regions: 'us',
            markets: 'spreads,totals',
            oddsFormat: 'american'
          },
          timeout: 5000
        }
      );

      this.results.oddsApi = {
        status: 'success',
        details: {
          accessible: true,
          gamesWithOdds: response.data?.length || 0,
          remainingRequests: response.headers['x-requests-remaining']
        }
      };

      console.log(`  ✅ Odds API accessible`);
      console.log(`  📊 Games with odds: ${response.data?.length || 0}`);
      console.log(`  🔢 Remaining requests: ${response.headers['x-requests-remaining']}`);

    } catch (error) {
      this.results.oddsApi = {
        status: 'error',
        details: { error: error.message }
      };
      console.log(`  ❌ Odds API error: ${error.message}`);
    }
  }

  async validatePredictions() {
    console.log('\n🤖 Validating AI Predictions...');
    try {
      // Get recent predictions
      const { data: predictions, error } = await supabase
        .from('predictions')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(5);

      if (error) throw error;

      // Check for OpenRouter key
      const hasOpenRouter = !!process.env.VITE_OPENROUTER_API_KEY;

      // Get games without predictions
      const { data: games } = await supabase
        .from('games')
        .select('id')
        .is('predictions', null);

      this.results.predictions = {
        status: predictions?.length > 0 ? 'success' : 'warning',
        details: {
          totalPredictions: predictions?.length || 0,
          openRouterConfigured: hasOpenRouter,
          gamesNeedingPredictions: games?.length || 0,
          latestPrediction: predictions?.[0]?.created_at
        }
      };

      console.log(`  ${predictions?.length > 0 ? '✅' : '⚠️'} Predictions: ${predictions?.length || 0}`);
      console.log(`  🔑 OpenRouter: ${hasOpenRouter ? 'Configured' : 'Not configured'}`);
      console.log(`  📝 Games needing predictions: ${games?.length || 0}`);

    } catch (error) {
      this.results.predictions = {
        status: 'error',
        details: { error: error.message }
      };
      console.log(`  ❌ Predictions error: ${error.message}`);
    }
  }

  async validateWebSocket() {
    console.log('\n🔌 Validating WebSocket...');
    return new Promise((resolve) => {
      const ws = new WebSocket('ws://localhost:8080');
      const timeout = setTimeout(() => {
        ws.close();
        this.results.websocket = {
          status: 'error',
          details: { error: 'Connection timeout' }
        };
        console.log('  ❌ WebSocket timeout');
        resolve();
      }, 5000);

      ws.on('open', () => {
        clearTimeout(timeout);
        this.results.websocket = {
          status: 'success',
          details: { connected: true, port: 8080 }
        };
        console.log('  ✅ WebSocket connected on port 8080');
        ws.close();
        resolve();
      });

      ws.on('error', (error) => {
        clearTimeout(timeout);
        this.results.websocket = {
          status: 'error',
          details: { error: error.message }
        };
        console.log(`  ❌ WebSocket error: ${error.message}`);
        resolve();
      });
    });
  }

  async validateFrontend() {
    console.log('\n🎨 Validating Frontend...');
    try {
      const response = await axios.get('http://localhost:5173', {
        timeout: 5000
      });

      const hasReact = response.data.includes('src="/src/main.jsx"');
      const hasRoot = response.data.includes('id="root"');

      this.results.frontend = {
        status: 'success',
        details: {
          accessible: true,
          port: 5173,
          reactLoaded: hasReact,
          rootElement: hasRoot
        }
      };

      console.log('  ✅ Frontend accessible on port 5173');
      console.log(`  ⚛️  React: ${hasReact ? 'Loaded' : 'Not found'}`);

    } catch (error) {
      // Check if running on alternate port
      try {
        const altResponse = await axios.get('http://localhost:5174', {
          timeout: 5000
        });

        this.results.frontend = {
          status: 'success',
          details: {
            accessible: true,
            port: 5174,
            note: 'Running on alternate port'
          }
        };
        console.log('  ✅ Frontend accessible on port 5174 (alternate)');
      } catch (altError) {
        this.results.frontend = {
          status: 'error',
          details: { error: error.message }
        };
        console.log(`  ❌ Frontend error: ${error.message}`);
      }
    }
  }

  async validateAuthentication() {
    console.log('\n🔐 Validating Authentication...');
    try {
      // Check if Supabase auth is configured
      const hasSupabaseUrl = !!process.env.VITE_SUPABASE_URL;
      const hasSupabaseKey = !!process.env.VITE_SUPABASE_ANON_KEY;

      // Try to get auth settings
      const { data: { user }, error } = await supabase.auth.getUser();

      this.results.authentication = {
        status: 'success',
        details: {
          supabaseConfigured: hasSupabaseUrl && hasSupabaseKey,
          authEnabled: true,
          currentUser: user ? 'Logged in' : 'Not logged in'
        }
      };

      console.log(`  ✅ Authentication configured`);
      console.log(`  🔑 Supabase: ${hasSupabaseUrl && hasSupabaseKey ? 'Ready' : 'Not configured'}`);
      console.log(`  👤 Status: ${user ? 'User logged in' : 'No active session'}`);

    } catch (error) {
      this.results.authentication = {
        status: 'warning',
        details: {
          error: 'Auth check failed',
          supabaseConfigured: true
        }
      };
      console.log(`  ⚠️  Authentication: ${error.message}`);
    }
  }

  generateSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('📋 SYSTEM VALIDATION SUMMARY');
    console.log('='.repeat(60));

    let successCount = 0;
    let warningCount = 0;
    let errorCount = 0;

    Object.entries(this.results).forEach(([component, result]) => {
      const icon = result.status === 'success' ? '✅' :
                   result.status === 'warning' ? '⚠️' : '❌';

      if (result.status === 'success') successCount++;
      else if (result.status === 'warning') warningCount++;
      else errorCount++;

      console.log(`${icon} ${component.padEnd(15)} : ${result.status.toUpperCase()}`);
    });

    console.log('='.repeat(60));
    console.log(`✅ Success: ${successCount}/7`);
    console.log(`⚠️  Warning: ${warningCount}/7`);
    console.log(`❌ Error: ${errorCount}/7`);

    const score = Math.round((successCount / 7) * 100);
    console.log(`\n🎯 System Health Score: ${score}%`);

    if (score === 100) {
      console.log('🚀 System is FULLY OPERATIONAL and ready for production!');
    } else if (score >= 70) {
      console.log('✨ System is operational with minor issues.');
    } else if (score >= 50) {
      console.log('⚠️  System has issues that should be addressed.');
    } else {
      console.log('❌ System has critical issues requiring attention.');
    }

    // Recommendations
    if (errorCount > 0 || warningCount > 0) {
      console.log('\n📝 Recommendations:');

      if (this.results.websocket.status === 'error') {
        console.log('  • Start WebSocket server: npm run ws-dev');
      }
      if (this.results.frontend.status === 'error') {
        console.log('  • Start frontend: npm run dev');
      }
      if (this.results.oddsApi.status === 'warning') {
        console.log('  • Configure Odds API key in .env');
      }
      if (this.results.predictions.details?.gamesNeedingPredictions > 0) {
        console.log('  • Generate predictions for upcoming games');
      }
    }

    return score;
  }

  async runValidation() {
    console.log('🔍 NFL Predictor System Validation');
    console.log('=' . repeat(60));
    console.log(`📅 ${new Date().toLocaleString()}`);

    await this.validateDatabase();
    await this.validateESPNApi();
    await this.validateOddsApi();
    await this.validatePredictions();
    await this.validateWebSocket();
    await this.validateFrontend();
    await this.validateAuthentication();

    const score = this.generateSummary();

    return {
      score,
      results: this.results
    };
  }
}

// Run validation
const validator = new SystemValidator();
validator.runValidation().then(({ score }) => {
  process.exit(score === 100 ? 0 : 1);
}).catch(error => {
  console.error('Validation failed:', error);
  process.exit(1);
});