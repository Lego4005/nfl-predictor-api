import { supabase } from './supabaseClient.js'

class VectorSearchService {
  constructor() {
    this.embeddingDimensions = 384
  }

  // Generate embedding for text using Edge Function
  async generateEmbedding(text) {
    try {
      const { data, error } = await supabase.functions.invoke('generate-embeddings', {
        body: {
          text,
          table: 'temp', // Placeholder - not updating any table
          id: 0,
          column: 'embedding'
        }
      })

      if (error) throw error
      return data.embedding
    } catch (error) {
      console.error('Error generating embedding:', error)
      // Return zero vector as fallback
      return new Array(this.embeddingDimensions).fill(0)
    }
  }

  // Search knowledge base for relevant information
  async searchKnowledgeBase(query, options = {}) {
    const {
      matchThreshold = 0.8,
      matchCount = 5,
      categoryFilter = null
    } = options

    try {
      // Generate embedding for search query
      const queryEmbedding = await this.generateEmbedding(query)

      // Call the vector search function
      const { data, error } = await supabase.rpc('search_knowledge_base', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount,
        category_filter: categoryFilter
      })

      if (error) throw error

      return {
        success: true,
        results: data || [],
        query,
        matchCount: data?.length || 0
      }
    } catch (error) {
      console.error('Error searching knowledge base:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0
      }
    }
  }

  // Search expert research data
  async searchExpertResearch(query, options = {}) {
    const {
      matchThreshold = 0.8,
      matchCount = 10,
      expertIdFilter = null,
      researchTypeFilter = null
    } = options

    try {
      const queryEmbedding = await this.generateEmbedding(query)

      const { data, error } = await supabase.rpc('search_expert_research', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount,
        expert_id_filter: expertIdFilter,
        research_type_filter: researchTypeFilter
      })

      if (error) throw error

      return {
        success: true,
        results: data || [],
        query,
        matchCount: data?.length || 0
      }
    } catch (error) {
      console.error('Error searching expert research:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0
      }
    }
  }

  // Search news articles
  async searchNewsArticles(query, options = {}) {
    const {
      matchThreshold = 0.8,
      matchCount = 5
    } = options

    try {
      const queryEmbedding = await this.generateEmbedding(query)

      const { data, error } = await supabase.rpc('search_news_articles', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount
      })

      if (error) throw error

      return {
        success: true,
        results: data || [],
        query,
        matchCount: data?.length || 0
      }
    } catch (error) {
      console.error('Error searching news articles:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0
      }
    }
  }

  // Search similar expert betting patterns
  async searchSimilarBets(query, options = {}) {
    const {
      matchThreshold = 0.8,
      matchCount = 10,
      expertIdFilter = null,
      onlyWinners = false
    } = options

    try {
      const queryEmbedding = await this.generateEmbedding(query)

      const { data, error } = await supabase.rpc('search_similar_bets', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount,
        expert_id_filter: expertIdFilter,
        only_winners: onlyWinners
      })

      if (error) throw error

      return {
        success: true,
        results: data || [],
        query,
        matchCount: data?.length || 0
      }
    } catch (error) {
      console.error('Error searching similar bets:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0
      }
    }
  }

  // Search prediction analysis
  async searchPredictionAnalysis(query, options = {}) {
    const {
      matchThreshold = 0.8,
      matchCount = 5
    } = options

    try {
      const queryEmbedding = await this.generateEmbedding(query)

      const { data, error } = await supabase.rpc('search_prediction_analysis', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount
      })

      if (error) throw error

      return {
        success: true,
        results: data || [],
        query,
        matchCount: data?.length || 0
      }
    } catch (error) {
      console.error('Error searching prediction analysis:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0
      }
    }
  }

  // Multi-source semantic search
  async searchAllContent(query, options = {}) {
    const {
      matchThreshold = 0.8,
      matchCount = 20
    } = options

    try {
      const queryEmbedding = await this.generateEmbedding(query)

      const { data, error } = await supabase.rpc('search_all_content', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount
      })

      if (error) throw error

      return {
        success: true,
        results: data || [],
        query,
        matchCount: data?.length || 0,
        sources: this.groupResultsBySource(data || [])
      }
    } catch (error) {
      console.error('Error searching all content:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0,
        sources: {}
      }
    }
  }

  // Helper function to group results by source
  groupResultsBySource(results) {
    return results.reduce((groups, result) => {
      const source = result.source_table
      if (!groups[source]) {
        groups[source] = []
      }
      groups[source].push(result)
      return groups
    }, {})
  }

  // Store expert research with automatic embedding generation
  async storeExpertResearch(expertId, researchType, content, metadata = {}) {
    try {
      const { data, error } = await supabase
        .from('expert_research')
        .insert({
          expert_id: expertId,
          research_type: researchType,
          content,
          metadata,
          created_at: new Date().toISOString()
        })
        .select()
        .single()

      if (error) throw error

      console.log(`Stored research for expert ${expertId}:`, {
        id: data.id,
        type: researchType,
        contentLength: content.length
      })

      return {
        success: true,
        research: data
      }
    } catch (error) {
      console.error('Error storing expert research:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }

  // Store expert bet with reasoning
  async storeExpertBet(expertId, gameId, betType, betValue, confidence, reasoning) {
    try {
      const { data, error } = await supabase
        .from('expert_bets')
        .insert({
          expert_id: expertId,
          game_id: gameId,
          bet_type: betType,
          bet_value: betValue,
          confidence_level: confidence,
          reasoning,
          created_at: new Date().toISOString()
        })
        .select()
        .single()

      if (error) throw error

      console.log(`Stored bet for expert ${expertId}:`, {
        id: data.id,
        betType,
        confidence
      })

      return {
        success: true,
        bet: data
      }
    } catch (error) {
      console.error('Error storing expert bet:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }

  // Add knowledge to the base
  async addKnowledge(category, title, content, sourceUrl = null, trustScore = 50) {
    try {
      const { data, error } = await supabase
        .from('knowledge_base')
        .insert({
          category,
          title,
          content,
          source_url: sourceUrl,
          trust_score: trustScore,
          created_at: new Date().toISOString()
        })
        .select()
        .single()

      if (error) throw error

      console.log(`Added knowledge:`, {
        id: data.id,
        category,
        title
      })

      return {
        success: true,
        knowledge: data
      }
    } catch (error) {
      console.error('Error adding knowledge:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }

  // Bulk embed existing content
  async bulkEmbedExistingContent(table, textColumn, embeddingColumn) {
    try {
      // Get all records without embeddings
      const { data: records, error } = await supabase
        .from(table)
        .select('*')
        .is(embeddingColumn, null)
        .limit(100) // Process in batches

      if (error) throw error

      if (!records || records.length === 0) {
        return {
          success: true,
          message: `No records to process in ${table}`,
          processed: 0
        }
      }

      let processed = 0
      for (const record of records) {
        const text = record[textColumn]
        if (text && text.trim()) {
          // Generate embedding using the Edge Function
          await supabase.functions.invoke('generate-embeddings', {
            body: {
              text: text.trim(),
              table,
              id: record.id,
              column: embeddingColumn
            }
          })
          processed++

          // Small delay to avoid overwhelming the service
          await new Promise(resolve => setTimeout(resolve, 200))
        }
      }

      return {
        success: true,
        message: `Processed ${processed} records in ${table}`,
        processed
      }
    } catch (error) {
      console.error(`Error bulk embedding ${table}:`, error)
      return {
        success: false,
        error: error.message,
        processed: 0
      }
    }
  }
}

// Create singleton instance
const vectorSearchService = new VectorSearchService()

export default vectorSearchService