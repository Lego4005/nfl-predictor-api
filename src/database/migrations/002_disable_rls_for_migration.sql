-- Disable RLS for public data tables to allow migration
-- This allows anonymous users to read public NFL data

-- Teams table - public data
alter table if exists public.teams disable row level security;

-- Games table - public data
alter table if exists public.games disable row level security;

-- Predictions table - public read access
alter table if exists public.predictions disable row level security;

-- Odds history - public read access
alter table if exists public.odds_history disable row level security;

-- Weather data - public read access
alter table if exists public.weather_data disable row level security;

-- News sentiment - public read access
alter table if exists public.news_sentiment disable row level security;

-- Model performance - public read access
alter table if exists public.model_performance disable row level security;

-- Expert research - public read access for viewing research
alter table if exists public.expert_research disable row level security;

-- Expert bets - public read access for viewing bets
alter table if exists public.expert_bets disable row level security;

-- Knowledge base - public read access
alter table if exists public.knowledge_base disable row level security;

-- Venues - public data
alter table if exists public.venues disable row level security;

-- Injury reports - public data
alter table if exists public.injury_reports disable row level security;

-- Keep RLS enabled for user-specific tables (these will need proper policies later)
-- alter table if exists public.user_picks enable row level security;
-- alter table if exists public.user_stats enable row level security;

-- Note: In production, you should create proper RLS policies instead of disabling RLS
-- For example:
-- create policy "Public read access" on public.teams for select using (true);
-- create policy "Service role insert" on public.teams for insert using (auth.role() = 'service_role');