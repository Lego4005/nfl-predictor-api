/**
 * Tests for APIService
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { apiService } from '../../../src/services/apiService';
import { DataSource } from '../../../src/types/nfl.types';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('APIService', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  describe('getWeeklyPredictions', () => {
    it('makes correct API call for weekly predictions', async () => {
      const mockData = {
        best_picks: [{ home: 'BUF', away: 'NYJ', su_pick: 'BUF', su_confidence: 0.75 }],
        ats_picks: [],
        totals_picks: [],
        prop_bets: [],
        fantasy_picks: [],
        classic_lineup: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/best-picks/2025/1'),
        expect.objectContaining({
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        })
      );

      expect(result.data).toEqual(mockData);
      expect(result.source).toBe(DataSource.MOCK);
      expect(result.cached).toBe(false);
      expect(result.timestamp).toBeDefined();
    });

    it('includes cache-busting timestamp in URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: new Map()
      });

      await apiService.getWeeklyPredictions(5);

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toMatch(/t=\d+/);
    });

    it('handles HTTP errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('HTTP 404: Not Found');
    });

    it('handles network errors correctly', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Failed to fetch'));

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Network error. Please check your connection and try again.');
    });

    it('handles timeout correctly', async () => {
      mockFetch.mockImplementationOnce(() => 
        new Promise((resolve) => {
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({})
          }), 15000); // Longer than default timeout
        })
      );

      const promise = apiService.getWeeklyPredictions(1);
      
      // Fast-forward time to trigger timeout
      vi.advanceTimersByTime(11000);

      await expect(promise).rejects.toThrow('Request timed out. Please try again.');
    });

    it('retries on server errors', async () => {
      // First call fails with 500
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        })
        // Second call succeeds
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: 'success' }),
          headers: new Map()
        });

      const result = await apiService.getWeeklyPredictions(1);

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result.data).toEqual({ data: 'success' });
    });

    it('retries on rate limit errors (429)', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          statusText: 'Too Many Requests'
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: 'success' }),
          headers: new Map()
        });

      const result = await apiService.getWeeklyPredictions(1);

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result.data).toEqual({ data: 'success' });
    });

    it('does not retry on client errors (4xx except 429)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request'
      });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('HTTP 400: Bad Request');
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('implements exponential backoff for retries', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error'
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: 'success' }),
          headers: new Map()
        });

      const promise = apiService.getWeeklyPredictions(1);

      // Fast-forward through retry delays
      vi.advanceTimersByTime(1000); // First retry delay
      vi.advanceTimersByTime(2000); // Second retry delay (exponential backoff)

      const result = await promise;

      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result.data).toEqual({ data: 'success' });
    });

    it('stops retrying after max attempts', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Server error. Our team has been notified. Please try again later.');
      expect(mockFetch).toHaveBeenCalledTimes(4); // 1 initial + 3 retries
    });
  });

  describe('downloadData', () => {
    it('downloads JSON data correctly', async () => {
      const mockBlob = new Blob(['{"data": "test"}'], { type: 'application/json' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });

      const result = await apiService.downloadData(1, 'json');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/best-picks/2025/1/download?format=json'),
        expect.objectContaining({ method: 'GET' })
      );

      expect(result).toEqual(mockBlob);
    });

    it('downloads CSV data correctly', async () => {
      const mockBlob = new Blob(['header1,header2\nvalue1,value2'], { type: 'text/csv' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });

      const result = await apiService.downloadData(2, 'csv');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/best-picks/2025/2/download?format=csv'),
        expect.objectContaining({ method: 'GET' })
      );

      expect(result).toEqual(mockBlob);
    });

    it('downloads PDF data correctly', async () => {
      const mockBlob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });

      const result = await apiService.downloadData(3, 'pdf');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/best-picks/2025/3/download?format=pdf'),
        expect.objectContaining({ method: 'GET' })
      );

      expect(result).toEqual(mockBlob);
    });

    it('handles download errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      await expect(apiService.downloadData(1, 'json')).rejects.toThrow('Download failed: HTTP 404');
    });

    it('handles download timeout correctly', async () => {
      mockFetch.mockImplementationOnce(() => 
        new Promise((resolve) => {
          setTimeout(() => resolve({
            ok: true,
            blob: async () => new Blob()
          }), 15000);
        })
      );

      const promise = apiService.downloadData(1, 'json');
      vi.advanceTimersByTime(11000);

      await expect(promise).rejects.toThrow('Request timed out. Please try again.');
    });
  });

  describe('data source detection', () => {
    it('detects data source from response source field', async () => {
      const mockData = {
        source: DataSource.ODDS_API,
        best_picks: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.source).toBe(DataSource.ODDS_API);
    });

    it('detects data source from first pick source', async () => {
      const mockData = {
        best_picks: [{ source: DataSource.SPORTSDATA_IO }],
        ats_picks: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.source).toBe(DataSource.SPORTSDATA_IO);
    });

    it('defaults to MOCK when no source detected', async () => {
      const mockData = {
        best_picks: [],
        ats_picks: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.source).toBe(DataSource.MOCK);
    });
  });

  describe('cache detection', () => {
    it('detects cached response from x-cache-status header', async () => {
      const headers = new Map();
      headers.set('x-cache-status', 'hit');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.cached).toBe(true);
    });

    it('detects cached response from cache-control header', async () => {
      const headers = new Map();
      headers.set('cache-control', 'max-age=3600');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.cached).toBe(true);
    });

    it('detects non-cached response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.cached).toBe(false);
    });
  });

  describe('notification extraction', () => {
    it('extracts notifications from response data', async () => {
      const mockNotifications = [
        { type: 'warning', message: 'API rate limit approaching', retryable: false }
      ];

      const mockData = {
        best_picks: [],
        notifications: mockNotifications
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.notifications).toEqual(mockNotifications);
    });

    it('returns empty array when no notifications', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ best_picks: [] }),
        headers: new Map()
      });

      const result = await apiService.getWeeklyPredictions(1);
      expect(result.notifications).toEqual([]);
    });
  });

  describe('configuration', () => {
    it('allows updating configuration', () => {
      const newConfig = {
        baseUrl: 'https://new-api.example.com',
        timeout: 15000
      };

      apiService.updateConfig(newConfig);
      const config = apiService.getConfig();

      expect(config.baseUrl).toBe(newConfig.baseUrl);
      expect(config.timeout).toBe(newConfig.timeout);
      expect(config.maxRetries).toBe(3); // Should keep existing values
    });

    it('returns current configuration', () => {
      const config = apiService.getConfig();

      expect(config).toHaveProperty('baseUrl');
      expect(config).toHaveProperty('timeout');
      expect(config).toHaveProperty('maxRetries');
      expect(config).toHaveProperty('retryDelay');
    });
  });

  describe('error message formatting', () => {
    it('formats timeout errors correctly', async () => {
      mockFetch.mockRejectedValueOnce({ name: 'AbortError' });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Request timed out. Please try again.');
    });

    it('formats network errors correctly', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Failed to fetch'));

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Network error. Please check your connection and try again.');
    });

    it('formats rate limit errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests'
      });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Rate limit exceeded. Please wait a moment and try again.');
    });

    it('formats server errors correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Server error. Our team has been notified. Please try again later.');
    });

    it('formats client errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request'
      });

      await expect(apiService.getWeeklyPredictions(1)).rejects.toThrow('Request failed. Please refresh the page and try again.');
    });
  });
});