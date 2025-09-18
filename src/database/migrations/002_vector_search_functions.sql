-- Vector search functions for semantic similarity queries
-- These functions enable intelligent expert research strategies

-- 1. Search knowledge base for relevant information
create or replace function search_knowledge_base(
  query_embedding vector(384),
  match_threshold float default 0.8,
  match_count int default 5,
  category_filter text default null
)
returns table (
  id bigint,
  category text,
  title text,
  content text,
  source_url text,
  trust_score int,
  similarity float
)
language sql stable
as $$
  select
    k.id,
    k.category,
    k.title,
    k.content,
    k.source_url,
    k.trust_score,
    1 - (k.embedding <=> query_embedding) as similarity
  from knowledge_base k
  where 1 - (k.embedding <=> query_embedding) > match_threshold
    and (category_filter is null or k.category = category_filter)
  order by k.embedding <=> query_embedding
  limit match_count;
$$;

-- 2. Search expert research data
create or replace function search_expert_research(
  query_embedding vector(384),
  match_threshold float default 0.8,
  match_count int default 10,
  expert_id_filter text default null,
  research_type_filter text default null
)
returns table (
  id bigint,
  expert_id text,
  research_type text,
  content text,
  metadata jsonb,
  relevance_score float,
  similarity float
)
language sql stable
as $$
  select
    r.id,
    r.expert_id,
    r.research_type,
    r.content,
    r.metadata,
    r.relevance_score,
    1 - (r.embedding <=> query_embedding) as similarity
  from expert_research r
  where 1 - (r.embedding <=> query_embedding) > match_threshold
    and (expert_id_filter is null or r.expert_id = expert_id_filter)
    and (research_type_filter is null or r.research_type = research_type_filter)
  order by r.embedding <=> query_embedding
  limit match_count;
$$;

-- 3. Search news articles for relevant information
create or replace function search_news_articles(
  query_embedding vector(384),
  match_threshold float default 0.8,
  match_count int default 5
)
returns table (
  id bigint,
  title text,
  content text,
  url text,
  published_at timestamp with time zone,
  sentiment_score float,
  team_mentions text[],
  similarity float
)
language sql stable
as $$
  select
    n.id,
    n.title,
    n.content,
    n.url,
    n.published_at,
    n.sentiment_score,
    n.team_mentions,
    1 - (n.embedding <=> query_embedding) as similarity
  from news_articles n
  where n.embedding is not null
    and 1 - (n.embedding <=> query_embedding) > match_threshold
  order by n.embedding <=> query_embedding
  limit match_count;
$$;

-- 4. Find similar expert betting patterns
create or replace function search_similar_bets(
  query_embedding vector(384),
  match_threshold float default 0.8,
  match_count int default 10,
  expert_id_filter text default null,
  only_winners boolean default false
)
returns table (
  id bigint,
  expert_id text,
  bet_type text,
  bet_value decimal(10,2),
  confidence_level int,
  reasoning text,
  points_won int,
  is_winner boolean,
  similarity float
)
language sql stable
as $$
  select
    b.id,
    b.expert_id,
    b.bet_type,
    b.bet_value,
    b.confidence_level,
    b.reasoning,
    b.points_won,
    b.is_winner,
    1 - (b.reasoning_embedding <=> query_embedding) as similarity
  from expert_bets b
  where b.reasoning_embedding is not null
    and 1 - (b.reasoning_embedding <=> query_embedding) > match_threshold
    and (expert_id_filter is null or b.expert_id = expert_id_filter)
    and (not only_winners or b.is_winner = true)
  order by b.reasoning_embedding <=> query_embedding
  limit match_count;
$$;

-- 5. Search prediction analysis for similar reasoning
create or replace function search_prediction_analysis(
  query_embedding vector(384),
  match_threshold float default 0.8,
  match_count int default 5
)
returns table (
  id bigint,
  game_id bigint,
  model_version text,
  reasoning_text text,
  confidence int,
  home_win_prob float,
  similarity float
)
language sql stable
as $$
  select
    p.id,
    p.game_id,
    p.model_version,
    p.reasoning_text,
    p.confidence,
    p.home_win_prob,
    1 - (p.analysis_embedding <=> query_embedding) as similarity
  from predictions p
  where p.analysis_embedding is not null
    and 1 - (p.analysis_embedding <=> query_embedding) > match_threshold
  order by p.analysis_embedding <=> query_embedding
  limit match_count;
$$;

-- 6. Multi-category semantic search across all tables
create or replace function search_all_content(
  query_embedding vector(384),
  match_threshold float default 0.8,
  match_count int default 20
)
returns table (
  source_table text,
  id bigint,
  title text,
  content text,
  metadata jsonb,
  similarity float,
  created_at timestamp with time zone
)
language sql stable
as $$
  -- Search knowledge base
  select
    'knowledge_base' as source_table,
    k.id,
    k.title,
    k.content,
    jsonb_build_object('category', k.category, 'trust_score', k.trust_score, 'source_url', k.source_url) as metadata,
    1 - (k.embedding <=> query_embedding) as similarity,
    k.created_at
  from knowledge_base k
  where k.embedding is not null
    and 1 - (k.embedding <=> query_embedding) > match_threshold

  union all

  -- Search expert research
  select
    'expert_research' as source_table,
    r.id,
    r.research_type as title,
    r.content,
    jsonb_build_object('expert_id', r.expert_id, 'research_type', r.research_type) || r.metadata as metadata,
    1 - (r.embedding <=> query_embedding) as similarity,
    r.created_at
  from expert_research r
  where r.embedding is not null
    and 1 - (r.embedding <=> query_embedding) > match_threshold

  union all

  -- Search news articles
  select
    'news_articles' as source_table,
    n.id,
    n.title,
    n.content,
    jsonb_build_object('sentiment_score', n.sentiment_score, 'url', n.url, 'team_mentions', n.team_mentions) as metadata,
    1 - (n.embedding <=> query_embedding) as similarity,
    n.created_at
  from news_articles n
  where n.embedding is not null
    and 1 - (n.embedding <=> query_embedding) > match_threshold

  order by similarity desc
  limit match_count;
$$;

-- 7. Helper function to generate text embedding (placeholder for Edge Function)
create or replace function generate_embedding_placeholder(input_text text)
returns vector(384)
language sql
as $$
  -- This is a placeholder function that returns a zero vector
  -- The actual embedding generation will be handled by Edge Functions
  select array_fill(0.0, array[384])::vector(384);
$$;