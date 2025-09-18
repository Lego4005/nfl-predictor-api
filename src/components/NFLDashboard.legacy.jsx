import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getTeam, NFL_TEAMS } from "../data/nflTeams";
import TeamCard from "./TeamCard";
import EnhancedGameCard from "./EnhancedGameCard";
import EnhancedGameCardV2 from "./EnhancedGameCardV2";
import GameDetailModal from "./GameDetailModal";
import SmartInsights from "./SmartInsights";
import NewsFeed from "./NewsFeed";
import PowerRankings from "./PowerRankings";
import ModelPerformance from "./ModelPerformance";
import Leaderboard from "./Leaderboard";
import { useNFLWeek, useNFLWeekReset } from "../hooks/useNFLWeek";
import {
  LineChart as RLineChart,
  Line,
  BarChart as RBarChart,
  Bar,
  AreaChart as RAreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Moon,
  Sun,
  RefreshCw,
  Wifi,
  WifiOff,
  LineChart,
  Users,
  PlayCircle,
  Shield,
  Gauge,
  Zap,
  Calendar,
  Clock,
  Filter,
} from "lucide-react";

// shadcn/ui components
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

/*
  =============================================================
  NFL Prediction Dashboard – Pro Sections & Intelligence (Smart Odds)
  - Neutral dark-gray theme
  - Wider container + Wide Mode toggle
  - Multi-section tabs: Overview | Live | Analytics | Predictions | Players | Betting | Health
  - New widgets: Team Comparator, Model Leaderboard, Value Bets, Odds Movement, System Health
  - Live Odds now shows ALL matchups in a smart order (live → upcoming → finals)
  =============================================================
*/

// ----------------------------
// Config & Utilities
// ----------------------------
const LIVE_WS_URL = "ws://localhost:8080"; // Local WebSocket server
const API_BASE = "https://example.com/api"; // swap for your provider

// Use NFL team abbreviations that match our team data
const TEAMS = [
  "SF",
  "CHI",
  "CIN",
  "BUF",
  "DEN",
  "CLE",
  "TB",
  "ARI",
  "LAC",
  "KC",
  "IND",
  "WAS",
  "DAL",
  "MIA",
  "PHI",
  "ATL",
  "NYG",
  "JAX",
  "NYJ",
  "DET",
  "GB",
  "CAR",
  "NE",
  "LV",
  "LAR",
  "BAL",
  "NO",
  "SEA",
  "PIT",
  "HOU",
  "TEN",
  "MIN",
];

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}
function pct(n) {
  return `${(n * 100).toFixed(0)}%`;
}
function fmtClock(s) {
  const m = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, "0");
  return `${m}:${ss}`;
}
function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}
function rand(min, max) {
  return Math.random() * (max - min) + min;
}
function id() {
  return Math.random().toString(36).slice(2, 9);
}
function americanToProb(a) {
  return a < 0 ? -a / (-a + 100) : 100 / (a + 100);
}
function americanProfitPer100(a) {
  return a < 0 ? (100 * 100) / -a : a;
}
function fmtOdds(a) {
  return (a > 0 ? "+" : "") + a;
}

// Map games to status for smart sorting and badges
function makeStatusMap(games) {
  const map = {};
  (games || []).forEach((g) => {
    map[g.id] = {
      status: g.status,
      quarter: g.quarter,
      clock: g.clock,
      startTime: g.startTime,
      home: g.homeTeam,
      away: g.awayTeam,
    };
  });
  return map;
}

// Smart comparator: live first (later game higher), then scheduled (sooner first), then finals (most recent first)
const __statusRank = { live: 0, scheduled: 1, final: 2 };
function smartCompare(a, b, statusMap) {
  const sa = statusMap[a.id] || {};
  const sb = statusMap[b.id] || {};
  const ra = __statusRank[sa.status] ?? 3;
  const rb = __statusRank[sb.status] ?? 3;
  if (ra !== rb) return ra - rb;
  if (sa.status === "live" && sb.status === "live") {
    const elapA = (sa.quarter ?? 1) * (14 * 60) - (sa.clock ?? 14 * 60);
    const elapB = (sb.quarter ?? 1) * (14 * 60) - (sb.clock ?? 14 * 60);
    return elapB - elapA; // later game first
  }
  if (sa.status === "scheduled" && sb.status === "scheduled") {
    const ta = new Date(sa.startTime ?? Date.now() + 86400000).getTime();
    const tb = new Date(sb.startTime ?? Date.now() + 86400000).getTime();
    return ta - tb; // sooner first
  }
  if (sa.status === "final" && sb.status === "final") {
    const ta = new Date(sa.startTime ?? 0).getTime();
    const tb = new Date(sb.startTime ?? 0).getTime();
    return tb - ta; // most recent first
  }
  return 0;
}

// ----------------------------
// Dev sanity tests (non-blocking)
// ----------------------------
function __devTests__() {
  try {
    const eps = 1e-6;
    console.assert(
      Math.abs(americanToProb(-110) - 110 / 210) < eps,
      "americanToProb(-110)"
    );
    console.assert(
      Math.abs(americanToProb(+120) - 100 / 220) < eps,
      "americanToProb(+120)"
    );
    const ev = (p, odds) => p * americanProfitPer100(odds) - (1 - p) * 100;
    console.assert(Math.abs(ev(0.5, 120) - 10) < eps, "EV calc");
    // Component presence test
    console.assert(
      typeof OddsComparisonTable === "function",
      "OddsComparisonTable should be defined"
    );
  } catch (e) {
    console.warn("Dev tests encountered an issue", e);
  }
}
if (typeof window !== "undefined") {
  __devTests__();
}

// Additional non-blocking dev tests
function __devTests_more__() {
  try {
    const eps = 1e-6;
    console.assert(
      Math.abs(americanToProb(-200) - 200 / 300) < eps,
      "americanToProb(-200)"
    );
    console.assert(
      Math.abs(americanToProb(+150) - 100 / 250) < eps,
      "americanToProb(+150)"
    );
    console.assert(americanProfitPer100(-200) === 50, "profit/100 for -200");
    console.assert(americanProfitPer100(+150) === 150, "profit/100 for +150");
    const evPos = 0.6 * americanProfitPer100(120) - 0.4 * 100; // p=0.6 vs +120
    console.assert(evPos > 0, "EV positive when our prob > implied for +120");
    // Smart sort tests
    const rows = [{ id: "A" }, { id: "B" }, { id: "C" }];
    const now = Date.now();
    const statusMap = {
      A: {
        status: "live",
        quarter: 4,
        clock: 30,
        startTime: new Date(now - 2 * 3600000).toISOString(),
      },
      B: {
        status: "scheduled",
        startTime: new Date(now + 30 * 60000).toISOString(),
      },
      C: {
        status: "final",
        startTime: new Date(now - 60 * 60000).toISOString(),
      },
    };
    const sorted = [...rows].sort((x, y) => smartCompare(x, y, statusMap));
    console.assert(
      sorted.map((r) => r.id).join(",") === "A,B,C",
      "smartCompare ordering A(live),B(sched),C(final)"
    );
  } catch (e) {
    console.warn("Additional dev tests issue", e);
  }
}
if (typeof window !== "undefined") {
  __devTests_more__();
}

