/**
 * 2025 NFL Season Schedule Framework
 * Complete 18-week regular season + playoff structure
 */

export interface NFLTeam {
  id: string;
  name: string;
  city: string;
  abbreviation: string;
  conference: 'AFC' | 'NFC';
  division: 'North' | 'South' | 'East' | 'West';
  logo?: string;
  primaryColor: string;
  secondaryColor: string;
  stadium: string;
  timezone: string;
}

export interface NFLGame {
  id: string;
  week: number;
  season: number;
  gameType: 'regular' | 'wildcard' | 'divisional' | 'conference' | 'superbowl';
  homeTeam: string; // Team ID
  awayTeam: string; // Team ID
  gameDate: string; // ISO date string
  gameTime: string; // Time in ET
  network: string;
  venue: string;
  isNeutralSite: boolean;
  isPrimetime: boolean;
  isInternational: boolean;
  gameStatus: 'scheduled' | 'live' | 'final' | 'postponed' | 'cancelled';
  homeScore?: number;
  awayScore?: number;
  quarter?: number;
  timeRemaining?: string;
  lastUpdated: string;
}

export interface WeekSchedule {
  weekNumber: number;
  weekType: 'regular' | 'wildcard' | 'divisional' | 'conference' | 'superbowl';
  startDate: string;
  endDate: string;
  games: NFLGame[];
  primetimeGames: NFLGame[];
  internationalGames: NFLGame[];
  byeTeams: string[]; // Team IDs on bye
}

export interface SeasonSchedule {
  season: number;
  weeks: WeekSchedule[];
  regularSeasonWeeks: number;
  playoffWeeks: number;
  totalGames: number;
  superbowlDate: string;
}

