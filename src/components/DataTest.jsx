import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { supabase, supabaseHelpers } from '../services/supabaseClient';
import espnService from '../services/espnApiService';
import { RefreshCw, Database, Wifi, CheckCircle, XCircle } from 'lucide-react';

const DataTest = () => {
  const [supabaseStatus, setSupabaseStatus] = useState('checking');
  const [espnStatus, setEspnStatus] = useState('checking');
  const [games, setGames] = useState([]);
  const [syncResult, setSyncResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Test Supabase connection
  const testSupabase = async () => {
    try {
      const { data, error } = await supabase
        .from('games')
        .select('count')
        .limit(1);

      if (error) throw error;
      setSupabaseStatus('connected');
      console.log('Supabase connected!');
    } catch (error) {
      setSupabaseStatus('error');
      console.error('Supabase error:', error);
    }
  };

  // Test ESPN API
  const testESPN = async () => {
    try {
      const scoreboard = await espnService.getScoreboard();
      if (scoreboard && scoreboard.events) {
        setEspnStatus('connected');
        console.log('ESPN API connected! Found', scoreboard.events.length, 'games');
      }
    } catch (error) {
      setEspnStatus('error');
      console.error('ESPN error:', error);
    }
  };

  // Sync ESPN data to Supabase
  const syncData = async () => {
    setLoading(true);
    try {
      const result = await espnService.syncGamesToSupabase();
      setSyncResult(result);

      // Fetch games after sync
      const gamesData = await supabaseHelpers.getCurrentGames();
      setGames(gamesData || []);
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Initial tests
  useEffect(() => {
    testSupabase();
    testESPN();
  }, []);

  // Subscribe to real-time updates
  useEffect(() => {
    const subscription = supabaseHelpers.subscribeToGames((payload) => {
      console.log('Real-time update:', payload);
      if (payload.eventType === 'INSERT' || payload.eventType === 'UPDATE') {
        // Refresh games list
        supabaseHelpers.getCurrentGames().then(data => {
          setGames(data || []);
        });
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const getStatusIcon = (status) => {
    if (status === 'connected') return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (status === 'error') return <XCircle className="w-4 h-4 text-red-500" />;
    return <RefreshCw className="w-4 h-4 animate-spin" />;
  };

  const getStatusColor = (status) => {
    if (status === 'connected') return 'bg-green-600';
    if (status === 'error') return 'bg-red-600';
    return 'bg-yellow-600';
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">Data Integration Test</h2>

      {/* Connection Status */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                <span className="font-semibold">Supabase Database</span>
              </div>
              {getStatusIcon(supabaseStatus)}
            </div>
          </CardHeader>
          <CardContent>
            <Badge className={getStatusColor(supabaseStatus)}>
              {supabaseStatus.toUpperCase()}
            </Badge>
            <p className="text-sm text-muted-foreground mt-2">
              Project: vaypgzvivahnfegnlinn
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wifi className="w-5 h-5" />
                <span className="font-semibold">ESPN API</span>
              </div>
              {getStatusIcon(espnStatus)}
            </div>
          </CardHeader>
          <CardContent>
            <Badge className={getStatusColor(espnStatus)}>
              {espnStatus.toUpperCase()}
            </Badge>
            <p className="text-sm text-muted-foreground mt-2">
              No authentication required
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Sync Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Data Sync</h3>
            <Button onClick={syncData} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Sync ESPN Data
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {syncResult && (
            <div className="space-y-2">
              <p className="text-sm">
                <strong>Total Games:</strong> {syncResult.total}
              </p>
              <p className="text-sm">
                <strong>Synced:</strong> {syncResult.synced}
              </p>
              {syncResult.errors.length > 0 && (
                <p className="text-sm text-red-600">
                  <strong>Errors:</strong> {syncResult.errors.length}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Games from Database */}
      <Card>
        <CardHeader>
          <h3 className="font-semibold">Games in Database</h3>
        </CardHeader>
        <CardContent>
          {games.length === 0 ? (
            <p className="text-muted-foreground">No games found. Click "Sync ESPN Data" to populate.</p>
          ) : (
            <div className="space-y-2">
              {games.slice(0, 5).map(game => (
                <div key={game.id} className="flex items-center justify-between p-2 bg-muted rounded">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{game.status}</Badge>
                    <span className="text-sm font-medium">
                      {game.away_team} @ {game.home_team}
                    </span>
                  </div>
                  <div className="text-sm">
                    {game.away_score} - {game.home_score}
                  </div>
                </div>
              ))}
              {games.length > 5 && (
                <p className="text-sm text-muted-foreground">
                  ... and {games.length - 5} more games
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <h3 className="font-semibold">Next Steps</h3>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2 text-sm">
            <li>Click "Sync ESPN Data" to populate the database with current NFL games</li>
            <li>Real-time updates will appear automatically when games change</li>
            <li>Check the browser console for detailed logs</li>
            <li>The data will now be available in your main dashboard</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataTest;