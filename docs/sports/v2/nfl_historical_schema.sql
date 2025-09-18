
-- NFL Historical Data Schema for Supabase
-- Generated from nflfastR data analysis

-- Teams table
CREATE TABLE nfl_teams (
    team_id varchar(3) PRIMARY KEY,
    team_name varchar(100) NOT NULL,
    team_city varchar(50),
    team_state varchar(2),
    conference varchar(3), -- AFC/NFC
    division varchar(10), -- North/South/East/West
    team_color varchar(7), -- Hex color
    team_color_secondary varchar(7),
    founded_year integer,
    stadium_name varchar(100),
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- Players table
CREATE TABLE nfl_players (
    player_id varchar(20) PRIMARY KEY,
    player_name varchar(100) NOT NULL,
    position varchar(10),
    jersey_number integer,
    height_inches integer,
    weight_lbs integer,
    birth_date date,
    college varchar(100),
    draft_year integer,
    draft_round integer,
    draft_pick integer,
    rookie_year integer,
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- Games table (enhanced from existing schedule)
CREATE TABLE nfl_games (
    game_id varchar(20) PRIMARY KEY,
    season integer NOT NULL,
    week integer,
    game_type varchar(10), -- REG, WC, DIV, CONF, SB
    game_date date NOT NULL,
    game_time time,
    game_datetime timestamp,
    home_team varchar(3) REFERENCES nfl_teams(team_id),
    away_team varchar(3) REFERENCES nfl_teams(team_id),
    home_score integer,
    away_score integer,
    overtime boolean DEFAULT false,
    stadium varchar(100),
    weather_temperature integer,
    weather_wind_mph integer,
    weather_humidity integer,
    weather_description text,
    surface varchar(20), -- grass, turf, etc.
    roof varchar(20), -- dome, retractable, open
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

-- Play by play table (main historical data)
CREATE TABLE nfl_plays (
    play_id varchar(30) PRIMARY KEY, -- game_id + play sequence
    game_id varchar(20) REFERENCES nfl_games(game_id),
    drive_id varchar(30),
    play_sequence integer,
    quarter integer,
    quarter_seconds_remaining integer,
    game_seconds_remaining integer,
    down integer,
    yards_to_go integer,
    yardline_100 integer, -- yards from opponent goal line
    play_type varchar(20),
    play_description text,
    yards_gained integer,
    
    -- Team information
    possession_team varchar(3) REFERENCES nfl_teams(team_id),
    defense_team varchar(3) REFERENCES nfl_teams(team_id),
    
    -- Score information
    home_score integer,
    away_score integer,
    score_differential integer,
    
    -- Advanced analytics
    expected_points_added decimal(6,3),
    win_probability decimal(6,4),
    win_probability_added decimal(6,4),
    
    -- Pass-specific data
    pass_attempt boolean DEFAULT false,
    pass_completion boolean DEFAULT false,
    pass_touchdown boolean DEFAULT false,
    pass_interception boolean DEFAULT false,
    pass_length varchar(10), -- short, medium, long
    air_yards integer,
    yards_after_catch integer,
    completion_probability decimal(6,4),
    
    -- Rush-specific data
    rush_attempt boolean DEFAULT false,
    rush_touchdown boolean DEFAULT false,
    
    -- Kicking data
    field_goal_attempt boolean DEFAULT false,
    field_goal_made boolean DEFAULT false,
    kick_distance integer,
    extra_point_attempt boolean DEFAULT false,
    extra_point_made boolean DEFAULT false,
    
    -- Penalty data
    penalty boolean DEFAULT false,
    penalty_team varchar(3),
    penalty_yards integer,
    
    -- Player involvement
    passer_id varchar(20) REFERENCES nfl_players(player_id),
    rusher_id varchar(20) REFERENCES nfl_players(player_id),
    receiver_id varchar(20) REFERENCES nfl_players(player_id),
    kicker_id varchar(20) REFERENCES nfl_players(player_id),
    
    created_at timestamp DEFAULT now()
);

-- Drive summary table
CREATE TABLE nfl_drives (
    drive_id varchar(30) PRIMARY KEY,
    game_id varchar(20) REFERENCES nfl_games(game_id),
    drive_number integer,
    possession_team varchar(3) REFERENCES nfl_teams(team_id),
    drive_start_quarter integer,
    drive_start_time integer,
    drive_start_yardline integer,
    drive_end_quarter integer,
    drive_end_time integer,
    drive_end_yardline integer,
    drive_plays integer,
    drive_yards integer,
    drive_time_seconds integer,
    drive_result varchar(20), -- touchdown, field_goal, punt, etc.
    drive_score_points integer,
    created_at timestamp DEFAULT now()
);

-- Player game statistics
CREATE TABLE nfl_player_stats_game (
    stat_id varchar(40) PRIMARY KEY, -- game_id + player_id
    game_id varchar(20) REFERENCES nfl_games(game_id),
    player_id varchar(20) REFERENCES nfl_players(player_id),
    team_id varchar(3) REFERENCES nfl_teams(team_id),
    
    -- Passing stats
    pass_attempts integer DEFAULT 0,
    pass_completions integer DEFAULT 0,
    pass_yards integer DEFAULT 0,
    pass_touchdowns integer DEFAULT 0,
    pass_interceptions integer DEFAULT 0,
    pass_sacks integer DEFAULT 0,
    pass_sack_yards integer DEFAULT 0,
    
    -- Rushing stats
    rush_attempts integer DEFAULT 0,
    rush_yards integer DEFAULT 0,
    rush_touchdowns integer DEFAULT 0,
    rush_long integer DEFAULT 0,
    
    -- Receiving stats
    receptions integer DEFAULT 0,
    receiving_yards integer DEFAULT 0,
    receiving_touchdowns integer DEFAULT 0,
    receiving_targets integer DEFAULT 0,
    receiving_long integer DEFAULT 0,
    
    -- Kicking stats
    field_goals_made integer DEFAULT 0,
    field_goals_attempted integer DEFAULT 0,
    extra_points_made integer DEFAULT 0,
    extra_points_attempted integer DEFAULT 0,
    
    -- Defensive stats
    tackles integer DEFAULT 0,
    assists integer DEFAULT 0,
    sacks decimal(3,1) DEFAULT 0,
    interceptions integer DEFAULT 0,
    fumbles_forced integer DEFAULT 0,
    fumbles_recovered integer DEFAULT 0,
    
    created_at timestamp DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_nfl_games_season_week ON nfl_games(season, week);
CREATE INDEX idx_nfl_games_date ON nfl_games(game_date);
CREATE INDEX idx_nfl_games_teams ON nfl_games(home_team, away_team);

CREATE INDEX idx_nfl_plays_game ON nfl_plays(game_id);
CREATE INDEX idx_nfl_plays_type ON nfl_plays(play_type);
CREATE INDEX idx_nfl_plays_quarter ON nfl_plays(quarter);
CREATE INDEX idx_nfl_plays_down ON nfl_plays(down);
CREATE INDEX idx_nfl_plays_possession ON nfl_plays(possession_team);

CREATE INDEX idx_nfl_drives_game ON nfl_drives(game_id);
CREATE INDEX idx_nfl_drives_team ON nfl_drives(possession_team);

CREATE INDEX idx_nfl_player_stats_game ON nfl_player_stats_game(game_id);
CREATE INDEX idx_nfl_player_stats_player ON nfl_player_stats_game(player_id);
CREATE INDEX idx_nfl_player_stats_team ON nfl_player_stats_game(team_id);

-- Row Level Security policies
ALTER TABLE nfl_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfl_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfl_games ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfl_plays ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfl_drives ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfl_player_stats_game ENABLE ROW LEVEL SECURITY;

-- Public read access policies
CREATE POLICY "Public read access" ON nfl_teams FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nfl_players FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nfl_games FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nfl_plays FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nfl_drives FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nfl_player_stats_game FOR SELECT USING (true);
