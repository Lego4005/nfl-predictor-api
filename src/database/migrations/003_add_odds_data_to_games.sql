-- Add odds_data column to games table for storing consensus odds
-- This migration adds the odds_data JSONB column to store aggregated odds data

alter table games add column if not exists odds_data jsonb default '{}';

-- Add index for odds_data queries
create index if not exists games_odds_data_idx on games using gin(odds_data);

-- Add comment to document the structure
comment on column games.odds_data is 'JSONB field storing consensus odds data structure: {
  "consensus_spread": number,
  "consensus_total": number,
  "consensus_ml_home": number,
  "consensus_ml_away": number,
  "bookmaker_count": number,
  "last_updated": "ISO timestamp"
}';