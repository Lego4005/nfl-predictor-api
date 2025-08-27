import { 
  APIResponse, 
  APIConfig, 
  RequestOptions, 
  RetryOptions, 
  Notification, 
  ErrorType 
} from '../types/api.types';
import { 
  GamePrediction, 
  ATSPrediction, 
  TotalsPrediction, 
  PropBet, 
  FantasyPick,
  DataSource 
} from '../types/nfl.types';

// Weekly predictions data structure (legacy format)
export interface WeeklyPredictions {
  best_picks: GamePrediction[];
  ats_picks: ATSPrediction[];
  totals_picks: TotalsPrediction[];
  prop_bets: PropBet[];
  fantasy_picks: FantasyPick[];
  classic_lineup: FantasyPick[];
}

class APIService {
  private config: APIConfig;
  private retryOptions: RetryOptions;

  constructor() {
    this.config = {
      baseUrl: import.meta.env.VITE_API_BASE || 'http://localhost:8080',
      timeout: 10000, // 10 seconds
      maxRetries: 3,
      retryDelay: 1000 // 1 second
    };

    this.retryOptions = {
      maxRetries: this.config.maxRetries,
      retryDelay: this.config.retryDelay,
      backoffFactor: 2.0
    };
  }

  /**
   * Makes HTTP request with timeout and error handling
   */
  private async makeRequest<T>(
    url: string, 
    options: RequestOptions = {}
  ): Promise<APIResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.config.timeout);

    try {
      const response = await fetch(url, {
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        body: options.body,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Wrap response in APIResponse format
      return {
        data,
        source: this.determineDataSource(data),
        cached: this.isCachedResponse(response),
        timestamp: new Date().toISOString(),
        notifications: this.extractNotifications(data)
      };

    } catch (error) {
      clearTimeout(timeoutId);
      throw this.handleRequestError(error, url);
    }
  }

  /**
   * Makes request with retry logic and exponential backoff
   */
  private async makeRequestWithRetry<T>(
    url: string,
    options: RequestOptions = {}
  ): Promise<APIResponse<T>> {
    let lastError: Error;

    for (let attempt = 0; attempt <= this.retryOptions.maxRetries; attempt++) {
      try {
        return await this.makeRequest<T>(url, options);
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on client errors (4xx) except 429 (rate limited)
        if (this.isClientError(error) && !this.isRateLimited(error)) {
          throw error;
        }

        // Don't retry on last attempt
        if (attempt === this.retryOptions.maxRetries) {
          break;
        }

        // Calculate delay with exponential backoff
        const delay = this.retryOptions.retryDelay * Math.pow(this.retryOptions.backoffFactor, attempt);
        await this.sleep(delay);
      }
    }

    throw lastError!;
  }

  /**
   * Fetches weekly predictions data
   */
  async getWeeklyPredictions(week: number): Promise<APIResponse<WeeklyPredictions>> {
    const url = `${this.config.baseUrl}/v1/best-picks/2025/${week}?t=${Date.now()}`;
    return this.makeRequestWithRetry<WeeklyPredictions>(url);
  }

  /**
   * Downloads data in specified format
   */
  async downloadData(week: number, format: 'json' | 'csv' | 'pdf'): Promise<Blob> {
    const url = `${this.config.baseUrl}/v1/best-picks/2025/${week}/download?format=${format}&t=${Date.now()}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Download failed: HTTP ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      clearTimeout(timeoutId);
      throw this.handleRequestError(error, url);
    }
  }

  /**
   * Determines data source from response
   */
  private determineDataSource(data: any): DataSource {
    if (data.source) {
      return data.source as DataSource;
    }
    
    // Check for indicators of live vs mock data
    if (data.best_picks && data.best_picks.length > 0) {
      const firstPick = data.best_picks[0];
      if (firstPick.source) {
        return firstPick.source as DataSource;
      }
    }
    
    return DataSource.MOCK; // Default fallback
  }

  /**
   * Checks if response is from cache
   */
  private isCachedResponse(response: Response): boolean {
    return response.headers.get('x-cache-status') === 'hit' ||
           response.headers.get('cache-control')?.includes('max-age') === true;
  }

  /**
   * Extracts notifications from response data
   */
  private extractNotifications(data: any): Notification[] {
    if (data.notifications && Array.isArray(data.notifications)) {
      return data.notifications;
    }
    return [];
  }

  /**
   * Handles request errors and creates user-friendly messages
   */
  private handleRequestError(error: any, url: string): Error {
    if (error.name === 'AbortError') {
      return new Error('Request timed out. Please try again.');
    }

    if (error.message?.includes('Failed to fetch')) {
      return new Error('Network error. Please check your connection and try again.');
    }

    if (error.message?.includes('HTTP 429')) {
      return new Error('Rate limit exceeded. Please wait a moment and try again.');
    }

    if (error.message?.includes('HTTP 5')) {
      return new Error('Server error. Our team has been notified. Please try again later.');
    }

    if (error.message?.includes('HTTP 4')) {
      return new Error('Request failed. Please refresh the page and try again.');
    }

    return new Error(`Request failed: ${error.message || 'Unknown error'}`);
  }

  /**
   * Checks if error is a client error (4xx)
   */
  private isClientError(error: any): boolean {
    return error.message?.includes('HTTP 4') === true;
  }

  /**
   * Checks if error is rate limiting (429)
   */
  private isRateLimited(error: any): boolean {
    return error.message?.includes('HTTP 429') === true;
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Updates API configuration
   */
  updateConfig(newConfig: Partial<APIConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Gets current configuration
   */
  getConfig(): APIConfig {
    return { ...this.config };
  }
}

// Export singleton instance
export const apiService = new APIService();
export default apiService;