import React from "react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

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

export default LiveTicker;