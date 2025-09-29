-- Migration: 001 - Create Betting and Data Ingestion Tables
-- Created: 2025-09-29
-- Description: Add missing tables for virtual betting system and real-time data ingestion

-- ============================================================================
-- BETTING SYSTEM TABLES
-- ============================================================================

-- Expert Virtual Bets: Track all bets placed by experts
CREATE TABLE IF NOT EXISTS expert_virtual_bets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id VARCHAR(50) NOT NULL REFERENCES expert_models(expert_id) ON DELETE CASCADE,
    game_id VARCHAR(100) NOT NULL,
    prediction_category VARCHAR(100) NOT NULL, -- 'spread', 'moneyline', 'total', 'prop'
    bet_amount NUMERIC(10,2) NOT NULL CHECK (bet_amount > 0),
    vegas_odds VARCHAR(20) NOT NULL, -- e.g., '-110', '+150', 'EVEN'
    prediction_confidence NUMERIC(5,2) NOT NULL CHECK (prediction_confidence >= 0 AND prediction_confidence <= 1),
    bet_placed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    result VARCHAR(20) DEFAULT 'pending' CHECK (result IN ('pending', 'won', 'lost', 'push', 'cancelled')),
    payout_amount NUMERIC(10,2), -- NULL until settled
    bankroll_before NUMERIC(10,2) NOT NULL,
    bankroll_after NUMERIC(10,2), -- NULL until settled
    reasoning TEXT, -- Why this bet was placed
    kelly_criterion_suggested NUMERIC(5,4), -- What Kelly Criterion recommended
    personality_adjustment NUMERIC(5,4), -- How personality modified the bet size
    edge_calculation NUMERIC(5,4), -- Calculated edge (prob - implied prob)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for betting queries
CREATE INDEX idx_virtual_bets_expert ON expert_virtual_bets(expert_id);
CREATE INDEX idx_virtual_bets_game ON expert_virtual_bets(game_id);
CREATE INDEX idx_virtual_bets_result ON expert_virtual_bets(result);
CREATE INDEX idx_virtual_bets_placed_at ON expert_virtual_bets(bet_placed_at DESC);
CREATE INDEX idx_virtual_bets_pending ON expert_virtual_bets(result) WHERE result = 'pending';

-- Composite index for common queries
CREATE INDEX idx_virtual_bets_expert_game ON expert_virtual_bets(expert_id, game_id);

COMMENT ON TABLE expert_virtual_bets IS 'All bets placed by AI experts with outcomes and analytics';
COMMENT ON COLUMN expert_virtual_bets.kelly_criterion_suggested IS 'Optimal bet size from Kelly Criterion (0-1 fraction of bankroll)';
COMMENT ON COLUMN expert_virtual_bets.personality_adjustment IS 'Personality-based adjustment factor applied to Kelly suggestion';
COMMENT ON COLUMN expert_virtual_bets.edge_calculation IS 'Calculated betting edge: true_probability - implied_probability';

-- ============================================================================
-- BETTING SYSTEM EXTENSIONS TO EXISTING TABLES
-- ============================================================================

-- Extend expert_virtual_bankrolls table with new columns
DO $$
BEGIN
    -- Add bets_placed JSONB to track quick bet summary
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'expert_virtual_bankrolls' AND column_name = 'bets_placed'
    ) THEN
        ALTER TABLE expert_virtual_bankrolls
        ADD COLUMN bets_placed JSONB DEFAULT '[]'::jsonb;
    END IF;

    -- Add season_status for tracking elimination
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'expert_virtual_bankrolls' AND column_name = 'season_status'
    ) THEN
        ALTER TABLE expert_virtual_bankrolls
        ADD COLUMN season_status VARCHAR(20) DEFAULT 'active' CHECK (season_status IN ('active', 'warning', 'danger', 'critical', 'eliminated'));
    END IF;

    -- Add elimination_date
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'expert_virtual_bankrolls' AND column_name = 'elimination_date'
    ) THEN
        ALTER TABLE expert_virtual_bankrolls
        ADD COLUMN elimination_date TIMESTAMP;
    END IF;

    -- Add risk_metrics JSONB for analytics
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'expert_virtual_bankrolls' AND column_name = 'risk_metrics'
    ) THEN
        ALTER TABLE expert_virtual_bankrolls
        ADD COLUMN risk_metrics JSONB DEFAULT '{}'::jsonb;
    END IF;

    -- Add elimination_risk_level for UI indicators
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'expert_virtual_bankrolls' AND column_name = 'elimination_risk_level'
    ) THEN
        ALTER TABLE expert_virtual_bankrolls
        ADD COLUMN elimination_risk_level VARCHAR(20) DEFAULT 'safe' CHECK (elimination_risk_level IN ('safe', 'at_risk', 'danger', 'critical'));
    END IF;