// 2025 NFL Teams
export const NFL_TEAMS_2025: NFLTeam[] = [
  // AFC East
  {
    id: 'buf',
    name: 'Bills',
    city: 'Buffalo',
    abbreviation: 'BUF',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#00338D',
    secondaryColor: '#C60C30',
    stadium: 'Highmark Stadium',
    timezone: 'ET'
  },
  {
    id: 'mia',
    name: 'Dolphins',
    city: 'Miami',
    abbreviation: 'MIA',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#008E97',
    secondaryColor: '#FC4C02',
    stadium: 'Hard Rock Stadium',
    timezone: 'ET'
  },
  {
    id: 'ne',
    name: 'Patriots',
    city: 'New England',
    abbreviation: 'NE',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#002244',
    secondaryColor: '#C60C30',
    stadium: 'Gillette Stadium',
    timezone: 'ET'
  },
  {
    id: 'nyj',
    name: 'Jets',
    city: 'New York',
    abbreviation: 'NYJ',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#125740',
    secondaryColor: '#000000',
    stadium: 'MetLife Stadium',
    timezone: 'ET'
  },

  // AFC North
  {
    id: 'bal',
    name: 'Ravens',
    city: 'Baltimore',
    abbreviation: 'BAL',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#241773',
    secondaryColor: '#000000',
    stadium: 'M&T Bank Stadium',
    timezone: 'ET'
  },
  {
    id: 'cin',
    name: 'Bengals',
    city: 'Cincinnati',
    abbreviation: 'CIN',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#FB4F14',
    secondaryColor: '#000000',
    stadium: 'Paycor Stadium',
    timezone: 'ET'
  },
  {
    id: 'cle',
    name: 'Browns',
    city: 'Cleveland',
    abbreviation: 'CLE',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#311D00',
    secondaryColor: '#FF3C00',
    stadium: 'Cleveland Browns Stadium',
    timezone: 'ET'
  },
  {
    id: 'pit',
    name: 'Steelers',
    city: 'Pittsburgh',
    abbreviation: 'PIT',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#FFB612',
    secondaryColor: '#000000',
    stadium: 'Acrisure Stadium',
    timezone: 'ET'
  },

  // AFC South
  {
    id: 'hou',
    name: 'Texans',
    city: 'Houston',
    abbreviation: 'HOU',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#03202F',
    secondaryColor: '#A71930',
    stadium: 'NRG Stadium',
    timezone: 'CT'
  },
  {
    id: 'ind',
    name: 'Colts',
    city: 'Indianapolis',
    abbreviation: 'IND',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#002C5F',
    secondaryColor: '#A2AAAD',
    stadium: 'Lucas Oil Stadium',
    timezone: 'ET'
  },
  {
    id: 'jax',
    name: 'Jaguars',
    city: 'Jacksonville',
    abbreviation: 'JAX',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#006778',
    secondaryColor: '#9F792C',
    stadium: 'TIAA Bank Field',
    timezone: 'ET'
  },
  {
    id: 'ten',
    name: 'Titans',
    city: 'Tennessee',
    abbreviation: 'TEN',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#0C2340',
    secondaryColor: '#4B92DB',
    stadium: 'Nissan Stadium',
    timezone: 'CT'
  },

  // AFC West
  {
    id: 'den',
    name: 'Broncos',
    city: 'Denver',
    abbreviation: 'DEN',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#FB4F14',
    secondaryColor: '#002244',
    stadium: 'Empower Field at Mile High',
    timezone: 'MT'
  },
  {
    id: 'kc',
    name: 'Chiefs',
    city: 'Kansas City',
    abbreviation: 'KC',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#E31837',
    secondaryColor: '#FFB81C',
    stadium: 'GEHA Field at Arrowhead Stadium',
    timezone: 'CT'
  },
  {
    id: 'lv',
    name: 'Raiders',
    city: 'Las Vegas',
    abbreviation: 'LV',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#000000',
    secondaryColor: '#A5ACAF',
    stadium: 'Allegiant Stadium',
    timezone: 'PT'
  },
  {
    id: 'lac',
    name: 'Chargers',
    city: 'Los Angeles',
    abbreviation: 'LAC',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#0080C6',
    secondaryColor: '#FFC20E',
    stadium: 'SoFi Stadium',
    timezone: 'PT'
  },

  // NFC East
  {
    id: 'dal',
    name: 'Cowboys',
    city: 'Dallas',
    abbreviation: 'DAL',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#003594',
    secondaryColor: '#041E42',
    stadium: 'AT&T Stadium',
    timezone: 'CT'
  },
  {
    id: 'nyg',
    name: 'Giants',
    city: 'New York',
    abbreviation: 'NYG',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#0B2265',
    secondaryColor: '#A71930',
    stadium: 'MetLife Stadium',
    timezone: 'ET'
  },
  {
    id: 'phi',
    name: 'Eagles',
    city: 'Philadelphia',
    abbreviation: 'PHI',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#004C54',
    secondaryColor: '#A5ACAF',
    stadium: 'Lincoln Financial Field',
    timezone: 'ET'
  },
  {
    id: 'was',
    name: 'Commanders',
    city: 'Washington',
    abbreviation: 'WAS',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#5A1414',
    secondaryColor: '#FFB612',
    stadium: 'FedExField',
    timezone: 'ET'
  },

  // NFC North
  {
    id: 'chi',
    name: 'Bears',
    city: 'Chicago',
    abbreviation: 'CHI',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#0B162A',
    secondaryColor: '#C83803',
    stadium: 'Soldier Field',
    timezone: 'CT'
  },
  {
    id: 'det',
    name: 'Lions',
    city: 'Detroit',
    abbreviation: 'DET',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#0076B6',
    secondaryColor: '#B0B7BC',
    stadium: 'Ford Field',
    timezone: 'ET'
  },
  {
    id: 'gb',
    name: 'Packers',
    city: 'Green Bay',
    abbreviation: 'GB',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#203731',
    secondaryColor: '#FFB612',
    stadium: 'Lambeau Field',
    timezone: 'CT'
  },
  {
    id: 'min',
    name: 'Vikings',
    city: 'Minnesota',
    abbreviation: 'MIN',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#4F2683',
    secondaryColor: '#FFC62F',
    stadium: 'U.S. Bank Stadium',
    timezone: 'CT'
  },

  // NFC South
  {
    id: 'atl',
    name: 'Falcons',
    city: 'Atlanta',
    abbreviation: 'ATL',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#A71930',
    secondaryColor: '#000000',
    stadium: 'Mercedes-Benz Stadium',
    timezone: 'ET'
  },
  {
    id: 'car',
    name: 'Panthers',
    city: 'Carolina',
    abbreviation: 'CAR',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#0085CA',
    secondaryColor: '#101820',
    stadium: 'Bank of America Stadium',
    timezone: 'ET'
  },
  {
    id: 'no',
    name: 'Saints',
    city: 'New Orleans',
    abbreviation: 'NO',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#D3BC8D',
    secondaryColor: '#101820',
    stadium: 'Caesars Superdome',
    timezone: 'CT'
  },
  {
    id: 'tb',
    name: 'Buccaneers',
    city: 'Tampa Bay',
    abbreviation: 'TB',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#D50A0A',
    secondaryColor: '#FF7900',
    stadium: 'Raymond James Stadium',
    timezone: 'ET'
  },

  // NFC West
  {
    id: 'ari',
    name: 'Cardinals',
    city: 'Arizona',
    abbreviation: 'ARI',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#97233F',
    secondaryColor: '#000000',
    stadium: 'State Farm Stadium',
    timezone: 'MT'
  },
  {
    id: 'lar',
    name: 'Rams',
    city: 'Los Angeles',
    abbreviation: 'LAR',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#003594',
    secondaryColor: '#FFA300',
    stadium: 'SoFi Stadium',
    timezone: 'PT'
  },
  {
    id: 'sf',
    name: '49ers',
    city: 'San Francisco',
    abbreviation: 'SF',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#AA0000',
    secondaryColor: '#B3995D',
    stadium: 'Levi\\'s Stadium',
    timezone: 'PT'
  },
  {
    id: 'sea',
    name: 'Seahawks',
    city: 'Seattle',
    abbreviation: 'SEA',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#002244',
    secondaryColor: '#69BE28',
    stadium: 'Lumen Field',
    timezone: 'PT'
  }
];

