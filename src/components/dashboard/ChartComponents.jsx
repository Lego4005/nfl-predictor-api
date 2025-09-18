import React, { useState } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { LineChart, TrendingUp, Users } from "lucide-react";
import {
  LineChart as RLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

// Utility function
function pct(n) {
  return `${(n * 100).toFixed(0)}%`;
}

export function MiniStat({ icon: Icon, label, value, hint }) {
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

export function PredictionAccuracyChart({ rows }) {
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

export function ModelLeaderboard({ rows }) {
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

export function TeamComparator({ analytics }) {
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