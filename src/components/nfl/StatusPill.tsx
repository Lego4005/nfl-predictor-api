import React from "react";
import { classNames } from "@/lib/nfl-utils";
import type { Game } from "@/lib/nfl-data";

interface StatusPillProps {
  status: Game['status'];
}

export const StatusPill: React.FC<StatusPillProps> = ({ status }) => {
  const statusStyles = {
    FINAL: 'status-final',
    LIVE: 'status-live',
    SCHEDULED: 'status-scheduled'
  };

  return (
    <span className={classNames(
      'px-2 py-0.5 text-xs rounded border',
      statusStyles[status]
    )}>
      {status}
    </span>
  );
};