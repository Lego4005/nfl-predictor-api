-- NFL Historical Data Import Scripts
-- Run these in Supabase SQL Editor
-- Generated: 2025-01-17

-- ============================================
-- STEP 1: INSERT NFL TEAMS (32 teams)
-- ============================================

INSERT INTO nfl_teams (team_id, team_name, team_city, team_state, conference, division, team_color, team_color_secondary) VALUES
('ARI', 'Arizona Cardinals', 'Glendale', 'AZ', 'NFC', 'West', '#97233F', '#000000'),
('ATL', 'Atlanta Falcons', 'Atlanta', 'GA', 'NFC', 'South', '#A71930', '#000000'),
('BAL', 'Baltimore Ravens', 'Baltimore', 'MD', 'AFC', 'North', '#241773', '#9E7C0C'),
('BUF', 'Buffalo Bills', 'Buffalo', 'NY', 'AFC', 'East', '#00338D', '#C60C30'),
('CAR', 'Carolina Panthers', 'Charlotte', 'NC', 'NFC', 'South', '#0085CA', '#101820'),
('CHI', 'Chicago Bears', 'Chicago', 'IL', 'NFC', 'North', '#0B162A', '#C83803'),
('CIN', 'Cincinnati Bengals', 'Cincinnati', 'OH', 'AFC', 'North', '#FB4F14', '#000000'),
('CLE', 'Cleveland Browns', 'Cleveland', 'OH', 'AFC', 'North', '#311D00', '#FF3C00'),
('DAL', 'Dallas Cowboys', 'Dallas', 'TX', 'NFC', 'East', '#003594', '#869397'),
('DEN', 'Denver Broncos', 'Denver', 'CO', 'AFC', 'West', '#FB4F14', '#002244'),
('DET', 'Detroit Lions', 'Detroit', 'MI', 'NFC', 'North', '#0076B6', '#B0B7BC'),
('GB', 'Green Bay Packers', 'Green Bay', 'WI', 'NFC', 'North', '#203731', '#FFB612'),
('HOU', 'Houston Texans', 'Houston', 'TX', 'AFC', 'South', '#03202F', '#A71930'),
('IND', 'Indianapolis Colts', 'Indianapolis', 'IN', 'AFC', 'South', '#002C5F', '#A2AAAD'),
('JAX', 'Jacksonville Jaguars', 'Jacksonville', 'FL', 'AFC', 'South', '#101820', '#D7A22A'),
('KC', 'Kansas City Chiefs', 'Kansas City', 'MO', 'AFC', 'West', '#E31837', '#FFB81C'),
('LAC', 'Los Angeles Chargers', 'Los Angeles', 'CA', 'AFC', 'West', '#0080C6', '#FFC20E'),
('LAR', 'Los Angeles Rams', 'Los Angeles', 'CA', 'NFC', 'West', '#003594', '#FFA300'),
('LV', 'Las Vegas Raiders', 'Las Vegas', 'NV', 'AFC', 'West', '#000000', '#A5ACAF'),
('MIA', 'Miami Dolphins', 'Miami', 'FL', 'AFC', 'East', '#008E97', '#FC4C02'),
('MIN', 'Minnesota Vikings', 'Minneapolis', 'MN', 'NFC', 'North', '#4F2683', '#FFC62F'),
('NE', 'New England Patriots', 'Foxborough', 'MA', 'AFC', 'East', '#002244', '#C60C30'),
('NO', 'New Orleans Saints', 'New Orleans', 'LA', 'NFC', 'South', '#D3BC8D', '#101820'),
('NYG', 'New York Giants', 'East Rutherford', 'NJ', 'NFC', 'East', '#0B2265', '#A71930'),
('NYJ', 'New York Jets', 'East Rutherford', 'NJ', 'AFC', 'East', '#125740', '#FFFFFF'),
('PHI', 'Philadelphia Eagles', 'Philadelphia', 'PA', 'NFC', 'East', '#004C54', '#A5ACAF'),
('PIT', 'Pittsburgh Steelers', 'Pittsburgh', 'PA', 'AFC', 'North', '#FFB612', '#101820'),
('SEA', 'Seattle Seahawks', 'Seattle', 'WA', 'NFC', 'West', '#002244', '#69BE28'),
('SF', 'San Francisco 49ers', 'Santa Clara', 'CA', 'NFC', 'West', '#AA0000', '#B3995D'),
('TB', 'Tampa Bay Buccaneers', 'Tampa', 'FL', 'NFC', 'South', '#D50A0A', '#34302B'),
('TEN', 'Tennessee Titans', 'Nashville', 'TN', 'AFC', 'South', '#0C2340', '#4B92DB'),
('WAS', 'Washington Commanders', 'Landover', 'MD', 'NFC', 'East', '#5A1414', '#FFB612')
ON CONFLICT (team_id) DO UPDATE SET
  team_name = EXCLUDED.team_name,
  team_color = EXCLUDED.team_color,
  team_color_secondary = EXCLUDED.team_color_secondary;

