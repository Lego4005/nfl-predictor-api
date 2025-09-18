import axios from 'axios';
import { supabase } from './supabaseClient.js';

const NEWS_API_KEY = import.meta.env.VITE_NEWS_API_KEY;
const NEWS_BASE_URL = 'https://newsapi.org/v2';

class NewsService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 30 * 60 * 1000; // 30 minutes for news
    this.teamKeywords = this.buildTeamKeywords();
  }

  // Build search keywords for each team
  buildTeamKeywords() {
    return {
      'ARI': ['Arizona Cardinals', 'Cardinals'],
      'ATL': ['Atlanta Falcons', 'Falcons'],
      'BAL': ['Baltimore Ravens', 'Ravens'],
      'BUF': ['Buffalo Bills', 'Bills'],
      'CAR': ['Carolina Panthers', 'Panthers'],
      'CHI': ['Chicago Bears', 'Bears'],
      'CIN': ['Cincinnati Bengals', 'Bengals'],
      'CLE': ['Cleveland Browns', 'Browns'],
      'DAL': ['Dallas Cowboys', 'Cowboys'],
      'DEN': ['Denver Broncos', 'Broncos'],
      'DET': ['Detroit Lions', 'Lions'],
      'GB': ['Green Bay Packers', 'Packers'],
      'HOU': ['Houston Texans', 'Texans'],
      'IND': ['Indianapolis Colts', 'Colts'],
      'JAX': ['Jacksonville Jaguars', 'Jaguars'],
      'KC': ['Kansas City Chiefs', 'Chiefs'],
      'LV': ['Las Vegas Raiders', 'Raiders'],
      'LAC': ['Los Angeles Chargers', 'Chargers'],
      'LAR': ['Los Angeles Rams', 'Rams'],
      'MIA': ['Miami Dolphins', 'Dolphins'],
      'MIN': ['Minnesota Vikings', 'Vikings'],
      'NE': ['New England Patriots', 'Patriots'],
      'NO': ['New Orleans Saints', 'Saints'],
      'NYG': ['New York Giants', 'Giants NFL'],
      'NYJ': ['New York Jets', 'Jets'],
      'PHI': ['Philadelphia Eagles', 'Eagles'],
      'PIT': ['Pittsburgh Steelers', 'Steelers'],
      'SF': ['San Francisco 49ers', '49ers', 'Niners'],
      'SEA': ['Seattle Seahawks', 'Seahawks'],
      'TB': ['Tampa Bay Buccaneers', 'Buccaneers', 'Bucs'],
      'TEN': ['Tennessee Titans', 'Titans'],
      'WAS': ['Washington Commanders', 'Commanders']
    };
  }

  // Get NFL news from News API
  async getNFLNews(query = 'NFL', pageSize = 20) {
    if (!NEWS_API_KEY) {
      console.warn('No News API key configured');
      return null;
    }

    const cacheKey = `news-${query}-${pageSize}`;
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    try {
      const response = await axios.get(`${NEWS_BASE_URL}/everything`, {
        params: {
          q: query,
          language: 'en',
          sortBy: 'publishedAt',
          pageSize: pageSize,
          apiKey: NEWS_API_KEY,
          domains: 'espn.com,nfl.com,cbssports.com,foxsports.com,theringer.com,bleacherreport.com,profootballtalk.nbcsports.com'
        }
      });

      const data = response.data.articles;

      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      console.log(`Fetched ${data.length} NFL news articles`);
      return data;

    } catch (error) {
      console.error('News API Error:', error.response?.data || error.message);
      return null;
    }
  }

  // Get team-specific news
  async getTeamNews(teamCode) {
    const keywords = this.teamKeywords[teamCode];
    if (!keywords) return null;

    const query = keywords.join(' OR ');
    return this.getNFLNews(query, 10);
  }

  // Analyze sentiment of text (simple implementation)
  analyzeSentiment(text) {
    if (!text) return 0;

    // Positive words
    const positive = [
      'win', 'victory', 'great', 'excellent', 'strong', 'dominant', 'impressive',
      'success', 'triumph', 'outstanding', 'comeback', 'momentum', 'confidence',
      'healthy', 'return', 'cleared', 'ready', 'optimistic', 'upgrade', 'improve'
    ];

    // Negative words
    const negative = [
      'loss', 'defeat', 'injured', 'injury', 'out', 'questionable', 'doubtful',
      'struggle', 'poor', 'weak', 'concern', 'worry', 'setback', 'disappoint',
      'suspend', 'fine', 'penalty', 'turnover', 'mistake', 'problem', 'issue'
    ];

    const lowerText = text.toLowerCase();
    let score = 0;

    // Count positive and negative words
    positive.forEach(word => {
      if (lowerText.includes(word)) score += 0.1;
    });

    negative.forEach(word => {
      if (lowerText.includes(word)) score -= 0.1;
    });

    // Normalize to -1 to 1 range
    return Math.max(-1, Math.min(1, score));
  }

  // Extract teams mentioned in article
  extractTeamsMentioned(title, description) {
    const text = `${title} ${description}`.toLowerCase();
    const mentioned = [];

    for (const [code, keywords] of Object.entries(this.teamKeywords)) {
      if (keywords.some(keyword => text.includes(keyword.toLowerCase()))) {
        mentioned.push(code);
      }
    }

    return mentioned;
  }

  // Determine market impact based on news content
  determineMarketImpact(title, description, sentiment) {
    const text = `${title} ${description}`.toLowerCase();

    // High impact keywords
    const highImpact = ['injury', 'suspend', 'out', 'trade', 'fire', 'release', 'sign'];
    const hasHighImpact = highImpact.some(word => text.includes(word));

    if (hasHighImpact) {
      return sentiment < 0 ? 'Negative - Line may move against team' : 'Positive - Line may favor team';
    }

    if (Math.abs(sentiment) > 0.5) {
      return sentiment > 0 ? 'Slightly positive' : 'Slightly negative';
    }

    return 'Neutral';
  }

  // Sync news to Supabase
  async syncNewsToSupabase() {
    try {
      console.log('Starting News API to Supabase sync...');

      const newsData = await this.getNFLNews('NFL', 50);
      if (!newsData) {
        console.log('No news data available');
        return { total: 0, synced: 0, errors: [] };
      }

      const syncResults = {
        total: newsData.length,
        synced: 0,
        errors: []
      };

      for (const article of newsData) {
        try {
          const sentiment = this.analyzeSentiment(`${article.title} ${article.description}`);
          const teamsMentioned = this.extractTeamsMentioned(article.title, article.description);
          const marketImpact = this.determineMarketImpact(article.title, article.description, sentiment);

          // Build impact teams object
          const impactTeams = {};
          teamsMentioned.forEach(team => {
            impactTeams[team] = sentiment * 0.5; // Reduced impact per team
          });

          const newsRecord = {
            article_url: article.url,
            title: article.title,
            source: article.source.name,
            published_at: new Date(article.publishedAt).toISOString(),
            teams_mentioned: teamsMentioned,
            sentiment_score: sentiment,
            impact_teams: impactTeams,
            market_impact: marketImpact,
            created_at: new Date().toISOString()
          };

          // Upsert to Supabase
          const { error } = await supabase
            .from('news_sentiment')
            .upsert(newsRecord, {
              onConflict: 'article_url'
            });

          if (error) {
            syncResults.errors.push({
              url: article.url,
              error: error.message
            });
          } else {
            syncResults.synced++;
          }

        } catch (articleError) {
          syncResults.errors.push({
            url: article.url,
            error: articleError.message
          });
        }
      }

      console.log('News sync complete:', syncResults);
      return syncResults;

    } catch (error) {
      console.error('News sync failed:', error);
      throw error;
    }
  }

  // Get recent news with sentiment for specific teams
  async getTeamSentiment(teams) {
    try {
      const { data, error } = await supabase
        .from('news_sentiment')
        .select('*')
        .contains('teams_mentioned', teams)
        .order('published_at', { ascending: false })
        .limit(10);

      if (error) throw error;

      // Calculate aggregate sentiment
      if (data && data.length > 0) {
        const avgSentiment = data.reduce((sum, item) => sum + item.sentiment_score, 0) / data.length;

        return {
          articles: data,
          aggregateSentiment: avgSentiment,
          sentimentTrend: this.calculateSentimentTrend(data),
          marketOutlook: this.getMarketOutlook(avgSentiment)
        };
      }

      return null;

    } catch (error) {
      console.error('Error getting team sentiment:', error);
      return null;
    }
  }

  // Calculate sentiment trend
  calculateSentimentTrend(articles) {
    if (articles.length < 2) return 'stable';

    const recent = articles.slice(0, Math.floor(articles.length / 2));
    const older = articles.slice(Math.floor(articles.length / 2));

    const recentAvg = recent.reduce((sum, a) => sum + a.sentiment_score, 0) / recent.length;
    const olderAvg = older.reduce((sum, a) => sum + a.sentiment_score, 0) / older.length;

    const diff = recentAvg - olderAvg;

    if (diff > 0.2) return 'improving';
    if (diff < -0.2) return 'declining';
    return 'stable';
  }

  // Get market outlook based on sentiment
  getMarketOutlook(sentiment) {
    if (sentiment > 0.5) return 'Very Positive - Team likely favored';
    if (sentiment > 0.2) return 'Positive - Slight advantage';
    if (sentiment < -0.5) return 'Very Negative - Team likely unfavored';
    if (sentiment < -0.2) return 'Negative - Slight disadvantage';
    return 'Neutral - No significant impact';
  }

  // Start auto-sync for news
  startAutoSync(intervalMs = 1800000) { // Default 30 minutes
    console.log(`Starting news auto-sync every ${intervalMs/1000} seconds`);

    // Initial sync
    this.syncNewsToSupabase();

    // Set interval
    this.syncInterval = setInterval(() => {
      this.syncNewsToSupabase();
    }, intervalMs);

    return this.syncInterval;
  }

  // Stop auto-sync
  stopAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
      console.log('News auto-sync stopped');
    }
  }

  // Get news by category
  async getNewsByCategory(category) {
    const categoryQueries = {
      injuries: 'NFL injury report',
      trades: 'NFL trade rumors',
      betting: 'NFL betting odds lines',
      analysis: 'NFL game analysis preview',
      scores: 'NFL scores highlights'
    };

    const query = categoryQueries[category] || 'NFL';
    return this.getNFLNews(query, 15);
  }
}

// Create singleton instance
const newsService = new NewsService();

export default newsService;