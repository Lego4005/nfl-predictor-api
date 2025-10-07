#!/usr/bin/env python3
"""
Simple embedding worker that only uses OpenAI for embeddings
No OpenRouter, no complex routing - just embeddings
"""
import os, time, sys
from datetime import datetime
from typing import Dict, Any, Optional

# pip install supabase openai python-dotenv
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
BATCH = 5  # Process 5 at a time to avoid rate limits
MAX_TRIES = 3

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL/SUPABASE_KEY environment variables")

if not OPENAI_KEY:
    raise ValueError("Missing OPENAI_API_KEY - required for embeddings")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# Simple OpenAI client for embeddings only
try:
    openai_client = OpenAI(api_key=OPENAI_KEY)
    print("✅ OpenAI client initialized for embeddings")
except Exception as e:
    print(f"❌ OpenAI client initialization failed: {e}")
    print("Trying alternative initialization...")
    try:
        # Try without any extra parameters
        import openai
        openai.api_key = OPENAI_KEY
        openai_client = OpenAI(api_key=OPENAI_KEY, timeout=30.0)
        print("✅ OpenAI client initialized with alternative method")
    except Exception as e2:
        print(f"❌ Alternative initialization also failed: {e2}")
        exit(1)

def mk_text(parts):
    return " | ".join([p for p in parts if p])

def render_memory_text(mem: Dict[str, Any]) -> Dict[str, str]:
    """Extract text content from memory for embedding"""
    home, away = mem.get("home_team"), mem.get("away_team")
    head = f"{away} at {home}" if (home and away) else ""

    pred = mem.get("prediction_data") or {}
    outcome = mem.get("actual_outcome") or {}
    reasons = mem.get("lessons_learned") or []

    # Context text
    ctx = mem.get("contextual_factors") or []
    ctx_bits = []
    for f in ctx:
        if isinstance(f, dict):
            k = f.get("factor"); v = f.get("value")
            if k and v:
                ctx_bits.append(f"{k}:{v}")

    context_text = mk_text([head] + ctx_bits)

    # Prediction text
    prediction_text = mk_text([
        head,
        f"predicted_winner:{pred.get('predicted_winner')}",
        f"home_win_prob:{pred.get('home_win_prob')}",
        f"away_win_prob:{pred.get('away_win_prob')}",
        f"confidence:{pred.get('confidence')}"
    ])

    # Outcome text
    outcome_text = mk_text([
        head,
        f"actual_winner:{(outcome.get('winner') or outcome.get('actual_winner'))}",
        f"home_score:{outcome.get('home_score')}",
        f"away_score:{outcome.get('away_score')}"
    ])

    # Lessons text
    lessons_text = mk_text([str(x) for x in reasons if isinstance(x, (str, int, float))])
    combined = mk_text([context_text, prediction_text, outcome_text, lessons_text])

    return {
        "game_context": context_text or combined,
        "prediction": prediction_text or combined,
        "outcome": outcome_text or combined,
        "combined": combined
    }

def embed(text: str) -> Optional[list]:
    """Create embedding using OpenAI"""
    if not text:
        return None
    try:
        response = openai_client.embeddings.create(
            model=EMBED_MODEL,
            input=text[:8000]  # Truncate to avoid token limits
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding failed for text: {text[:100]}... Error: {e}")
        return None

def fetch_pending_memories(limit=BATCH):
    """Fetch memories that need embeddings"""
    result = sb.table("expert_episodic_memories").select(
        "memory_id,expert_id,game_id,home_team,away_team,contextual_factors,prediction_data,actual_outcome,lessons_learned"
    ).eq("embedding_status", "pending").limit(limit).execute()

    return result.data or []

def update_memory_embeddings(memory_id: str, facet_texts: Dict[str, str]):
    """Update memory with generated embeddings"""
    # Generate embeddings for each facet
    gc = embed(facet_texts["game_context"])
    pr = embed(facet_texts["prediction"])
    oc = embed(facet_texts["outcome"])
    cb = embed(facet_texts["combined"])

    if not cb:
        raise RuntimeError("Combined embedding is required")

    # Update the memory record
    update_data = {
        "game_context_embedding": gc,
        "prediction_embedding": pr,
        "outcome_embedding": oc,
        "combined_embedding": cb,
        "embedding_model": EMBED_MODEL,
        "embedding_generated_at": datetime.utcnow().isoformat(),
        "embedding_version": 1,
        "embedding_status": "ready",
    }

    sb.table("expert_episodic_memories").update(update_data).eq("memory_id", memory_id).execute()

def mark_failed(memory_id: str):
    """Mark memory as failed embedding"""
    sb.table("expert_episodic_memories").update({
        "embedding_status": "failed"
    }).eq("memory_id", memory_id).execute()

def main():
    print("🚀 Simple embedding worker starting...")

    # Process all pending memories
    while True:
        memories = fetch_pending_memories()
        if not memories:
            print("✅ No more pending memories to process")
            break

        print(f"📝 Processing {len(memories)} memories...")

        for mem in memories:
            memory_id = mem["memory_id"]
            try:
                # Extract text content
                texts = render_memory_text(mem)

                # Generate and save embeddings
                update_memory_embeddings(memory_id, texts)

                print(f"✅ Processed {memory_id}")

                # Small delay to avoid rate limits
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Failed to process {memory_id}: {e}")
                mark_failed(memory_id)

        # Check if there are more to process
        remaining = sb.table("expert_episodic_memories").select("memory_id").eq("embedding_status", "pending").limit(1).execute()
        if not remaining.data:
            break

    print("🎉 Embedding worker completed!")

if __name__ == "__main__":
    main()
