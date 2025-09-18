-- Create base tables for NFL predictor platform
-- This migration creates the fundamental tables needed for the application

-- 1. Teams table - NFL teams information
create table if not exists teams (
  id bigint primary key generated always as identity,
  abbreviation varchar(3) not null unique,
  name varchar(100) not null,
  city varchar(100) not null,
  full_name varchar(200) not null,
  conference varchar(3) not null check (conference in ('AFC', 'NFC')),
  division varchar(10) not null,
  primary_color varchar(7),
  secondary_color varchar(7),
  tertiary_color varchar(7),
  logo_url text,
  gradient text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 2. Games table - NFL games information
create table if not exists games (
  id bigint primary key generated always as identity,
  espn_game_id varchar(50) unique,
  home_team varchar(3) references teams(abbreviation),
  away_team varchar(3) references teams(abbreviation),
  home_score integer,
  away_score integer,
  game_time timestamp with time zone not null,
  week integer,
  season integer,
  venue text,
  status varchar(20) default 'scheduled',
  weather jsonb,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 3. Predictions table - AI model predictions
create table if not exists predictions (
  id bigint primary key generated always as identity,
  game_id bigint references games(id),
  model_name varchar(100) not null,
  prediction_type varchar(50) not null, -- 'spread', 'total', 'moneyline'
  predicted_value decimal(10,2),
  confidence_score decimal(5,4) check (confidence_score between 0 and 1),
  reasoning text,
  metadata jsonb default '{}',
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 4. News articles table - NFL news and analysis
create table if not exists news_articles (
  id bigint primary key generated always as identity,
  title text not null,
  content text not null,
  author varchar(200),
  source varchar(100),
  published_at timestamp with time zone,
  url text unique,
  teams_mentioned varchar(3)[] default '{}',
  sentiment_score decimal(3,2) check (sentiment_score between -1 and 1),
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 5. Odds history table - betting odds tracking
create table if not exists odds_history (
  id bigint primary key generated always as identity,
  game_id bigint references games(id),
  sportsbook varchar(50) not null,
  bet_type varchar(50) not null,
  odds_value decimal(10,2),
  line_value decimal(10,2),
  recorded_at timestamp with time zone default now(),
  created_at timestamp with time zone default now()
);

-- 6. User picks table - user predictions/picks
create table if not exists user_picks (
  id bigint primary key generated always as identity,
  user_id uuid references auth.users(id),
  game_id bigint references games(id),
  pick_type varchar(50) not null,
  pick_value decimal(10,2),
  confidence_level integer check (confidence_level between 1 and 100),
  points_wagered integer default 0,
  is_winner boolean,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 7. User stats table - user performance tracking
create table if not exists user_stats (
  id bigint primary key generated always as identity,
  user_id uuid references auth.users(id) unique,
  total_picks integer default 0,
  correct_picks integer default 0,
  win_percentage decimal(5,4) default 0,
  total_points integer default 0,
  current_streak integer default 0,
  best_streak integer default 0,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 8. News sentiment table - sentiment analysis of news
create table if not exists news_sentiment (
  id bigint primary key generated always as identity,
  article_id bigint references news_articles(id),
  teams_mentioned varchar(3)[] default '{}',
  sentiment_score decimal(3,2) check (sentiment_score between -1 and 1),
  keywords text[] default '{}',
  published_at timestamp with time zone,
  created_at timestamp with time zone default now()
);

-- 9. Model performance table - tracking AI model accuracy
create table if not exists model_performance (
  id bigint primary key generated always as identity,
  model_name varchar(100) not null,
  prediction_type varchar(50) not null,
  total_predictions integer default 0,
  correct_predictions integer default 0,
  accuracy_percentage decimal(5,4) default 0,
  avg_confidence decimal(5,4) default 0,
  evaluation_date date not null,
  created_at timestamp with time zone default now()
);

-- Create indexes for better query performance
create index if not exists games_game_time_idx on games(game_time);
create index if not exists games_status_idx on games(status);
create index if not exists games_teams_idx on games(home_team, away_team);
create index if not exists games_season_week_idx on games(season, week);

create index if not exists predictions_game_id_idx on predictions(game_id);
create index if not exists predictions_model_name_idx on predictions(model_name);

create index if not exists odds_history_game_id_idx on odds_history(game_id);
create index if not exists odds_history_recorded_at_idx on odds_history(recorded_at);

create index if not exists news_articles_published_at_idx on news_articles(published_at);
create index if not exists news_articles_teams_mentioned_idx on news_articles using gin(teams_mentioned);

create index if not exists user_picks_user_id_idx on user_picks(user_id);
create index if not exists user_picks_game_id_idx on user_picks(game_id);

-- Enable Row Level Security
alter table teams enable row level security;
alter table games enable row level security;
alter table predictions enable row level security;
alter table news_articles enable row level security;
alter table odds_history enable row level security;
alter table user_picks enable row level security;
alter table user_stats enable row level security;
alter table news_sentiment enable row level security;
alter table model_performance enable row level security;

-- Create RLS policies (allow read access for all, can be restricted later)
create policy "Enable read access for teams" on teams for select using (true);
create policy "Enable read access for games" on games for select using (true);
create policy "Enable read access for predictions" on predictions for select using (true);
create policy "Enable read access for news_articles" on news_articles for select using (true);
create policy "Enable read access for odds_history" on odds_history for select using (true);
create policy "Enable read access for news_sentiment" on news_sentiment for select using (true);
create policy "Enable read access for model_performance" on model_performance for select using (true);

-- User-specific policies for user_picks and user_stats
create policy "Users can manage their own picks" on user_picks for all using (auth.uid() = user_id);
create policy "Users can read their own stats" on user_stats for select using (auth.uid() = user_id);

-- Add tables to realtime publication for live updates
alter publication supabase_realtime add table games;
alter publication supabase_realtime add table predictions;
alter publication supabase_realtime add table odds_history;
alter publication supabase_realtime add table user_picks;
alter publication supabase_realtime add table news_sentiment;