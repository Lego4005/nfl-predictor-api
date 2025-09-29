export interface NFLWeekInfo {
  weekNumber: number;
  weekType: "preseason" | "regular" | "playoff";
  weekStart: Date;
  weekEnd: Date;
  isCurrentWeek: boolean;
  daysIntoWeek: number;
  seasonProgress: number;
}

export interface WeekBoundaries {
  weekNumber: number;
  weekStart: Date;
  weekEnd: Date;
  isCurrentWeek: boolean;
  weekType: "preseason" | "regular" | "playoff";
}

export interface PriorityGames {
  live: any[];
  today: any[];
  tomorrow: any[];
  thisWeek: any[];
  nextWeek: any[];
}

export declare function getCurrentNFLWeek(currentDate?: Date): NFLWeekInfo;
export declare function getWeekBoundaries(weekNumber: number): WeekBoundaries;
export declare function isGameInCurrentWeek(gameDate: Date | string): boolean;
export declare function getGamesForWeek(
  games: any[],
  weekNumber?: number | null
): any[];
export declare function getPriorityGames(games: any[]): PriorityGames;
export declare function getNextWeekReset(fromDate?: Date): Date;