-- ============================================
-- STEP 2: INSERT SAMPLE PLAYERS (Top QBs)
-- ============================================

INSERT INTO nfl_players (player_id, player_name, position, jersey_number, height_inches, weight_lbs, birth_date, college, draft_year, draft_round, draft_pick) VALUES
('00-0034796', 'Patrick Mahomes', 'QB', 15, 75, 230, '1995-09-17', 'Texas Tech', 2017, 1, 10),
('00-0033873', 'Josh Allen', 'QB', 17, 77, 237, '1996-05-21', 'Wyoming', 2018, 1, 7),
('00-0034855', 'Lamar Jackson', 'QB', 8, 74, 212, '1997-01-07', 'Louisville', 2018, 1, 32),
('00-0035228', 'Joe Burrow', 'QB', 9, 76, 221, '1996-12-10', 'LSU', 2020, 1, 1),
('00-0036355', 'Justin Herbert', 'QB', 10, 78, 236, '1998-03-10', 'Oregon', 2020, 1, 6),
('00-0031280', 'Dak Prescott', 'QB', 4, 74, 238, '1993-07-29', 'Mississippi State', 2016, 4, 135),
('00-0036442', 'Jalen Hurts', 'QB', 1, 73, 223, '1998-08-07', 'Oklahoma', 2020, 2, 53),
('00-0036212', 'Tua Tagovailoa', 'QB', 1, 73, 217, '1998-03-02', 'Alabama', 2020, 1, 5),
('00-0023459', 'Aaron Rodgers', 'QB', 8, 74, 225, '1983-12-02', 'California', 2005, 1, 24),
('00-0032950', 'Jared Goff', 'QB', 16, 76, 222, '1994-10-14', 'California', 2016, 1, 1),
-- Top RBs
('00-0034791', 'Christian McCaffrey', 'RB', 23, 71, 205, '1996-06-07', 'Stanford', 2017, 1, 8),
('00-0033857', 'Saquon Barkley', 'RB', 26, 72, 232, '1997-02-09', 'Penn State', 2018, 1, 2),
('00-0035676', 'Jonathan Taylor', 'RB', 28, 70, 226, '1999-01-19', 'Wisconsin', 2020, 2, 41),
('00-0033553', 'Derrick Henry', 'RB', 22, 75, 247, '1994-01-04', 'Alabama', 2016, 2, 45),
('00-0034790', 'Dalvin Cook', 'RB', 4, 70, 210, '1995-08-10', 'Florida State', 2017, 2, 41),
-- Top WRs
('00-0036322', 'Justin Jefferson', 'WR', 18, 73, 195, '1999-06-16', 'LSU', 2020, 1, 22),
('00-0034857', 'Tyreek Hill', 'WR', 10, 70, 185, '1994-03-01', 'West Alabama', 2016, 5, 165),
('00-0035682', 'CeeDee Lamb', 'WR', 88, 74, 198, '1999-04-08', 'Oklahoma', 2020, 1, 17),
('00-0035659', 'Ja''Marr Chase', 'WR', 1, 72, 201, '2000-03-01', 'LSU', 2021, 1, 5),
('00-0033283', 'Davante Adams', 'WR', 17, 73, 215, '1992-12-24', 'Fresno State', 2014, 2, 53)
ON CONFLICT (player_id) DO UPDATE SET
  player_name = EXCLUDED.player_name,
  position = EXCLUDED.position,
  jersey_number = EXCLUDED.jersey_number;

-- ============================================
-- STEP 3: INSERT SAMPLE GAMES (Recent games)
-- ============================================

