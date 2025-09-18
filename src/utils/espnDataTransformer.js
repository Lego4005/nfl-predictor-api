// Transform ESPN API data to include all the rich information for enhanced cards
export const transformESPNGame = (event, espnData) => {
  const competition = event.competitions[0];
  const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
  const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

  // Get status
  const statusType = competition.status?.type?.name;
  let status = 'scheduled';
  if (statusType === 'STATUS_IN_PROGRESS') status = 'live';
  else if (statusType === 'STATUS_FINAL') status = 'final';

  // Base game data
  const gameData = {
    id: event.id,
    espn_game_id: event.id,
    homeTeam: homeTeam.team.abbreviation,
    awayTeam: awayTeam.team.abbreviation,
    homeScore: parseInt(homeTeam.score) || 0,
    awayScore: parseInt(awayTeam.score) || 0,
    status: status,
    gameTime: event.date,
    week: espnData.week?.number || event.week?.number,
    season: espnData.season?.year || 2025,
    venue: competition.venue?.fullName || null,

    // Status details
    quarter: competition.status?.period || 0,
    clock: competition.status?.displayClock || '0:00',
    statusDetail: competition.status?.type?.shortDetail || '',

    // Team records
    homeRecord: homeTeam.records?.[0]?.summary || null,
    awayRecord: awayTeam.records?.[0]?.summary || null,
  };

  // Add situation data for live games
  if (competition.situation) {
    gameData.situation = {
      downDistanceText: competition.situation.downDistanceText,
      possession: competition.situation.possession,
      yardLine: competition.situation.yardLine,
      isRedZone: competition.situation.isRedZone || false,
      lastPlay: competition.situation.lastPlay?.text || null,
    };
  }

  // Add odds/betting data
  if (competition.odds && competition.odds.length > 0) {
    const odds = competition.odds[0];
    gameData.odds = {
      spread: odds.details || odds.spread,
      total: odds.overUnder,
      homeML: odds.homeTeamOdds?.moneyLine,
      awayML: odds.awayTeamOdds?.moneyLine,
      provider: odds.provider?.name || 'Consensus',
    };
  }

  // Add weather data
  if (event.weather) {
    gameData.weather = {
      temp: event.weather.temperature,
      conditions: event.weather.displayValue,
      wind: event.weather.windSpeed || 0,
    };
  }

  // Add broadcast info
  if (competition.broadcasts && competition.broadcasts.length > 0) {
    gameData.broadcast = competition.broadcasts[0].names.join(', ');
  }

  // Add game leaders for live/completed games
  if (competition.leaders && status !== 'scheduled') {
    gameData.leaders = competition.leaders.slice(0, 2).map(leader => ({
      category: leader.shortDisplayName,
      player: leader.leaders[0].athlete.displayName,
      stats: leader.leaders[0].displayValue,
    }));
  }

  // Add top performers for completed games
  if (status === 'final' && competition.leaders) {
    gameData.topPerformers = competition.leaders.slice(0, 3).map(leader => ({
      position: leader.shortDisplayName,
      name: leader.leaders[0].athlete.displayName,
      stats: leader.leaders[0].displayValue,
      team: leader.leaders[0].team.abbreviation,
    }));
  }

  // Add attendance for live/completed games
  if (competition.attendance) {
    gameData.attendance = competition.attendance;
  }

  // Add cover result for completed games
  if (status === 'final' && gameData.odds) {
    const spread = parseFloat(gameData.odds.spread);
    const actualDiff = gameData.homeScore - gameData.awayScore;
    gameData.coverResult = actualDiff > spread ? 'covered' : 'failed';
  }

  return gameData;
};