END $$;

COMMENT ON COLUMN expert_virtual_bankrolls.season_status IS 'Expert status: active, warning, danger, critical, eliminated';
COMMENT ON COLUMN expert_virtual_bankrolls.risk_metrics IS 'JSON: {volatility, sharpe_ratio, max_drawdown, win_streak, lose_streak}';
COMMENT ON COLUMN expert_virtual_bankrolls.elimination_risk_level IS 'UI-friendly risk indicator for frontend display';

-- ============================================================================
-- DATA INGESTION TABLES
-- ============================================================================

-- Weather Conditions: Real-time weather data for game predictions
CREATE TABLE IF NOT EXISTS weather_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id VARCHAR(100) NOT NULL,
    temperature NUMERIC(5,2), -- Fahrenheit
    wind_speed NUMERIC(5,2), -- MPH
    wind_direction VARCHAR(10), -- N, NE, E, SE, S, SW, W, NW
    precipitation NUMERIC(5,2), -- Inches
    humidity NUMERIC(5,2), -- Percentage
    conditions VARCHAR(100), -- 'Clear', 'Cloudy', 'Rain', 'Snow', etc.
    field_conditions VARCHAR(50), -- 'Dry', 'Wet', 'Muddy', 'Snow-covered'
    dome_stadium BOOLEAN DEFAULT false,
    forecast_confidence NUMERIC(3,2), -- 0-1 confidence in forecast accuracy
    data_source VARCHAR(50) NOT NULL, -- 'OpenWeatherMap', 'WeatherAPI', etc.
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    game_time TIMESTAMP, -- When game is scheduled
    hours_before_game INT, -- How far in advance this was fetched
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_weather_game ON weather_conditions(game_id);
CREATE INDEX idx_weather_fetched ON weather_conditions(fetched_at DESC);
CREATE INDEX idx_weather_game_time ON weather_conditions(game_time);

COMMENT ON TABLE weather_conditions IS 'Real-time weather data for NFL games from external APIs';
COMMENT ON COLUMN weather_conditions.forecast_confidence IS 'How confident the weather service is (closer to game = higher confidence)';

-- Vegas Lines: Real-time betting odds and line movements
CREATE TABLE IF NOT EXISTS vegas_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id VARCHAR(100) NOT NULL,
    sportsbook VARCHAR(50) NOT NULL, -- 'DraftKings', 'FanDuel', 'BetMGM', 'Caesars'
    spread NUMERIC(5,2), -- e.g., -3.5 for home team
    spread_odds_home VARCHAR(10), -- e.g., '-110'
    spread_odds_away VARCHAR(10),
    moneyline_home INT, -- e.g., -150
    moneyline_away INT, -- e.g., +130
    total NUMERIC(5,2), -- Over/Under points
    total_over_odds VARCHAR(10),
    total_under_odds VARCHAR(10),
    opening_spread NUMERIC(5,2), -- Opening line
    opening_total NUMERIC(5,2),
    line_movement NUMERIC(5,2), -- How much spread has moved
    sharp_money_indicator BOOLEAN DEFAULT false, -- True if sharp money detected
    public_bet_percentage_home NUMERIC(5,2), -- % of public bets on home team
    public_bet_percentage_away NUMERIC(5,2),
    money_percentage_home NUMERIC(5,2), -- % of money on home team (vs % of bets)
    data_source VARCHAR(50) NOT NULL, -- 'TheOddsAPI', 'ActionNetwork'
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vegas_game ON vegas_lines(game_id);
CREATE INDEX idx_vegas_book ON vegas_lines(sportsbook);
CREATE INDEX idx_vegas_fetched ON vegas_lines(fetched_at DESC);
CREATE INDEX idx_vegas_sharp_money ON vegas_lines(sharp_money_indicator) WHERE sharp_money_indicator = true;