// Helper functions
export const getTeamById = (id: string): NFLTeam | undefined => {
  return NFL_TEAMS_2025.find(team => team.id === id);
};

export const getTeamsByDivision = (conference: 'AFC' | 'NFC', division: string): NFLTeam[] => {
  return NFL_TEAMS_2025.filter(team => 
    team.conference === conference && team.division === division
  );
};

export const getTeamsByConference = (conference: 'AFC' | 'NFC'): NFLTeam[] => {
  return NFL_TEAMS_2025.filter(team => team.conference === conference);
};

// Mock 2025 Schedule (Week 3 example)
export const MOCK_2025_SCHEDULE: WeekSchedule[] = [
  {
    weekNumber: 3,
    weekType: 'regular',
    startDate: '2025-09-18',
    endDate: '2025-09-23',
    byeTeams: [],
    games: [
      {
        id: 'week3-kc-buf',
        week: 3,
        season: 2025,
        gameType: 'regular',
        homeTeam: 'kc',
        awayTeam: 'buf',
        gameDate: '2025-09-21',
        gameTime: '13:00',
        network: 'CBS',
        venue: 'GEHA Field at Arrowhead Stadium',
        isNeutralSite: false,
        isPrimetime: false,
        isInternational: false,
        gameStatus: 'scheduled',
        lastUpdated: new Date().toISOString()
      },
      {
        id: 'week3-sf-dal',
        week: 3,
        season: 2025,
        gameType: 'regular',
        homeTeam: 'dal',
        awayTeam: 'sf',
        gameDate: '2025-09-21',
        gameTime: '20:30',
        network: 'NBC',
        venue: 'AT&T Stadium',
        isNeutralSite: false,
        isPrimetime: true,
        isInternational: false,
        gameStatus: 'scheduled',
        lastUpdated: new Date().toISOString()
      },
      {
        id: 'week3-phi-nyg',
        week: 3,
        season: 2025,
        gameType: 'regular',
        homeTeam: 'phi',
        awayTeam: 'nyg',
        gameDate: '2025-09-22',
        gameTime: '20:15',
        network: 'ESPN',
        venue: 'Lincoln Financial Field',
        isNeutralSite: false,
        isPrimetime: true,
        isInternational: false,
        gameStatus: 'scheduled',
        lastUpdated: new Date().toISOString()
      }
    ],
    primetimeGames: [],
    internationalGames: []
  }
];

