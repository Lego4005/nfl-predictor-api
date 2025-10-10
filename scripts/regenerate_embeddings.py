#!/usr/bin/env python3
"""
Regenerate embeddings with correct dimensions (1536) using OpenAI text-embedding-3-small
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        sys.exit(1)

    if not openai_key:
        print("❌ Missing OPENAI_API_KEY environment variable")
        sys.exit(1)

    print("🔄 Regenerating embeddings with correct dimensions...")
    print(f"📡 Connecting to: {supabase_url}")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Get all records that need embedding regeneration
        result = supabase.table('expert_episodic_memories').select(
            'id, memory_id, expert_id, game_id, home_team, away_team, '
            'contextual_factors, prediction_data, actual_outcome, lessons_learned, '
            'combined_embedding'
        ).execute()

        if not result.data:
            print("   ❌ No records found in expert_episodic_memories table")
            return False

        records = result.data
        print(f"   📊 Found {len(records)} records to process")

        # Check current embedding dimensions
        oversized_count = 0
        for record in records:
            if record.get('combined_embedding'):
                dims = len(record['combined_embedding'])
                if dims != 1536:
                    oversized_count += 1

        print(f"   🔍 Found {oversized_count} records with incorrect embedding dimensions")

        if oversized_count == 0:
            print("   ✅ All embeddings already have correct dimensions!")
            return True

        # Process each record
        processed = 0
        failed = 0

        for i, record in enumerate(records):
            record_id = record['id']
            memory_id = record.get('memory_id', f'mem_{record_id}')

            # Check if this record needs regeneration
            current_embedding = record.get('combined_embedding')
            if current_embedding and len(current_embedding) == 1536:
                print(f"   ⏭️  Skipping {memory_id} (already correct dimensions)")
                continue

            print(f"   🔄 Processing {memory_id} ({i+1}/{len(records)})...")

            try:
                # Extract text content for embedding
                text_content = extract_memory_text(record)

                if not text_content:
                    print(f"      ⚠️  No text content found for {memory_id}")
                    continue

                # Generate new embedding
                embedding = generate_embedding(text_content, openai_key)

                if not embedding:
                    print(f"      ❌ Failed to generate embedding for {memory_id}")
                    failed += 1
                    continue

                if len(embedding) != 1536:
                    print(f"      ❌ Generated embedding has wrong dimensions: {len(embedding)}")
                    failed += 1
                    continue

                # Update the record
                update_result = supabase.table('expert_episodic_memories').update({
                    'combined_embedding': embedding,
                    'embedding_model': 'text-embedding-3-small',
                    'embedding_generated_at': datetime.utcnow().isoformat(),
                    'embedding_version': 2
                }).eq('id', record_id).execute()

                if update_result.data:
                    processed += 1
                    print(f"      ✅ Updated {memory_id} with {len(embedding)}-dimensional embedding")
                else:
                    print(f"      ❌ Failed to update {memory_id} in database")
                    failed += 1

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"      ❌ Error processing {memory_id}: {str(e)}")
                failed += 1

        print(f"\n📊 Regeneration Summary:")
        print(f"   ✅ Successfully processed: {processed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Total records: {len(records)}")

        if processed > 0:
            print(f"\n🎉 Embedding regeneration completed!")

            # Verify the results
            print("🔍 Verifying updated embeddings...")
            verify_result = supabase.table('expert_episodic_memories').select(
                'id, combined_embedding, embedding_model'
            ).not_.is_('combined_embedding', 'null').execute()

            if verify_result.data:
                correct_dims = sum(1 for r in verify_result.data if len(r['combined_embedding']) == 1536)
                total_with_embeddings = len(verify_result.data)

                print(f"   📊 Verification: {correct_dims}/{total_with_embeddings} embeddings have correct dimensions")

                if correct_dims == total_with_embeddings:
                    print("   ✅ All embeddings now have correct dimensions!")
                    return True
                else:
                    print("   ⚠️  Some embeddings still have incorrect dimensions")
                    return False
            else:
                print("   ❌ No embeddings found during verification")
                return False
        else:
            print("   ❌ No embeddings were successfully regenerated")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def extract_memory_text(record: Dict[str, Any]) -> str:
    """Extract meaningful text content from a memory record"""
    parts = []

    # Game context
    home_team = record.get('home_team', '')
    away_team = record.get('away_team', '')
    if home_team and away_team:
        parts.append(f"{away_team} at {home_team}")

    # Contextual factors
    contextual_factors = record.get('contextual_factors', [])
    if contextual_factors:
        for factor in contextual_factors:
            if isinstance(factor, dict):
                factor_name = factor.get('factor', '')
                factor_value = factor.get('value', '')
                if factor_name and factor_value:
                    parts.append(f"{factor_name}: {factor_value}")

    # Prediction data
    prediction_data = record.get('prediction_data', {})
    if prediction_data:
        if 'predicted_winner' in prediction_data:
            parts.append(f"Predicted winner: {prediction_data['predicted_winner']}")
        if 'confidence' in prediction_data:
            parts.append(f"Confidence: {prediction_data['confidence']}")
        if 'reasoning' in prediction_data:
            parts.append(f"Reasoning: {prediction_data['reasoning']}")

    # Actual outcome
    actual_outcome = record.get('actual_outcome', {})
    if actual_outcome:
        if 'winner' in actual_outcome:
            parts.append(f"Actual winner: {actual_outcome['winner']}")
        if 'home_score' in actual_outcome and 'away_score' in actual_outcome:
            parts.append(f"Final score: {actual_outcome['home_score']}-{actual_outcome['away_score']}")

    # Lessons learned
    lessons_learned = record.get('lessons_learned', [])
    if lessons_learned:
        for lesson in lessons_learned:
            if isinstance(lesson, str):
                parts.append(f"Lesson: {lesson}")

    return " | ".join(parts)

def generate_embedding(text: str, openai_key: str) -> Optional[List[float]]:
    """Generate embedding using OpenAI API"""
    if not text:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "text-embedding-3-small",
            "input": text[:8000]  # Truncate to avoid token limits
        }

        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result["data"][0]["embedding"]
        else:
            print(f"      API error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"      Embedding generation failed: {e}")
        return None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
