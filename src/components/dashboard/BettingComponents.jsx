import React, { useState, useMemo } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { TrendingUp, Gauge } from "lucide-react";
import {
  LineChart as RLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

// Utility functions
function pct(n) {
  return `${(n * 100).toFixed(0)}%`;
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

// Smart comparator function needed for sorting
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

export function OddsComparisonTable({ rows, statusMap = {}, smartDefault = true }) {
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

export function ValueBetsTable({ games, oddsRows }) {
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

export function OddsMovementChart({ movements, oddsRows }) {
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