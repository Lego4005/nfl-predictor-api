#!/usr/bin/env python3
"""
Fix embedding forconvert from string to proper vector format
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import List, Optional

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        sys.exit(1)

    if not openai_key:
        print("❌ Missing OPENAI_API_KEY environment variable")
        sys.exit(1)

    print("🔧 Fixing embedding format...")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Get all records
        result = supabase.table('expert_episodic_memories').select(
            'id, memory_id, combined_embedding, home_team, away_team'
        ).execute()

        if not result.data:
            print("   ❌ No records found")
            return False

        records = result.data
        print(f"   📊 Found {len(records)} records to check")

        fixed_count = 0

        for i, record in enumerate(records):
            record_id = record['id']
            memory_id = record.get('memory_id', f'mem_{record_id}')
            embedding = record.get('combined_embedding')

            print(f"   🔍 Checking {memory_id} ({i+1}/{len(records)})...")

            # Check if embedding is stored as string
            if isinstance(embedding, str):
                print(f"      ⚠️  Embedding is stored as string (length: {len(embedding)})")

                # Try to parse as JSON
                try:
                    parsed_embedding = json.loads(embedding)
                    if isinstance(parsed_embedding, list) and len(parsed_embedding) == 1536:
                        print(f"      ✅ Parsed valid 1536-dimensional embedding from string")

                        # Update with proper vector format
                        update_result = supabase.table('expert_episodic_memories').update({
                            'combined_embedding': parsed_embedding
                        }).eq('id', record_id).execute()

                        if update_result.data:
                            fixed_count += 1
                            print(f"      ✅ Fixed embedding format for {memory_id}")
                        else:
                            print(f"      ❌ Failed to update {memory_id}")
                    else:
                        print(f"      ❌ Parsed embedding has wrong dimensions: {len(parsed_embedding) if isinstance(parsed_embedding, list) else 'not a list'}")

                        # Generate new embedding
                        new_embedding = generate_new_embedding(record, openai_key)
                        if new_embedding:
                            update_result = supabase.table('expert_episodic_memories').update({
                                'combined_embedding': new_embedding,
                                'embedding_model': 'text-embedding-3-small',
                                'embedding_generated_at': datetime.now().isoformat()
                            }).eq('id', record_id).execute()

                            if update_result.data:
                                fixed_count += 1
                                print(f"      ✅ Generated new embedding for {memory_id}")
                            else:
                                print(f"      ❌ Failed to update {memory_id} with new embedding")

                except json.JSONDecodeError:
                    print(f"      ❌ Could not parse embedding as JSON")

                    # Generate new embedding
                    new_embedding = generate_new_embedding(record, openai_key)
                    if new_embedding:
                        update_result = supabase.table('expert_episodic_memories').update({
                            'combined_embedding': new_embedding,
                            'embedding_model': 'text-embedding-3-small',
                            'embedding_generated_at': datetime.now().isoformat()
                        }).eq('id', record_id).execute()

                        if update_result.data:
                            fixed_count += 1
                            print(f"      ✅ Generated new embedding for {memory_id}")
                        else:
                            print(f"      ❌ Failed to update {memory_id} with new embedding")

            elif isinstance(embedding, list):
                if len(embedding) == 1536:
                    print(f"      ✅ Embedding already has correct format and dimensions")
                else:
                    print(f"      ⚠️  Embedding is list but wrong dimensions: {len(embedding)}")

                    # Generate new embedding
                    new_embedding = generate_new_embedding(record, openai_key)
                    if new_embedding:
                        update_result = supabase.table('expert_episodic_memories').update({
                            'combined_embedding': new_embedding,
                            'embedding_model': 'text-embedding-3-small',
                            'embedding_generated_at': datetime.now().isoformat()
                        }).eq('id', record_id).execute()

                        if update_result.data:
                            fixed_count += 1
                            print(f"      ✅ Generated new embedding for {memory_id}")
                        else:
                            print(f"      ❌ Failed to update {memory_id} with new embedding")
            else:
                print(f"      ❌ Embedding has unexpected type: {type(embedding)}")

            # Rate limiting
            time.sleep(0.5)

        print(f"\n📊 Fix Summary:")
        print(f"   ✅ Fixed embeddings: {fixed_count}")
        print(f"   📈 Total records: {len(records)}")

        # Verify the results
        print("\n🔍 Verifying fixed embeddings...")
        verify_result = supabase.table('expert_episodic_memories').select(
            'id, combined_embedding'
        ).execute()

        if verify_result.data:
            correct_count = 0
            for record in verify_result.data:
                embedding = record.get('combined_embedding')
                if isinstance(embedding, list) and len(embedding) == 1536:
                    correct_count += 1

            print(f"   📊 Verification: {correct_count}/{len(verify_result.data)} embeddings have correct format and dimensions")

            if correct_count == len(verify_result.data):
                print("   🎉 All embeddings now have correct format and dimensions!")
                return True
            else:
                print("   ⚠️  Some embeddings still need fixing")
                return False
        else:
            print("   ❌ No records found during verification")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def generate_new_embedding(record: dict, openai_key: str) -> Optional[List[float]]:
    """Generate a new embedding for a record"""
    # Create text content
    home_team = record.get('home_team', '')
    away_team = record.get('away_team', '')
    text = f"NFL game: {away_team} at {home_team}" if home_team and away_team else "NFL game memory"

    try:
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "text-embedding-3-small",
            "input": text
        }

        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            embedding = result["data"][0]["embedding"]
            if len(embedding) == 1536:
                return embedding
            else:
                print(f"      ❌ Generated embedding has wrong dimensions: {len(embedding)}")
                return None
        else:
            print(f"      ❌ API error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"      ❌ Embedding generation failed: {e}")
        return None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
