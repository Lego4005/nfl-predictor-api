export interface Team {
  name: string;
  abbr: string;
  elo: number;
  color: string;
}

export interface Game {
  id: string;
  week: number;
  date: string;
  status: "SCHEDULED" | "LIVE" | "FINAL";
  quarter?: string;
  away: string;
  home: string;
  score: { away: number; home: number } | null;
  network: string;
  venue: string;
}

export const TEAMS: Record<string, Team> = {
  KC: { name: "Kansas City Chiefs", abbr: "KC", elo: 1692, color: "#E31837" },
  BUF: { name: "Buffalo Bills", abbr: "BUF", elo: 1638, color: "#00338D" },
  PHI: {
    name: "Philadelphia Eagles",
    abbr: "PHI",
    elo: 1645,
    color: "#004C54",
  },
  DAL: { name: "Dallas Cowboys", abbr: "DAL", elo: 1610, color: "#041E42" },
  SF: { name: "San Francisco 49ers", abbr: "SF", elo: 1675, color: "#AA0000" },
  DET: { name: "Detroit Lions", abbr: "DET", elo: 1602, color: "#0076B6" },
  NYJ: { name: "New York Jets", abbr: "NYJ", elo: 1560, color: "#125740" },
  NE: { name: "New England Patriots", abbr: "NE", elo: 1508, color: "#002244" },
  CIN: { name: "Cincinnati Bengals", abbr: "CIN", elo: 1620, color: "#FB4F14" },
  BAL: { name: "Baltimore Ravens", abbr: "BAL", elo: 1650, color: "#241773" },
  MIA: { name: "Miami Dolphins", abbr: "MIA", elo: 1605, color: "#008E97" },
  LAR: { name: "Los Angeles Rams", abbr: "LAR", elo: 1580, color: "#003594" },
  GB: { name: "Green Bay Packers", abbr: "GB", elo: 1588, color: "#203731" },
  MIN: { name: "Minnesota Vikings", abbr: "MIN", elo: 1572, color: "#4F2683" },
  TB: { name: "Tampa Bay Buccaneers", abbr: "TB", elo: 1565, color: "#D50A0A" },
  CAR: { name: "Carolina Panthers", abbr: "CAR", elo: 1485, color: "#0085CA" },
  ATL: { name: "Atlanta Falcons", abbr: "ATL", elo: 1520, color: "#A71930" },
  NO: { name: "New Orleans Saints", abbr: "NO", elo: 1540, color: "#D3BC8D" },
  SEA: { name: "Seattle Seahawks", abbr: "SEA", elo: 1598, color: "#002244" },
  ARI: { name: "Arizona Cardinals", abbr: "ARI", elo: 1495, color: "#97233F" },
  DEN: { name: "Denver Broncos", abbr: "DEN", elo: 1532, color: "#FB4F14" },
  LV: { name: "Las Vegas Raiders", abbr: "LV", elo: 1505, color: "#000000" },
  LAC: {
    name: "Los Angeles Chargers",
    abbr: "LAC",
    elo: 1558,
    color: "#0080C6",
  },
  HOU: { name: "Houston Texans", abbr: "HOU", elo: 1575, color: "#03202F" },
  IND: { name: "Indianapolis Colts", abbr: "IND", elo: 1522, color: "#002C5F" },
  JAX: {
    name: "Jacksonville Jaguars",
    abbr: "JAX",
    elo: 1490,
    color: "#006778",
  },
  TEN: { name: "Tennessee Titans", abbr: "TEN", elo: 1498, color: "#0C2340" },
  CLE: { name: "Cleveland Browns", abbr: "CLE", elo: 1515, color: "#311D00" },
  PIT: {
    name: "Pittsburgh Steelers",
    abbr: "PIT",
    elo: 1555,
    color: "#FFB612",
  },
  CHI: { name: "Chicago Bears", abbr: "CHI", elo: 1510, color: "#0B162A" },
  WAS: {
    name: "Washington Commanders",
    abbr: "WAS",
    elo: 1556,
    color: "#5A1414",
  },
  NYG: { name: "New York Giants", abbr: "NYG", elo: 1485, color: "#0B2265" },
};

const today = new Date();
const dayOffset = (n: number): string => {
  const d = new Date(today);
  d.setDate(d.getDate() + n);
  d.setHours(13, 0, 0, 0);
  return d.toISOString();
};

export const GAMES: Game[] = [
  // Week 3 Thursday games
  {
    id: "g1",
    week: 3,
    date: dayOffset(-3),
    status: "FINAL",
    away: "DET",
    home: "SF",
    score: { away: 20, home: 27 },
    network: "TNF",
    venue: "Levi's Stadium",
  },

  // Week 3 Sunday games (early and late)
  {
    id: "g2",
    week: 3,
    date: dayOffset(0),
    status: "LIVE",
    quarter: "Q3 08:21",
    away: "DAL",
    home: "PHI",
    score: { away: 14, home: 20 },
    network: "FOX",
    venue: "Lincoln Financial Field",
  },
  {
    id: "g3",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "BUF",
    home: "KC",
    score: null,
    network: "CBS",
    venue: "GEHA Field at Arrowhead",
  },
  {
    id: "g4",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "BAL",
    home: "CIN",
    score: null,
    network: "CBS",
    venue: "Paycor Stadium",
  },
  {
    id: "g5",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "NYJ",
    home: "NE",
    score: null,
    network: "FOX",
    venue: "Gillette Stadium",
  },
  {
    id: "g6",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "MIA",
    home: "LAR",
    score: null,
    network: "FOX",
    venue: "SoFi Stadium",
  },
  {
    id: "g7",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "GB",
    home: "MIN",
    score: null,
    network: "CBS",
    venue: "U.S. Bank Stadium",
  },
  {
    id: "g8",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "SF",
    home: "BUF",
    score: null,
    network: "FOX",
    venue: "Highmark Stadium",
  },
  {
    id: "g9",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "KC",
    home: "DAL",
    score: null,
    network: "CBS",
    venue: "AT&T Stadium",
  },
  {
    id: "g10",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "CIN",
    home: "DET",
    score: null,
    network: "FOX",
    venue: "Ford Field",
  },
  {
    id: "g11",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "PHI",
    home: "MIA",
    score: null,
    network: "CBS",
    venue: "Hard Rock Stadium",
  },
  {
    id: "g12",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "LAR",
    home: "NYJ",
    score: null,
    network: "FOX",
    venue: "MetLife Stadium",
  },
  {
    id: "g13",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "MIN",
    home: "BAL",
    score: null,
    network: "CBS",
    venue: "M&T Bank Stadium",
  },
  {
    id: "g14",
    week: 3,
    date: dayOffset(0),
    status: "SCHEDULED",
    away: "NE",
    home: "GB",
    score: null,
    network: "FOX",
    venue: "Lambeau Field",
  },

  // Week 3 Monday game
  {
    id: "g15",
    week: 3,
    date: dayOffset(1),
    status: "SCHEDULED",
    away: "BUF",
    home: "NYJ",
    score: null,
    network: "MNF",
    venue: "MetLife Stadium",
  },
];
