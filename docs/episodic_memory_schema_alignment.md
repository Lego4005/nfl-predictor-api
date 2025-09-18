# Episodic Memory System Schema Alignment

## Overview

This document outlines the schema alignment implemented in migration 011 to support the episodic memory services (`belief_revision_service.py` and `episodic_memory_manager.py`).

## Migration 011: Expert Episodic Memory System

### Purpose
- Creates missing database tables required by episodic memory services
- Ensures compatibility with existing expert competition system (migration 20250116)
- Adds proper indexing and constraints for performance optimization

### New Tables Created

#### 1. expert_belief_revisions
Tracks when experts change their minds about predictions with causal analysis.

**Key Fields:**
- `expert_id`: Links to expert_models table
- `revision_type`: Type of belief change (complete_reversal, confidence_shift, etc.)
- `trigger_type`: What caused the revision (injury_report, line_movement, etc.)
- `original_prediction` / `revised_prediction`: JSONB prediction data
- `causal_chain`: JSONB array of reasoning steps
- `confidence_delta`: Numeric change in confidence
- `emotional_state`: Expert's emotional response to revision
- `impact_score`: Calculated impact of the revision

#### 2. expert_episodic_memories
Stores game experiences with emotional encoding and lesson extraction.

**Key Fields:**
- `memory_id`: Unique 32-character hash for memory identification
- `expert_id`: Links to expert_models table
- `memory_type`: Classification (upset_detection, learning_moment, etc.)
- `emotional_state`: Emotional response (euphoria, devastation, etc.)
- `prediction_data` / `actual_outcome`: JSONB game data
- `contextual_factors`: JSONB array of situational factors
- `lessons_learned`: JSONB array of extracted insights
- `emotional_intensity`: 0-1 scale of emotional response
- `memory_vividness`: 0-1 scale of memory strength
- `memory_decay`: 0-1 scale for memory degradation over time
- `retrieval_count`: How often this memory has been accessed

#### 3. Supporting Tables

##### weather_conditions
- Stores weather data for games
- Referenced by episodic memory contextual factors

##### injury_reports
- Stores injury information for players
- Referenced by episodic memory contextual factors

### Indexes and Performance Optimization

#### Belief Revisions Indexes:
- `idx_belief_revisions_expert`: Fast expert lookups
- `idx_belief_revisions_game`: Fast game lookups
- `idx_belief_revisions_created_at`: Chronological ordering
- `idx_belief_revisions_type`: Revision type filtering
- `idx_belief_revisions_trigger`: Trigger analysis

#### Episodic Memories Indexes:
- `idx_episodic_memories_expert`: Fast expert lookups
- `idx_episodic_memories_game`: Fast game lookups
- `idx_episodic_memories_memory_id`: Unique memory identification
- `idx_episodic_memories_vividness`: Memory strength ordering
- `idx_episodic_memories_retrieval`: Composite index for memory retrieval with decay

### Database Functions

#### decay_episodic_memories()
- Automatically degrades old memories over time
- Strengthens frequently accessed memories
- Maintains memory ecosystem health

#### calculate_revision_impact()
- Calculates impact score for belief revisions
- Considers revision type and confidence changes
- Used for ranking revision significance

### Views for Service Integration

#### expert_memory_summary
Aggregates memory and revision statistics per expert:
- Total memories and revisions
- Average emotional intensity and vividness
- Total memory retrievals
- Average revision impact

#### recent_memory_activity
Shows recent memory and revision activity across all experts:
- Activity type (memory/revision)
- Activity details and timestamps
- Useful for monitoring system activity

### Service Integration

#### BeliefRevisionService
- **Status**: ✅ Compatible - No changes required
- Service already uses correct field mappings
- Stores revisions in expert_belief_revisions table
- Tracks causal chains and emotional states

#### EpisodicMemoryManager
- **Status**: ✅ Compatible - No changes required
- Service already uses correct field mappings
- Stores memories in expert_episodic_memories table
- Handles memory retrieval with similarity scoring

## Validation

### Schema Validation Script
Location: `scripts/validate_episodic_memory_schema.py`

**Features:**
- Validates table structure and indexes
- Tests service integration
- Verifies foreign key constraints
- Runs end-to-end functionality tests
- Cleans up test data automatically

**Usage:**
```bash
# Run validation
python scripts/validate_episodic_memory_schema.py

# Or make executable and run
chmod +x scripts/validate_episodic_memory_schema.py
./scripts/validate_episodic_memory_schema.py
```

### Validation Checklist
- ✅ Table structure matches service expectations
- ✅ Indexes created for performance optimization
- ✅ Foreign key constraints properly defined
- ✅ BeliefRevisionService integration working
- ✅ EpisodicMemoryManager integration working
- ✅ Supporting tables (weather, injuries) created
- ✅ Database functions and views operational

## Migration Dependencies

### Prerequisites
1. **20250116_expert_competition_tables.sql** must be applied first
   - Creates expert_models table required for foreign keys
   - Establishes base expert competition system

### Compatibility
- Compatible with existing expert prediction system
- Does not modify existing tables
- Uses soft references to expert_models
- Graceful degradation if expert_models missing

## Performance Considerations

### Memory Management
- Automatic decay system prevents unlimited memory growth
- Frequently accessed memories are strengthened
- Composite indexes optimize retrieval queries

### Belief Revision Tracking
- Efficient indexing on expert, game, and time dimensions
- JSONB storage for flexible prediction data structures
- Trigger-based automatic timestamp updates

## Security

### Row Level Security (RLS)
- RLS policies commented out in migration
- Can be enabled based on security requirements
- Foreign key constraints provide data integrity

### Data Privacy
- No personally identifiable information stored
- Expert IDs are system-generated identifiers
- Game data is anonymized prediction information

## Future Enhancements

### Potential Additions
1. **Vector embeddings** for semantic memory search
2. **Memory consolidation** algorithms for long-term storage
3. **Cross-expert memory sharing** for collective intelligence
4. **Real-time memory decay** scheduling
5. **Memory visualization** tools for analysis

### Monitoring
- Memory growth rate tracking
- Revision frequency analysis
- Expert memory pattern identification
- Performance metric collection

## Troubleshooting

### Common Issues

#### Foreign Key Constraint Errors
```sql
-- Check if expert_models table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_name = 'expert_models'
);
```

#### Missing Indexes
```sql
-- List all indexes on episodic memory tables
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('expert_belief_revisions', 'expert_episodic_memories');
```

#### Service Connection Issues
- Verify database configuration in services
- Check database permissions for schema access
- Ensure all required extensions are installed (uuid-ossp, vector)

### Support

For issues with the episodic memory system:
1. Run the validation script first
2. Check database logs for constraint violations
3. Verify service configuration matches database schema
4. Review migration logs for any errors during application

## Conclusion

Migration 011 successfully aligns the database schema with the episodic memory services, providing a robust foundation for expert belief revision tracking and episodic memory management. The implementation ensures backward compatibility while adding powerful new capabilities for understanding expert decision-making patterns.