-- Composite index for latest lines per game/book
CREATE INDEX idx_vegas_game_book_latest ON vegas_lines(game_id, sportsbook, fetched_at DESC);

COMMENT ON TABLE vegas_lines IS 'Real-time betting lines and odds from multiple sportsbooks';
COMMENT ON COLUMN vegas_lines.sharp_money_indicator IS 'True when line moves against public betting percentage (sharp money detected)';
COMMENT ON COLUMN vegas_lines.money_percentage_home IS 'Percentage of MONEY on home team (higher $ per bet = sharp bettors)';

-- Injury Reports: Real-time player injury status
CREATE TABLE IF NOT EXISTS injury_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_name VARCHAR(200) NOT NULL,
    player_id VARCHAR(50), -- NFL player ID if available
    team VARCHAR(10) NOT NULL,
    position VARCHAR(10),
    injury_status VARCHAR(50) NOT NULL, -- 'Out', 'Questionable', 'Doubtful', 'Probable', 'IR'
    injury_type VARCHAR(100), -- 'Knee', 'Hamstring', 'Concussion', etc.
    injury_details TEXT,
    game_id VARCHAR(100), -- Which game this affects
    practice_status VARCHAR(50), -- 'Full', 'Limited', 'DNP' (Did Not Practice)
    game_status VARCHAR(50), -- 'Active', 'Inactive', 'TBD'
    fantasy_impact VARCHAR(20), -- 'High', 'Medium', 'Low', 'None'
    reported_at TIMESTAMP NOT NULL,
    data_source VARCHAR(50) NOT NULL, -- 'ESPN', 'NFL.com', 'Twitter'
    source_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_injury_player ON injury_reports(player_name);
CREATE INDEX idx_injury_team ON injury_reports(team);
CREATE INDEX idx_injury_game ON injury_reports(game_id);
CREATE INDEX idx_injury_status ON injury_reports(injury_status);
CREATE INDEX idx_injury_reported ON injury_reports(reported_at DESC);

-- Composite index for latest injury status per player
CREATE INDEX idx_injury_player_latest ON injury_reports(player_name, reported_at DESC);

COMMENT ON TABLE injury_reports IS 'Real-time player injury reports and status updates';
COMMENT ON COLUMN injury_reports.fantasy_impact IS 'How much this injury impacts fantasy/betting (High = star player out)';

-- News Events: Breaking news and important updates
CREATE TABLE IF NOT EXISTS news_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- 'injury', 'trade', 'suspension', 'coaching_change', 'weather_alert'
    title VARCHAR(500) NOT NULL,
    content TEXT,
    affected_teams VARCHAR(10)[], -- Array of team codes
    affected_players VARCHAR(200)[], -- Array of player names
    affected_games VARCHAR(100)[], -- Array of game IDs
    importance_score NUMERIC(3,2) CHECK (importance_score >= 0 AND importance_score <= 1), -- 0-1 impact rating
    sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral'
    data_source VARCHAR(50) NOT NULL, -- 'ESPN', 'NFL.com', 'Twitter', 'Reddit'
    source_url TEXT,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_news_type ON news_events(event_type);
CREATE INDEX idx_news_teams ON news_events USING GIN (affected_teams);
CREATE INDEX idx_news_importance ON news_events(importance_score DESC);
CREATE INDEX idx_news_published ON news_events(published_at DESC);

