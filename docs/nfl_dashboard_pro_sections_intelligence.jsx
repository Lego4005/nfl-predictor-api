import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
} from "lucide-react";

// shadcn/ui components
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
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
const LIVE_WS_URL = import.meta?.env?.VITE_NFL_WS_URL || "wss://example.com/nfl-live"; // swap for your provider
const API_BASE = import.meta?.env?.VITE_NFL_API_URL || "https://example.com/api"; // swap for your provider

const TEAMS = [
  "49ers","Bears","Bengals","Bills","Broncos","Browns","Buccaneers","Cardinals","Chargers","Chiefs","Colts","Commanders","Cowboys","Dolphins","Eagles","Falcons","Giants","Jaguars","Jets","Lions","Packers","Panthers","Patriots","Raiders","Rams","Ravens","Saints","Seahawks","Steelers","Texans","Titans","Vikings"
];

function clamp(n, min, max){ return Math.max(min, Math.min(max, n)); }
function pct(n){ return `${(n*100).toFixed(0)}%`; }
function fmtClock(s){ const m = Math.floor(s/60); const ss = String(s%60).padStart(2,"0"); return `${m}:${ss}`; }
function pick(arr){ return arr[Math.floor(Math.random()*arr.length)]; }
function rand(min,max){ return Math.random()*(max-min)+min; }
function id(){ return Math.random().toString(36).slice(2,9); }
function americanToProb(a){ return a<0 ? (-a)/((-a)+100) : 100/(a+100); }
function americanProfitPer100(a){ return a<0 ? 100*100/(-a) : a; }
function fmtOdds(a){ return (a>0?"+":"")+a; }

// Map games to status for smart sorting and badges
function makeStatusMap(games){
  const map = {};
  (games||[]).forEach(g=>{ map[g.id] = { status:g.status, quarter:g.quarter, clock:g.clock, startTime:g.startTime, home:g.homeTeam, away:g.awayTeam }; });
  return map;
}

// Smart comparator: live first (later game higher), then scheduled (sooner first), then finals (most recent first)
const __statusRank = { live:0, scheduled:1, final:2 };
function smartCompare(a, b, statusMap){
  const sa = statusMap[a.id] || {}; const sb = statusMap[b.id] || {};
  const ra = __statusRank[sa.status] ?? 3; const rb = __statusRank[sb.status] ?? 3;
  if(ra !== rb) return ra - rb;
  if(sa.status === 'live' && sb.status === 'live'){
    const elapA = (sa.quarter??1)*(14*60) - (sa.clock??(14*60));
    const elapB = (sb.quarter??1)*(14*60) - (sb.clock??(14*60));
    return elapB - elapA; // later game first
  }
  if(sa.status === 'scheduled' && sb.status === 'scheduled'){
    const ta = new Date(sa.startTime ?? Date.now()+86400000).getTime();
    const tb = new Date(sb.startTime ?? Date.now()+86400000).getTime();
    return ta - tb; // sooner first
  }
  if(sa.status === 'final' && sb.status === 'final'){
    const ta = new Date(sa.startTime ?? 0).getTime();
    const tb = new Date(sb.startTime ?? 0).getTime();
    return tb - ta; // most recent first
  }
  return 0;
}

// ----------------------------
// Dev sanity tests (non-blocking)
// ----------------------------
function __devTests__(){
  try{
    const eps = 1e-6;
    console.assert(Math.abs(americanToProb(-110) - 110/210) < eps, "americanToProb(-110)");
    console.assert(Math.abs(americanToProb(+120) - 100/220) < eps, "americanToProb(+120)");
    const ev = (p, odds) => p*americanProfitPer100(odds) - (1-p)*100;
    console.assert(Math.abs(ev(0.5, 120) - 10) < eps, "EV calc");
    // Component presence test
    console.assert(typeof OddsComparisonTable === 'function', 'OddsComparisonTable should be defined');
  }catch(e){ console.warn("Dev tests encountered an issue", e); }
}
if (typeof window !== 'undefined') { __devTests__(); }

