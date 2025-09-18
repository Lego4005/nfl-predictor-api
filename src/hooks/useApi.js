import { useState, useEffect, useRef } from "react";

// Mock data generators
function mockApi(path) {
  const TEAMS = [
    "SF", "CHI", "CIN", "BUF", "DEN", "CLE", "TB", "ARI", "LAC", "KC",
    "IND", "WAS", "DAL", "MIA", "PHI", "ATL", "NYG", "JAX", "NYJ", "DET",
    "GB", "CAR", "NE", "LV", "LAR", "BAL", "NO", "SEA", "PIT", "HOU",
    "TEN", "MIN"
  ];

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function rand(min, max) {
    return Math.random() * (max - min) + min;
  }

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  function fmtClock(s) {
    const m = Math.floor(s / 60);
    const ss = String(s % 60).padStart(2, "0");
    return `${m}:${ss}`;
  }

  function id() {
    return Math.random().toString(36).slice(2, 9);
  }

  function mockGame() {
    const home = pick(TEAMS),
      away = pick(TEAMS.filter((t) => t !== home));
    const hs = Math.round(rand(0, 35));
    const as = Math.round(rand(0, 35));
    const q = Math.ceil(rand(1, 4));
    const status = pick(["live", "scheduled", "final"]);
    const clock = Math.round(rand(0, 14 * 60));
    const homeProb = clamp(rand(0.35, 0.7), 0, 1);
    return {
      id: id(),
      homeTeam: home,
      awayTeam: away,
      homeScore: status === "scheduled" ? 0 : hs,
      awayScore: status === "scheduled" ? 0 : as,
      status,
      quarter: status === "scheduled" ? 0 : q,
      clock,
      time: fmtClock(clock),
      startTime: new Date(Date.now() + rand(-2, 6) * 3600000).toISOString(),
      prediction: {
        homeWinProb: +homeProb.toFixed(2),
        awayWinProb: +(1 - homeProb).toFixed(2),
        line: +rand(-7, 7).toFixed(1),
        confidence: +rand(0.55, 0.9).toFixed(2),
      },
      homeWinProb: Math.round(homeProb * 100),
      awayWinProb: Math.round((1 - homeProb) * 100),
      hasAIPrediction: true, // Enable AI predictions for mock data
    };
  }

  if (path.startsWith("/games")) {
    return Array.from({ length: 12 }).map(() => mockGame());
  }
  if (path.startsWith("/teams/analytics")) {
    return TEAMS.map((t) => ({
      team: t,
      ppg: +rand(17, 34).toFixed(1),
      oppg: +rand(16, 30).toFixed(1),
      offenseRank: Math.ceil(rand(1, 32)),
      defenseRank: Math.ceil(rand(1, 32)),
      elo: Math.round(rand(1350, 1750)),
      recent: Array.from({ length: 10 }).map(() => pick(["W", "L"])),
    }));
  }
  return [];
}

