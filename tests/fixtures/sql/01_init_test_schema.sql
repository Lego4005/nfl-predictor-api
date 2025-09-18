-- NFL Predictor API Test Database Initialization
-- This script sets up the test database schema and initial data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Create test-specific schemas
CREATE SCHEMA IF NOT EXISTS test_data;
CREATE SCHEMA IF NOT EXISTS test_ml;
CREATE SCHEMA IF NOT EXISTS test_cache;

-- Grant permissions to test user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_data TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_ml TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_cache TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_data TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_ml TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_cache TO test_user;

-- Create test data tables for fixtures
CREATE TABLE IF NOT EXISTS test_data.teams (
    team_id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(3) NOT NULL,
    conference VARCHAR(3) NOT NULL,
    division VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_data.games (
    game_id VARCHAR(50) PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    game_type VARCHAR(20) DEFAULT 'regular',
    home_team_id VARCHAR(3) REFERENCES test_data.teams(team_id),
    away_team_id VARCHAR(3) REFERENCES test_data.teams(team_id),
    game_date TIMESTAMP NOT NULL,
    venue VARCHAR(100),
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    weather_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_data.predictions (
    prediction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(50) REFERENCES test_data.games(game_id),
    model_version VARCHAR(20) NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    home_win_probability DECIMAL(5,4),
    away_win_probability DECIMAL(5,4),
    spread_prediction DECIMAL(5,2),
    total_prediction DECIMAL(5,2),
    confidence_score DECIMAL(5,4),
    feature_importance JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better test performance
CREATE INDEX IF NOT EXISTS idx_test_games_season_week ON test_data.games(season, week);
CREATE INDEX IF NOT EXISTS idx_test_games_date ON test_data.games(game_date);
CREATE INDEX IF NOT EXISTS idx_test_games_status ON test_data.games(status);
CREATE INDEX IF NOT EXISTS idx_test_predictions_game ON test_data.predictions(game_id);
CREATE INDEX IF NOT EXISTS idx_test_predictions_time ON test_data.predictions(prediction_time);

-- Insert sample teams data
INSERT INTO test_data.teams (team_id, name, abbreviation, conference, division, city, primary_color, secondary_color) VALUES
('KC', 'Kansas City Chiefs', 'KC', 'AFC', 'West', 'Kansas City', '#E31837', '#FFB81C'),
('DET', 'Detroit Lions', 'DET', 'NFC', 'North', 'Detroit', '#0076B6', '#B0B7BC'),
('BUF', 'Buffalo Bills', 'BUF', 'AFC', 'East', 'Buffalo', '#00338D', '#C60C30'),
('MIA', 'Miami Dolphins', 'MIA', 'AFC', 'East', 'Miami', '#008E97', '#FC4C02'),
('NE', 'New England Patriots', 'NE', 'AFC', 'East', 'Foxborough', '#002244', '#C60C30'),
('NYJ', 'New York Jets', 'NYJ', 'AFC', 'East', 'East Rutherford', '#125740', '#FFFFFF'),
('BAL', 'Baltimore Ravens', 'BAL', 'AFC', 'North', 'Baltimore', '#241773', '#000000'),
('CIN', 'Cincinnati Bengals', 'CIN', 'AFC', 'North', 'Cincinnati', '#FB4F14', '#000000'),
('CLE', 'Cleveland Browns', 'CLE', 'AFC', 'North', 'Cleveland', '#311D00', '#FF3C00'),
('PIT', 'Pittsburgh Steelers', 'PIT', 'AFC', 'North', 'Pittsburgh', '#FFB612', '#101820'),
('HOU', 'Houston Texans', 'HOU', 'AFC', 'South', 'Houston', '#03202F', '#A71930'),
('IND', 'Indianapolis Colts', 'IND', 'AFC', 'South', 'Indianapolis', '#002C5F', '#A2AAAD'),
('JAX', 'Jacksonville Jaguars', 'JAX', 'AFC', 'South', 'Jacksonville', '#101820', '#D7A22A'),
('TEN', 'Tennessee Titans', 'TEN', 'AFC', 'South', 'Nashville', '#0C2340', '#4B92DB'),
('DEN', 'Denver Broncos', 'DEN', 'AFC', 'West', 'Denver', '#FB4F14', '#002244'),
('LV', 'Las Vegas Raiders', 'LV', 'AFC', 'West', 'Las Vegas', '#000000', '#A5ACAF'),
('LAC', 'Los Angeles Chargers', 'LAC', 'AFC', 'West', 'Los Angeles', '#0080C6', '#FFC20E'),
('DAL', 'Dallas Cowboys', 'DAL', 'NFC', 'East', 'Arlington', '#003594', '#869397'),
('NYG', 'New York Giants', 'NYG', 'NFC', 'East', 'East Rutherford', '#0B2265', '#A71930'),
('PHI', 'Philadelphia Eagles', 'PHI', 'NFC', 'East', 'Philadelphia', '#004C54', '#A5ACAF'),
('WAS', 'Washington Commanders', 'WAS', 'NFC', 'East', 'Landover', '#5A1414', '#FFB612'),
('CHI', 'Chicago Bears', 'CHI', 'NFC', 'North', 'Chicago', '#0B162A', '#C83803'),
('GB', 'Green Bay Packers', 'GB', 'NFC', 'North', 'Green Bay', '#203731', '#FFB612'),
('MIN', 'Minnesota Vikings', 'MIN', 'NFC', 'North', 'Minneapolis', '#4F2683', '#FFC62F'),
('ATL', 'Atlanta Falcons', 'ATL', 'NFC', 'South', 'Atlanta', '#A71930', '#000000'),
('CAR', 'Carolina Panthers', 'CAR', 'NFC', 'South', 'Charlotte', '#0085CA', '#101820'),
('NO', 'New Orleans Saints', 'NO', 'NFC', 'South', 'New Orleans', '#D3BC8D', '#101820'),
('TB', 'Tampa Bay Buccaneers', 'TB', 'NFC', 'South', 'Tampa', '#D50A0A', '#FF7900'),
('ARI', 'Arizona Cardinals', 'ARI', 'NFC', 'West', 'Glendale', '#97233F', '#000000'),
('LAR', 'Los Angeles Rams', 'LAR', 'NFC', 'West', 'Los Angeles', '#003594', '#FFA300'),
('SF', 'San Francisco 49ers', 'SF', 'NFC', 'West', 'Santa Clara', '#AA0000', '#B3995D'),
('SEA', 'Seattle Seahawks', 'SEA', 'NFC', 'West', 'Seattle', '#002244', '#69BE28')
ON CONFLICT (team_id) DO NOTHING;

-- Insert sample games for testing
INSERT INTO test_data.games (game_id, season, week, home_team_id, away_team_id, game_date, venue, status) VALUES
('2024_W01_KC_DET', 2024, 1, 'DET', 'KC', '2024-09-15 17:00:00', 'Ford Field', 'scheduled'),
('2024_W01_BUF_MIA', 2024, 1, 'MIA', 'BUF', '2024-09-15 13:00:00', 'Hard Rock Stadium', 'scheduled'),
('2024_W01_NE_NYJ', 2024, 1, 'NYJ', 'NE', '2024-09-15 13:00:00', 'MetLife Stadium', 'scheduled'),
('2024_W01_BAL_CIN', 2024, 1, 'CIN', 'BAL', '2024-09-15 13:00:00', 'Paul Brown Stadium', 'scheduled'),
('2024_W01_CLE_PIT', 2024, 1, 'PIT', 'CLE', '2024-09-15 20:20:00', 'Heinz Field', 'scheduled')
ON CONFLICT (game_id) DO NOTHING;

-- Create test utility functions
CREATE OR REPLACE FUNCTION test_data.create_sample_game(
    p_home_team VARCHAR(3),
    p_away_team VARCHAR(3),
    p_season INTEGER DEFAULT 2024,
    p_week INTEGER DEFAULT 1
) RETURNS VARCHAR(50) AS $$
DECLARE
    game_id VARCHAR(50);
BEGIN
    game_id := p_season || '_W' || LPAD(p_week::TEXT, 2, '0') || '_' || p_away_team || '_' || p_home_team;

    INSERT INTO test_data.games (game_id, season, week, home_team_id, away_team_id, game_date, venue, status)
    VALUES (
        game_id,
        p_season,
        p_week,
        p_home_team,
        p_away_team,
        CURRENT_TIMESTAMP + INTERVAL '1 day',
        p_home_team || ' Stadium',
        'scheduled'
    )
    ON CONFLICT (game_id) DO NOTHING;

    RETURN game_id;
END;
$$ LANGUAGE plpgsql;

-- Create test cleanup function
CREATE OR REPLACE FUNCTION test_data.cleanup_test_data() RETURNS void AS $$
BEGIN
    TRUNCATE test_data.predictions CASCADE;
    TRUNCATE test_data.games CASCADE;
    -- Don't truncate teams as they're reference data
END;
$$ LANGUAGE plpgsql;

-- Create performance monitoring views
CREATE OR REPLACE VIEW test_data.performance_summary AS
SELECT
    'games' as table_name,
    COUNT(*) as record_count,
    pg_size_pretty(pg_relation_size('test_data.games')) as table_size
FROM test_data.games
UNION ALL
SELECT
    'predictions' as table_name,
    COUNT(*) as record_count,
    pg_size_pretty(pg_relation_size('test_data.predictions')) as table_size
FROM test_data.predictions
UNION ALL
SELECT
    'teams' as table_name,
    COUNT(*) as record_count,
    pg_size_pretty(pg_relation_size('test_data.teams')) as table_size
FROM test_data.teams;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION test_data.create_sample_game TO test_user;
GRANT EXECUTE ON FUNCTION test_data.cleanup_test_data TO test_user;
GRANT SELECT ON test_data.performance_summary TO test_user;

-- Log initialization completion
INSERT INTO test_data.games (game_id, season, week, home_team_id, away_team_id, game_date, venue, status)
VALUES ('test_init_marker', 2024, 0, 'KC', 'KC', CURRENT_TIMESTAMP, 'Test Stadium', 'completed')
ON CONFLICT (game_id) DO UPDATE SET status = 'completed';