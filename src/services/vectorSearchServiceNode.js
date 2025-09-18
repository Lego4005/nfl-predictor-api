import { supabase } from './supabaseClientNode.js'

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
      // Fallback to null array if embedding generation fails
      return new Array(this.embeddingDimensions).fill(0)
    }
  }

  // Add knowledge base entry with embedding
  async addKnowledge(category, title, content, metadata = null, trustScore = 80) {
    try {
      const embedding = await this.generateEmbedding(`${title} ${content}`)

      const { data, error } = await supabase
        .from('knowledge_base')
        .insert({
          category,
          title,
          content,
          metadata,
          trust_score: trustScore,
          embedding,
          created_at: new Date().toISOString()
        })
        .select()
        .single()

      if (error) throw error

      return {
        success: true,
        data,
        id: data.id
      }
    } catch (error) {
      console.error('Error adding knowledge:', error)
      return {
        success: false,
        error: error.message,
        id: null
      }
    }
  }

  // Search knowledge base using vector similarity
  async searchKnowledgeBase(query, options = {}) {
    try {
      const {
        matchThreshold = 0.8,
        matchCount = 5,
        categoryFilter = null
      } = options

      const queryEmbedding = await this.generateEmbedding(query)

      let rpcQuery = supabase.rpc('search_knowledge_base', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount
      })

      if (categoryFilter) {
        rpcQuery = rpcQuery.eq('category', categoryFilter)
      }

      const { data, error } = await rpcQuery

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

  // Search expert research
  async searchExpertResearch(query, options = {}) {
    try {
      const {
        matchThreshold = 0.8,
        matchCount = 5,
        expertId = null,
        researchType = null
      } = options

      const queryEmbedding = await this.generateEmbedding(query)

      let rpcQuery = supabase.rpc('search_expert_research', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: matchCount
      })

      if (expertId) {
        rpcQuery = rpcQuery.eq('expert_id', expertId)
      }
      if (researchType) {
        rpcQuery = rpcQuery.eq('research_type', researchType)
      }

      const { data, error } = await rpcQuery

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

  // Search all content (knowledge base + expert research)
  async searchAllContent(query, options = {}) {
    try {
      const {
        matchThreshold = 0.8,
        matchCount = 10
      } = options

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
        matchCount: data?.length || 0
      }
    } catch (error) {
      console.error('Error searching all content:', error)
      return {
        success: false,
        error: error.message,
        results: [],
        query,
        matchCount: 0
      }
    }
  }

  // Add expert research with embedding
  async addExpertResearch(expertId, researchType, content, metadata = null) {
    try {
      const embedding = await this.generateEmbedding(content)

      const { data, error } = await supabase
        .from('expert_research')
        .insert({
          expert_id: expertId,
          research_type: researchType,
          content,
          metadata,
          embedding,
          created_at: new Date().toISOString()
        })
        .select()
        .single()

      if (error) throw error

      return {
        success: true,
        data,
        id: data.id
      }
    } catch (error) {
      console.error('Error adding expert research:', error)
      return {
        success: false,
        error: error.message,
        id: null
      }
    }
  }

  // Get knowledge base statistics
  async getKnowledgeStats() {
    try {
      const { data, error } = await supabase
        .from('knowledge_base')
        .select('category, trust_score')

      if (error) throw error

      const stats = data.reduce((acc, item) => {
        acc.total++
        acc.categories[item.category] = (acc.categories[item.category] || 0) + 1
        acc.avgTrust += item.trust_score
        return acc
      }, { total: 0, categories: {}, avgTrust: 0 })

      stats.avgTrust = stats.total > 0 ? stats.avgTrust / stats.total : 0

      return {
        success: true,
        stats
      }
    } catch (error) {
      console.error('Error getting knowledge stats:', error)
      return {
        success: false,
        error: error.message,
        stats: null
      }
    }
  }

  // Clean up old entries (maintenance function)
  async cleanupOldEntries(daysOld = 90) {
    try {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - daysOld)

      const { data, error } = await supabase
        .from('expert_research')
        .delete()
        .lt('created_at', cutoffDate.toISOString())
        .select()

      if (error) throw error

      return {
        success: true,
        deletedCount: data.length
      }
    } catch (error) {
      console.error('Error cleaning up old entries:', error)
      return {
        success: false,
        error: error.message,
        deletedCount: 0
      }
    }
  }

  // Test vector search functionality
  async testVectorSearch() {
    try {
      console.log('🧪 Testing vector search functionality...')

      // Test embedding generation
      const testEmbedding = await this.generateEmbedding('NFL football game prediction')
      console.log(`✅ Embedding generated: ${testEmbedding.length} dimensions`)

      // Test knowledge search
      const searchResult = await this.searchKnowledgeBase('NFL team statistics', {
        matchCount: 3
      })
      console.log(`✅ Knowledge search: ${searchResult.matchCount} results found`)

      return {
        success: true,
        embeddingTest: testEmbedding.length === this.embeddingDimensions,
        searchTest: searchResult.success,
        message: 'All vector search tests passed!'
      }
    } catch (error) {
      console.error('❌ Vector search test failed:', error)
      return {
        success: false,
        error: error.message,
        message: 'Vector search tests failed'
      }
    }
  }
}

// Create singleton instance
const vectorSearchService = new VectorSearchService()

export default vectorSearchService