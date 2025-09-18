/**
 * ESPN API Service - Live NFL Data Integration
 * Fetches current 2025 NFL games, scores, and real-time data
 */

const ESPN_API_BASE = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl';

class ESPNApiService {
  /**
   * Fetch current NFL scoreboard with live games
   */
  async getCurrentGames() {
    try {
      const response = await fetch(`${ESPN_API_BASE}/scoreboard`);

      if (!response.ok) {
        throw new Error(`ESPN API error: ${response.status}`);
      }

      const data = await response.json();

      // Transform ESPN data to our format
      const games = data.events?.map(event => {
        const competition = event.competitions[0];
        const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
        const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

        return {
          id: event.id,
          espn_game_id: event.id,
          home_team: homeTeam.team.abbreviation,
          away_team: awayTeam.team.abbreviation,
          home_score: parseInt(homeTeam.score) || 0,
          away_score: parseInt(awayTeam.score) || 0,
          game_time: event.date,
          week: event.week?.number || null,
          season: event.season?.year || 2025,
          venue: competition.venue?.fullName || null,
          status: this.mapESPNStatus(competition.status),
          status_detail: competition.status.type.shortDetail,
          broadcast: event.broadcast || null,
          weather: competition.weather ? {
            temperature: competition.weather.temperature,
            condition: competition.weather.displayValue
          } : null,
          // Live game specific data
          is_live: competition.status.type.state === 'in',
          current_period: competition.status.period,
          clock: competition.status.displayClock,
          last_play: competition.situation?.lastPlay?.text || null,
          leaders: this.extractLeaders(event.competitions[0].leaders || [])
        };
      }) || [];

      return {
        success: true,
        games,
        season_info: {
          year: data.season?.year || 2025,
          week: data.week?.number || null,
          season_type: data.season?.type || 2
        }
      };

    } catch (error) {
      console.error('ESPN API error:', error);
      return {
        success: false,
        error: error.message,
        games: []
      };
    }
  }

  /**
   * Fetch specific game details with more comprehensive data
   */
  async getGameDetails(gameId) {
    try {
      const response = await fetch(`${ESPN_API_BASE}/summary?event=${gameId}`);

      if (!response.ok) {
        throw new Error(`ESPN Game API error: ${response.status}`);
      }

      const data = await response.json();

      return {
        success: true,
        game: this.transformGameDetail(data)
      };

    } catch (error) {
      console.error('ESPN Game Detail error:', error);
      return {
        success: false,
        error: error.message,
        game: null
      };
    }
  }

  /**
   * Fetch NFL standings
   */
  async getStandings() {
    try {
      const response = await fetch(`${ESPN_API_BASE}/standings`);

      if (!response.ok) {
        throw new Error(`ESPN Standings API error: ${response.status}`);
      }

      const data = await response.json();

      return {
        success: true,
        standings: this.transformStandings(data)
      };

    } catch (error) {
      console.error('ESPN Standings error:', error);
      return {
        success: false,
        error: error.message,
        standings: []
      };
    }
  }

  /**
   * Get team schedule
   */
  async getTeamSchedule(teamAbbr) {
    try {
      const response = await fetch(`${ESPN_API_BASE}/teams/${teamAbbr}/schedule`);

      if (!response.ok) {
        throw new Error(`ESPN Team Schedule API error: ${response.status}`);
      }

      const data = await response.json();

      return {
        success: true,
        schedule: this.transformSchedule(data)
      };

    } catch (error) {
      console.error('ESPN Team Schedule error:', error);
      return {
        success: false,
        error: error.message,
        schedule: []
      };
    }
  }

  /**
   * Map ESPN status to our format
   */
  mapESPNStatus(status) {
    const statusType = status.type.name;

    switch (statusType) {
      case 'STATUS_SCHEDULED':
        return 'scheduled';
      case 'STATUS_IN_PROGRESS':
        return 'live';
      case 'STATUS_FINAL':
        return 'final';
      case 'STATUS_POSTPONED':
        return 'postponed';
      case 'STATUS_CANCELED':
        return 'canceled';
      default:
        return 'unknown';
    }
  }

  /**
   * Extract game leaders (passing, rushing, receiving)
   */
  extractLeaders(leaders) {
    const result = {};

    leaders.forEach(leader => {
      const category = leader.name;
      const topLeader = leader.leaders?.[0];

      if (topLeader) {
        result[category] = {
          player: {
            name: topLeader.athlete.displayName,
            team: topLeader.team.abbreviation
          },
          stats: topLeader.displayValue,
          value: topLeader.value
        };
      }
    });

    return result;
  }

