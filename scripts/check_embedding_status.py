#!/usr/bin/env python3
"""
Check the status of embeddings in the database
"""

import os
import sys
import json

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables")
        sys.exit(1)

    print("🔍 Checking embedding status in expert_episodic_memories...")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Get all records with their embedding info
        result = supabase.table('expert_episodic_memories').select(
            'id, memory_id, expert_id, game_id, combined_embedding, game_context_embedding, prediction_embedding, outcome_embedding, embedding_model, embedding_generated_at'
        ).execute()

        if not result.data:
            print("   ❌ No data found in expert_episodic_memories table")
            return False

        print(f"   📊 Found {len(result.data)} total records")

        # Analyze embeddings
        records_with_combined = 0
        records_with_context = 0
        records_with_prediction = 0
        records_with_outcome = 0
        embedding_dimensions = set()
        embedding_models = set()

        for record in result.data:
            if record.get('combined_embedding'):
                records_with_combined += 1
                embedding_dimensions.add(len(record['combined_embedding']))

            if record.get('game_context_embedding'):
                records_with_context += 1

            if record.get('prediction_embedding'):
                records_with_prediction += 1

            if record.get('outcome_embedding'):
                records_with_outcome += 1

            if record.get('embedding_model'):
                embedding_models.add(record['embedding_model'])

        total_records = len(result.data)

        print(f"\n📈 Embedding Coverage:")
        print(f"   Combined embeddings: {records_with_combined}/{total_records} ({records_with_combined/total_records*100:.1f}%)")
        print(f"   Context embeddings:  {records_with_context}/{total_records} ({records_with_context/total_records*100:.1f}%)")
        print(f"   Prediction embeddings: {records_with_prediction}/{total_records} ({records_with_prediction/total_records*100:.1f}%)")
        print(f"   Outcome embeddings:  {records_with_outcome}/{total_records} ({records_with_outcome/total_records*100:.1f}%)")

        print(f"\n🔢 Embedding Dimensions Found: {list(embedding_dimensions)}")
        print(f"🤖 Embedding Models Used: {list(embedding_models)}")

        # Check if dimensions match expected (1536 for text-embedding-3-small)
        expected_dims = 1536
        if expected_dims in embedding_dimensions:
            print(f"   ✅ Found expected {expected_dims}-dimensional embeddings")
        else:
            print(f"   ⚠️  Expected {expected_dims}-dimensional embeddings not found")
            if embedding_dimensions:
                print(f"   📝 Consider regenerating embeddings with correct model")

        # Show sample records
        print(f"\n📋 Sample Records:")
        for i, record in enumerate(result.data[:3]):
            print(f"   {i+1}. ID: {record['id']}")
            print(f"      Memory ID: {record.get('memory_id', 'N/A')}")
            print(f"      Expert: {record.get('expert_id', 'N/A')}")
            print(f"      Game: {record.get('game_id', 'N/A')}")
            print(f"      Combined embedding: {'✅' if record.get('combined_embedding') else '❌'}")
            print(f"      Embedding model: {record.get('embedding_model', 'N/A')}")
            print(f"      Generated at: {record.get('embedding_generated_at', 'N/A')}")
            print()

        # Overall assessment
        if records_with_combined >= total_records * 0.8:
            print("✅ Good embedding coverage - ready for vector search")
            return True
        elif records_with_combined >= total_records * 0.5:
            print("⚠️  Moderate embedding coverage - consider regenerating missing embeddings")
            return True
        else:
            print("❌ Low embedding coverage - embeddings need to be generated")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