-- Sample games from 2024 season Week 1
INSERT INTO nfl_games (game_id, season, week, game_type, game_date, home_team, away_team, home_score, away_score, stadium, weather_temperature, weather_description, attendance, overtime) VALUES
('2024_01_BAL_KC', 2024, 1, 'REG', '2024-09-05', 'KC', 'BAL', 27, 20, 'GEHA Field at Arrowhead Stadium', 78, 'Clear', 73426, false),
('2024_01_GB_PHI', 2024, 1, 'REG', '2024-09-06', 'PHI', 'GB', 34, 29, 'Lincoln Financial Field', 82, 'Partly Cloudy', 69879, false),
('2024_01_PIT_ATL', 2024, 1, 'REG', '2024-09-08', 'ATL', 'PIT', 10, 18, 'Mercedes-Benz Stadium', 72, 'Dome', 70512, false),
('2024_01_ARI_BUF', 2024, 1, 'REG', '2024-09-08', 'BUF', 'ARI', 34, 28, 'Highmark Stadium', 75, 'Clear', 70892, false),
('2024_01_TEN_CHI', 2024, 1, 'REG', '2024-09-08', 'CHI', 'TEN', 24, 17, 'Soldier Field', 68, 'Overcast', 61470, false),
('2024_01_NE_CIN', 2024, 1, 'REG', '2024-09-08', 'CIN', 'NE', 16, 10, 'Paycor Stadium', 79, 'Clear', 66483, false),
('2024_01_HOU_IND', 2024, 1, 'REG', '2024-09-08', 'IND', 'HOU', 27, 29, 'Lucas Oil Stadium', 72, 'Dome', 67059, false),
('2024_01_JAX_MIA', 2024, 1, 'REG', '2024-09-08', 'MIA', 'JAX', 20, 17, 'Hard Rock Stadium', 88, 'Humid', 64702, false),
('2024_01_CAR_NO', 2024, 1, 'REG', '2024-09-08', 'NO', 'CAR', 47, 10, 'Caesars Superdome', 73, 'Dome', 70021, false),
('2024_01_MIN_NYG', 2024, 1, 'REG', '2024-09-08', 'NYG', 'MIN', 6, 28, 'MetLife Stadium', 71, 'Clear', 79823, false),
('2024_01_LV_LAC', 2024, 1, 'REG', '2024-09-08', 'LAC', 'LV', 22, 10, 'SoFi Stadium', 75, 'Clear', 70240, false),
('2024_01_DEN_SEA', 2024, 1, 'REG', '2024-09-08', 'SEA', 'DEN', 26, 20, 'Lumen Field', 65, 'Overcast', 68516, false),
('2024_01_DAL_CLE', 2024, 1, 'REG', '2024-09-08', 'CLE', 'DAL', 33, 17, 'Cleveland Browns Stadium', 70, 'Clear', 67431, false),
('2024_01_WAS_TB', 2024, 1, 'REG', '2024-09-08', 'TB', 'WAS', 37, 20, 'Raymond James Stadium', 89, 'Hot', 65620, false),
('2024_01_LAR_DET', 2024, 1, 'REG', '2024-09-08', 'DET', 'LAR', 26, 20, 'Ford Field', 72, 'Dome', 64897, true),
('2024_01_NYJ_SF', 2024, 1, 'REG', '2024-09-09', 'SF', 'NYJ', 32, 19, 'Levi''s Stadium', 73, 'Clear', 71223, false)
ON CONFLICT (game_id) DO UPDATE SET
  home_score = EXCLUDED.home_score,
  away_score = EXCLUDED.away_score,
  attendance = EXCLUDED.attendance;

-- ============================================
-- STEP 4: INSERT SAMPLE PLAYS
-- ============================================

