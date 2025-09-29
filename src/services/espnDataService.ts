/**
 * ESPN NFL Data Service
 * Fetches accurate NFL game data from ESPN's unofficial but reliable API endpoints
 * Includes game outcomes, winners, dates, times, and TV networks
 */

interface ESPNGame {
  id: string;
  date: string;
  name: string;
  shortName: string;
  season: {
    year: number;
    type: number;
  };
  week: {
    number: number;
  };
  status: {
    type: {
      name: string;
      state: string;
      completed: boolean;
    };
    displayClock: string;
  };
  competitions: Array<{
    id: string;
    date: string;
    attendance: number;
    type: {
      id: string;
      abbreviation: string;
    };
    timeValid: boolean;
    neutralSite: boolean;
    playByPlayAvailable: boolean;
    recent: boolean;
    venue: {
      id: string;
      fullName: string;
      address: {
        city: string;
        state: string;
      };
      indoor: boolean;
    };
    competitors: Array<{
      id: string;
      uid: string;
      type: string;
      order: number;
      homeAway: string;
      winner: boolean;
      team: {
        id: string;
        uid: string;
        location: string;
        name: string;
        abbreviation: string;
        displayName: string;
        shortDisplayName: string;
        color: string;
        alternateColor: string;
        isActive: boolean;
        logo: string;
      };
      score: string;
      linescores: Array<{
        value: number;
      }>;
      statistics: any[];
      records: Array<{
        name: string;
        abbreviation: string;
        type: string;
        summary: string;
      }>;
    }>;
    notes: any[];
    broadcasts: Array<{
      market: string;
      names: string[];
    }>;
    leaders: any[];
    format: {
      regulation: {
        periods: number;
      };
    };
    startDate: string;
    geoBroadcasts: Array<{
      type: {
        id: string;
        shortName: string;
      };
      market: {
        id: string;
        type: string;
      };
      media: {
        shortName: string;
      };
    }>;
  }>;
  links: Array<{
    language: string;
    rel: string[];
    href: string;
    text: string;
    shortText: string;
    isExternal: boolean;
    isPremium: boolean;
  }>;
  weather: {
    displayValue: string;
    temperature: number;
    highTemperature: number;
    conditionId: string;
    link: {
      language: string;
      rel: string[];
      href: string;
      text: string;
      shortText: string;
      isExternal: boolean;
      isPremium: boolean;
    };
  };
}

interface ESPNScoreboardResponse {
  leagues: Array<{
    id: string;
    uid: string;
    name: string;
    abbreviation: string;
    slug: string;
    season: {
      year: number;
      startDate: string;
      endDate: string;
      displayName: string;
      type: {
        id: string;
        type: number;
        name: string;
        abbreviation: string;
      };
    };
    logos: Array<{
      href: string;
      width: number;
      height: number;
      alt: string;
      rel: string[];
      lastUpdated: string;
    }>;
    calendarType: string;
    calendarIsWhitelist: boolean;
    calendarStartDate: string;
    calendarEndDate: string;
    calendar: string[];
  }>;
  season: {
    type: number;
    year: number;
  };
  week: {
    number: number;
  };
  events: ESPNGame[];
}

interface ProcessedGame {
  id: string;
  espn_game_id: string;
  season: number;
  week: number;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  status: string;
  game_time: string;
  venue: string;
  venue_city: string;
  venue_state: string;
  network: string;
  winner: string | null;
  temperature: number | null;
  weather_condition: string | null;
  attendance: number | null;
}

export class ESPNDataService {
  private baseUrl =
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl";

  /**
   * Fetch NFL scoreboard data for a specific date range
   */
  async fetchScoreboardData(
    startDate: string,
    endDate: string
  ): Promise<ESPNScoreboardResponse> {
    const url = `${this.baseUrl}/scoreboard?limit=1000&dates=${startDate}-${endDate}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(
          `ESPN API request failed: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error fetching ESPN scoreboard data:", error);
      throw error;
    }
  }

  /**
   * Fetch NFL schedule data for a specific season and week
   */
  async fetchWeekSchedule(
    year: number,
    week: number
  ): Promise<ESPNScoreboardResponse> {
    const url = `${this.baseUrl}/scoreboard?seasontype=2&week=${week}&year=${year}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(
          `ESPN API request failed: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error fetching ESPN week schedule:", error);
      throw error;
    }
  }

  /**
   * Process ESPN game data into our database format
   */
  processGameData(espnGame: ESPNGame): ProcessedGame {
    const competition = espnGame.competitions[0];
    const homeTeam = competition.competitors.find(
      (team) => team.homeAway === "home"
    );
    const awayTeam = competition.competitors.find(
      (team) => team.homeAway === "away"
    );

    // Determine winner
    let winner: string | null = null;
    if (espnGame.status.type.completed) {
      const winningTeam = competition.competitors.find((team) => team.winner);
      winner = winningTeam ? winningTeam.team.abbreviation : null;
    }

    // Extract TV network from broadcasts
    let network = "TBD";
    if (competition.broadcasts && competition.broadcasts.length > 0) {
      network = competition.broadcasts[0].names[0] || "TBD";
    }

    // Map ESPN status to our format
    let status = "scheduled";
    if (espnGame.status.type.completed) {
      status = "final";
    } else if (espnGame.status.type.state === "in") {
      status = "live";
    }

    return {
      id: espnGame.id,
      espn_game_id: espnGame.id,
      season: espnGame.season.year,
      week: espnGame.week.number,
      home_team: homeTeam?.team.abbreviation || "TBD",
      away_team: awayTeam?.team.abbreviation || "TBD",
      home_score: homeTeam?.score ? parseInt(homeTeam.score) : null,
      away_score: awayTeam?.score ? parseInt(awayTeam.score) : null,
      status,
      game_time: competition.date,
      venue: competition.venue.fullName,
      venue_city: competition.venue.address.city,
      venue_state: competition.venue.address.state,
      network,
      winner,
      temperature: espnGame.weather?.temperature || null,
      weather_condition: espnGame.weather?.displayValue || null,
      attendance: competition.attendance || null,
    };
  }

  /**
   * Fetch and process games for a specific week
   */
  async getWeekGames(year: number, week: number): Promise<ProcessedGame[]> {
    try {
      const scoreboardData = await this.fetchWeekSchedule(year, week);
      const processedGames = scoreboardData.events.map((game) =>
        this.processGameData(game)
      );

      console.log(
        `✅ Fetched ${processedGames.length} games for ${year} Week ${week} from ESPN`
      );
      return processedGames;
    } catch (error) {
      console.error(`Error fetching week ${week} games:`, error);
      throw error;
    }
  }

  /**
   * Fetch games for a date range
   */
  async getGamesForDateRange(
    startDate: string,
    endDate: string
  ): Promise<ProcessedGame[]> {
    try {
      const scoreboardData = await this.fetchScoreboardData(startDate, endDate);
      const processedGames = scoreboardData.events.map((game) =>
        this.processGameData(game)
      );

      console.log(
        `✅ Fetched ${processedGames.length} games for ${startDate} to ${endDate} from ESPN`
      );
      return processedGames;
    } catch (error) {
      console.error(
        `Error fetching games for date range ${startDate}-${endDate}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Get current NFL week games with real data
   */
  async getCurrentWeekGames(): Promise<ProcessedGame[]> {
    const currentYear = 2025;
    const currentWeek = 4; // Can be made dynamic based on current date

    return this.getWeekGames(currentYear, currentWeek);
  }
}

export const espnDataService = new ESPNDataService();