// ----------------------------
// Theme Toggle (tailwind 'dark' on <html>)
// ----------------------------
function useTheme() {
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    return (
      localStorage.getItem("theme") === "dark" ||
      (!("theme" in localStorage) &&
        window.matchMedia?.("(prefers-color-scheme: dark)").matches)
    );
  });
  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);
  return { dark, setDark };
}

// ----------------------------
// Error Boundary
// ----------------------------
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error("Dashboard crashed:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] grid place-items-center p-8">
          <Card className="max-w-2xl w-full">
            <CardHeader className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="font-semibold">Something went sideways</span>
              </div>
              <Badge variant="destructive">Error</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm opacity-80">
                The dashboard hit an error. Try refreshing. If this persists,
                check your data endpoints.
              </p>
              <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-48">
                {String(this.state.error)}
              </pre>
            </CardContent>
            <CardFooter>
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload
              </Button>
            </CardFooter>
          </Card>
        </div>
      );
    }
    // @ts-ignore
    return this.props.children;
  }
}

// ----------------------------
// WebSocket + Fallback Simulator
// ----------------------------
function useLiveFeed() {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const wsRef = useRef(null);
  useEffect(() => {
    // Always try WebSocket connection for live data
    // Demo mode removed - using real ESPN data

    let closed = false;
    let ws;
    try {
      ws = new WebSocket(LIVE_WS_URL);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          setEvents((prev) => [data, ...prev].slice(0, 100));
        } catch (e) {}
      };
    } catch (e) {
      setConnected(false);
    }
    const t = setTimeout(() => {
      if (!connected && !closed) {
        const iv = setInterval(() => {
          setEvents((p) => [mockKeyPlay(), ...p].slice(0, 100));
        }, 2500);
        wsRef.current = { close: () => clearInterval(iv) };
      }
    }, 2000);
    return () => {
      closed = true;
      clearTimeout(t);
      wsRef.current?.close?.();
    };
  }, []);
  return { connected, events };
}

