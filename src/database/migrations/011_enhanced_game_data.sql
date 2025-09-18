-- Enhanced NFL Game Data Tables
-- Stores detailed game analytics from SportsData.io APIs for comprehensive expert verification

-- ================================================
-- ENHANCED GAME DATA TABLES
-- ================================================

-- Table: enhanced_game_data
-- Stores comprehensive game information beyond basic scores
CREATE TABLE IF NOT EXISTS enhanced_game_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id VARCHAR(100) UNIQUE NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,

    -- Basic Game Info
    home_team VARCHAR(10) NOT NULL,
    away_team VARCHAR(10) NOT NULL,
    game_date TIMESTAMP WITH TIME ZONE,
    final_score_home INTEGER,
    final_score_away INTEGER,
    status VARCHAR(50),

    -- Weather and Conditions
    weather_temperature INTEGER,
    weather_humidity INTEGER,
    weather_wind_speed INTEGER,
    weather_wind_direction VARCHAR(10),
    weather_condition VARCHAR(100),
    stadium_name VARCHAR(200),
    attendance INTEGER,

    -- Game Flow and Timing
    total_plays INTEGER,
    game_duration_minutes INTEGER,
    overtime_periods INTEGER,

    -- Advanced Team Stats
    home_time_of_possession VARCHAR(10),
    away_time_of_possession VARCHAR(10),
    home_first_downs INTEGER,
    away_first_downs INTEGER,
    home_total_yards INTEGER,
    away_total_yards INTEGER,
    home_passing_yards INTEGER,
    away_passing_yards INTEGER,
    home_rushing_yards INTEGER,
    away_rushing_yards INTEGER,

    -- Efficiency Metrics
    home_third_down_attempts INTEGER,
    home_third_down_conversions INTEGER,
    away_third_down_attempts INTEGER,
    away_third_down_conversions INTEGER,
    home_red_zone_attempts INTEGER,
    home_red_zone_scores INTEGER,
    away_red_zone_attempts INTEGER,
    away_red_zone_scores INTEGER,

    -- Turnovers and Penalties
    home_turnovers INTEGER,
    away_turnovers INTEGER,
    home_penalties INTEGER,
    home_penalty_yards INTEGER,
    away_penalties INTEGER,
    away_penalty_yards INTEGER,

    -- Special Teams
    home_punt_return_yards INTEGER,
    away_punt_return_yards INTEGER,
    home_kick_return_yards INTEGER,
    away_kick_return_yards INTEGER,

    -- API Data Store (JSONB for flexibility)
    raw_score_data JSONB,
    raw_stats_data JSONB,
    raw_advanced_metrics JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: game_play_by_play
-- Stores individual plays for drive outcome verification
CREATE TABLE IF NOT EXISTS game_play_by_play (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id VARCHAR(100) NOT NULL,
    play_id VARCHAR(100) NOT NULL,

    -- Play Context
    quarter INTEGER,
    time_remaining VARCHAR(10),
    down INTEGER,
    yards_to_go INTEGER,
    yard_line INTEGER,
    possession_team VARCHAR(10),

    -- Play Details
    play_type VARCHAR(50),
    play_description TEXT,
    yards_gained INTEGER,
    is_touchdown BOOLEAN DEFAULT FALSE,
    is_field_goal BOOLEAN DEFAULT FALSE,
    is_safety BOOLEAN DEFAULT FALSE,
    is_turnover BOOLEAN DEFAULT FALSE,
    is_penalty BOOLEAN DEFAULT FALSE,

    -- Players Involved
    primary_player VARCHAR(200),
    secondary_players JSONB,

    -- Situational Data
    is_red_zone BOOLEAN DEFAULT FALSE,
    is_goal_to_go BOOLEAN DEFAULT FALSE,
    is_fourth_down BOOLEAN DEFAULT FALSE,
    is_two_minute_warning BOOLEAN DEFAULT FALSE,

    -- Raw Play Data
    raw_play_data JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES enhanced_game_data(game_id)
);

