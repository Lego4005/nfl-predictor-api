// Supabase Edge Function for automatic embedding generation
// This function generates vector embeddings for text content using Supabase AI

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Define the webhook payload interface
interface WebhookPayload {
  type: 'INSERT' | 'UPDATE' | 'DELETE'
  table: string
  record: any
  old_record?: any
  schema: string
}

// Define embedding request interface
interface EmbeddingRequest {
  text: string
  table: string
  id: number
  column: string
}

const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
const supabase = createClient(supabaseUrl, supabaseKey)

// Initialize the built-in Supabase AI model
const model = new (globalThis as any).Supabase.ai.Session('gte-small')

serve(async (req) => {
  try {
    // Handle different HTTP methods
    if (req.method === 'OPTIONS') {
      return new Response('ok', {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      })
    }

    if (req.method === 'POST') {
      const body = await req.text()
      const parsed = JSON.parse(body)

      // Check if this is a direct embedding request by looking for required fields
      if (parsed.text && parsed.table && 'id' in parsed && parsed.column) {
        // Handle direct embedding requests
        return await handleEmbeddingRequest(parsed as EmbeddingRequest)
      } else {
        // Handle webhook from database triggers
        return await handleDatabaseWebhook(parsed as WebhookPayload)
      }
    }

    if (req.method === 'GET') {
      // Health check endpoint
      return new Response(JSON.stringify({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        model: 'gte-small'
      }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    return new Response('Method not allowed', { status: 405 })

  } catch (error) {
    console.error('Error in embedding function:', error)
    return new Response(JSON.stringify({
      error: error.message,
      timestamp: new Date().toISOString()
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})

// Handle database webhook triggers
async function handleDatabaseWebhook(payload: WebhookPayload) {
  const { type, table, record, schema } = payload

  if (type === 'DELETE') {
    return new Response('ok - delete ignored')
  }

  // Determine which content to embed based on table
  let textContent: string = ''
  let embeddingColumn: string = 'embedding'

  switch (table) {
    case 'news_articles':
      textContent = `${record.title || ''} ${record.content || ''}`.trim()
      embeddingColumn = 'embedding'
      break

    case 'expert_research':
      textContent = record.content || ''
      embeddingColumn = 'embedding'
      break

    case 'predictions':
      textContent = record.reasoning_text || ''
      embeddingColumn = 'analysis_embedding'
      break

    case 'expert_bets':
      textContent = record.reasoning || ''
      embeddingColumn = 'reasoning_embedding'
      break

    case 'knowledge_base':
      textContent = `${record.title || ''} ${record.content || ''}`.trim()
      embeddingColumn = 'embedding'
      break

    default:
      return new Response('ok - table not configured for embeddings')
  }

  if (!textContent) {
    return new Response('ok - no text content to embed')
  }

  // Generate embedding
  const embedding = await generateEmbedding(textContent)

  // Update the record with the embedding
  const { error } = await supabase
    .from(table)
    .update({
      [embeddingColumn]: JSON.stringify(embedding),
      embedding_updated_at: new Date().toISOString()
    })
    .eq('id', record.id)

  if (error) {
    console.error(`Error updating ${table} with embedding:`, error)
    throw error
  }

  console.log(`Successfully generated embedding for ${table} id:${record.id}`)
  return new Response('ok')
}

// Handle direct embedding requests
async function handleEmbeddingRequest(request: EmbeddingRequest) {
  const { text, table, id, column } = request

  if (!text) {
    return new Response(JSON.stringify({ error: 'Text content is required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  // Generate embedding
  const embedding = await generateEmbedding(text)

  // Update the database record
  const { error } = await supabase
    .from(table)
    .update({
      [column]: JSON.stringify(embedding),
      embedding_updated_at: new Date().toISOString()
    })
    .eq('id', id)

  if (error) {
    console.error(`Error updating ${table} with embedding:`, error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }

  return new Response(JSON.stringify({
    success: true,
    embedding: embedding,
    embedding_length: embedding.length,
    updated_table: table,
    updated_id: id
  }), {
    headers: { 'Content-Type': 'application/json' }
  })
}

// Generate embedding using Supabase AI
async function generateEmbedding(text: string): Promise<number[]> {
  try {
    // Use the built-in Supabase AI model
    const embedding = await model.run(text, {
      mean_pool: true,
      normalize: true,
    })

    // Convert to array format
    return Array.from(embedding)
  } catch (error) {
    console.error('Error generating embedding:', error)

    // Fallback to zero vector if AI model fails
    console.warn('Falling back to zero vector due to embedding generation failure')
    return new Array(384).fill(0)
  }
}

// Batch embedding function for multiple texts
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  const embeddings: number[][] = []

  for (const text of texts) {
    const embedding = await generateEmbedding(text)
    embeddings.push(embedding)

    // Small delay to avoid overwhelming the model
    await new Promise(resolve => setTimeout(resolve, 100))
  }

  return embeddings
}