import React from "react";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff } from "lucide-react";

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

export default WsBadge;