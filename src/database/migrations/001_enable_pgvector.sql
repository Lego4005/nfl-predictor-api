-- Enable pgvector extension for vector similarity search
-- This migration enables vector database capabilities for semantic search
-- on news articles, expert research, and prediction analysis

-- Enable the pgvector extension
create extension if not exists vector with schema extensions;

-- Add vector columns to existing tables for semantic search capabilities

-- 1. News articles semantic search
alter table news_articles add column if not exists embedding vector(384);
alter table news_articles add column if not exists embedding_updated_at timestamp with time zone;

-- 2. Expert research data vectorization
create table if not exists expert_research (
  id bigint primary key generated always as identity,
  expert_id varchar(50) not null,
  research_type varchar(100) not null, -- 'news', 'stats', 'weather', 'betting_trends', etc.
  content text not null,
  metadata jsonb default '{}',
  embedding vector(384),
  relevance_score float default 0,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 3. Prediction analysis embeddings
alter table predictions add column if not exists analysis_embedding vector(384);
alter table predictions add column if not exists reasoning_text text;

-- 4. Expert betting history with semantic analysis
create table if not exists expert_bets (
  id bigint primary key generated always as identity,
  expert_id varchar(50) not null,
  game_id bigint references games(id),
  bet_type varchar(50) not null, -- 'spread', 'total', 'moneyline', 'prop'
  bet_value decimal(10,2),
  confidence_level integer check (confidence_level between 1 and 100),
  reasoning text,
  reasoning_embedding vector(384),
  points_wagered integer default 0,
  points_won integer default 0,
  is_winner boolean,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 5. Research knowledge base for expert strategies
create table if not exists knowledge_base (
  id bigint primary key generated always as identity,
  category varchar(100) not null, -- 'team_stats', 'player_injury', 'weather_impact', etc.
  title text not null,
  content text not null,
  source_url text,
  embedding vector(384),
  trust_score integer default 50 check (trust_score between 0 and 100),
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Create HNSW indexes for efficient vector similarity search
create index if not exists news_articles_embedding_idx on news_articles
using hnsw (embedding vector_cosine_ops);

create index if not exists expert_research_embedding_idx on expert_research
using hnsw (embedding vector_cosine_ops);

create index if not exists predictions_analysis_embedding_idx on predictions
using hnsw (analysis_embedding vector_cosine_ops);

create index if not exists expert_bets_reasoning_embedding_idx on expert_bets
using hnsw (reasoning_embedding vector_cosine_ops);

create index if not exists knowledge_base_embedding_idx on knowledge_base
using hnsw (embedding vector_cosine_ops);

-- Enable Row Level Security on new tables
alter table expert_research enable row level security;
alter table expert_bets enable row level security;
alter table knowledge_base enable row level security;

-- Create RLS policies (allow all for now, can be restricted later)
create policy "Enable all access for expert_research" on expert_research for all using (true);
create policy "Enable all access for expert_bets" on expert_bets for all using (true);
create policy "Enable all access for knowledge_base" on knowledge_base for all using (true);

-- Add tables to realtime publication for live updates
alter publication supabase_realtime add table expert_research;
alter publication supabase_realtime add table expert_bets;
alter publication supabase_realtime add table knowledge_base;