// Initialize primetime and international games
MOCK_2025_SCHEDULE[0].primetimeGames = MOCK_2025_SCHEDULE[0].games.filter(game => game.isPrimetime);
MOCK_2025_SCHEDULE[0].internationalGames = MOCK_2025_SCHEDULE[0].games.filter(game => game.isInternational);

// Complete season structure
export const NFL_2025_SEASON: SeasonSchedule = {
  season: 2025,
  weeks: MOCK_2025_SCHEDULE, // In real app, this would include all 18 weeks + playoffs
  regularSeasonWeeks: 18,
  playoffWeeks: 4,
  totalGames: 272, // 17 games * 16 teams = 272 regular season games
  superbowlDate: '2026-02-09'
};

// Schedule utility functions
export const getCurrentWeek = (): number => {
  // Mock implementation - in real app, calculate based on current date
  return 3;
};

export const getWeekSchedule = (week: number): WeekSchedule | undefined => {
  return NFL_2025_SEASON.weeks.find(w => w.weekNumber === week);
};

export const getGameById = (gameId: string): NFLGame | undefined => {
  for (const week of NFL_2025_SEASON.weeks) {
    const game = week.games.find(g => g.id === gameId);
    if (game) return game;
  }
  return undefined;
};

export const getTeamSchedule = (teamId: string, week?: number): NFLGame[] => {
  const games: NFLGame[] = [];
  
  for (const weekSchedule of NFL_2025_SEASON.weeks) {
    if (week && weekSchedule.weekNumber !== week) continue;
    
    for (const game of weekSchedule.games) {
      if (game.homeTeam === teamId || game.awayTeam === teamId) {
        games.push(game);
      }
    }
  }
  
  return games;
};

export const getPrimetimeGames = (week?: number): NFLGame[] => {
  const games: NFLGame[] = [];
  
  for (const weekSchedule of NFL_2025_SEASON.weeks) {
    if (week && weekSchedule.weekNumber !== week) continue;
    games.push(...weekSchedule.primetimeGames);
  }
  
  return games;
};

export const getInternationalGames = (week?: number): NFLGame[] => {
  const games: NFLGame[] = [];
  
  for (const weekSchedule of NFL_2025_SEASON.weeks) {
    if (week && weekSchedule.weekNumber !== week) continue;
    games.push(...weekSchedule.internationalGames);
  }
  
  return games;
};

export const getByeTeams = (week: number): NFLTeam[] => {
  const weekSchedule = getWeekSchedule(week);
  if (!weekSchedule) return [];
  
  return weekSchedule.byeTeams.map(teamId => getTeamById(teamId)).filter(Boolean) as NFLTeam[];
};

export const isTeamOnBye = (teamId: string, week: number): boolean => {
  const weekSchedule = getWeekSchedule(week);
  return weekSchedule?.byeTeams.includes(teamId) || false;
};

export const formatGameTime = (gameTime: string, timezone: string = 'ET'): string => {
  // Convert time to specified timezone
  // This is a simplified implementation
  const hour = parseInt(gameTime.split(':')[0]);
  const minute = gameTime.split(':')[1];
  
  if (hour >= 12) {
    return `${hour === 12 ? 12 : hour - 12}:${minute} PM ${timezone}`;
  } else {
    return `${hour === 0 ? 12 : hour}:${minute} AM ${timezone}`;
  }
};

export const getGameStatus = (game: NFLGame): { 
  status: string; 
  color: string; 
  showScore: boolean 
} => {
  switch (game.gameStatus) {
    case 'scheduled':
      return { status: 'Scheduled', color: 'gray', showScore: false };
    case 'live':
      return { status: 'Live', color: 'red', showScore: true };
    case 'final':
      return { status: 'Final', color: 'green', showScore: true };
    case 'postponed':
      return { status: 'Postponed', color: 'yellow', showScore: false };
    case 'cancelled':
      return { status: 'Cancelled', color: 'red', showScore: false };
    default:
      return { status: 'Unknown', color: 'gray', showScore: false };
  }
};