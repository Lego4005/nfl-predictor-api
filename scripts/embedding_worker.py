#!/usr/bin/env python3
"""
Embedding Worker Service
Processes embedding_jobs queue and generates vector embeddings for expert memories
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import openai
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingWorker:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = 'text-embedding-3-large'
        self.embedding_version = 1

    async def process_embedding_jobs(self, batch_size: int = 10):
        """Process embedding jobs from the queue"""
        while True:
            try:
                # Get pending jobs
                jobs = self.supabase.table('embedding_jobs')\
                    .select('*')\
                    .order('enqueued_at')\
                    .limit(batch_size)\
                    .execute()

                if not jobs.data:
                    logger.info("No pending embedding jobs, sleeping...")
                    await asyncio.sleep(30)
                    continue

                logger.info(f"Processing {len(jobs.data)} embedding jobs")

                for job in jobs.data:
                    await self.process_single_job(job)

            except Exception as e:
                logger.error(f"Error processing embedding jobs: {e}")
                await asyncio.sleep(60)

    async def process_single_job(self, job: Dict):
        """Process a single embedding job"""
        memory_id = job['memory_id']

        try:
            # Get memory data
            memory = self.supabase.table('expert_episodic_memories')\
                .select('*')\
                .eq('memory_id', memory_id)\
                .single()\
                .execute()

            if not memory.data:
                logger.warning(f"Memory {memory_id} not found, removing job")
                self.remove_job(job['id'])
                return

            memory_data = memory.data

            # Generate embeddings
            embeddings = await self.generate_embeddings(memory_data)

            # Update memory with embeddings
            self.supabase.table('expert_episodic_memories')\
                .update({
                    'game_context_embedding': embeddings['game_context'],
                    'prediction_embedding': embeddings['prediction'],
                    'outcome_embedding': embeddings['outcome'],
                    'combined_embedding': embeddings['combined'],
                    'embedding_model': self.embedding_model,
                    'embedding_generated_at': datetime.now().isoformat(),
                    'embedding_version': self.embedding_version,
                    'embedding_status': 'ready'
                })\
                .eq('memory_id', memory_id)\
                .execute()

            # Remove job from queue
            self.remove_job(job['id'])

            logger.info(f"Successfully processed embedding for memory {memory_id}")

        except Exception as e:
            logger.error(f"Error processing job {job['id']} for memory {memory_id}: {e}")

            # Increment tries and potentially fail the job
            tries = job.get('tries', 0) + 1
            if tries >= 3:
                # Mark as failed
                self.supabase.table('expert_episodic_memories')\
                    .update({'embedding_status': 'failed'})\
                    .eq('memory_id', memory_id)\
                    .execute()

                self.remove_job(job['id'])
                logger.error(f"Job {job['id']} failed after {tries} tries")
            else:
                # Update tries count
                self.supabase.table('embedding_jobs')\
                    .update({'tries': tries})\
                    .eq('id', job['id'])\
                    .execute()

    def remove_job(self, job_id: int):
        """Remove job from queue"""
        self.supabase.table('embedding_jobs')\
            .delete()\
            .eq('id', job_id)\
            .execute()

    async def generate_embeddings(self, memory_data: Dict) -> Dict[str, List[float]]:
        """Generate embeddings for different aspects of the memory"""

        # Extract text for different embedding types
        game_context_text = self.extract_game_context(memory_data)
        prediction_text = self.extract_prediction_text(memory_data)
        outcome_text = self.extract_outcome_text(memory_data)
        combined_text = f"{game_context_text} {prediction_text} {outcome_text}"

        # Generate embeddings
        texts = [game_context_text, prediction_text, outcome_text, combined_text]

        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )

        return {
            'game_context': response.data[0].embedding,
            'prediction': response.data[1].embedding,
            'outcome': response.data[2].embedding,
            'combined': response.data[3].embedding
        }

    def extract_game_context(self, memory_data: Dict) -> str:
        """Extract game context text for embedding"""
        contextual_factors = memory_data.get('contextual_factors', [])
        if isinstance(contextual_factors, list):
            context_text = ' '.join([str(factor) for factor in contextual_factors])
        else:
            context_text = str(contextual_factors)

        game_info = f"Game: {memory_data.get('home_team', '')} vs {memory_data.get('away_team', '')}"
        return f"{game_info} Context: {context_text}"

    def extract_prediction_text(self, memory_data: Dict) -> str:
        """Extract prediction text for embedding"""
        prediction_data = memory_data.get('prediction_data', {})
        if isinstance(prediction_data, dict):
            prediction_text = json.dumps(prediction_data)
        else:
            prediction_text = str(prediction_data)

        return f"Prediction: {prediction_text}"

    def extract_outcome_text(self, memory_data: Dict) -> str:
        """Extract outcome text for embedding"""
        actual_outcome = memory_data.get('actual_outcome', {})
        if isinstance(actual_outcome, dict):
            outcome_text = json.dumps(actual_outcome)
        else:
            outcome_text = str(actual_outcome)

        lessons_learned = memory_data.get('lessons_learned', {})
        if isinstance(lessons_learned, dict):
            lessons_text = json.dumps(lessons_learned)
        else:
            lessons_text = str(lessons_learned)

        return f"Outcome: {outcome_text} Lessons: {lessons_text}"

async def main():
    """Main worker loop"""
    worker = EmbeddingWorker()
    logger.info("Starting embedding worker...")

    try:
        await worker.process_embedding_jobs()
    except KeyboardInterrupt:
        logger.info("Embedding worker stopped by user")
    except Exception as e:
        logger.error(f"Embedding worker crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
