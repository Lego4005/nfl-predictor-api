import React from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Activity } from "lucide-react";

export function InjuriesPanel({ items }) {
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

export function SystemHealthPanel({ health, wsConnected }) {
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
            {health?.feeds?.map((f) => (
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
            )) || <div className="text-xs text-gray-500">No feeds available</div>}
          </div>
        </div>
        <div>
          <div className="text-xs opacity-70 mb-2">Models</div>
          <div className="space-y-2">
            {health?.models?.map((m) => (
              <div
                key={m.name}
                className="flex items-center justify-between py-2 border-b last:border-none"
              >
                <div className="font-medium">{m.name}</div>
                <Badge variant={m.status === "ok" ? "default" : "secondary"}>
                  {m.status}
                </Badge>
              </div>
            )) || <div className="text-xs text-gray-500">No models available</div>}
            <div className="flex items-center justify-between py-2">
              <div className="font-medium">WebSocket</div>
              {wsConnected ? (
                <Badge className="bg-emerald-600">connected</Badge>
              ) : (
                <Badge variant="secondary">disconnected</Badge>
              )}
            </div>
            <div className="text-xs opacity-70">
              Last sync: {health?.lastSync ? new Date(health.lastSync).toLocaleString() : 'Never'}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}