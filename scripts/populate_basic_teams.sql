-- Populate basic NFL teams for foreign key constraints
-- This matches the minimal structure needed for nfl_games table

INSERT INTO nfl_teams (team_id) VALUES 
  ('ARI'), ('ATL'), ('BAL'), ('BUF'), ('CAR'), ('CHI'), ('CIN'), ('CLE'),
  ('DAL'), ('DEN'), ('DET'), ('GB'), ('HOU'), ('IND'), ('JAX'), ('KC'),
  ('LAC'), ('LAR'), ('LV'), ('MIA'), ('MIN'), ('NE'), ('NO'), ('NYG'),
  ('NYJ'), ('PHI'), ('PIT'), ('SEA'), ('SF'), ('TB'), ('TEN'), ('WAS'),
  
  -- Historical teams for older games
  ('OAK'), ('SD'), ('STL')
ON CONFLICT (team_id) DO NOTHING;