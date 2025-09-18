CREATE TABLE nfl_games_2025 (
  game_id varchar(20) PRIMARY KEY,
  season integer,
  week integer,
  game_type varchar(10),
  game_date date,
  game_time time,
  game_datetime timestamp,
  day_of_week varchar(10),
  away_team varchar(3),
  away_team_name varchar(50),
  home_team varchar(3),
  home_team_name varchar(50),
  network varchar(20),
  stadium varchar(100),
  city varchar(50),
  state varchar(2),
  timezone varchar(3),
  is_primetime boolean,
  is_playoff boolean,
  is_international boolean,
  international_location varchar(50),
  kickoff_time_et time,
  kickoff_time_local time,
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now()
);

CREATE INDEX idx_season_week ON nfl_games_2025 (season, week);
CREATE INDEX idx_game_date ON nfl_games_2025 (game_date);
CREATE INDEX idx_teams ON nfl_games_2025 (away_team, home_team);
CREATE INDEX idx_network ON nfl_games_2025 (network);