  /**
   * Transform detailed game data
   */
  transformGameDetail(data) {
    // More detailed transformation for individual game data
    const header = data.header;
    const competition = header.competitions[0];

    return {
      id: header.id,
      home_team: competition.competitors.find(c => c.homeAway === 'home'),
      away_team: competition.competitors.find(c => c.homeAway === 'away'),
      status: competition.status,
      plays: data.drives?.recent || [],
      box_score: data.boxscore,
      game_info: data.gameInfo,
      odds: data.predictor
    };
  }

  /**
   * Transform standings data
   */
  transformStandings(data) {
    return data.standings?.map(conference => ({
      conference: conference.name,
      divisions: conference.entries?.map(division => ({
        division: division.name,
        teams: division.stats?.map(team => ({
          team: team.name,
          abbreviation: team.abbreviation,
          wins: team.stats.find(s => s.name === 'wins')?.value || 0,
          losses: team.stats.find(s => s.name === 'losses')?.value || 0,
          ties: team.stats.find(s => s.name === 'ties')?.value || 0
        }))
      }))
    })) || [];
  }

  /**
   * Transform schedule data
   */
  transformSchedule(data) {
    return data.events?.map(event => ({
      id: event.id,
      date: event.date,
      opponent: event.competitions[0].competitors.find(c =>
        c.team.abbreviation !== data.team.abbreviation
      ),
      home_away: event.competitions[0].competitors.find(c =>
        c.team.abbreviation === data.team.abbreviation
      )?.homeAway,
      result: event.competitions[0].status.type.completed ? {
        score: event.competitions[0].competitors.map(c => ({
          team: c.team.abbreviation,
          score: c.score
        })),
        outcome: event.competitions[0].competitors.find(c =>
          c.team.abbreviation === data.team.abbreviation
        )?.winner ? 'W' : 'L'
      } : null
    })) || [];
  }

  /**
   * Get live game updates (for real-time polling)
   */
  async getLiveUpdates() {
    const result = await this.getCurrentGames();

    if (result.success) {
      // Filter only live games
      const liveGames = result.games.filter(game => game.is_live);

      return {
        success: true,
        live_games: liveGames,
        count: liveGames.length,
        last_updated: new Date().toISOString()
      };
    }

    return result;
  }

  /**
   * Get upcoming games (next 7 days)
   */
  async getUpcomingGames() {
    // ESPN API includes upcoming games in scoreboard
    const result = await this.getCurrentGames();

    if (result.success) {
      const now = new Date();
      const weekFromNow = new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000));

      const upcomingGames = result.games.filter(game => {
        const gameTime = new Date(game.game_time);
        return gameTime > now && gameTime <= weekFromNow && game.status === 'scheduled';
      });

      return {
        success: true,
        upcoming_games: upcomingGames,
        count: upcomingGames.length
      };
    }

    return result;
  }

  /**
   * Get full season schedule (for discovering new games)
   */
  async getSeasonSchedule() {
    try {
      // ESPN provides current week by default, but we can also get specific weeks
      const currentWeek = new Date().getMonth() >= 8 ? Math.ceil((new Date() - new Date(2025, 8, 1)) / (1000 * 60 * 60 * 24 * 7)) : 1;

      // Get current and next few weeks to catch schedule updates
      const weeks = [currentWeek, currentWeek + 1, currentWeek + 2].filter(w => w <= 18);
      const allGames = [];

      for (const week of weeks) {
        try {
          const response = await fetch(`${ESPN_API_BASE}/scoreboard?week=${week}&seasontype=2`);

          if (response.ok) {
            const data = await response.json();
            const weekGames = data.events?.map(event => {
              const competition = event.competitions[0];
              const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
              const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

              return {
                id: event.id,
                espn_game_id: event.id,
                home_team: homeTeam.team.abbreviation,
                away_team: awayTeam.team.abbreviation,
                home_score: parseInt(homeTeam.score) || 0,
                away_score: parseInt(awayTeam.score) || 0,
                game_time: event.date,
                week: event.week?.number || week,
                season: event.season?.year || 2025,
                venue: competition.venue?.fullName || null,
                status: this.mapESPNStatus(competition.status),
                status_detail: competition.status.type.shortDetail,
                is_live: competition.status.type.state === 'in',
                current_period: competition.status.period,
                clock: competition.status.displayClock
              };
            }) || [];

            allGames.push(...weekGames);
          }
        } catch (weekError) {
          console.warn(`Week ${week} schedule fetch failed:`, weekError.message);
        }
      }

      return {
        success: true,
        games: allGames,
        totalGames: allGames.length
      };

    } catch (error) {
      console.error('Season schedule fetch failed:', error);
      return {
        success: false,
        error: error.message,
        games: []
      };
    }
  }
}

// Create singleton instance
const espnApiService = new ESPNApiService();

export default espnApiService;