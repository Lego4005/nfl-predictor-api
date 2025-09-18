// NFL Team Data with Colors and Logo URLs
// Using local logos with ESPN CDN fallback

export const NFL_TEAMS = {
  // AFC East
  BUF: {
    name: 'Bills',
    city: 'Buffalo',
    abbreviation: 'BUF',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#00338D',
    secondaryColor: '#C60C30',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/buf.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #00338D 0%, #C60C30 100%)'
  },
  MIA: {
    name: 'Dolphins',
    city: 'Miami',
    abbreviation: 'MIA',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#008E97',
    secondaryColor: '#FC4C02',
    tertiaryColor: '#005778',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/mia.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #008E97 0%, #FC4C02 100%)'
  },
  NE: {
    name: 'Patriots',
    city: 'New England',
    abbreviation: 'NE',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#002244',
    secondaryColor: '#C60C30',
    tertiaryColor: '#B0B7BC',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ne.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #002244 0%, #C60C30 100%)'
  },
  NYJ: {
    name: 'Jets',
    city: 'New York',
    abbreviation: 'NYJ',
    conference: 'AFC',
    division: 'East',
    primaryColor: '#125740',
    secondaryColor: '#000000',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/nyj.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #125740 0%, #000000 100%)'
  },

  // AFC North
  BAL: {
    name: 'Ravens',
    city: 'Baltimore',
    abbreviation: 'BAL',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#241773',
    secondaryColor: '#000000',
    tertiaryColor: '#9E7C0C',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/bal.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #241773 0%, #9E7C0C 100%)'
  },
  CIN: {
    name: 'Bengals',
    city: 'Cincinnati',
    abbreviation: 'CIN',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#FB4F14',
    secondaryColor: '#000000',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/cin.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #FB4F14 0%, #000000 100%)'
  },
  CLE: {
    name: 'Browns',
    city: 'Cleveland',
    abbreviation: 'CLE',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#311D00',
    secondaryColor: '#FF3C00',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/cle.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #311D00 0%, #FF3C00 100%)'
  },
  PIT: {
    name: 'Steelers',
    city: 'Pittsburgh',
    abbreviation: 'PIT',
    conference: 'AFC',
    division: 'North',
    primaryColor: '#FFB612',
    secondaryColor: '#101820',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/pit.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #FFB612 0%, #101820 100%)'
  },

  // AFC South
  HOU: {
    name: 'Texans',
    city: 'Houston',
    abbreviation: 'HOU',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#03202F',
    secondaryColor: '#A71930',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/hou.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #03202F 0%, #A71930 100%)'
  },
  IND: {
    name: 'Colts',
    city: 'Indianapolis',
    abbreviation: 'IND',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#002C5F',
    secondaryColor: '#A2AAAD',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ind.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #002C5F 0%, #A2AAAD 100%)'
  },
  JAX: {
    name: 'Jaguars',
    city: 'Jacksonville',
    abbreviation: 'JAX',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#101820',
    secondaryColor: '#D7A22A',
    tertiaryColor: '#006778',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/jax.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #006778 0%, #D7A22A 100%)'
  },
  TEN: {
    name: 'Titans',
    city: 'Tennessee',
    abbreviation: 'TEN',
    conference: 'AFC',
    division: 'South',
    primaryColor: '#0C2340',
    secondaryColor: '#4B92DB',
    tertiaryColor: '#C8102E',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ten.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #0C2340 0%, #4B92DB 100%)'
  },

  // AFC West
  DEN: {
    name: 'Broncos',
    city: 'Denver',
    abbreviation: 'DEN',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#FB4F14',
    secondaryColor: '#002244',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/den.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #FB4F14 0%, #002244 100%)'
  },
  KC: {
    name: 'Chiefs',
    city: 'Kansas City',
    abbreviation: 'KC',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#E31837',
    secondaryColor: '#FFB81C',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/kc.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #E31837 0%, #FFB81C 100%)'
  },
  LV: {
    name: 'Raiders',
    city: 'Las Vegas',
    abbreviation: 'LV',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#000000',
    secondaryColor: '#A5ACAF',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lv.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #000000 0%, #A5ACAF 100%)'
  },
  LAC: {
    name: 'Chargers',
    city: 'Los Angeles',
    abbreviation: 'LAC',
    conference: 'AFC',
    division: 'West',
    primaryColor: '#0080C6',
    secondaryColor: '#FFC20E',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lac.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #0080C6 0%, #FFC20E 100%)'
  },

  // NFC East
  DAL: {
    name: 'Cowboys',
    city: 'Dallas',
    abbreviation: 'DAL',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#041E42',
    secondaryColor: '#869397',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/dal.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #041E42 0%, #869397 100%)'
  },
  NYG: {
    name: 'Giants',
    city: 'New York',
    abbreviation: 'NYG',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#0B2265',
    secondaryColor: '#A71930',
    tertiaryColor: '#A5ACAF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/nyg.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #0B2265 0%, #A71930 100%)'
  },
  PHI: {
    name: 'Eagles',
    city: 'Philadelphia',
    abbreviation: 'PHI',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#004C54',
    secondaryColor: '#A5ACAF',
    tertiaryColor: '#ACC0C6',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/phi.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #004C54 0%, #A5ACAF 100%)'
  },
  WAS: {
    name: 'Commanders',
    city: 'Washington',
    abbreviation: 'WAS',
    conference: 'NFC',
    division: 'East',
    primaryColor: '#5A1414',
    secondaryColor: '#FFB612',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/wsh.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #5A1414 0%, #FFB612 100%)'
  },

  // NFC North
  CHI: {
    name: 'Bears',
    city: 'Chicago',
    abbreviation: 'CHI',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#0B162A',
    secondaryColor: '#C83803',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/chi.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #0B162A 0%, #C83803 100%)'
  },
  DET: {
    name: 'Lions',
    city: 'Detroit',
    abbreviation: 'DET',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#0076B6',
    secondaryColor: '#B0B7BC',
    tertiaryColor: '#000000',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/det.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #0076B6 0%, #B0B7BC 100%)'
  },
  GB: {
    name: 'Packers',
    city: 'Green Bay',
    abbreviation: 'GB',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#203731',
    secondaryColor: '#FFB612',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/gb.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #203731 0%, #FFB612 100%)'
  },
  MIN: {
    name: 'Vikings',
    city: 'Minnesota',
    abbreviation: 'MIN',
    conference: 'NFC',
    division: 'North',
    primaryColor: '#4F2683',
    secondaryColor: '#FFC62F',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/min.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #4F2683 0%, #FFC62F 100%)'
  },

  // NFC South
  ATL: {
    name: 'Falcons',
    city: 'Atlanta',
    abbreviation: 'ATL',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#A71930',
    secondaryColor: '#000000',
    tertiaryColor: '#A5ACAF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/atl.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #A71930 0%, #000000 100%)'
  },
  CAR: {
    name: 'Panthers',
    city: 'Carolina',
    abbreviation: 'CAR',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#0085CA',
    secondaryColor: '#101820',
    tertiaryColor: '#BFC0BF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/car.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #0085CA 0%, #101820 100%)'
  },
  NO: {
    name: 'Saints',
    city: 'New Orleans',
    abbreviation: 'NO',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#D3BC8D',
    secondaryColor: '#101820',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/no.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #D3BC8D 0%, #101820 100%)'
  },
  TB: {
    name: 'Buccaneers',
    city: 'Tampa Bay',
    abbreviation: 'TB',
    conference: 'NFC',
    division: 'South',
    primaryColor: '#D50A0A',
    secondaryColor: '#34302B',
    tertiaryColor: '#B1BABF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/tb.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #D50A0A 0%, #34302B 100%)'
  },

  // NFC West
  ARI: {
    name: 'Cardinals',
    city: 'Arizona',
    abbreviation: 'ARI',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#97233F',
    secondaryColor: '#000000',
    tertiaryColor: '#FFB612',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/ari.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #97233F 0%, #FFB612 100%)'
  },
  LAR: {
    name: 'Rams',
    city: 'Los Angeles',
    abbreviation: 'LAR',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#003594',
    secondaryColor: '#FFA300',
    tertiaryColor: '#FF8200',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/lar.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #003594 0%, #FFA300 100%)'
  },
  SF: {
    name: '49ers',
    city: 'San Francisco',
    abbreviation: 'SF',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#AA0000',
    secondaryColor: '#B3995D',
    tertiaryColor: '#FFFFFF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/sf.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #AA0000 0%, #B3995D 100%)'
  },
  SEA: {
    name: 'Seahawks',
    city: 'Seattle',
    abbreviation: 'SEA',
    conference: 'NFC',
    division: 'West',
    primaryColor: '#002244',
    secondaryColor: '#69BE28',
    tertiaryColor: '#A5ACAF',
    logo: 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/sea.png&h=200&w=200',
    gradient: 'linear-gradient(135deg, #002244 0%, #69BE28 100%)'
  }
};