function useApi(path, { refreshMs = 30000, demo = false } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const loadedRef = useRef(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    // Prevent multiple loads for the same path
    if (loadedRef.current) return;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        let result;
        if (demo) {
          // Demo mode with small delay
          await new Promise((resolve) => setTimeout(resolve, 100));
          result = mockApi(path);
        } else if (path === "/games") {
          // Import and use supabaseHelpers for real game data - CACHED
          const { supabaseHelpers } = await import(
            "../services/supabaseClient.js"
          );
          const rawGames = await supabaseHelpers.getCurrentGames();

          // Transform Supabase data format to match frontend expectations
          result = rawGames.map((game) => {
            // Extract AI prediction data from Supabase
            const aiPrediction =
              game.predictions && game.predictions.length > 0
                ? game.predictions[0]
                : null;

            return {
              id: game.id,
              homeTeam: game.home_team,
              awayTeam: game.away_team,
              homeScore: game.home_score || 0,
              awayScore: game.away_score || 0,
              status: game.status,
              quarter: game.quarter || 0,
              clock: game.time_remaining
                ? game.time_remaining.includes(":")
                  ? parseInt(game.time_remaining.split(":")[0]) * 60 +
                    parseInt(game.time_remaining.split(":")[1])
                  : 0
                : 0,
              time: game.time_remaining || "0:00",
              startTime: game.game_time,
              prediction: {
                homeWinProb: aiPrediction?.home_win_prob
                  ? aiPrediction.home_win_prob / 100
                  : 0.5,
                awayWinProb: aiPrediction?.away_win_prob
                  ? aiPrediction.away_win_prob / 100
                  : 0.5,
                line: aiPrediction?.predicted_spread || 0,
                confidence: aiPrediction?.confidence
                  ? aiPrediction.confidence / 100
                  : 0.5,
                predictedTotal: aiPrediction?.predicted_total || null,
              },
              homeWinProb: aiPrediction?.home_win_prob || 50,
              awayWinProb: aiPrediction?.away_win_prob || 50,
              // Add AI prediction flags for the card component
              hasAIPrediction: !!aiPrediction,
              aiPrediction: aiPrediction,
            };
          });
        } else {
          // For other paths, check if we have specific handlers
          if (!demo) {
            // Real data mode - return empty data for all non-games endpoints
            result = [];
          } else if (
            path === "/teams/analytics" ||
            path === "/predictions/accuracy" ||
            path === "/odds" ||
            path === "/odds/movements" ||
            path === "/injuries" ||
            path === "/models/leaderboard" ||
            path === "/system/health"
          ) {
            // Demo mode - return empty or minimal data instead of random mock data
            result = [];
          } else {
            // Fallback for unknown paths
            result = [];
          }
        }

        setData(result);
        loadedRef.current = true;
      } catch (e) {
        console.error("API Error for", path, ":", e);
        setError(e);
        // Don't fallback to mock data - show empty instead
        if (!data) {
          setData([]);
        }
      } finally {
        setLoading(false);
      }
    }

    // Initial load
    load();

    // Set up background refresh interval only for live data
    if (!demo && path === "/games") {
      intervalRef.current = setInterval(async () => {
        try {
          const { supabaseHelpers } = await import(
            "../services/supabaseClient.js"
          );
          const rawGames = await supabaseHelpers.getCurrentGames();
          const result = rawGames.map((game) => {
            // Extract AI prediction data from Supabase
            const aiPrediction =
              game.predictions && game.predictions.length > 0
                ? game.predictions[0]
                : null;

            return {
              id: game.id,
              homeTeam: game.home_team,
              awayTeam: game.away_team,
              homeScore: game.home_score || 0,
              awayScore: game.away_score || 0,
              status: game.status,
              quarter: game.quarter || 0,
              clock: game.time_remaining
                ? game.time_remaining.includes(":")
                  ? parseInt(game.time_remaining.split(":")[0]) * 60 +
                    parseInt(game.time_remaining.split(":")[1])
                  : 0
                : 0,
              time: game.time_remaining || "0:00",
              startTime: game.game_time,
              prediction: {
                homeWinProb: aiPrediction?.home_win_prob
                  ? aiPrediction.home_win_prob / 100
                  : 0.5,
                awayWinProb: aiPrediction?.away_win_prob
                  ? aiPrediction.away_win_prob / 100
                  : 0.5,
                line: aiPrediction?.predicted_spread || 0,
                confidence: aiPrediction?.confidence
                  ? aiPrediction.confidence / 100
                  : 0.5,
                predictedTotal: aiPrediction?.predicted_total || null,
              },
              homeWinProb: aiPrediction?.home_win_prob || 50,
              awayWinProb: aiPrediction?.away_win_prob || 50,
              // Add AI prediction flags for the card component
              hasAIPrediction: !!aiPrediction,
              aiPrediction: aiPrediction,
            };
          });
          setData(result);
        } catch (e) {
          console.error("Background refresh error:", e);
        }
      }, refreshMs);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []); // Empty dependency array to prevent re-runs

  return { data, loading, error };
}

export default useApi;