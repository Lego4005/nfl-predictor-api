import React, { useMemo } from "react";
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
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Activity, Gauge } from "lucide-react";

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

export default AnalyticsCharts;