// Team name to abbreviation mapping
const TEAM_NAME_TO_ABB = {
  // AFC East
  'Bills': 'BUF',
  'Dolphins': 'MIA',
  'Patriots': 'NE',
  'Jets': 'NYJ',

  // AFC North
  'Ravens': 'BAL',
  'Bengals': 'CIN',
  'Browns': 'CLE',
  'Steelers': 'PIT',

  // AFC South
  'Texans': 'HOU',
  'Colts': 'IND',
  'Jaguars': 'JAX',
  'Titans': 'TEN',

  // AFC West
  'Broncos': 'DEN',
  'Chiefs': 'KC',
  'Raiders': 'LV',
  'Chargers': 'LAC',

  // NFC East
  'Cowboys': 'DAL',
  'Giants': 'NYG',
  'Eagles': 'PHI',
  'Commanders': 'WAS',

  // NFC North
  'Bears': 'CHI',
  'Lions': 'DET',
  'Packers': 'GB',
  'Vikings': 'MIN',

  // NFC South
  'Falcons': 'ATL',
  'Panthers': 'CAR',
  'Saints': 'NO',
  'Buccaneers': 'TB',

  // NFC West
  'Cardinals': 'ARI',
  'Rams': 'LAR',
  '49ers': 'SF',
  'Seahawks': 'SEA'
};

// Helper function to get team by abbreviation OR name with enhanced logo support
export const getTeam = (teamIdentifier) => {
  if (!teamIdentifier) return null;

  // First try direct abbreviation lookup
  let team = NFL_TEAMS[teamIdentifier];
  let abbreviation = teamIdentifier;

  // If not found, try name lookup
  if (!team) {
    abbreviation = TEAM_NAME_TO_ABB[teamIdentifier];
    if (abbreviation) {
      team = NFL_TEAMS[abbreviation];
    }
  }

  if (!team) return null;

  // Return team with enhanced logo information
  return {
    ...team,
    logoLocal: `/logos/${abbreviation}.svg`,
    logoLocalPng: `/logos/${abbreviation}.png`,
    logoFallback: team.logo
  };
};

// Get all teams as array
export const getAllTeams = () => {
  return Object.values(NFL_TEAMS);
};

// Get teams by conference
export const getTeamsByConference = (conference) => {
  return Object.values(NFL_TEAMS).filter(team => team.conference === conference);
};

// Get teams by division
export const getTeamsByDivision = (conference, division) => {
  return Object.values(NFL_TEAMS).filter(
    team => team.conference === conference && team.division === division
  );
};