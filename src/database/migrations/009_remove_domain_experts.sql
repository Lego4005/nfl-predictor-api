-- Migration: Remove Domain-Based Expert System Tables
-- Date: 2025-01-15
-- Purpose: Clean up deprecated domain-biased expert tables after migrating to personality-driven system

-- IMPORTANT: Run this ONLY after confirming personality_experts system is working
-- This removes the old domain-biased expert infrastructure permanently

-- 1. Backup old data first (optional - uncomment if you want to preserve)
-- CREATE TABLE IF NOT EXISTS deprecated_expert_council_backup AS SELECT * FROM expert_council;
-- CREATE TABLE IF NOT EXISTS deprecated_expert_predictions_backup AS SELECT * FROM expert_predictions;

-- 2. Drop old domain-based expert tables
DROP TABLE IF EXISTS expert_predictions CASCADE;  -- Had domain-specific predictions
DROP TABLE IF EXISTS expert_council CASCADE;      -- Domain expert definitions
DROP TABLE IF EXISTS expert_consensus CASCADE;    -- Old consensus mechanism

-- 3. Drop any related indexes that might remain
DROP INDEX IF EXISTS idx_expert_predictions_game;
DROP INDEX IF EXISTS idx_expert_predictions_expert;
DROP INDEX IF EXISTS idx_expert_council_domain;

-- 4. Drop old functions related to domain experts
DROP FUNCTION IF EXISTS calculate_expert_consensus CASCADE;
DROP FUNCTION IF EXISTS get_domain_expert_prediction CASCADE;
DROP FUNCTION IF EXISTS update_expert_weights CASCADE;

-- 5. Clean up any orphaned sequences
DROP SEQUENCE IF EXISTS expert_predictions_id_seq CASCADE;
DROP SEQUENCE IF EXISTS expert_council_id_seq CASCADE;

-- 6. Add migration record
INSERT INTO schema_migrations (version, description, migrated_at)
VALUES (
    '009_remove_domain_experts',
    'Removed deprecated domain-based expert tables in favor of personality-driven system',
    NOW()
) ON CONFLICT (version) DO NOTHING;

-- 7. Vacuum to reclaim space
-- VACUUM ANALYZE;  -- Uncomment if you want to reclaim disk space immediately

-- Migration Complete
-- The personality_experts system in migration 008 is now the sole expert infrastructure