COMMENT ON TABLE news_events IS 'Breaking news and important events affecting NFL games';
COMMENT ON COLUMN news_events.importance_score IS 'Impact rating 0-1: 1.0 = major impact (star QB out), 0.1 = minor news';

-- Social Sentiment: Public opinion and betting percentages
CREATE TABLE IF NOT EXISTS social_sentiment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id VARCHAR(100) NOT NULL,
    team VARCHAR(10) NOT NULL,
    platform VARCHAR(50) NOT NULL, -- 'Reddit', 'Twitter', 'Instagram'
    sentiment_score NUMERIC(5,2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1), -- -1 (very negative) to +1 (very positive)
    mention_count INT NOT NULL DEFAULT 0,
    positive_mentions INT DEFAULT 0,
    negative_mentions INT DEFAULT 0,
    neutral_mentions INT DEFAULT 0,
    public_bet_percentage NUMERIC(5,2), -- % of public betting on this team
    trending BOOLEAN DEFAULT false, -- Is this team trending on social media?
    top_keywords TEXT[], -- Most mentioned keywords
    sample_comments TEXT[], -- Sample comments for context
    data_source VARCHAR(50) NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sentiment_game ON social_sentiment(game_id);
CREATE INDEX idx_sentiment_team ON social_sentiment(team);
CREATE INDEX idx_sentiment_platform ON social_sentiment(platform);
CREATE INDEX idx_sentiment_trending ON social_sentiment(trending) WHERE trending = true;
CREATE INDEX idx_sentiment_fetched ON social_sentiment(fetched_at DESC);

-- Composite index for latest sentiment per game/team
CREATE INDEX idx_sentiment_game_team_latest ON social_sentiment(game_id, team, fetched_at DESC);

COMMENT ON TABLE social_sentiment IS 'Public sentiment analysis from social media and betting trends';
COMMENT ON COLUMN social_sentiment.sentiment_score IS 'Aggregate sentiment: -1 (very negative) to +1 (very positive)';
COMMENT ON COLUMN social_sentiment.trending IS 'True if team is trending on social media (unusual mention volume)';

-- Advanced Stats: Historical and advanced analytics
CREATE TABLE IF NOT EXISTS advanced_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team VARCHAR(10) NOT NULL,
    season INT NOT NULL,
    week INT,
    stat_type VARCHAR(50) NOT NULL, -- 'EPA', 'CPOE', 'DVOA', 'success_rate', 'explosive_play_rate'
    stat_value NUMERIC(10,4) NOT NULL,
    stat_rank INT, -- Rank among all teams (1 = best)
    opponent VARCHAR(10), -- If stat is for specific matchup
    split_type VARCHAR(50), -- 'overall', 'home', 'away', 'vs_division', 'last_3_games'
    data_source VARCHAR(50) NOT NULL, -- 'nflfastR', 'PFR', 'FootballOutsiders'
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stats_team ON advanced_stats(team);
CREATE INDEX idx_stats_season_week ON advanced_stats(season, week);
CREATE INDEX idx_stats_type ON advanced_stats(stat_type);
CREATE INDEX idx_stats_team_season ON advanced_stats(team, season);

COMMENT ON TABLE advanced_stats IS 'Advanced analytics from nflfastR, PFR, Football Outsiders';
COMMENT ON COLUMN advanced_stats.stat_type IS 'EPA=Expected Points Added, CPOE=Completion % Over Expected, DVOA=Defense-adjusted Value Over Average';

-- ============================================================================
-- DATA QUALITY MONITORING
-- ============================================================================

-- Data Freshness Monitor: Track when data sources were last updated
CREATE TABLE IF NOT EXISTS data_freshness_monitor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source VARCHAR(50) NOT NULL UNIQUE, -- 'weather', 'odds', 'injuries', 'sentiment', 'stats'
    last_successful_fetch TIMESTAMP,
    last_attempted_fetch TIMESTAMP,
    fetch_status VARCHAR(20) NOT NULL CHECK (fetch_status IN ('success', 'failure', 'timeout', 'rate_limited')),
    error_message TEXT,
    records_fetched INT DEFAULT 0,
    fetch_duration_ms INT, -- How long the fetch took
    next_scheduled_fetch TIMESTAMP,
    consecutive_failures INT DEFAULT 0,
    is_healthy BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_freshness_source ON data_freshness_monitor(data_source);
