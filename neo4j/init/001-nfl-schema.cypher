// NFL Knowledge Graph Schema Initialization
// This creates the foundational structure for NFL relationships

// Create constraints for unique identifiers
CREATE CONSTRAINT team_id_unique IF NOT EXISTS FOR (t:Team) REQUIRE t.team_id IS UNIQUE;
CREATE CONSTRAINT player_id_unique IF NOT EXISTS FOR (p:Player) REQUIRE p.player_id IS UNIQUE;
CREATE CONSTRAINT coach_id_unique IF NOT EXISTS FOR (c:Coach) REQUIRE c.coach_id IS UNIQUE;
CREATE CONSTRAINT game_id_unique IF NOT EXISTS FOR (g:Game) REQUIRE g.game_id IS UNIQUE;
CREATE CONSTRAINT expert_id_unique IF NOT EXISTS FOR (e:Expert) REQUIRE e.expert_id IS UNIQUE;
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.memory_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX team_name_index IF NOT EXISTS FOR (t:Team) ON (t.name);
CREATE INDEX player_name_index IF NOT EXISTS FOR (p:Player) ON (p.name);
CREATE INDEX game_date_index IF NOT EXISTS FOR (g:Game) ON (g.date);
CREATE INDEX memory_created_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at);

// Node Labels and Properties:

// Team nodes
// (:Team {team_id, name, city, conference, division, founded_year, stadium})

// Player nodes
// (:Player {player_id, name, position, jersey_number, height, weight, college, draft_year})

// Coach nodes
// (:Coach {coach_id, name, position, experience_years, coaching_tree})

// Game nodes
// (:Game {game_id, date, week, season, home_score, away_score, weather, venue})

// Expert nodes
// (:Expert {expert_id, name, personality_type, specializations, created_at})

// Memory nodes
// (:Memory {memory_id, expert_id, memory_type, content, confidence, created_at, last_accessed})

// Relationship Types:

// Team relationships
// (Team)-[:PLAYS_IN]->(Conference)
// (Team)-[:MEMBER_OF]->(Division)
// (Team)-[:PLAYS_AT]->(Stadium)

// Player relationships
// (Player)-[:PLAYS_FOR]->(Team)
// (Player)-[:DRAFTED_BY]->(Team)
// (Player)-[:ATTENDED]->(College)

// Coach relationships
// (Coach)-[:COACHES]->(Team)
// (Coach)-[:MENTORED_BY]->(Coach)
// (Coach)-[:COACHED_WITH]->(Coach)

// Game relationships
// (Team)-[:PLAYED_HOME]->(Game)
// (Team)-[:PLAYED_AWAY]->(Game)
// (Game)-[:PLAYED_AT]->(Stadium)

// Expert relationships
// (Expert)-[:PREDICTED]->(Game)
// (Expert)-[:LEARNED_FROM]->(Game)
// (Expert)-[:HAS_MEMORY]->(Memory)

// Memory relationships
// (Memory)-[:ABOUT_TEAM]->(Team)
// (Memory)-[:ABOUT_GAME]->(Game)
// (Memory)-[:ABOUT_MATCHUP]->(Team)
// (Memory)-[:SIMILAR_TO]->(Memory)
// (Memory)-[:DERIVED_FROM]->(Memory)

// Expert learning relationships
// (Expert)-[:LEARNED_PATTERN]->(Pattern)
// (Expert)-[:DISCOVERED_INSIGHT]->(Insight)
// (Expert)-[:SHARES_KNOWLEDGE]->(Expert)

// Initialize basic NFL structure
MERGE (afc:Conference {name: 'AFC'})
MERGE (nfc:Conference {name: 'NFC'})

// AFC Divisions
MERGE (afc_east:Division {name: 'AFC East', conference: 'AFC'})
MERGE (afc_north:Division {name: 'AFC North', conference: 'AFC'})
MERGE (afc_south:Division {name: 'AFC South', conference: 'AFC'})
MERGE (afc_west:Division {name: 'AFC West', conference: 'AFC'})

// NFC Divisions
MERGE (nfc_east:Division {name: 'NFC East', conference: 'NFC'})
MERGE (nfc_north:Division {name: 'NFC North', conference: 'NFC'})
MERGE (nfc_south:Division {name: 'NFC South', conference: 'NFC'})
MERGE (nfc_west:Division {name: 'NFC West', conference: 'NFC'})

// Create division relationships
MERGE (afc_east)-[:PART_OF]->(afc)
MERGE (afc_north)-[:PART_OF]->(afc)
MERGE (afc_south)-[:PART_OF]->(afc)
MERGE (afc_west)-[:PART_OF]->(afc)
MERGE (nfc_east)-[:PART_OF]->(nfc)
MERGE (nfc_north)-[:PART_OF]->(nfc)
MERGE (nfc_south)-[:PART_OF]->(nfc)
MERGE (nfc_west)-[:PART_OF]->(nfc);