-- Sample plays from a game (simplified)
INSERT INTO nfl_plays (play_id, game_id, play_type, quarter, down, yards_to_go, yard_line, yards_gained, play_description, possession_team, defense_team, quarter_seconds_remaining) VALUES
('2024_01_BAL_KC_1', '2024_01_BAL_KC', 'kickoff', 1, NULL, NULL, 35, 25, 'Harrison Butker kicks off 65 yards, returned by Devin Duvernay for 25 yards', 'KC', 'BAL', 900),
('2024_01_BAL_KC_2', '2024_01_BAL_KC', 'pass', 1, 1, 10, 30, 8, 'Lamar Jackson pass short right to Mark Andrews for 8 yards', 'BAL', 'KC', 874),
('2024_01_BAL_KC_3', '2024_01_BAL_KC', 'run', 1, 2, 2, 38, 4, 'J.K. Dobbins run middle for 4 yards', 'BAL', 'KC', 832),
('2024_01_BAL_KC_4', '2024_01_BAL_KC', 'pass', 1, 1, 10, 42, 15, 'Lamar Jackson pass deep left to Rashod Bateman for 15 yards', 'BAL', 'KC', 790),
('2024_01_BAL_KC_5', '2024_01_BAL_KC', 'run', 1, 1, 10, 43, 2, 'Gus Edwards run left end for 2 yards', 'BAL', 'KC', 748),
('2024_01_BAL_KC_6', '2024_01_BAL_KC', 'pass', 1, 2, 8, 45, 12, 'Lamar Jackson pass middle to Zay Flowers for 12 yards', 'BAL', 'KC', 706),
('2024_01_BAL_KC_7', '2024_01_BAL_KC', 'pass', 1, 1, 10, 43, 0, 'Lamar Jackson pass incomplete deep right intended for Odell Beckham Jr.', 'BAL', 'KC', 664),
('2024_01_BAL_KC_8', '2024_01_BAL_KC', 'run', 1, 2, 10, 43, 7, 'J.K. Dobbins run right tackle for 7 yards', 'BAL', 'KC', 622),
('2024_01_BAL_KC_9', '2024_01_BAL_KC', 'pass', 1, 3, 3, 36, 18, 'Lamar Jackson pass deep middle to Mark Andrews for 18 yards', 'BAL', 'KC', 580),
('2024_01_BAL_KC_10', '2024_01_BAL_KC', 'field_goal', 1, 4, 2, 18, 0, 'Justin Tucker 35 yard field goal is GOOD', 'BAL', 'KC', 538)
ON CONFLICT (play_id) DO NOTHING;

-- ============================================
-- STEP 5: INSERT SAMPLE DRIVES
-- ============================================

INSERT INTO nfl_drives (drive_id, game_id, drive_number, possession_team, start_quarter, end_quarter, start_time, end_time, start_yard_line, end_yard_line, drive_result, drive_yards, drive_play_count) VALUES
('2024_01_BAL_KC_D1', '2024_01_BAL_KC', 1, 'BAL', 1, 1, '15:00', '9:00', 30, 18, 'Field Goal', 52, 10),
('2024_01_BAL_KC_D2', '2024_01_BAL_KC', 2, 'KC', 1, 1, '9:00', '4:30', 25, 45, 'Punt', 20, 6),
('2024_01_BAL_KC_D3', '2024_01_BAL_KC', 3, 'BAL', 1, 1, '4:30', '0:00', 15, 50, 'End of Quarter', 35, 8)
ON CONFLICT (drive_id) DO NOTHING;

-- ============================================
-- STEP 6: INSERT SAMPLE PLAYER STATS
-- ============================================

INSERT INTO nfl_player_stats_game (stat_id, player_id, game_id, team, passing_attempts, passing_completions, passing_yards, passing_tds, passing_ints, rushing_attempts, rushing_yards, rushing_tds) VALUES
('PS_2024_01_LJ', '00-0034855', '2024_01_BAL_KC', 'BAL', 41, 26, 273, 1, 0, 6, 45, 0),
('PS_2024_01_PM', '00-0034796', '2024_01_BAL_KC', 'KC', 39, 28, 291, 1, 1, 3, 12, 0)
ON CONFLICT (stat_id) DO UPDATE SET
  passing_yards = EXCLUDED.passing_yards,
  passing_tds = EXCLUDED.passing_tds;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Run these to verify data was imported:
/*
SELECT 'Teams' as table_name, COUNT(*) as count FROM nfl_teams
UNION ALL
SELECT 'Players', COUNT(*) FROM nfl_players
UNION ALL
SELECT 'Games', COUNT(*) FROM nfl_games
UNION ALL
SELECT 'Plays', COUNT(*) FROM nfl_plays
UNION ALL
SELECT 'Drives', COUNT(*) FROM nfl_drives
UNION ALL
SELECT 'Player Stats', COUNT(*) FROM nfl_player_stats_game;

-- Check some sample data
SELECT * FROM nfl_teams WHERE conference = 'NFC' AND division = 'East';
SELECT * FROM nfl_players WHERE position = 'QB' LIMIT 5;
SELECT * FROM nfl_games WHERE season = 2024 LIMIT 5;
*/