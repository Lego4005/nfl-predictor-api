-- Summary statistics function for historical player stats
-- This function provides quick insights into the uploaded data

CREATE OR REPLACE FUNCTION get_player_stats_summary()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    WITH stats AS (
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT player_id) as unique_players,
            COUNT(DISTINCT team) as unique_teams,
            COUNT(DISTINCT position) as unique_positions,
            MIN(season) as earliest_season,
            MAX(season) as latest_season,
            MIN(week) as min_week,
            MAX(week) as max_week,
            COUNT(DISTINCT CONCAT(season, '-', week)) as unique_game_weeks
        FROM historical_player_stats
    ),
    position_counts AS (
        SELECT 
            position,
            COUNT(*) as record_count,
            COUNT(DISTINCT player_id) as unique_players
        FROM historical_player_stats
        GROUP BY position
        ORDER BY record_count DESC
    ),
    top_players AS (
        SELECT 
            player_name,
            position,
            team,
            COUNT(*) as games_recorded,
            ROUND(AVG(CASE WHEN position = 'QB' THEN passing_yards ELSE 0 END), 1) as avg_passing_yards,
            ROUND(AVG(CASE WHEN position IN ('RB', 'WR', 'TE') THEN receiving_yards ELSE 0 END), 1) as avg_receiving_yards,
            ROUND(AVG(CASE WHEN position = 'RB' THEN rushing_yards ELSE 0 END), 1) as avg_rushing_yards
        FROM historical_player_stats
        GROUP BY player_name, position, team
        HAVING COUNT(*) >= 5
        ORDER BY games_recorded DESC
        LIMIT 10
    )
    SELECT json_build_object(
        'summary', (SELECT row_to_json(s) FROM stats s),
        'position_breakdown', (
            SELECT json_agg(row_to_json(pc))
            FROM position_counts pc
        ),
        'top_players_by_games', (
            SELECT json_agg(row_to_json(tp))
            FROM top_players tp
        )
    ) INTO result;
    
    RETURN result;
END;
$$;