CREATE INDEX idx_freshness_healthy ON data_freshness_monitor(is_healthy);

COMMENT ON TABLE data_freshness_monitor IS 'Track data source health and freshness for monitoring';
COMMENT ON COLUMN data_freshness_monitor.is_healthy IS 'False if source has failed multiple times or data is too stale';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to automatically update elimination_risk_level based on current_balance
CREATE OR REPLACE FUNCTION update_elimination_risk_level()
RETURNS TRIGGER AS $$
BEGIN
    -- Update risk level based on current balance percentage
    IF NEW.current_balance <= 0 THEN
        NEW.season_status := 'eliminated';
        NEW.elimination_risk_level := 'critical';
        NEW.elimination_date := NOW();
    ELSIF NEW.current_balance < (NEW.starting_balance * 0.20) THEN
        NEW.elimination_risk_level := 'critical'; -- < 20% of starting
        IF NEW.season_status = 'active' THEN
            NEW.season_status := 'critical';
        END IF;
    ELSIF NEW.current_balance < (NEW.starting_balance * 0.40) THEN
        NEW.elimination_risk_level := 'danger'; -- 20-40% of starting
        IF NEW.season_status = 'active' THEN
            NEW.season_status := 'danger';
        END IF;
    ELSIF NEW.current_balance < (NEW.starting_balance * 0.70) THEN
        NEW.elimination_risk_level := 'at_risk'; -- 40-70% of starting
        IF NEW.season_status = 'active' THEN
            NEW.season_status := 'warning';
        END IF;
    ELSE
        NEW.elimination_risk_level := 'safe'; -- >= 70% of starting
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update risk level when balance changes
DROP TRIGGER IF EXISTS trigger_update_elimination_risk ON expert_virtual_bankrolls;
CREATE TRIGGER trigger_update_elimination_risk
    BEFORE UPDATE OF current_balance ON expert_virtual_bankrolls
    FOR EACH ROW
    EXECUTE FUNCTION update_elimination_risk_level();

-- Function to calculate bet payout from Vegas odds
CREATE OR REPLACE FUNCTION calculate_payout(
    bet_amount NUMERIC,
    vegas_odds VARCHAR,
    result VARCHAR
) RETURNS NUMERIC AS $$
DECLARE
    odds_value INT;
    payout NUMERIC;
BEGIN
    -- Only calculate payout for won bets
    IF result != 'won' THEN
        RETURN 0;
    END IF;

    -- Remove '+' or '-' and convert to integer
    odds_value := CAST(REPLACE(REPLACE(vegas_odds, '+', ''), '-', '') AS INT);

    -- Calculate payout based on American odds
    IF vegas_odds LIKE '+%' THEN
        -- Positive odds: profit = (bet_amount * odds / 100)
        payout := bet_amount + (bet_amount * odds_value / 100.0);
    ELSIF vegas_odds LIKE '-%' THEN
        -- Negative odds: profit = (bet_amount * 100 / odds)
        payout := bet_amount + (bet_amount * 100.0 / odds_value);
    ELSIF vegas_odds = 'EVEN' THEN
        -- Even odds: profit = bet_amount
        payout := bet_amount * 2;
    ELSE
        -- Unknown format, return bet amount
        payout := bet_amount;
    END IF;

    RETURN ROUND(payout, 2);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_payout IS 'Calculate payout from American odds format (+150, -110, EVEN)';

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Initialize data freshness monitor for all sources
INSERT INTO data_freshness_monitor (data_source, fetch_status, is_healthy)
VALUES
    ('weather', 'success', true),
    ('odds', 'success', true),
    ('injuries', 'success', true),
    ('sentiment', 'success', true),
    ('stats', 'success', true),
    ('news', 'success', true)
ON CONFLICT (data_source) DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================