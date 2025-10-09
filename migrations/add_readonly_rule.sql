-- One-line shim: if any legacy code still writes to expert_memory_embeddings,
-- reject writes at the DB level to avoid drift
CREATE OR REPLACE RULE r_expert_memory_embeddings_readonly AS
ON INSERT TO expert_memory_embeddings DO INSTEAD NOTHING;
