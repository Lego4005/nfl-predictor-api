-- Add missing historical NFL teams for data loading
-- These teams are needed for foreign key constraints

INSERT INTO nfl_teams (team_id) VALUES 
  ('LA'),   -- Los Angeles Rams (historical)
  ('OAK'),  -- Oakland Raiders (historical) 
  ('SD'),   -- San Diego Chargers (historical)
  ('STL')   -- St. Louis Rams (historical)
ON CONFLICT (team_id) DO NOTHING;

-- Verify all teams exist
SELECT COUNT(*) as total_teams FROM nfl_teams;