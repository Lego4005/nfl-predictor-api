import React, { useState, useEffect } from 'react';
import UserPicks from './UserPicks';
import userPicksService from '../services/userPicksService';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingIndicator } from './LoadingIndicator';
import { Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react';

const UserPicksContainer = () => {
  const [games, setGames] = useState([]);
  const [currentPicks, setCurrentPicks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [serverOnline, setServerOnline] = useState(true);

  // Fetch games data
  const fetchGames = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8084/api/predictions/1');
      if (!response.ok) {
        throw new Error(`Failed to fetch games: ${response.status}`);
      }

      const data = await response.json();

      // Transform the API data to match our component expectations
      const transformedGames = data.best_picks?.map(game => ({
        id: `${game.away_team}_vs_${game.home_team}_${Date.now()}`,
        homeTeam: game.home_team,
        awayTeam: game.away_team,
        homeScore: game.home_score || 0,
        awayScore: game.away_score || 0,
        homeWinProb: Math.round((game.home_win_prob || 0.5) * 100),
        awayWinProb: Math.round((game.away_win_prob || 0.5) * 100),
        status: game.status || 'scheduled',
        startTime: game.kickoff || new Date().toISOString(),
        quarter: game.quarter,
        time: game.time_remaining,
        spread: game.spread,
        total: game.total
      })) || [];

      setGames(transformedGames);
    } catch (error) {
      console.error('Error fetching games:', error);
      setError('Failed to load games. Using sample data.');

      // Fallback to sample data
      setGames([
        {
          id: 'sample_1',
          homeTeam: 'KC',
          awayTeam: 'BUF',
          homeScore: 0,
          awayScore: 0,
          homeWinProb: 55,
          awayWinProb: 45,
          status: 'scheduled',
          startTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
        },
        {
          id: 'sample_2',
          homeTeam: 'LAR',
          awayTeam: 'SF',
          homeScore: 0,
          awayScore: 0,
          homeWinProb: 48,
          awayWinProb: 52,
          status: 'scheduled',
          startTime: new Date(Date.now() + 25 * 60 * 60 * 1000).toISOString()
        },
        {
          id: 'sample_3',
          homeTeam: 'DAL',
          awayTeam: 'PHI',
          homeScore: 0,
          awayScore: 0,
          homeWinProb: 42,
          awayWinProb: 58,
          status: 'scheduled',
          startTime: new Date(Date.now() + 26 * 60 * 60 * 1000).toISOString()
        }
      ]);
    }
  };

  // Fetch current user picks
  const fetchCurrentPicks = async () => {
    try {
      const picks = await userPicksService.getUserPicks();
      setCurrentPicks(picks);
    } catch (error) {
      console.error('Error fetching current picks:', error);
      setCurrentPicks([]);
    }
  };

  // Check server health
  const checkServerHealth = async () => {
    try {
      const isOnline = await userPicksService.checkServerHealth();
      setServerOnline(isOnline);
    } catch (error) {
      setServerOnline(false);
    }
  };

  // Handle picks submission
  const handlePicksSubmit = async (picks) => {
    try {
      setError(null);
      const result = await userPicksService.submitPicks(picks);

      // Refresh current picks after successful submission
      await fetchCurrentPicks();

      return result;
    } catch (error) {
      console.error('Error submitting picks:', error);
      throw error;
    }
  };

  // Initial data loading
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        await Promise.all([
          checkServerHealth(),
          fetchGames(),
          fetchCurrentPicks()
        ]);
      } catch (error) {
        console.error('Error loading initial data:', error);
        setError('Failed to load data. Please try refreshing the page.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Refresh data
  const handleRefresh = async () => {
    setLoading(true);
    await loadData();
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <Card className="w-full max-w-md text-center p-8">
          <LoadingIndicator />
          <h3 className="text-lg font-semibold mt-4 mb-2">Loading NFL Picks</h3>
          <p className="text-muted-foreground">
            Fetching games and your current picks...
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Server Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {serverOnline ? (
              <>
                <Wifi className="w-5 h-5 text-green-500" />
                <span className="text-sm text-green-600 font-medium">Server Online</span>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-red-500" />
                <span className="text-sm text-red-600 font-medium">Server Offline</span>
              </>
            )}
          </div>

          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-white rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Server Offline Warning */}
        {!serverOnline && (
          <Alert>
            <WifiOff className="h-4 w-4" />
            <AlertDescription>
              The picks server appears to be offline. You can still view games and make picks,
              but they won't be saved until the server is back online.
            </AlertDescription>
          </Alert>
        )}

        {/* Main User Picks Component */}
        <UserPicks
          games={games}
          currentPicks={currentPicks}
          onPicksSubmit={handlePicksSubmit}
        />
      </div>
    </div>
  );
};

export default UserPicksContainer;