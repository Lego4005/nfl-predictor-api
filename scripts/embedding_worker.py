#!/usr/bin/env python3
import os, time, json, math, sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for unified client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# pip install supabase openai python-dotenv
from supabase import create_client
from dotenv import load_dotenv
from services.unified_ai_client import UnifiedAIClient

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # 1536 dims
BATCH = int(os.getenv("EMBED_BATCH", "16"))
POLL_SEC = int(os.getenv("EMBED_POLL_SEC", "3"))
MAX_TRIES = int(os.getenv("EMBED_MAX_TRIES", "5"))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL/SUPABASE_KEY environment variables")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Unified AI Client (handles OpenAI for embeddings automatically)
try:
    ai_client = UnifiedAIClient()
    print("✅ Unified AI client initialized successfully")
except Exception as e:
    print(f"❌ Unified AI client initialization failed: {e}")
    exit(1)

def mk_text(parts):
    return " | ".join([p for p in parts if p])

def render_memory_text(mem: Dict[str, Any]) -> Dict[str, str]:
    # robust string builders per vector "facet"
    home, away = mem.get("home_team"), mem.get("away_team")
    head = f"{away} at {home}" if (home and away) else ""

    pred = mem.get("prediction_data") or {}
    outcome = mem.get("actual_outcome") or {}
    reasons = mem.get("lessons_learned") or []

    # context text can also use weather/market fields if present in contextual_factors
    ctx = mem.get("contextual_factors") or []
    ctx_bits = []
    for f in ctx:
        if isinstance(f, dict):
            k = f.get("factor"); v = f.get("value")
            if k and v:
                ctx_bits.append(f"{k}:{v}")

    context_text = mk_text([head] + ctx_bits)

    prediction_text = mk_text([
        head,
        f"predicted_winner:{pred.get('predicted_winner')}",
        f"home_win_prob:{pred.get('home_win_prob')}",
        f"away_win_prob:{pred.get('away_win_prob')}",
        f"confidence:{pred.get('confidence')}"
    ])

    outcome_text = mk_text([
        head,
        f"actual_winner:{(outcome.get('winner') or outcome.get('actual_winner'))}",
        f"home_score:{outcome.get('home_score')}",
        f"away_score:{outcome.get('away_score')}"
    ])

    lessons_text = mk_text([str(x) for x in reasons if isinstance(x, (str, int, float))])
    combined = mk_text([context_text, prediction_text, outcome_text, lessons_text])

    return {
        "game_context": context_text or combined,
        "prediction": prediction_text or combined,
        "outcome": outcome_text or combined,
        "combined": combined
    }

def embed(text: str) -> Optional[list]:
    if not text:
        return None
    try:
        # Use unified client (automatically uses OpenAI for embeddings)
        response = ai_client.create_embedding(text[:8000], EMBED_MODEL)
        return response.embedding
    except Exception as e:
        print(f"Embedding failed for text: {text[:100]}... Error: {e}")
        return None

def fetch_jobs(limit=BATCH):
    r = sb.table("embedding_jobs").select("id,memory_id,tries").order("enqueued_at", desc=False).limit(limit).execute()
    return r.data or []

def fetch_memory(mid: str):
    r = sb.table("expert_episodic_memories").select(
        "memory_id,expert_id,game_id,home_team,away_team,contextual_factors,prediction_data,actual_outcome,lessons_learned"
    ).eq("memory_id", mid).execute()

    if r.data and len(r.data) > 0:
        return r.data[0]  # Take first result if multiple
    return None

def write_vectors(mid: str, facet_texts: Dict[str, str]):
    fields = {}

    # generate four embeddings; if any fail, mark failed
    gc = embed(facet_texts["game_context"])
    pr = embed(facet_texts["prediction"])
    oc = embed(facet_texts["outcome"])
    cb = embed(facet_texts["combined"])

    if not cb:
        raise RuntimeError("combined embedding missing")

    fields.update({
        "game_context_embedding": gc,
        "prediction_embedding": pr,
        "outcome_embedding": oc,
        "combined_embedding": cb,
        "embedding_model": EMBED_MODEL,
        "embedding_generated_at": datetime.utcnow().isoformat(),
        "embedding_version": 1,
        "embedding_status": "ready",
    })

    sb.table("expert_episodic_memories").update(fields).eq("memory_id", mid).execute()

def mark_fail(job_id: int, mem_id: str, tries: int):
    sb.table("embedding_jobs").update({"tries": tries+1}).eq("id", job_id).execute()
    if tries+1 >= MAX_TRIES:
        sb.table("expert_episodic_memories").update({"embedding_status": "failed"}).eq("memory_id", mem_id).execute()

def delete_job(job_id: int):
    sb.table("embedding_jobs").delete().eq("id", job_id).execute()

def main():
    print("embedding worker online.")
    while True:
        jobs = fetch_jobs()
        if not jobs:
            time.sleep(POLL_SEC); continue

        for j in jobs:
            jid, mid, tries = j["id"], j["memory_id"], j.get("tries", 0)
            try:
                mem = fetch_memory(mid)
                if not mem:
                    delete_job(jid); continue

                texts = render_memory_text(mem)
                write_vectors(mid, texts)
                delete_job(jid)
                print(f"✅ Processed {mid}")

            except Exception as e:
                print("ERR", mid, e)
                mark_fail(jid, mid, tries)

            # small breather to avoid hammering
            time.sleep(0.2)

if __name__ == "__main__":
    main()