// Additional non-blocking dev tests
function __devTests_more__(){
  try{
    const eps = 1e-6;
    console.assert(Math.abs(americanToProb(-200) - 200/300) < eps, "americanToProb(-200)");
    console.assert(Math.abs(americanToProb(+150) - 100/250) < eps, "americanToProb(+150)");
    console.assert(americanProfitPer100(-200) === 50, "profit/100 for -200");
    console.assert(americanProfitPer100(+150) === 150, "profit/100 for +150");
    const evPos = 0.6*americanProfitPer100(120) - 0.4*100; // p=0.6 vs +120
    console.assert(evPos > 0, "EV positive when our prob > implied for +120");
    // Smart sort tests
    const rows = [{id:'A'},{id:'B'},{id:'C'}];
    const now = Date.now();
    const statusMap = {
      A:{status:'live', quarter:4, clock:30, startTime:new Date(now-2*3600000).toISOString()},
      B:{status:'scheduled', startTime:new Date(now+30*60000).toISOString()},
      C:{status:'final', startTime:new Date(now-60*60000).toISOString()},
    };
    const sorted = [...rows].sort((x,y)=>smartCompare(x,y,statusMap));
    console.assert(sorted.map(r=>r.id).join(',') === 'A,B,C', 'smartCompare ordering A(live),B(sched),C(final)');
  }catch(e){ console.warn("Additional dev tests issue", e); }
}
if (typeof window !== 'undefined') { __devTests_more__(); }

// ----------------------------
// Theme Toggle (tailwind 'dark' on <html>)
// ----------------------------
function useTheme(){
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("theme") === "dark" ||
      (!("theme" in localStorage) && window.matchMedia?.("(prefers-color-scheme: dark)").matches);
  });
  useEffect(()=>{
    const root = document.documentElement;
    if(dark){ root.classList.add("dark"); localStorage.setItem("theme","dark"); }
    else { root.classList.remove("dark"); localStorage.setItem("theme","light"); }
  },[dark]);
  return { dark, setDark };
}

// ----------------------------
// Error Boundary
// ----------------------------
class ErrorBoundary extends React.Component { 
  constructor(props){ super(props); this.state = { hasError:false, error:null }; }
  static getDerivedStateFromError(error){ return { hasError:true, error }; }
  componentDidCatch(error, info){ console.error("Dashboard crashed:", error, info); }
  render(){
    if(this.state.hasError){
      return (
        <div className="min-h-[50vh] grid place-items-center p-8">
          <Card className="max-w-2xl w-full">
            <CardHeader className="flex items-center justify-between">
              <div className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500"/><span className="font-semibold">Something went sideways</span></div>
              <Badge variant="destructive">Error</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm opacity-80">The dashboard hit an error. Try refreshing. If this persists, check your data endpoints.</p>
              <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-48">{String(this.state.error)}</pre>
            </CardContent>
            <CardFooter>
              <Button onClick={()=>window.location.reload()}><RefreshCw className="h-4 w-4 mr-2"/>Reload</Button>
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
function useLiveFeed(){
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const wsRef = useRef(null);
  useEffect(()=>{
    let closed = false; let ws;
    try{
      ws = new WebSocket(LIVE_WS_URL);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (msg) => {
        try{ const data = JSON.parse(msg.data); setEvents(prev=>[data, ...prev].slice(0,100)); }catch(e){}
      };
    }catch(e){ setConnected(false); }
    const t = setTimeout(()=>{
      if(!connected && !closed){
        const iv = setInterval(()=>{ setEvents(p=>[mockKeyPlay(), ...p].slice(0,100)); }, 2500);
        wsRef.current = { close: () => clearInterval(iv) };
      }
    },2000);
    return ()=>{ closed = true; clearTimeout(t); wsRef.current?.close?.(); };
  },[]);
  return { connected, events };
}

// ----------------------------
// API fetch with loading & error
// ----------------------------
function useApi(path, { refreshMs = 30000 } = {}){
  const [data,setData] = useState(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState(null);
  async function load(){
    try{ setLoading(true); setError(null); const r = await fetch(`${API_BASE}${path}`); if(!r.ok) throw new Error(`HTTP ${r.status}`); const json = await r.json(); setData(json); }
    catch(e){ setError(e); setData(mockApi(path)); }
    finally{ setLoading(false); }
  }
  useEffect(()=>{ load(); const iv = setInterval(load, refreshMs); return ()=>clearInterval(iv); },[path]);
  return { data, loading, error, reload: load };
}

// ----------------------------
// Mock Generators (demo-only)
// ----------------------------
function mockKeyPlay(){
  const home = pick(TEAMS), away = pick(TEAMS.filter(t=>t!==home));
  const verbs = ["touchdown","field goal","interception","fumble","sack","big run","deep pass"];
  const play = pick(verbs);
  const q = Math.ceil(rand(1,4));
  const clock = Math.floor(rand(0, 14*60));
  return { id:id(), type:"play", text:`${home} vs ${away}: ${play} in Q${q} (${fmtClock(clock)})`, ts: Date.now() };
}

function mockApi(path){
  if(path.startsWith("/games")){
    return Array.from({length: 12}).map(()=>mockGame());
  }
  if(path.startsWith("/teams/analytics")){
    return TEAMS.map(t=>({ team:t, ppg:+rand(17,34).toFixed(1), oppg:+rand(16,30).toFixed(1), offenseRank:Math.ceil(rand(1,32)), defenseRank:Math.ceil(rand(1,32)), elo: Math.round(rand(1350,1750)), recent: Array.from({length:10}).map(()=> pick(["W","L"])) }));
  }
  if(path.startsWith("/predictions/accuracy")){
    const days = 21; return Array.from({length: days}).map((_,i)=>({ date: new Date(Date.now()-(days-i)*86400000).toISOString().slice(0,10), accuracy:+rand(0.52,0.74).toFixed(3) }));
  }
  if(path.startsWith("/odds/movements")){
    // return a dict keyed by matchup id -> timeseries
    const ids = Array.from({length:8}).map(()=>id());
    const makeSeries = ()=> Array.from({length: 24}).map((_,i)=>({ t: i, Pinnacle: +(rand(-3.5,3.5).toFixed(1)), DraftKings: +(rand(-3.5,3.5).toFixed(1)), FanDuel: +(rand(-3.5,3.5).toFixed(1)) }));
    return ids.reduce((acc, k)=>{ acc[k]=makeSeries(); return acc; },{});
  }
  if(path.startsWith("/odds")){
    const books = ["Pinnacle","DraftKings","FanDuel","Caesars","BetMGM"];
    return Array.from({length: 10}).map(()=>{ const g = mockGame(); return { id: g.id, match: `${g.awayTeam} @ ${g.homeTeam}`, books: books.map(b=>({ book:b, spread:+(rand(-7.5,7.5).toFixed(1)), home:+(rand(-140,+130).toFixed(0)), away:+(rand(-140,+130).toFixed(0)), total:+(rand(38.5,52.5).toFixed(1)) })) }; });
  }
  if(path.startsWith("/injuries")){
    const statuses = ["Questionable","Doubtful","Out","Probable"];
    return Array.from({length: 20}).map(()=>({ id:id(), team:pick(TEAMS), player:`${pick(["J.","M.","C.","L.","T."])} ${pick(["Smith","Allen","Johnson","Brown","Davis","Hill","Jackson"])}`, position: pick(["QB","RB","WR","TE","LB","CB","S","DL"]), status:pick(statuses), severity: pick(["minor","moderate","critical"]), note: pick(["hamstring","ankle","concussion protocol","illness","coach's decision","limited practice"]), updatedAt: new Date(Date.now()-rand(0,36)*3600000).toISOString() }));
  }
  if(path.startsWith("/models/leaderboard")){
    return [
      { model:"Ensemble v3", accuracy:0.69, brier:0.185, logloss:0.58, lastTrained: new Date(Date.now()-86400000).toISOString() },
      { model:"XGB v9", accuracy:0.67, brier:0.192, logloss:0.60, lastTrained: new Date(Date.now()-2*86400000).toISOString() },
      { model:"NN v12", accuracy:0.665, brier:0.19, logloss:0.595, lastTrained: new Date(Date.now()-3*86400000).toISOString() },
      { model:"Logit baseline", accuracy:0.61, brier:0.215, logloss:0.67, lastTrained: new Date(Date.now()-10*86400000).toISOString() }
    ];
  }
  if(path.startsWith("/system/health")){
    return {
      feeds:[
        {name:"Scores API", status: pick(["ok","ok","ok","warn"]) , latency: +(rand(90, 250).toFixed(0))},
        {name:"Injuries API", status: pick(["ok","ok","warn"]) , latency: +(rand(120, 300).toFixed(0))},
        {name:"Sportsbooks", status: pick(["ok","ok","ok","down"]) , latency: +(rand(200, 400).toFixed(0))},
        {name:"Weather", status: pick(["ok","ok","ok","warn"]) , latency: +(rand(100, 220).toFixed(0))},
      ],
      models:[
        {name:"Ensemble v3", status:"ok"},
        {name:"XGB v9", status:"ok"},
        {name:"NN v12", status: pick(["ok","warn"])},
      ],
      lastSync: new Date().toISOString()
    };
  }
  return null;
}

function mockGame(){
  const home = pick(TEAMS), away = pick(TEAMS.filter(t=>t!==home));
  const hs = Math.round(rand(0,35));
  const as = Math.round(rand(0,35));
  const q = Math.ceil(rand(1,4));
  const status = pick(["live","scheduled","final"]);
  const clock = Math.round(rand(0, 14*60));
  const homeProb = clamp(rand(0.35,0.7),0,1);
  return {
    id: id(),
    homeTeam: home,
    awayTeam: away,
    homeScore: status==="scheduled"?0:hs,
    awayScore: status==="scheduled"?0:as,
    status,
    quarter: status==="scheduled"?0:q,
    clock,
    startTime: new Date(Date.now()+rand(-2,6)*3600000).toISOString(),
    prediction: { homeWinProb:+homeProb.toFixed(2), awayWinProb:+(1-homeProb).toFixed(2), line:+(rand(-7,7).toFixed(1)), confidence:+rand(0.55,0.9).toFixed(2) }
  };
}

// ----------------------------
// UI Bits
// ----------------------------
function WsBadge({ connected }){ return connected ? (<Badge className="bg-emerald-600 hover:bg-emerald-600"><Wifi className="h-3.5 w-3.5 mr-1"/>Live</Badge>) : (<Badge variant="secondary" className="bg-muted text-muted-foreground"><WifiOff className="h-3.5 w-3.5 mr-1"/>Simulated</Badge>); }

function MiniStat({ icon:Icon, label, value, hint }){
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50 border border-border">
      <div className="p-2 rounded-lg bg-background shadow-sm"><Icon className="h-5 w-5"/></div>
      <div>
        <div className="text-xs opacity-70">{label}</div>
        <div className="font-semibold leading-tight">{value}</div>
        {hint && <div className="text-[11px] opacity-60">{hint}</div>}
      </div>
    </div>
  );
}

function LiveTicker({ events }){
  return (
    <div className="relative overflow-hidden rounded-2xl border bg-background">
      <div className="p-2 flex items-center gap-2 text-xs">
        <Badge className="bg-indigo-600">Live Ticker</Badge>
        <span className="opacity-70">Key plays & updates</span>
      </div>
      <Separator />
      <div className="h-10 flex items-center">
        <div className="whitespace-nowrap animate-[ticker_25s_linear_infinite] will-change-transform">
          {events.slice(0, 30).map((e) => (<span key={e.id} className="mx-6 text-sm opacity-90">{e.text}</span>))}
        </div>
      </div>
      <style>{`@keyframes ticker { from { transform: translateX(0); } to { transform: translateX(-50%); } } @media (prefers-reduced-motion: reduce) { .animate-[ticker_25s_linear_infinite]{ animation: none !important; } }`}</style>
    </div>
  );
}

function GameCard({ g }){
  const leadHome = g.homeScore - g.awayScore >= 0;
  const progress = g.status === "scheduled" ? 0 : g.status === "final" ? 1 : clamp((g.quarter-1)/4 + (1 - g.clock/(14*60))/16, 0, 1);
  const bar = Math.round(progress*100);
  return (
    <motion.div layout initial={{opacity:0, y:4}} animate={{opacity:1,y:0}}>
      <Card className="overflow-hidden hover:shadow-lg transition-shadow h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2"><Users className="h-4 w-4"/><span className="font-semibold">{g.awayTeam} @ {g.homeTeam}</span></div>
            <Badge variant={g.status==="live"?"default":"secondary"}>{g.status.toUpperCase()}</Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold tracking-tight">{g.awayScore}<span className="text-base opacity-50">–</span>{g.homeScore}</div>
            <div className="text-xs opacity-70">
              {g.status === "live" && (<div>Q{g.quarter} · {fmtClock(g.clock)}</div>)}
              {g.status === "scheduled" && (<div>Starts {new Date(g.startTime).toLocaleTimeString([], {hour:"numeric", minute:"2-digit"})}</div>)}
              {g.status === "final" && <div>Final</div>}
            </div>
          </div>
          <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden"><div className="h-full bg-primary" style={{ width: `${bar}%`}} /></div>
          <div className="grid grid-cols-2 gap-3">
            <MiniStat icon={TrendingUp} label="Home Win Prob" value={pct(g.prediction.homeWinProb)} hint={`Conf: ${pct(g.prediction.confidence)}`}/>
            <MiniStat icon={LineChart} label="Line" value={`${g.prediction.line > 0 ? "+" : ""}${g.prediction.line}`} hint={`Away Win Prob ${pct(g.prediction.awayWinProb)}`}/>
          </div>
        </CardContent>
        <CardFooter className="flex items-center justify-between text-xs opacity-70">
          <div className="flex items-center gap-2"><Shield className="h-3.5 w-3.5"/> {leadHome? g.homeTeam : g.awayTeam} leading</div>
          <div className="flex items-center gap-2"><PlayCircle className="h-3.5 w-3.5"/> {g.status === "live" ? "In-Game" : g.status === "final" ? "Completed" : "Awaiting Kickoff"}</div>
        </CardFooter>
      </Card>
    </motion.div>
  );
}

function AnalyticsCharts({ analytics }){
  const top = useMemo(()=>[...analytics].sort((a,b)=>b.elo-a.elo).slice(0,8),[analytics]);
  const offense = useMemo(()=>[...analytics].sort((a,b)=>a.offenseRank-b.offenseRank).slice(0,8),[analytics]);
  const axisTick = { fill: 'hsl(var(--muted-foreground))', fontSize: 12 };
  const axisStroke = 'hsl(var(--border))';
  const gridStroke = 'hsl(var(--chart-grid))';
  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="col-span-2">
        <CardHeader className="pb-2"><div className="flex items-center gap-2"><Activity className="h-4 w-4"/><span className="font-semibold">Team ELO (Top 8)</span></div></CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RBarChart data={top} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="team" tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
              <YAxis tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
              <Tooltip wrapperStyle={{ outline: 'none' }} contentStyle={{ background: 'hsl(var(--popover))', border: '1px solid hsl(var(--border))', color: 'hsl(var(--foreground))' }} />
              <Bar dataKey="elo" radius={[8,8,0,0]} fill="hsl(var(--chart-1))" stroke="hsl(var(--chart-1))" />
            </RBarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2"><div className="flex items-center gap-2"><Gauge className="h-4 w-4"/><span className="font-semibold">PPG vs OPPG</span></div></CardHeader>
        <CardContent className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RAreaChart data={offense} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="ppg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopOpacity={0.8} stopColor="hsl(var(--chart-2))"/><stop offset="95%" stopOpacity={0.1} stopColor="hsl(var(--chart-2))"/></linearGradient>
                <linearGradient id="oppg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopOpacity={0.7} stopColor="hsl(var(--chart-3))"/><stop offset="95%" stopOpacity={0.05} stopColor="hsl(var(--chart-3))"/></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="team" tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
              <YAxis tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
              <Tooltip wrapperStyle={{ outline: 'none' }} contentStyle={{ background: 'hsl(var(--popover))', border: '1px solid hsl(var(--border))', color: 'hsl(var(--foreground))' }} />
              <Area type="monotone" dataKey="ppg" stroke="hsl(var(--chart-2))" fillOpacity={1} fill="url(#ppg)" strokeWidth={2} />
              <Area type="monotone" dataKey="oppg" stroke="hsl(var(--chart-3))" fillOpacity={1} fill="url(#oppg)" strokeWidth={2} />
              <Legend wrapperStyle={{ color: 'hsl(var(--muted-foreground))' }} />
            </RAreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

function PredictionAccuracyChart({ rows }){
  const axisTick = { fill: 'hsl(var(--muted-foreground))', fontSize: 12 };
  const axisStroke = 'hsl(var(--border))';
  const gridStroke = 'hsl(var(--chart-grid))';
  return (
    <Card>
      <CardHeader className="pb-2"><div className="flex items-center gap-2"><LineChart className="h-4 w-4"/><span className="font-semibold">Prediction Accuracy (last {rows.length} days)</span></div></CardHeader>
      <CardContent className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RLineChart data={rows} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis dataKey="date" tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
            <YAxis domain={[0.4, 1]} tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
            <Tooltip formatter={(v)=>`${pct(v)}`} wrapperStyle={{ outline: 'none' }} contentStyle={{ background: 'hsl(var(--popover))', border: '1px solid hsl(var(--border))', color: 'hsl(var(--foreground))' }} />
            <Line type="monotone" dataKey="accuracy" strokeWidth={2} dot={false} stroke="hsl(var(--chart-1))" />
          </RLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function ModelLeaderboard({ rows }){
  return (
    <Card>
      <CardHeader className="pb-2"><div className="flex items-center gap-2"><TrendingUp className="h-4 w-4"/><span className="font-semibold">Model Leaderboard</span></div></CardHeader>
      <CardContent className="overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-xs text-muted-foreground">
            <tr><th className="text-left py-2">Model</th><th className="text-right">Accuracy</th><th className="text-right">Brier</th><th className="text-right">LogLoss</th><th className="text-right">Last Trained</th></tr>
          </thead>
          <tbody>
            {rows.map((r)=> (
              <tr key={r.model} className="border-t">
                <td className="py-2 font-medium">{r.model}</td>
                <td className="text-right">{pct(r.accuracy)}</td>
                <td className="text-right">{r.brier.toFixed(3)}</td>
                <td className="text-right">{r.logloss.toFixed(2)}</td>
                <td className="text-right text-xs opacity-70">{new Date(r.lastTrained).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function TeamComparator({ analytics }){
  const [a, setA] = useState("Chiefs");
  const [b, setB] = useState("Eagles");
  const A = analytics.find(t=>t.team===a) || {}; const B = analytics.find(t=>t.team===b) || {};
  function Row({name, av, bv, fmt=(x)=>x}){ return (<div className="grid grid-cols-5 items-center py-1 text-sm"><div className="col-span-2 font-medium">{a}</div><div className="text-right">{fmt(av??"-")}</div><div className="text-center text-xs opacity-60">{name}</div><div className="text-left">{fmt(bv??"-")}</div><div className="col-span-1 font-medium text-right">{b}</div></div>); }
  return (
    <Card>
      <CardHeader className="pb-2 flex flex-wrap items-center gap-3 justify-between">
        <div className="flex items-center gap-2"><Users className="h-4 w-4"/><span className="font-semibold">Team Comparator</span></div>
        <div className="flex items-center gap-2 text-sm">
          <select className="px-2 py-1 rounded-md bg-muted" value={a} onChange={e=>setA(e.target.value)}>{analytics.map(t=> <option key={t.team} value={t.team}>{t.team}</option>)}</select>
          <span className="opacity-50">vs</span>
          <select className="px-2 py-1 rounded-md bg-muted" value={b} onChange={e=>setB(e.target.value)}>{analytics.map(t=> <option key={t.team} value={t.team}>{t.team}</option>)}</select>
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

function StatusPill({ status }){
  const variant = status==='live' ? 'bg-emerald-600' : status==='scheduled' ? 'bg-sky-600' : 'bg-zinc-600';
  const label = status?.toUpperCase?.() || 'UNKNOWN';
  return <span className={`text-[10px] px-2 py-0.5 rounded-full text-white ${variant}`}>{label}</span>
}

function OddsComparisonTable({ rows, statusMap = {}, smartDefault = true }){
  const [q, setQ] = useState("");
  const [showFinals, setShowFinals] = useState(true);
  const [smart, setSmart] = useState(smartDefault);

  const enriched = useMemo(()=>{
    return (rows||[]).map(r=>({ ...r, _status: statusMap[r.id]?.status || 'unknown'}));
  },[rows, statusMap]);

  const filtered = useMemo(()=>{
    const byQ = enriched.filter(r => r.match.toLowerCase().includes(q.toLowerCase()));
    const byFinals = showFinals ? byQ : byQ.filter(r => (statusMap[r.id]?.status || '').toLowerCase() !== 'final');
    if(!smart) return byFinals;
    return [...byFinals].sort((a,b)=>smartCompare(a,b,statusMap));
  },[enriched, q, showFinals, smart, statusMap]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2"><TrendingUp className="h-4 w-4"/><span className="font-semibold">Betting Odds Comparison</span></div>
          <div className="flex items-center gap-2">
            <Input value={q} onChange={e=>setQ(e.target.value)} placeholder="Filter matchups…" className="h-8 w-[200px]"/>
            <label className="flex items-center gap-1 text-xs opacity-80">
              <Switch checked={smart} onCheckedChange={setSmart} aria-label="Smart order"/>
              Smart
            </label>
            <label className="flex items-center gap-1 text-xs opacity-80">
              <Switch checked={showFinals} onCheckedChange={setShowFinals} aria-label="Show finals"/>
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
                {rows[0]?.books?.map(b=> (
                  <th key={b.book} className="text-right px-3">{b.book}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(r=> (
                <tr key={r.id} className="border-t">
                  <td className="py-2 pr-3 font-medium whitespace-nowrap">{r.match}</td>
                  <td className="py-2 pr-3"><StatusPill status={statusMap[r.id]?.status}/></td>
                  {r.books.map(b=> (
                    <td key={b.book} className="px-3 py-2 text-right whitespace-nowrap">
                      <div className="grid grid-cols-2 gap-1 opacity-90">
                        <span className="text-xs">Spread</span><span className="text-xs justify-self-end">{b.spread > 0 ? "+" : ""}{b.spread}</span>
                        <span className="text-xs">Home</span><span className="text-xs justify-self-end">{b.home}</span>
                        <span className="text-xs">Away</span><span className="text-xs justify-self-end">{b.away}</span>
                        <span className="text-xs">Total</span><span className="text-xs justify-self-end">{b.total}</span>
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length===0 && <div className="text-sm opacity-70 py-4">No games match your filters.</div>}
        </div>
      </CardContent>
    </Card>
  );
}

function ValueBetsTable({ games, oddsRows }){
  const byGame = useMemo(()=>{
    const map = new Map();
    games.forEach(g=> map.set(g.id, g));
    const rows = [];
    oddsRows.forEach(row=>{
      const g = map.get(row.id); if(!g) return;
      // compute edges for each book and side, choose best positive
      let best = null;
      row.books.forEach(b=>{
        const homeImp = americanToProb(b.home); const awayImp = americanToProb(b.away);
        const homeEdge = (g.prediction.homeWinProb - homeImp);
        const awayEdge = (g.prediction.awayWinProb - awayImp);
        const side = homeEdge>awayEdge ? "Home" : "Away";
        const odds = side==="Home"? b.home : b.away;
        const p = side==="Home"? g.prediction.homeWinProb : g.prediction.awayWinProb;
        const imp = side==="Home"? homeImp : awayImp;
        const profit = americanProfitPer100(odds);
        const ev = p*profit - (1-p)*100; // per $100 stake
        const edge = (p-imp);
        const rec = { id: row.id+"-"+b.book+side, match: row.match, book:b.book, side, odds, ourProb:p, implied:imp, edge, ev };
        if(!best || rec.edge>best.edge) best = rec;
      });
      if(best && best.edge>0.03) rows.push(best); // threshold 3%
    });
    return rows.sort((a,b)=>b.edge-a.edge).slice(0,12);
  },[games, oddsRows]);

  return (
    <Card>
      <CardHeader className="pb-2"><div className="flex items-center gap-2"><TrendingUp className="h-4 w-4"/><span className="font-semibold">Value Bet Opportunities</span></div></CardHeader>
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
            {byGame.map(r=> (
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
        {byGame.length===0 && <div className="text-sm opacity-70 py-4">No positive edges over threshold right now.</div>}
      </CardContent>
    </Card>
  );
}

function OddsMovementChart({ movements, oddsRows }){
  const [sel, setSel] = useState(oddsRows[0]?.id || "");
  const data = movements?.[sel] || [];
  const axisTick = { fill: 'hsl(var(--muted-foreground))', fontSize: 12 };
  const axisStroke = 'hsl(var(--border))';
  const gridStroke = 'hsl(var(--chart-grid))';
  return (
    <Card>
      <CardHeader className="pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2"><Gauge className="h-4 w-4"/><span className="font-semibold">Odds Movement (spread)</span></div>
        <select className="px-2 py-1 rounded-md bg-muted" value={sel} onChange={e=>setSel(e.target.value)}>
          {oddsRows.map(r=> <option key={r.id} value={r.id}>{r.match}</option>)}
        </select>
      </CardHeader>
      <CardContent className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RLineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis dataKey="t" tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
            <YAxis tick={axisTick} stroke={axisStroke} tickLine={{ stroke: axisStroke }} />
            <Tooltip wrapperStyle={{ outline: 'none' }} contentStyle={{ background: 'hsl(var(--popover))', border: '1px solid hsl(var(--border))', color: 'hsl(var(--foreground))' }} />
            <Line type="monotone" dataKey="Pinnacle" strokeWidth={2} dot={false} stroke="hsl(var(--chart-1))" />
            <Line type="monotone" dataKey="DraftKings" strokeWidth={2} dot={false} stroke="hsl(var(--chart-2))" />
            <Line type="monotone" dataKey="FanDuel" strokeWidth={2} dot={false} stroke="hsl(var(--chart-3))" />
          </RLineChart>
        </CardContent>
      </CardContent>
    </Card>
  );
}

function InjuriesPanel({ items }){
  const color = (sev)=> sev==="critical"? "destructive" : sev==="moderate"? "secondary" : "default";
  return (
    <Card>
      <CardHeader className="pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4"/><span className="font-semibold">Player Injuries</span></div>
        <Badge variant="secondary">Tracked: {items.length}</Badge>
      </CardHeader>
      <CardContent className="space-y-2 max-h-96 overflow-auto">
        {items.map(it => (
          <div key={it.id} className="grid grid-cols-12 items-center gap-2 py-2 border-b last:border-none">
            <div className="col-span-4 md:col-span-3 font-medium">{it.player} <span className="text-xs opacity-60">({it.position})</span></div>
            <div className="col-span-3 md:col-span-2 text-sm opacity-80">{it.team}</div>
            <div className="col-span-2 md:col-span-2"><Badge variant={color(it.severity)}>{it.status}</Badge></div>
            <div className="hidden md:block md:col-span-3 text-sm">{it.note}</div>
            <div className="col-span-3 md:col-span-2 text-[11px] opacity-60 justify-self-end">{new Date(it.updatedAt).toLocaleString()}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function SystemHealthPanel({ health, wsConnected }){
  return (
    <Card>
      <CardHeader className="pb-2"><div className="flex items-center gap-2"><Activity className="h-4 w-4"/><span className="font-semibold">System Health</span></div></CardHeader>
      <CardContent className="grid md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs opacity-70 mb-2">Data Feeds</div>
          <div className="space-y-2">
            {health.feeds.map(f => (
              <div key={f.name} className="flex items-center justify-between py-2 border-b last:border-none">
                <div className="font-medium">{f.name}</div>
                <div className="flex items-center gap-2">
                  <Badge variant={f.status==="ok"?"default":(f.status==="warn"?"secondary":"destructive")}>{f.status}</Badge>
                  <span className="text-xs opacity-70">{f.latency}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs opacity-70 mb-2">Models</div>
          <div className="space-y-2">
            {health.models.map(m => (
              <div key={m.name} className="flex items-center justify-between py-2 border-b last:border-none">
                <div className="font-medium">{m.name}</div>
                <Badge variant={m.status==="ok"?"default":"secondary"}>{m.status}</Badge>
              </div>
            ))}
            <div className="flex items-center justify-between py-2">
              <div className="font-medium">WebSocket</div>
              {wsConnected ? <Badge className="bg-emerald-600">connected</Badge> : <Badge variant="secondary">disconnected</Badge>}
            </div>
            <div className="text-xs opacity-70">Last sync: {new Date(health.lastSync).toLocaleString()}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ----------------------------
// Main Component
// ----------------------------
export default function NFLPredictionDashboard(){
  const { dark, setDark } = useTheme();
  const { connected, events } = useLiveFeed();
  const [wide, setWide] = useState(true);

  // Data domains
  const games = useApi("/games");
  const analytics = useApi("/teams/analytics");
  const accuracy = useApi("/predictions/accuracy", { refreshMs: 60000 });
  const odds = useApi("/odds");
  const oddsMovements = useApi("/odds/movements");
  const injuries = useApi("/injuries", { refreshMs: 60000 });
  const models = useApi("/models/leaderboard", { refreshMs: 120000 });
  const health = useApi("/system/health", { refreshMs: 45000 });

  const isLoading = games.loading || analytics.loading || accuracy.loading || odds.loading || injuries.loading;

  return (
    <ErrorBoundary>
      {/* Neutral dark gray theme */}
      <style>{`
        :root{ --background:0 0% 100%; --foreground:222.2 84% 4.9%; --card:0 0% 100%; --card-foreground:222.2 84% 4.9%; --popover:0 0% 100%; --popover-foreground:222.2 84% 4.9%; --primary:222.2 47.4% 11.2%; --primary-foreground:210 40% 98%; --secondary:210 40% 96.1%; --secondary-foreground:222.2 47.4% 11.2%; --muted:210 40% 96.1%; --muted-foreground:215.4 16.3% 46.9%; --accent:210 40% 96.1%; --accent-foregr