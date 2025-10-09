-- === pgvector
create extension if not exists vector;

-- === TEAM KNOWLEDGE (FKs + HNSW)
create table if not exists team_knowledge (
    id uuid primary key default gen_random_uuid(),
    expert_id varchar(50) not null,
    team_id text not null,
    overall_assessment text,
    strengths text[],
    weaknesses text[],
    key_patterns jsonb,
    games_analyzed int default 0,
    predictions_made int default 0,
    predictions_correct int default 0,
    accuracy numeric(5,4),
    home_performance jsonb,
    away_performance jsonb,
    weather_impact jsonb,
    knowledge_embedding vector(1536),
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique(expert_id, team_id)
);

create index if not exists idx_tk_expert on team_knowledge(expert_id);
create index if not exists idx_tk_team   on team_knowledge(team_id);
create index if not exists idx_tk_hnsw   on team_knowledge using hnsw (knowledge_embedding vector_cosine_ops);

-- Strongly recommended if you have `teams(team_id)`:
do $$
begin
    if exists (select 1 from information_schema.tables where table_name='teams') then
        alter table team_knowledge
        drop constraint if exists fk_tk_team,
        add  constraint fk_tk_team foreign key (team_id) references teams(team_id) on delete cascade;
    end if;
end$$;

-- === MATCHUP MEMORIES (role-aware + sorted key + HNSW)
create table if not exists matchup_memories (
    id uuid primary key default gen_random_uuid(),
    expert_id varchar(50) not null,
    home_team text not null,
    away_team text not null,
    matchup_key_sorted text generated always as (
        case when home_team < away_team
        then home_team||'|'||away_team
        else away_team||'|'||home_team end
    ) stored,
    games_analyzed int default 0,
    predictions_made int default 0,
    predictions_correct int default 0,
    accuracy numeric(5,4),
    typical_margin numeric(5,2),
    scoring_pattern text,
    key_factors text[],
    matchup_embedding vector(1536),
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    constraint ux_mm_role unique (expert_id, home_team, away_team)
);

create index if not exists idx_mm_expert on matchup_memories(expert_id);
create index if not exists idx_mm_sorted on matchup_memories(expert_id, matchup_key_sorted);
create index if not exists idx_mm_hnsw   on matchup_memories using hnsw (matchup_embedding vector_cosine_ops);

do $$
begin
    if exists (select 1 from information_schema.tables where table_name='teams') then
        alter table matchup_memories
        drop constraint if exists fk_mm_home,
        drop constraint if exists fk_mm_away,
        add  constraint fk_mm_home foreign key (home_team) references teams(team_id) on delete cascade,
        add  constraint fk_mm_away foreign key (away_team) references teams(team_id) on delete cascade;
    end if;
end$$;

-- === COMPAT VIEW (optional): emulate expert_memory_embeddings without duplication
create or replace view expert_memory_embeddings as
select
    memory_id,
    expert_id,
    combined_embedding as memory_embedding,
    array[home_team, away_team]::text[] as teams_involved,
    null::text as memory_summary,
    memory_type
from expert_episodic_memories
where combined_embedding is not null;

-- === RECENCY-AWARE VECTOR SEARCH (alpha blend)
create or replace function search_expert_memories(
    p_expert_id text,
    p_query_embedding vector(1536),
    p_match_threshold float default 0.7,
    p_match_count int default 10,
    p_alpha float default 0.8
)
returns table (
    memory_id text,
    expert_id text,
    game_id text,
    home_team text,
    away_team text,
    game_date date,
    similarity_score float,
    recency_score float,
    combined_score float
)
language plpgsql as $$
begin
    return query
    select
        m.memory_id,
        m.expert_id,
        m.game_id,
        m.home_team,
        m.away_team,
        m.game_date,
        (1 - (m.combined_embedding <=> p_query_embedding)) as similarity_score,
        exp(-greatest(0, extract(epoch from (now() - m.game_date))/86400.0)/90.0) as recency_score,
        (p_alpha * (1 - (m.combined_embedding <=> p_query_embedding))
         + (1 - p_alpha) * exp(-greatest(0, extract(epoch from (now() - m.game_date))/86400.0)/90.0)) as combined_score
    from expert_episodic_memories m
    where m.expert_id = p_expert_id
    and m.combined_embedding is not null
    and (1 - (m.combined_embedding <=> p_query_embedding)) >= p_match_threshold
    order by combined_score desc
    limit p_match_count;
end $$;
