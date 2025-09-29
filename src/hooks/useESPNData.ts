import { useQuery } from "@tanstack/react-query";
import { espnDataService } from "../services/espnDataService";

/**
 * Hook to fetch real NFL games from ESPN API
 */
export const useESPNGames = (year: number, week: number) => {
  return useQuery({
    queryKey: ["espn-games", year, week],
    queryFn: () => espnDataService.getWeekGames(year, week),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds for live games
  });
};

/**
 * Hook to fetch current week games from ESPN
 */
export const useCurrentWeekESPNGames = () => {
  return useQuery({
    queryKey: ["espn-current-week-games"],
    queryFn: () => espnDataService.getCurrentWeekGames(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
};

/**
 * Hook to fetch games for a date range from ESPN
 */
export const useESPNGamesDateRange = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: ["espn-games-date-range", startDate, endDate],
    queryFn: () => espnDataService.getGamesForDateRange(startDate, endDate),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!startDate && !!endDate,
  });
};
