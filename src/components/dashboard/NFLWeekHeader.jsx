import React from 'react';
import { Calendar, Clock, Zap, Wifi, WifiOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

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

export default function NFLWeekHeader({
  connected,
  nflWeek,
  weekReset,
  isLoading,
  dataSource
}) {
  return (
    <div className="flex items-center gap-4">
      <h1 className="text-3xl font-bold">NFL Prediction Dashboard</h1>
      <WsBadge connected={connected} />

      {/* Live 2025 NFL Data */}
      <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-green-100 dark:bg-green-900 border border-green-200 dark:border-green-700">
        <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
        <span className="text-sm font-medium text-green-800 dark:text-green-200">
          {dataSource?.source === 'expert-observatory' ? 'Expert Observatory API' : 'Live 2025 NFL Data'}
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
    </div>
  );
}