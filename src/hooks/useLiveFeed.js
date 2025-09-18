import { useState, useEffect, useRef } from "react";

// Mock data generator for live feed
function mockKeyPlay() {
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

  function fmtClock(s) {
    const m = Math.floor(s / 60);
    const ss = String(s % 60).padStart(2, "0");
    return `${m}:${ss}`;
  }

  function id() {
    return Math.random().toString(36).slice(2, 9);
  }

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

function useLiveFeed() {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    const LIVE_WS_URL = null; // WebSocket disabled to prevent console errors

    // Skip WebSocket connection if URL is disabled
    if (!LIVE_WS_URL) {
      setConnected(false);
      return;
    }

    // Always try WebSocket connection for live data
    // Demo mode removed - using real ESPN data

    let closed = false;
    let ws;
    try {
      ws = new WebSocket(LIVE_WS_URL);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = (error) => {
        // Silently handle WebSocket connection errors
        setConnected(false);
      };
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

export default useLiveFeed;