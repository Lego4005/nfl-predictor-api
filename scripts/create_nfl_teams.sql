-- Create and populate nfl_teams table for foreign key constraints
-- Run this in Supabase SQL Editor BEFORE loading games data

-- First, create the nfl_teams table if it doesn't exist
CREATE TABLE IF NOT EXISTS nfl_teams (
    team_id VARCHAR(3) PRIMARY KEY,
    team_name VARCHAR(50) NOT NULL,
    team_city VARCHAR(30) NOT NULL,
    team_full_name VARCHAR(80) NOT NULL,
    conference VARCHAR(3) NOT NULL CHECK (conference IN ('AFC', 'NFC')),
    division VARCHAR(10) NOT NULL,
    established_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert all NFL teams found in the historical data
INSERT INTO nfl_teams (team_id, team_name, team_city, team_full_name, conference, division, established_year) VALUES
('ARI', 'Cardinals', 'Arizona', 'Arizona Cardinals', 'NFC', 'West', 1898),
('ATL', 'Falcons', 'Atlanta', 'Atlanta Falcons', 'NFC', 'South', 1965),
('BAL', 'Ravens', 'Baltimore', 'Baltimore Ravens', 'AFC', 'North', 1996),
('BUF', 'Bills', 'Buffalo', 'Buffalo Bills', 'AFC', 'East', 1960),
('CAR', 'Panthers', 'Carolina', 'Carolina Panthers', 'NFC', 'South', 1993),
('CHI', 'Bears', 'Chicago', 'Chicago Bears', 'NFC', 'North', 1919),
('CIN', 'Bengals', 'Cincinnati', 'Cincinnati Bengals', 'AFC', 'North', 1968),
('CLE', 'Browns', 'Cleveland', 'Cleveland Browns', 'AFC', 'North', 1946),
('DAL', 'Cowboys', 'Dallas', 'Dallas Cowboys', 'NFC', 'East', 1960),
('DEN', 'Broncos', 'Denver', 'Denver Broncos', 'AFC', 'West', 1960),
('DET', 'Lions', 'Detroit', 'Detroit Lions', 'NFC', 'North', 1930),
('GB', 'Packers', 'Green Bay', 'Green Bay Packers', 'NFC', 'North', 1919),
('HOU', 'Texans', 'Houston', 'Houston Texans', 'AFC', 'South', 2002),
('IND', 'Colts', 'Indianapolis', 'Indianapolis Colts', 'AFC', 'South', 1953),
('JAX', 'Jaguars', 'Jacksonville', 'Jacksonville Jaguars', 'AFC', 'South', 1993),
('KC', 'Chiefs', 'Kansas City', 'Kansas City Chiefs', 'AFC', 'West', 1960),
('LA', 'Rams', 'Los Angeles', 'Los Angeles Rams', 'NFC', 'West', 1936),
('LAC', 'Chargers', 'Los Angeles', 'Los Angeles Chargers', 'AFC', 'West', 1960),
('LV', 'Raiders', 'Las Vegas', 'Las Vegas Raiders', 'AFC', 'West', 1960),
('MIA', 'Dolphins', 'Miami', 'Miami Dolphins', 'AFC', 'East', 1966),
('MIN', 'Vikings', 'Minnesota', 'Minnesota Vikings', 'NFC', 'North', 1961),
('NE', 'Patriots', 'New England', 'New England Patriots', 'AFC', 'East', 1960),
('NO', 'Saints', 'New Orleans', 'New Orleans Saints', 'NFC', 'South', 1967),
('NYG', 'Giants', 'New York', 'New York Giants', 'NFC', 'East', 1925),
('NYJ', 'Jets', 'New York', 'New York Jets', 'AFC', 'East', 1960),
('OAK', 'Raiders', 'Oakland', 'Oakland Raiders', 'AFC', 'West', 1960),
('PHI', 'Eagles', 'Philadelphia', 'Philadelphia Eagles', 'NFC', 'East', 1933),
('PIT', 'Steelers', 'Pittsburgh', 'Pittsburgh Steelers', 'AFC', 'North', 1933),
('SD', 'Chargers', 'San Diego', 'San Diego Chargers', 'AFC', 'West', 1960),
('SEA', 'Seahawks', 'Seattle', 'Seattle Seahawks', 'NFC', 'West', 1976),
('SF', '49ers', 'San Francisco', 'San Francisco 49ers', 'NFC', 'West', 1946),
('STL', 'Rams', 'St. Louis', 'St. Louis Rams', 'NFC', 'West', 1936),
('TB', 'Buccaneers', 'Tampa Bay', 'Tampa Bay Buccaneers', 'NFC', 'South', 1974),
('TEN', 'Titans', 'Tennessee', 'Tennessee Titans', 'AFC', 'South', 1960),
('WAS', 'Commanders', 'Washington', 'Washington Commanders', 'NFC', 'East', 1932)
ON CONFLICT (team_id) DO UPDATE SET
    team_name = EXCLUDED.team_name,
    team_city = EXCLUDED.team_city,
    team_full_name = EXCLUDED.team_full_name,
    conference = EXCLUDED.conference,
    division = EXCLUDED.division,
    updated_at = NOW();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nfl_teams_conference ON nfl_teams(conference);
CREATE INDEX IF NOT EXISTS idx_nfl_teams_division ON nfl_teams(division);

-- Verify the teams were created
SELECT COUNT(*) as team_count FROM nfl_teams;