-- Table: game_drives
-- Stores drive-level data for drive outcome verification
CREATE TABLE IF NOT EXISTS game_drives (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id VARCHAR(100) NOT NULL,
    drive_id VARCHAR(100) NOT NULL,

    -- Drive Context
    quarter INTEGER,
    possession_team VARCHAR(10),
    starting_field_position INTEGER,

    -- Drive Outcome
    drive_result VARCHAR(50), -- 'touchdown', 'field_goal', 'punt', 'turnover', 'safety', 'end_of_half'
    ending_field_position INTEGER,
    total_plays INTEGER,
    total_yards INTEGER,
    time_consumed VARCHAR(10),

    -- Drive Quality Metrics
    plays_per_yard DECIMAL(5,2),
    yards_per_play DECIMAL(5,2),
    is_scoring_drive BOOLEAN DEFAULT FALSE,
    is_three_and_out BOOLEAN DEFAULT FALSE,

    -- Situational Context
    is_two_minute_drill BOOLEAN DEFAULT FALSE,
    is_goal_line_stand BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES enhanced_game_data(game_id)
);

-- Table: coaching_decisions
-- Stores coaching decision data for coaching advantage verification
CREATE TABLE IF NOT EXISTS coaching_decisions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id VARCHAR(100) NOT NULL,

    -- Decision Context
    team VARCHAR(10),
    quarter INTEGER,
    situation VARCHAR(100), -- 'fourth_down', 'two_point_conversion', 'timeout_usage', 'challenge', 'red_zone'

    -- Decision Details
    decision_type VARCHAR(50),
    decision_description TEXT,
    outcome VARCHAR(50), -- 'successful', 'failed', 'neutral'

    -- Decision Quality Metrics
    expected_value DECIMAL(5,2),
    actual_value DECIMAL(5,2),
    decision_quality_score DECIMAL(5,2), -- Advanced analytics score

    -- Context Data
    game_state JSONB, -- Score, time, field position, etc.
    alternative_decisions JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES enhanced_game_data(game_id)
);

-- Table: special_teams_performance
-- Stores special teams data for special teams edge verification
CREATE TABLE IF NOT EXISTS special_teams_performance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id VARCHAR(100) NOT NULL,
    team VARCHAR(10),

    -- Kicking Game
    field_goal_attempts INTEGER DEFAULT 0,
    field_goals_made INTEGER DEFAULT 0,
    longest_field_goal INTEGER,
    extra_point_attempts INTEGER DEFAULT 0,
    extra_points_made INTEGER DEFAULT 0,

    -- Punting Game
    punts INTEGER DEFAULT 0,
    punt_yards INTEGER DEFAULT 0,
    punts_inside_20 INTEGER DEFAULT 0,
    punt_return_yards_allowed INTEGER DEFAULT 0,

    -- Return Game
    kickoff_returns INTEGER DEFAULT 0,
    kickoff_return_yards INTEGER DEFAULT 0,
    punt_returns INTEGER DEFAULT 0,
    punt_return_yards INTEGER DEFAULT 0,
    return_touchdowns INTEGER DEFAULT 0,

    -- Coverage Units
    tackles_on_coverage INTEGER DEFAULT 0,
    coverage_efficiency_score DECIMAL(5,2),

    -- Game Impact
    field_position_advantage DECIMAL(5,2),
    special_teams_score DECIMAL(5,2), -- Overall ST performance score

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES enhanced_game_data(game_id)
);

-- Table: situational_performance
-- Stores situational data for specific prediction verification
CREATE TABLE IF NOT EXISTS situational_performance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id VARCHAR(100) NOT NULL,
    team VARCHAR(10),

    -- Clutch Performance
    points_final_2_minutes INTEGER DEFAULT 0,
    drives_final_2_minutes INTEGER DEFAULT 0,
    scoring_drives_final_2_minutes INTEGER DEFAULT 0,

    -- Pressure Situations
    fourth_down_attempts INTEGER DEFAULT 0,
    fourth_down_conversions INTEGER DEFAULT 0,
    red_zone_trips INTEGER DEFAULT 0,
    red_zone_touchdowns INTEGER DEFAULT 0,

    -- Home Field Factors (for home team only)
    crowd_noise_impact_score DECIMAL(5,2),
    home_field_advantage_score DECIMAL(5,2),
    referee_calls_differential INTEGER, -- Favorable calls vs opponent

    -- Momentum Indicators
    momentum_shifts INTEGER DEFAULT 0,
    largest_lead INTEGER DEFAULT 0,
    time_with_lead INTEGER, -- Minutes with the lead
    comeback_ability_score DECIMAL(5,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES enhanced_game_data(game_id)
);