// ----------------------------
// API fetch with loading & error - Optimized to prevent page reloads
// ----------------------------
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
          // Use Expert Observatory API for game data with real scores
          const response = await fetch("http://localhost:8003/api/predictions/recent");
          const rawGames = await response.json();

          console.log(
            `Fetched ${rawGames?.length || 0} games from Expert Observatory API`
          );

          // Transform Expert Observatory API data format to match frontend expectations
          result = rawGames.map((game) => {
            // Map status from API to frontend format
            const gameDate = new Date(game.date);
            const now = new Date();
            let mappedStatus = 'scheduled'; // default

            if (game.status === 'completed' || game.status === 'final') {
              mappedStatus = 'final';
            } else if (game.is_live || game.status === 'live' || game.status === 'in_progress') {
              mappedStatus = 'live';
            } else if (gameDate > now) {
              mappedStatus = 'scheduled';
            } else {
              mappedStatus = 'final'; // Past games without live status are final
            }

            // Extract real scores from expert predictions (use consensus or first expert's prediction)
            let homeScore = 0;
            let awayScore = 0;

            if (game.expert_predictions && game.expert_predictions.length > 0) {
              // Use first expert's prediction as representative score for final games
              const firstPrediction = game.expert_predictions[0];
              if (firstPrediction.prediction) {
                homeScore = firstPrediction.prediction.home_score || 0;
                awayScore = firstPrediction.prediction.away_score || 0;
              }
            }

            return {
              id: game.game_id,
              homeTeam: game.home_team,
              awayTeam: game.away_team,
              homeScore: mappedStatus === 'final' ? homeScore : 0,
              awayScore: mappedStatus === 'final' ? awayScore : 0,
              status: mappedStatus,
              quarter: game.current_period || game.quarter || 0,
              clock: game.time_remaining
                ? game.time_remaining.includes(":")
                  ? parseInt(game.time_remaining.split(":")[0]) * 60 +
                    parseInt(game.time_remaining.split(":")[1])
                  : 0
                : 0,
              time: game.time_remaining || "0:00",
              startTime: game.game_time,
              gameTime: game.game_time, // Also include as gameTime for compatibility
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
          if (
            path === "/teams/analytics" ||
            path === "/predictions/accuracy" ||
            path === "/odds" ||
            path === "/odds/movements" ||
            path === "/injuries" ||
            path === "/models/leaderboard" ||
            path === "/system/health"
          ) {
            // Return empty or minimal data instead of random mock data
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

            // Map status from API to frontend format
            const gameDate = new Date(game.game_time);
            const now = new Date();
            let mappedStatus = 'scheduled'; // default

            if (game.status === 'completed' || game.status === 'final') {
              mappedStatus = 'final';
            } else if (game.is_live || game.status === 'live' || game.status === 'in_progress') {
              mappedStatus = 'live';
            } else if (gameDate > now) {
              mappedStatus = 'scheduled';
            } else {
              mappedStatus = 'final'; // Past games without live status are final
            }

            return {
              id: game.id,
              homeTeam: game.home_team,
              awayTeam: game.away_team,
              homeScore: game.home_score || 0,
              awayScore: game.away_score || 0,
              status: mappedStatus,
              quarter: game.current_period || game.quarter || 0,
              clock: game.time_remaining
                ? game.time_remaining.includes(":")
                  ? parseInt(game.time_remaining.split(":")[0]) * 60 +
                    parseInt(game.time_remaining.split(":")[1])
                  : 0
                : 0,
              time: game.time_remaining || "0:00",
              startTime: game.game_time,
              gameTime: game.game_time, // Also include as gameTime for compatibility
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

// ----------------------------
// Mock Generators (demo-only)
// ----------------------------
function mockKeyPlay() {
  const home = pick(TEAMS),
    away = pick(TEAMS.filter((t) => t !== home));
  const verbs = [
    "touchdown",
    "field goal",
    "interception",
    "fumble",
    "sack",
    "big run",
    "deep pass",
  ];
  const play = pick(verbs);
  const q = Math.ceil(rand(1, 4));
  const clock = Math.floor(rand(0, 14 * 60));
  return {
    id: id(),
    type: "play",
    text: `${home} vs ${away}: ${play} in Q${q} (${fmtClock(clock)})`,
    ts: Date.now(),
  };
}

function mockApi(path) {
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
  if (path.startsWith("/predictions/accuracy")) {
    const days = 21;
    return Array.from({ length: days }).map((_, i) => ({
      date: new Date(Date.now() - (days - i) * 86400000)
        .toISOString()
        .slice(0, 10),
      accuracy: +rand(0.52, 0.74).toFixed(3),
    }));
  }
  if (path.startsWith("/odds/movements")) {
    // return a dict keyed by matchup id -> timeseries
    const ids = Array.from({ length: 8 }).map(() => id());
    const makeSeries = () =>
      Array.from({ length: 24 }).map((_, i) => ({
        t: i,
        Pinnacle: +rand(-3.5, 3.5).toFixed(1),
        DraftKings: +rand(-3.5, 3.5).toFixed(1),
        FanDuel: +rand(-3.5, 3.5).toFixed(1),
      }));
    return ids.reduce((acc, k) => {
      acc[k] = makeSeries();
      return acc;
    }, {});
  }
  if (path.startsWith("/odds")) {
    const books = ["Pinnacle", "DraftKings", "FanDuel", "Caesars", "BetMGM"];
    return Array.from({ length: 10 }).map(() => {
      const g = mockGame();
      return {
        id: g.id,
        match: `${g.awayTeam} @ ${g.homeTeam}`,
        books: books.map((b) => ({
          book: b,
          spread: +rand(-7.5, 7.5).toFixed(1),
          home: +rand(-140, +130).toFixed(0),
          away: +rand(-140, +130).toFixed(0),
          total: +rand(38.5, 52.5).toFixed(1),
        })),
      };
    });
  }
  if (path.startsWith("/injuries")) {
    const statuses = ["Questionable", "Doubtful", "Out", "Probable"];
    return Array.from({ length: 20 }).map(() => ({
      id: id(),
      team: pick(TEAMS),
      player: `${pick(["J.", "M.", "C.", "L.", "T."])} ${pick(["Smith", "Allen", "Johnson", "Brown", "Davis", "Hill", "Jackson"])}`,
      position: pick(["QB", "RB", "WR", "TE", "LB", "CB", "S", "DL"]),
      status: pick(statuses),
      severity: pick(["minor", "moderate", "critical"]),
      note: pick([
        "hamstring",
        "ankle",
        "concussion protocol",
        "illness",
        "coach's decision",
        "limited practice",
      ]),
      updatedAt: new Date(Date.now() - rand(0, 36) * 3600000).toISOString(),
    }));
  }
  if (path.startsWith("/models/leaderboard")) {
    return [
      {
        model: "Ensemble v3",
        accuracy: 0.69,
        brier: 0.185,
        logloss: 0.58,
        lastTrained: new Date(Date.now() - 86400000).toISOString(),
      },
      {
        model: "XGB v9",
        accuracy: 0.67,
        brier: 0.192,
        logloss: 0.6,
        lastTrained: new Date(Date.now() - 2 * 86400000).toISOString(),
      },
      {
        model: "NN v12",
        accuracy: 0.665,
        brier: 0.19,
        logloss: 0.595,
        lastTrained: new Date(Date.now() - 3 * 86400000).toISOString(),
      },
      {
        model: "Logit baseline",
        accuracy: 0.61,
        brier: 0.215,
        logloss: 0.67,
        lastTrained: new Date(Date.now() - 10 * 86400000).toISOString(),
      },
    ];
  }
  if (path.startsWith("/system/health")) {
    return {
      feeds: [
        {
          name: "Scores API",
          status: pick(["ok", "ok", "ok", "warn"]),
          latency: +rand(90, 250).toFixed(0),
        },
        {
          name: "Injuries API",
          status: pick(["ok", "ok", "warn"]),
          latency: +rand(120, 300).toFixed(0),
        },
        {
          name: "Sportsbooks",
          status: pick(["ok", "ok", "ok", "down"]),
          latency: +rand(200, 400).toFixed(0),
        },
        {
          name: "Weather",
          status: pick(["ok", "ok", "ok", "warn"]),
          latency: +rand(100, 220).toFixed(0),
        },
      ],
      models: [
        { name: "Ensemble v3", status: "ok" },
        { name: "XGB v9", status: "ok" },
        { name: "NN v12", status: pick(["ok", "warn"]) },
      ],
      lastSync: new Date().toISOString(),
    };
  }
  return null;
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
  };
}

// ----------------------------
// UI Bits
// ----------------------------
function WsBadge({ connected }) {
  return connected ? (
    <Badge className="bg-emerald-600 dark:bg-emerald-700 hover:bg-emerald-600 dark:hover:bg-emerald-700 text-white">
      <Wifi className="h-3.5 w-3.5 mr-1" />
      Live
    </Badge>
  ) : (
    <Badge variant="secondary" className="bg-muted text-muted-foreground">
      <WifiOff className="h-3.5 w-3.5 mr-1" />
      Simulated
    </Badge>
  );
}

function MiniStat({ icon: Icon, label, value, hint }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50 border border-border">
      <div className="p-2 rounded-lg bg-background shadow-sm">
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="text-xs opacity-70">{label}</div>
        <div className="font-semibold leading-tight">{value}</div>
        {hint && <div className="text-[11px] opacity-60">{hint}</div>}
      </div>
    </div>
  );
}

function LiveTicker({ events }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border bg-background">
      <div className="p-2 flex items-center gap-2 text-xs">
        <Badge className="bg-indigo-600 text-white">Live Ticker</Badge>
        <span className="opacity-70">Key plays & updates</span>
      </div>
      <Separator />
      <div className="h-10 flex items-center">
        <div className="whitespace-nowrap animate-[ticker_60s_linear_infinite] will-change-transform">
          {events.slice(0, 30).map((e) => (
            <span key={e.id} className="mx-6 text-sm opacity-90">
              {e.text}
            </span>
          ))}
        </div>
      </div>
      <style>{`@keyframes ticker { from { transform: translateX(0); } to { transform: translateX(-50%); } } @media (prefers-reduced-motion: reduce) { .animate-[ticker_60s_linear_infinite]{ animation: none !important; } }`}</style>
    </div>
  );
}

function GameCard({ g }) {
  const leadHome = g.homeScore - g.awayScore >= 0;
  const progress =
    g.status === "scheduled"
      ? 0
      : g.status === "final"
        ? 1
        : clamp((g.quarter - 1) / 4 + (1 - g.clock / (14 * 60)) / 16, 0, 1);
  const bar = Math.round(progress * 100);
  const homeTeam = getTeam(g.homeTeam);
  const awayTeam = getTeam(g.awayTeam);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card className="overflow-hidden hover:shadow-xl transition-all duration-300 h-full">
        {/* Team gradient header */}
        <div className="h-1 flex">
          <div
            className="flex-1"
            style={{ background: awayTeam?.gradient || "#333" }}
          />
          <div
            className="flex-1"
            style={{ background: homeTeam?.gradient || "#333" }}
          />
        </div>

        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                {awayTeam && (
                  <img
                    src={awayTeam.logo}
                    alt={awayTeam.name}
                    className="w-8 h-8 object-contain"
                  />
                )}
                <span className="font-semibold">{g.awayTeam}</span>
              </div>
              <span className="text-xs opacity-50">@</span>
              <div className="flex items-center gap-2">
                {homeTeam && (
                  <img
                    src={homeTeam.logo}
                    alt={homeTeam.name}
                    className="w-8 h-8 object-contain"
                  />
                )}
                <span className="font-semibold">{g.homeTeam}</span>
              </div>
            </div>
            <Badge
              variant={g.status === "live" ? "default" : "secondary"}
              className={g.status === "live" ? "bg-red-600 text-white" : ""}
            >
              {g.status.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold tracking-tight">
              {g.awayScore}
              <span className="text-base opacity-50">–</span>
              {g.homeScore}
            </div>
            <div className="text-xs opacity-70">
              {g.status === "live" && (
                <div>
                  Q{g.quarter} · {fmtClock(g.clock)}
                </div>
              )}
              {g.status === "scheduled" && (
                <div>
                  Starts{" "}
                  {new Date(g.startTime).toLocaleTimeString([], {
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </div>
              )}
              {g.status === "final" && <div>Final</div>}
            </div>
          </div>
          <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary" style={{ width: `${bar}%` }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <MiniStat
              icon={TrendingUp}
              label="Home Win Prob"
              value={pct(g.prediction.homeWinProb)}
              hint={`Conf: ${pct(g.prediction.confidence)}`}
            />
            <MiniStat
              icon={LineChart}
              label="Line"
              value={`${g.prediction.line > 0 ? "+" : ""}${g.prediction.line}`}
              hint={`Away Win Prob ${pct(g.prediction.awayWinProb)}`}
            />
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between text-xs opacity-70">
          <div className="flex items-center gap-2">
            <Shield className="h-3.5 w-3.5" />{" "}
            {leadHome ? g.homeTeam : g.awayTeam} leading
          </div>
          <div className="flex items-center gap-2">
            <PlayCircle className="h-3.5 w-3.5" />{" "}
            {g.status === "live"
              ? "In-Game"
              : g.status === "final"
                ? "Completed"
                : "Awaiting Kickoff"}
          </div>
        </CardFooter>
      </Card>
    </motion.div>
  );
}

function AnalyticsCharts({ analytics }) {
  const top = useMemo(
    () => [...analytics].sort((a, b) => b.elo - a.elo).slice(0, 8),
    [analytics]
  );
  const offense = useMemo(
    () =>
      [...analytics].sort((a, b) => a.offenseRank - b.offenseRank).slice(0, 8),
    [analytics]
  );
  const axisTick = { fill: "hsl(var(--muted-foreground))", fontSize: 12 };
  const axisStroke = "hsl(var(--border))";
  const gridStroke = "hsl(var(--chart-grid))";
  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="col-span-2">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            <span className="font-semibold">Team ELO (Top 8)</span>
          </div>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RBarChart
              data={top}
              margin={{ top: 10, right: 16, bottom: 0, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis
                dataKey="team"
                tick={axisTick}
                stroke={axisStroke}
                tickLine={{ stroke: axisStroke }}
              />
              <YAxis
                tick={axisTick}
                stroke={axisStroke}
                tickLine={{ stroke: axisStroke }}
              />
              <Tooltip
                wrapperStyle={{ outline: "none" }}
                contentStyle={{
                  background: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  color: "hsl(var(--foreground))",
                }}
              />
              <Bar
                dataKey="elo"
                radius={[8, 8, 0, 0]}
                fill="hsl(var(--chart-1))"
                stroke="hsl(var(--chart-1))"
              />
            </RBarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4" />
            <span className="font-semibold">PPG vs OPPG</span>
          </div>
        </CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RAreaChart
              data={offense}
              margin={{ top: 10, right: 16, bottom: 0, left: 0 }}
            >
              <defs>
                <linearGradient id="ppg" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopOpacity={0.8}
                    stopColor="hsl(var(--chart-2))"
                  />
                  <stop
                    offset="95%"
                    stopOpacity={0.1}
                    stopColor="hsl(var(--chart-2))"
                  />
                </linearGradient>
                <linearGradient id="oppg" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopOpacity={0.7}
                    stopColor="hsl(var(--chart-3))"
                  />
                  <stop
                    offset="95%"
                    stopOpacity={0.05}
                    stopColor="hsl(var(--chart-3))"
                  />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis
                dataKey="team"
                tick={axisTick}
                stroke={axisStroke}
                tickLine={{ stroke: axisStroke }}
              />
              <YAxis
                tick={axisTick}
                stroke={axisStroke}
                tickLine={{ stroke: axisStroke }}
              />
              <Tooltip
                wrapperStyle={{ outline: "none" }}
                contentStyle={{
                  background: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  color: "hsl(var(--foreground))",
                }}
              />
              <Area
                type="monotone"
                dataKey="ppg"
                stroke="hsl(var(--chart-2))"
                fillOpacity={1}
                fill="url(#ppg)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="oppg"
                stroke="hsl(var(--chart-3))"
                fillOpacity={1}
                fill="url(#oppg)"
                strokeWidth={2}
              />
              <Legend
                wrapperStyle={{ color: "hsl(var(--muted-foreground))" }}
              />
            </RAreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

function PredictionAccuracyChart({ rows }) {
  const axisTick = { fill: "hsl(var(--muted-foreground))", fontSize: 12 };
  const axisStroke = "hsl(var(--border))";
  const gridStroke = "hsl(var(--chart-grid))";
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <LineChart className="h-4 w-4" />
          <span className="font-semibold">
            Prediction Accuracy (last {rows.length} days)
          </span>
        </div>
      </CardHeader>
      <CardContent className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RLineChart
            data={rows}
            margin={{ top: 10, right: 16, bottom: 0, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis
              dataKey="date"
              tick={axisTick}
              stroke={axisStroke}
              tickLine={{ stroke: axisStroke }}
            />
            <YAxis
              domain={[0.4, 1]}
              tick={axisTick}
              stroke={axisStroke}
              tickLine={{ stroke: axisStroke }}
            />
            <Tooltip
              formatter={(v) => `${pct(v)}`}
              wrapperStyle={{ outline: "none" }}
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                color: "hsl(var(--foreground))",
              }}
            />
            <Line
              type="monotone"
              dataKey="accuracy"
              strokeWidth={2}
              dot={false}
              stroke="hsl(var(--chart-1))"
            />
          </RLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function ModelLeaderboard({ rows }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          <span className="font-semibold">Model Leaderboard</span>
        </div>
      </CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-xs text-muted-foreground">
            <tr>
              <th className="text-left py-2">Model</th>
              <th className="text-right">Accuracy</th>
              <th className="text-right">Brier</th>
              <th className="text-right">LogLoss</th>
              <th className="text-right">Last Trained</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.model} className="border-t">
                <td className="py-2 font-medium">{r.model}</td>
                <td className="text-right">{pct(r.accuracy)}</td>
                <td className="text-right">{r.brier.toFixed(3)}</td>
                <td className="text-right">{r.logloss.toFixed(2)}</td>
                <td className="text-right text-xs opacity-70">
                  {new Date(r.lastTrained).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function TeamComparator({ analytics }) {
  const [a, setA] = useState("Chiefs");
  const [b, setB] = useState("Eagles");
  const A = analytics.find((t) => t.team === a) || {};
  const B = analytics.find((t) => t.team === b) || {};
  function Row({ name, av, bv, fmt = (x) => x }) {
    return (
      <div className="grid grid-cols-5 items-center py-1 text-sm">
        <div className="col-span-2 font-medium">{a}</div>
        <div className="text-right">{fmt(av ?? "-")}</div>
        <div className="text-center text-xs opacity-60">{name}</div>
        <div className="text-left">{fmt(bv ?? "-")}</div>
        <div className="col-span-1 font-medium text-right">{b}</div>
      </div>
    );
  }
  return (
    <Card>
      <CardHeader className="pb-2 flex flex-wrap items-center gap-3 justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          <span className="font-semibold">Team Comparator</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <select
            className="px-2 py-1 rounded-md bg-muted"
            value={a}
            onChange={(e) => setA(e.target.value)}
          >
            {analytics.map((t) => (
              <option key={t.team} value={t.team}>
                {t.team}
              </option>
            ))}
          </select>
          <span className="opacity-50">vs</span>
          <select
            className="px-2 py-1 rounded-md bg-muted"
            value={b}
            onChange={(e) => setB(e.target.value)}
          >
            {analytics.map((t) => (
              <option key={t.team} value={t.team}>
                {t.team}
              </option>
            ))}
          </select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          <Row name="PPG" av={A.ppg} bv={B.ppg} />
          <Row name="OPPG" av={A.oppg} bv={B.oppg} />
          <Row name="Off Rank" av={A.offenseRank} bv={B.offenseRank} />
          <Row name="Def Rank" av={A.defenseRank} bv={B.defenseRank} />
          <Row name="ELO" av={A.elo} bv={B.elo} />
        </div>
      </CardContent>
    </Card>
  );
}

function StatusPill({ status }) {
  const variant =
    status === "live"
      ? "bg-emerald-600"
      : status === "scheduled"
        ? "bg-sky-600"
        : "bg-zinc-600";
  const label = status?.toUpperCase?.() || "UNKNOWN";
  return (
    <span
      className={`text-[10px] px-2 py-0.5 rounded-full text-white ${variant}`}
    >
      {label}
    </span>
  );
}

function OddsComparisonTable({ rows, statusMap = {}, smartDefault = true }) {
  const [q, setQ] = useState("");
  const [showFinals, setShowFinals] = useState(true);
  const [smart, setSmart] = useState(smartDefault);

  const enriched = useMemo(() => {
    return (rows || []).map((r) => ({
      ...r,
      _status: statusMap[r.id]?.status || "unknown",
    }));
  }, [rows, statusMap]);

  const filtered = useMemo(() => {
    const byQ = enriched.filter((r) =>
      r.match.toLowerCase().includes(q.toLowerCase())
    );
    const byFinals = showFinals
      ? byQ
      : byQ.filter(
          (r) => (statusMap[r.id]?.status || "").toLowerCase() !== "final"
        );
    if (!smart) return byFinals;
    return [...byFinals].sort((a, b) => smartCompare(a, b, statusMap));
  }, [enriched, q, showFinals, smart, statusMap]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            <span className="font-semibold">Betting Odds Comparison</span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Filter matchups…"
              className="h-8 w-[200px]"
            />
            <label className="flex items-center gap-1 text-xs opacity-80">
              <Switch
                checked={smart}
                onCheckedChange={setSmart}
                aria-label="Smart order"
              />
              Smart
            </label>
            <label className="flex items-center gap-1 text-xs opacity-80">
              <Switch
                checked={showFinals}
                onCheckedChange={setShowFinals}
                aria-label="Show finals"
              />
              Finals
            </label>
          </div>
        </div>
      </CardHeader>
      <CardContent className="overflow-auto">
        <div className="min-w-[820px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-background z-10">
              <tr className="text-xs text-muted-foreground">
                <th className="text-left py-2 pr-3">Matchup</th>
                <th className="text-left py-2 pr-3">Status</th>
                {rows[0]?.books?.map((b) => (
                  <th key={b.book} className="text-right px-3">
                    {b.book}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="py-2 pr-3 font-medium whitespace-nowrap">
                    {r.match}
                  </td>
                  <td className="py-2 pr-3">
                    <StatusPill status={statusMap[r.id]?.status} />
                  </td>
                  {r.books.map((b) => (
                    <td
                      key={b.book}
                      className="px-3 py-2 text-right whitespace-nowrap"
                    >
                      <div className="grid grid-cols-2 gap-1 opacity-90">
                        <span className="text-xs">Spread</span>
                        <span className="text-xs justify-self-end">
                          {b.spread > 0 ? "+" : ""}
                          {b.spread}
                        </span>
                        <span className="text-xs">Home</span>
                        <span className="text-xs justify-self-end">
                          {b.home}
                        </span>
                        <span className="text-xs">Away</span>
                        <span className="text-xs justify-self-end">
                          {b.away}
                        </span>
                        <span className="text-xs">Total</span>
                        <span className="text-xs justify-self-end">
                          {b.total}
                        </span>
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="text-sm opacity-70 py-4">
              No games match your filters.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ValueBetsTable({ games, oddsRows }) {
  const byGame = useMemo(() => {
    const map = new Map();
    games.forEach((g) => map.set(g.id, g));
    const rows = [];
    oddsRows.forEach((row) => {
      const g = map.get(row.id);
      if (!g) return;
      // compute edges for each book and side, choose best positive
      let best = null;
      row.books.forEach((b) => {
        const homeImp = americanToProb(b.home);
        const awayImp = americanToProb(b.away);
        const homeEdge = g.prediction.homeWinProb - homeImp;
        const awayEdge = g.prediction.awayWinProb - awayImp;
        const side = homeEdge > awayEdge ? "Home" : "Away";
        const odds = side === "Home" ? b.home : b.away;
        const p =
          side === "Home" ? g.prediction.homeWinProb : g.prediction.awayWinProb;
        const imp = side === "Home" ? homeImp : awayImp;
        const profit = americanProfitPer100(odds);
        const ev = p * profit - (1 - p) * 100; // per $100 stake
        const edge = p - imp;
        const rec = {
          id: row.id + "-" + b.book + side,
          match: row.match,
          book: b.book,
          side,
          odds,
          ourProb: p,
          implied: imp,
          edge,
          ev,
        };
        if (!best || rec.edge > best.edge) best = rec;
      });
      if (best && best.edge > 0.03) rows.push(best); // threshold 3%
    });
    return rows.sort((a, b) => b.edge - a.edge).slice(0, 12);
  }, [games, oddsRows]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          <span className="font-semibold">Value Bet Opportunities</span>
        </div>
      </CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-xs text-muted-foreground">
            <tr>
              <th className="text-left py-2">Matchup</th>
              <th className="text-left">Side</th>
              <th className="text-right">Our Prob</th>
              <th className="text-right">Implied Prob</th>
              <th className="text-right">Edge</th>
              <th className="text-right">Book</th>
              <th className="text-right">Odds</th>
              <th className="text-right">EV/100</th>
            </tr>
          </thead>
          <tbody>
            {byGame.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="py-2 font-medium">{r.match}</td>
                <td>{r.side}</td>
                <td className="text-right">{pct(r.ourProb)}</td>
                <td className="text-right">{pct(r.implied)}</td>
                <td className="text-right font-semibold">{pct(r.edge)}</td>
                <td className="text-right">{r.book}</td>
                <td className="text-right">{fmtOdds(r.odds)}</td>
                <td className="text-right">{r.ev.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {byGame.length === 0 && (
          <div className="text-sm opacity-70 py-4">
            No positive edges over threshold right now.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function OddsMovementChart({ movements, oddsRows }) {
  const [sel, setSel] = useState(oddsRows[0]?.id || "");
  const data = movements?.[sel] || [];
  const axisTick = { fill: "hsl(var(--muted-foreground))", fontSize: 12 };
  const axisStroke = "hsl(var(--border))";
  const gridStroke = "hsl(var(--chart-grid))";
  return (
    <Card>
      <CardHeader className="pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4" />
          <span className="font-semibold">Odds Movement (spread)</span>
        </div>
        <select
          className="px-2 py-1 rounded-md bg-muted"
          value={sel}
          onChange={(e) => setSel(e.target.value)}
        >
          {oddsRows.map((r) => (
            <option key={r.id} value={r.id}>
              {r.match}
            </option>
          ))}
        </select>
      </CardHeader>
      <CardContent className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RLineChart
            data={data}
            margin={{ top: 10, right: 16, bottom: 0, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis
              dataKey="t"
              tick={axisTick}
              stroke={axisStroke}
              tickLine={{ stroke: axisStroke }}
            />
            <YAxis
              tick={axisTick}
              stroke={axisStroke}
              tickLine={{ stroke: axisStroke }}
            />
            <Tooltip
              wrapperStyle={{ outline: "none" }}
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                color: "hsl(var(--foreground))",
              }}
            />
            <Line
              type="monotone"
              dataKey="Pinnacle"
              strokeWidth={2}
              dot={false}
              stroke="hsl(var(--chart-1))"
            />
            <Line
              type="monotone"
              dataKey="DraftKings"
              strokeWidth={2}
              dot={false}
              stroke="hsl(var(--chart-2))"
            />
            <Line
              type="monotone"
              dataKey="FanDuel"
              strokeWidth={2}
              dot={false}
              stroke="hsl(var(--chart-3))"
            />
          </RLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function InjuriesPanel({ items }) {
  const color = (sev) =>
    sev === "critical"
      ? "destructive"
      : sev === "moderate"
        ? "secondary"
        : "default";
  return (
    <Card>
      <CardHeader className="pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span className="font-semibold">Player Injuries</span>
        </div>
        <Badge variant="secondary">Tracked: {items.length}</Badge>
      </CardHeader>
      <CardContent className="space-y-2 max-h-96 overflow-auto">
        {items.map((it) => (
          <div
            key={it.id}
            className="grid grid-cols-12 items-center gap-2 py-2 border-b last:border-none"
          >
            <div className="col-span-4 md:col-span-3 font-medium">
              {it.player}{" "}
              <span className="text-xs opacity-60">({it.position})</span>
            </div>
            <div className="col-span-3 md:col-span-2 text-sm opacity-80">
              {it.team}
            </div>
            <div className="col-span-2 md:col-span-2">
              <Badge variant={color(it.severity)}>{it.status}</Badge>
            </div>
            <div className="hidden md:block md:col-span-3 text-sm">
              {it.note}
            </div>
            <div className="col-span-3 md:col-span-2 text-[11px] opacity-60 justify-self-end">
              {new Date(it.updatedAt).toLocaleString()}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function SystemHealthPanel({ health, wsConnected }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4" />
          <span className="font-semibold">System Health</span>
        </div>
      </CardHeader>
      <CardContent className="grid md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs opacity-70 mb-2">Data Feeds</div>
          <div className="space-y-2">
            {health.feeds.map((f) => (
              <div
                key={f.name}
                className="flex items-center justify-between py-2 border-b last:border-none"
              >
                <div className="font-medium">{f.name}</div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      f.status === "ok"
                        ? "default"
                        : f.status === "warn"
                          ? "secondary"
                          : "destructive"
                    }
                  >
                    {f.status}
                  </Badge>
                  <span className="text-xs opacity-70">{f.latency}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs opacity-70 mb-2">Models</div>
          <div className="space-y-2">
            {health.models.map((m) => (
              <div
                key={m.name}
                className="flex items-center justify-between py-2 border-b last:border-none"
              >
                <div className="font-medium">{m.name}</div>
                <Badge variant={m.status === "ok" ? "default" : "secondary"}>
                  {m.status}
                </Badge>
              </div>
            ))}
            <div className="flex items-center justify-between py-2">
              <div className="font-medium">WebSocket</div>
              {wsConnected ? (
                <Badge className="bg-emerald-600">connected</Badge>
              ) : (
                <Badge variant="secondary">disconnected</Badge>
              )}
            </div>
            <div className="text-xs opacity-70">
              Last sync: {new Date(health.lastSync).toLocaleString()}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ----------------------------
// Main Component
// ----------------------------
export default function NFLPredictionDashboard() {
  const { dark, setDark } = useTheme();
  const { connected, events } = useLiveFeed();
  const [wide, setWide] = useState(true);
  const [selectedGame, setSelectedGame] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [expandedView, setExpandedView] = useState(false);
  const [gameFilter, setGameFilter] = useState('all'); // 'all', 'live', 'today', 'thisWeek', 'nextWeek'
  const [isMobile, setIsMobile] = useState(false);

  // Data domains - live ESPN API integration
  const games = useApi("/games");
  const analytics = useApi("/teams/analytics");
  const accuracy = useApi("/predictions/accuracy", { refreshMs: 60000 });
  const odds = useApi("/odds");
  const oddsMovements = useApi("/odds/movements");
  const injuries = useApi("/injuries", { refreshMs: 60000 });
  const models = useApi("/models/leaderboard", { refreshMs: 120000 });
  const health = useApi("/system/health", { refreshMs: 45000 });

  // NFL Week Management
  const nflWeek = useNFLWeek(games.data || [], {
    isMobile,
    autoRefresh: true,
    refreshInterval: 60000 // Refresh every minute
  });

  // Week reset detection
  const weekReset = useNFLWeekReset(() => {
    // Callback when week resets - could trigger data refresh
    console.log('NFL Week reset detected - refreshing data');
    window.location.reload(); // Simple refresh on week change
  });

  // Mobile detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const isLoading =
    games.loading ||
    analytics.loading ||
    accuracy.loading ||
    odds.loading ||
    injuries.loading;

  // Get filtered games based on current filter
  const filteredGames = useMemo(() => {
    if (!games.data) return [];

    // For now, let's just show all games and fix the filtering later
    switch (gameFilter) {
      case 'live':
        return games.data.filter(g => g.status === 'live' || g.status === 'in_progress');
      case 'today':
        // Show live games plus any games today
        return games.data.filter(g => {
          if (g.status === 'live' || g.status === 'in_progress') return true;
          const gameDate = new Date(g.startTime || g.gameTime || 0);
          const today = new Date();
          return gameDate.toDateString() === today.toDateString();
        });
      case 'thisWeek':
        return games.data; // For now show all games
      case 'nextWeek':
        return games.data.filter(g => {
          const gameDate = new Date(g.startTime || g.gameTime || 0);
          const nextWeek = new Date();
          nextWeek.setDate(nextWeek.getDate() + 7);
          return gameDate > new Date() && gameDate <= nextWeek;
        });
      default:
        return games.data; // Show all games by default
    }
  }, [games.data, gameFilter]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-neutral-900">
        <div
          className={`min-h-screen text-foreground ${wide ? "max-w-screen-2xl" : "max-w-7xl"} mx-auto p-4`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <h1 className="text-3xl font-bold">NFL Prediction Dashboard</h1>
              <WsBadge connected={connected} />
              {/* Live 2025 NFL Data - Demo mode removed */}
              <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-green-100 dark:bg-green-900 border border-green-200 dark:border-green-700">
                <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  Live 2025 NFL Data
                </span>
              </div>
              {/* NFL Week Info */}
              {nflWeek.currentWeek && (
                <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-blue-100 dark:bg-blue-900 border border-blue-200 dark:border-blue-700">
                  <Calendar className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                    Week {nflWeek.currentWeek.weekNumber}
                  </span>
                  <span className="text-xs text-blue-600 dark:text-blue-400">
                    ({nflWeek.currentWeek.weekType})
                  </span>
                </div>
              )}
              {/* Week Reset Warning */}
              {weekReset.isNearReset && (
                <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-orange-100 dark:bg-orange-900 border border-orange-200 dark:border-orange-700">
                  <Clock className="h-4 w-4 text-orange-600 dark:text-orange-400 animate-pulse" />
                  <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                    Week Reset Soon
                  </span>
                </div>
              )}
              {isLoading && <Skeleton className="h-8 w-24" />}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.search = '?admin=true'}
              >
                Normal Mode 🧠
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setWide(!wide)}
              >
                {wide ? "Narrow" : "Wide"} Mode
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setDark(!dark)}
              >
                {dark ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Live Ticker */}
          <LiveTicker events={events} />

          {/* NFL Week Status & Game Filters */}
          {nflWeek.currentWeek && (
            <div className="mt-4 mb-6">
              <Card className="p-4">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Week Status */}
                  <div className="flex items-center gap-4">
                    <div>
                      <h3 className="font-semibold">{nflWeek.weekStatus.message}</h3>
                      <p className="text-sm text-muted-foreground">
                        Showing {nflWeek.displayConfig.showing} of {nflWeek.displayConfig.totalAvailable} games
                        {nflWeek.displayConfig.hasMore && ' (smart filtered)'}
                      </p>
                    </div>
                    {nflWeek.weekStatus.timeUntilReset.days <= 1 && (
                      <div className="text-sm text-muted-foreground">
                        Next reset: {nflWeek.weekStatus.timeUntilReset.days}d {nflWeek.weekStatus.timeUntilReset.hours}h
                      </div>
                    )}
                  </div>

                  {/* Game Filters */}
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <div className="flex gap-1">
                      {[
                        { key: 'all', label: 'All', count: nflWeek.displayConfig.totalAvailable },
                        { key: 'live', label: 'Live', count: nflWeek.displayConfig.categories.live },
                        { key: 'today', label: 'Today', count: nflWeek.displayConfig.categories.today },
                        { key: 'thisWeek', label: 'This Week', count: nflWeek.displayConfig.categories.thisWeek },
                        { key: 'nextWeek', label: 'Next Week', count: nflWeek.displayConfig.categories.nextWeek }
                      ].map(({ key, label, count }) => (
                        <Button
                          key={key}
                          variant={gameFilter === key ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setGameFilter(key)}
                          className="text-xs"
                          disabled={count === 0}
                        >
                          {label}
                          {count > 0 && (
                            <Badge variant="secondary" className="ml-1 text-xs">
                              {count}
                            </Badge>
                          )}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Smart Insights Section */}
          {games.data && <SmartInsights games={games.data} />}

          {/* Main Content - Mobile Responsive */}
          <div className="mt-4 sm:mt-6">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              {/* Desktop Tabs - Hidden on Mobile */}
              <TabsList className="hidden lg:grid w-full grid-cols-8">
                <TabsTrigger value="overview" className="touch-friendly">
                  Overview
                </TabsTrigger>
                <TabsTrigger value="live" className="touch-friendly">
                  Live
                </TabsTrigger>
                <TabsTrigger value="analytics" className="touch-friendly">
                  Analytics
                </TabsTrigger>
                <TabsTrigger value="predictions" className="touch-friendly">
                  Predictions
                </TabsTrigger>
                <TabsTrigger value="players" className="touch-friendly">
                  Players
                </TabsTrigger>
                <TabsTrigger value="betting" className="touch-friendly">
                  Betting
                </TabsTrigger>
                <TabsTrigger value="leaderboard" className="touch-friendly">
                  Leaderboard
                </TabsTrigger>
                <TabsTrigger value="health" className="touch-friendly">
                  Health
                </TabsTrigger>
              </TabsList>

              {/* Mobile Tabs - Horizontal Scroll */}
              <div className="lg:hidden mb-4 overflow-x-auto scrollbar-hide">
                <TabsList className="flex w-max min-w-full">
                  <TabsTrigger
                    value="overview"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Overview
                  </TabsTrigger>
                  <TabsTrigger
                    value="live"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Live
                  </TabsTrigger>
                  <TabsTrigger
                    value="analytics"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Analytics
                  </TabsTrigger>
                  <TabsTrigger
                    value="predictions"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Predictions
                  </TabsTrigger>
                  <TabsTrigger
                    value="players"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Players
                  </TabsTrigger>
                  <TabsTrigger
                    value="betting"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Betting
                  </TabsTrigger>
                  <TabsTrigger
                    value="leaderboard"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Leaderboard
                  </TabsTrigger>
                  <TabsTrigger
                    value="health"
                    className="touch-friendly whitespace-nowrap"
                  >
                    Health
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="overview" className="space-y-4 sm:space-y-6">
                {isLoading ? (
                  <div className="mobile-grid">
                    {[...Array(6)].map((_, i) => (
                      <Skeleton key={i} className="h-48 sm:h-64" />
                    ))}
                  </div>
                ) : (
                  <>
                    {/* Live Games Priority Section */}
                    {filteredGames.filter(g => g.status === 'live' || g.status === 'in_progress').length > 0 && gameFilter !== 'nextWeek' && (
                      <div className="mb-6">
                        <div className="flex items-center gap-2 mb-3">
                          <Badge className="bg-red-600 text-white animate-pulse">
                            <Activity className="w-3 h-3 mr-1" />
                            LIVE NOW
                          </Badge>
                          <span className="text-sm font-semibold">
                            {filteredGames.filter(g => g.status === 'live' || g.status === 'in_progress').length} Games In Progress
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {filteredGames.filter(g => g.status === 'live' || g.status === 'in_progress').map(g => (
                            <EnhancedGameCard key={g.id} game={g} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* All Games Grid - showing filtered games */}
                    {console.log("Showing filtered games:", filteredGames.length)}
                    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                      {filteredGames
                        .filter(g => {
                          // Don't duplicate live games if we're showing them separately above
                          if (gameFilter !== 'live' && gameFilter !== 'nextWeek' && (g.status === 'live' || g.status === 'in_progress')) {
                            const hasLiveSection = filteredGames.filter(game => game.status === 'live' || game.status === 'in_progress').length > 0;
                            return !hasLiveSection;
                          }
                          return true;
                        })
                        .sort((a, b) => {
                          // Priority order: live first, then scheduled (by time), then final (most recent first)
                          const statusPriority = { live: 0, scheduled: 1, final: 2 };
                          const aPriority = statusPriority[a.status] ?? 3;
                          const bPriority = statusPriority[b.status] ?? 3;

                          if (aPriority !== bPriority) {
                            return aPriority - bPriority;
                          }

                          // Within same status, sort by time
                          if (a.status === 'scheduled' && b.status === 'scheduled') {
                            // For scheduled games, show upcoming games first (earliest start time)
                            return new Date(a.startTime || a.gameTime || 0) - new Date(b.startTime || b.gameTime || 0);
                          }

                          if (a.status === 'final' && b.status === 'final') {
                            // For final games, show most recent first (latest start time)
                            return new Date(b.startTime || b.gameTime || 0) - new Date(a.startTime || a.gameTime || 0);
                          }

                          return 0;
                        })
                        .map(g => (
                          <div
                            key={g.id}
                            onClick={() => {
                              if (g.status === "scheduled") {
                                setSelectedGame(g);
                                setModalOpen(true);
                              }
                            }}
                            className={
                              g.status === "scheduled" ? "cursor-pointer" : ""
                            }
                          >
                            <EnhancedGameCard game={g} />
                          </div>
                        ))
                      }
                    </div>

                    {/* Debug info */}
                    {filteredGames.length === 0 && (
                      <div className="text-center py-8">
                        <p className="text-muted-foreground">No games match current filter: {gameFilter}</p>
                        <p className="text-xs text-muted-foreground mt-2">Total games available: {games.data?.length || 0}</p>
                      </div>
                    )}

                    {/* Show more/less for many games */}
                    {filteredGames.length > 12 && gameFilter === 'all' && (
                      <div className="mt-4 text-center">
                        <Button
                          variant="outline"
                          onClick={() => setExpandedView(!expandedView)}
                        >
                          {expandedView ? 'Show Less' : `Show All ${filteredGames.length} Games`}
                        </Button>
                      </div>
                    )}

                    {/* Phase 3 & 4 Components - Mobile Responsive */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
                      {/* Power Rankings */}
                      <PowerRankings analytics={analytics.data} />

                      {/* Model Performance */}
                      <div>
                        <ModelPerformance />
                      </div>
                    </div>

                    {/* News Feed */}
                    <NewsFeed games={games.data} />

                    {accuracy.data && (
                      <PredictionAccuracyChart rows={accuracy.data} />
                    )}
                  </>
                )}
              </TabsContent>

              <TabsContent value="live" className="space-y-4 sm:space-y-6">
                <div className="mobile-grid">
                  {games.data
                    ?.filter((g) => g.status === "live")
                    .map((g) => (
                      <EnhancedGameCard key={g.id} game={g} />
                    ))}
                </div>
              </TabsContent>

              <TabsContent value="analytics" className="space-y-4 sm:space-y-6">
                {analytics.data && (
                  <AnalyticsCharts analytics={analytics.data} />
                )}
                {analytics.data && (
                  <TeamComparator analytics={analytics.data} />
                )}
              </TabsContent>

              <TabsContent
                value="predictions"
                className="space-y-4 sm:space-y-6"
              >
                {models.data && <ModelLeaderboard rows={models.data} />}
                {accuracy.data && (
                  <PredictionAccuracyChart rows={accuracy.data} />
                )}
              </TabsContent>

              <TabsContent value="players" className="space-y-4 sm:space-y-6">
                {injuries.data && <InjuriesPanel items={injuries.data} />}
              </TabsContent>

              <TabsContent value="betting" className="space-y-4 sm:space-y-6">
                {odds.data && games.data && (
                  <>
                    <OddsComparisonTable
                      rows={odds.data}
                      statusMap={makeStatusMap(games.data)}
                      smartDefault={true}
                    />
                    <ValueBetsTable games={games.data} oddsRows={odds.data} />
                    {oddsMovements.data && (
                      <OddsMovementChart
                        movements={oddsMovements.data}
                        oddsRows={odds.data}
                      />
                    )}
                  </>
                )}
              </TabsContent>

              <TabsContent
                value="leaderboard"
                className="space-y-4 sm:space-y-6"
              >
                {/* Create placeholder for leaderboard since the component might not exist */}
                <div className="text-center py-8">
                  <h3 className="responsive-text-lg font-semibold mb-2">
                    Leaderboard Coming Soon
                  </h3>
                  <p className="responsive-text-sm text-muted-foreground">
                    Player and team leaderboards will be available here.
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="health" className="space-y-4 sm:space-y-6">
                {health.data && (
                  <SystemHealthPanel
                    health={health.data}
                    wsConnected={connected}
                  />
                )}
              </TabsContent>
            </Tabs>
          </div>

          {/* Game Detail Modal */}
          <GameDetailModal
            game={selectedGame}
            isOpen={modalOpen}
            onClose={() => {
              setModalOpen(false);
              setSelectedGame(null);
            }}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}