-- Table: expert_prediction_verification
-- Links expert predictions to actual game outcomes for accuracy calculation
CREATE TABLE IF NOT EXISTS expert_prediction_verification (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Link to Expert and Game
    expert_reasoning_chain_id UUID NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    expert_id VARCHAR(100) NOT NULL,

    -- Prediction Categories
    prediction_category VARCHAR(100), -- 'winner', 'score', 'total', 'coaching', 'special_teams', etc.
    predicted_value TEXT,
    actual_value TEXT,

    -- Verification Results
    is_correct BOOLEAN,
    accuracy_score DECIMAL(5,2), -- 0.0 to 1.0 for partial credit
    confidence_score DECIMAL(5,2),

    -- Supporting Data
    verification_method VARCHAR(100), -- 'exact_match', 'range_check', 'statistical_analysis'
    supporting_data JSONB,

    -- Metadata
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verification_source VARCHAR(100) DEFAULT 'sportsdata_io',

    FOREIGN KEY (expert_reasoning_chain_id) REFERENCES expert_reasoning_chains(id),
    FOREIGN KEY (game_id) REFERENCES enhanced_game_data(game_id)
);

-- ================================================
-- INDEXES FOR PERFORMANCE
-- ================================================

-- Game data indexes
CREATE INDEX IF NOT EXISTS idx_enhanced_game_data_game_id ON enhanced_game_data(game_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_game_data_season_week ON enhanced_game_data(season, week);
CREATE INDEX IF NOT EXISTS idx_enhanced_game_data_teams ON enhanced_game_data(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_enhanced_game_data_date ON enhanced_game_data(game_date);

-- Play-by-play indexes
CREATE INDEX IF NOT EXISTS idx_play_by_play_game_id ON game_play_by_play(game_id);
CREATE INDEX IF NOT EXISTS idx_play_by_play_quarter_time ON game_play_by_play(quarter, time_remaining);
CREATE INDEX IF NOT EXISTS idx_play_by_play_situation ON game_play_by_play(down, yards_to_go);

-- Drive indexes
CREATE INDEX IF NOT EXISTS idx_drives_game_id ON game_drives(game_id);
CREATE INDEX IF NOT EXISTS idx_drives_result ON game_drives(drive_result);
CREATE INDEX IF NOT EXISTS idx_drives_team ON game_drives(possession_team);

-- Coaching decision indexes
CREATE INDEX IF NOT EXISTS idx_coaching_decisions_game_id ON coaching_decisions(game_id);
CREATE INDEX IF NOT EXISTS idx_coaching_decisions_situation ON coaching_decisions(situation);
CREATE INDEX IF NOT EXISTS idx_coaching_decisions_team ON coaching_decisions(team);

-- Special teams indexes
CREATE INDEX IF NOT EXISTS idx_special_teams_game_id ON special_teams_performance(game_id);
CREATE INDEX IF NOT EXISTS idx_special_teams_team ON special_teams_performance(team);

-- Situational performance indexes
CREATE INDEX IF NOT EXISTS idx_situational_game_id ON situational_performance(game_id);
CREATE INDEX IF NOT EXISTS idx_situational_team ON situational_performance(team);

-- Verification indexes
CREATE INDEX IF NOT EXISTS idx_verification_expert_game ON expert_prediction_verification(expert_id, game_id);
CREATE INDEX IF NOT EXISTS idx_verification_category ON expert_prediction_verification(prediction_category);
CREATE INDEX IF NOT EXISTS idx_verification_accuracy ON expert_prediction_verification(is_correct, accuracy_score);

-- ================================================
-- ROW LEVEL SECURITY (RLS)
-- ================================================

-- Enable RLS on new tables
ALTER TABLE enhanced_game_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_play_by_play ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_drives ENABLE ROW LEVEL SECURITY;
ALTER TABLE coaching_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE special_teams_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE situational_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_prediction_verification ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for authenticated users, can be refined later)
CREATE POLICY "Allow all operations for authenticated users" ON enhanced_game_data
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON game_play_by_play
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON game_drives
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON coaching_decisions
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON special_teams_performance
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON situational_performance
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON expert_prediction_verification
    FOR ALL USING (auth.role() = 'authenticated');

-- ================================================
-- FUNCTIONS FOR DATA ANALYSIS
-- ================================================

-- Function: calculate_expert_comprehensive_accuracy
-- Calculates accuracy across all prediction dimensions using enhanced data
CREATE OR REPLACE FUNCTION calculate_expert_comprehensive_accuracy(
    p_expert_id VARCHAR(100),
    p_game_id VARCHAR(100)
)
RETURNS JSONB AS $$
DECLARE
    accuracy_result JSONB;
    total_predictions INTEGER := 0;
    correct_predictions INTEGER := 0;
    category_accuracies JSONB := '{}';
BEGIN
    -- Get all verifications for this expert and game
    SELECT
        json_build_object(
            'total_predictions', COUNT(*),
            'correct_predictions', COUNT(*) FILTER (WHERE is_correct = true),
            'overall_accuracy', COALESCE(AVG(accuracy_score), 0),
            'category_breakdown', json_object_agg(prediction_category, accuracy_score)
        )
    INTO accuracy_result
    FROM expert_prediction_verification
    WHERE expert_id = p_expert_id AND game_id = p_game_id;

    RETURN accuracy_result;
END;
$$ LANGUAGE plpgsql;

-- Function: get_game_coaching_advantage
-- Determines actual coaching advantage based on decision quality
CREATE OR REPLACE FUNCTION get_game_coaching_advantage(p_game_id VARCHAR(100))
RETURNS JSONB AS $$
DECLARE
    coaching_analysis JSONB;
BEGIN
    SELECT
        json_build_object(
            'home_coaching_score', AVG(CASE WHEN team = egd.home_team THEN decision_quality_score END),
            'away_coaching_score', AVG(CASE WHEN team = egd.away_team THEN decision_quality_score END),
            'advantage_team',
                CASE
                    WHEN AVG(CASE WHEN team = egd.home_team THEN decision_quality_score END) >
                         AVG(CASE WHEN team = egd.away_team THEN decision_quality_score END)
                    THEN egd.home_team
                    ELSE egd.away_team
                END,
            'decision_count', COUNT(*)
        )
    INTO coaching_analysis
    FROM coaching_decisions cd
    JOIN enhanced_game_data egd ON cd.game_id = egd.game_id
    WHERE cd.game_id = p_game_id;

    RETURN coaching_analysis;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ================================================

-- Update enhanced_game_data.updated_at on changes
CREATE OR REPLACE FUNCTION update_enhanced_game_data_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_enhanced_game_data_timestamp
    BEFORE UPDATE ON enhanced_game_data
    FOR EACH ROW EXECUTE FUNCTION update_enhanced_game_data_timestamp();

-- ================================================
-- COMMENTS
-- ================================================

COMMENT ON TABLE enhanced_game_data IS 'Comprehensive NFL game data from SportsData.io for expert prediction verification';
COMMENT ON TABLE game_play_by_play IS 'Individual play data for drive outcome and situational verification';
COMMENT ON TABLE game_drives IS 'Drive-level data for verifying drive outcome predictions';
COMMENT ON TABLE coaching_decisions IS 'Coaching decision quality data for coaching advantage verification';
COMMENT ON TABLE special_teams_performance IS 'Special teams metrics for special teams edge verification';
COMMENT ON TABLE situational_performance IS 'Situational performance data for clutch and momentum predictions';
COMMENT ON TABLE expert_prediction_verification IS 'Links expert predictions to actual outcomes with accuracy scores';