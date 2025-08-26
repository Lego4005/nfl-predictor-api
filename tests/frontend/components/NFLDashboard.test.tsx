/**
 * Tests for NFLDashboard component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import '@testing-library/jest-dom';
import NFLDashboard from '../../../src/NFLDashboard';
import { DataSource } from '../../../src/types/nfl.types';
import * as apiService from '../../../src/services/apiService';

// Mock the API service
vi.mock('../../../src/services/apiService');
const mockApiService = apiService as any;

// Mock URL methods for download tests
global.URL.createObjectURL = vi.fn(() => 'mock-url');
global.URL.revokeObjectURL = vi.fn();

describe('NFLDashboard', () => {
  const mockWeeklyData = {
    best_picks: [
      { home: 'BUF', away: 'NYJ', su_pick: 'BUF', su_confidence: 0.75, matchup: 'NYJ @ BUF' },
      { home: 'KC', away: 'DEN', su_pick: 'KC', su_confidence: 0.68, matchup: 'DEN @ KC' }
    ],
    ats_picks: [
      { matchup: 'NYJ @ BUF', ats_pick: 'BUF -3.5', spread: -3.5, ats_confidence: 0.72 },
      { matchup: 'DEN @ KC', ats_pick: 'KC -7.0', spread: -7.0, ats_confidence: 0.65 }
    ],
    totals_picks: [
      { matchup: 'NYJ @ BUF', tot_pick: 'Under 45.5', total_line: 45.5, tot_confidence: 0.58 },
      { matchup: 'DEN @ KC', tot_pick: 'Over 52.0', total_line: 52.0, tot_confidence: 0.63 }
    ],
    prop_bets: [
      { 
        player: 'Josh Allen', 
        prop_type: 'Passing Yards', 
        pick: 'Over', 
        line: 285.5, 
        units: 'yds',
        confidence: 0.67, 
        bookmaker: 'DraftKings', 
        team: 'BUF', 
        opponent: 'NYJ' 
      }
    ],
    fantasy_picks: [
      { 
        player: 'Josh Allen', 
        position: 'QB', 
        salary: 8800, 
        projected_points: 22.5, 
        value_score: 2.56 
      }
    ],
    classic_lineup: [
      { 
        player: 'Josh Allen', 
        position: 'QB', 
        salary: 8800, 
        projected_points: 22.5, 
        value_score: 2.56 
      }
    ]
  };

  const mockApiResponse = {
    data: mockWeeklyData,
    source: DataSource.ODDS_API,
    cached: false,
    timestamp: '2025-01-15T12:00:00Z',
    notifications: []
  };

  beforeEach(() => {
    mockApiService.apiService = {
      getWeeklyPredictions: vi.fn(),
      downloadData: vi.fn(),
      getConfig: vi.fn(() => ({ baseUrl: 'http://localhost:3000' }))
    } as any;

    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders dashboard with initial loading state', () => {
    mockApiService.apiService.getWeeklyPredictions.mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading state
    );

    render(<NFLDashboard />);

    expect(screen.getByText('NFL 2025 Predictions — Week 1')).toBeInTheDocument();
    expect(screen.getByText('Fetching NFL predictions...')).toBeInTheDocument();
  });

  it('loads and displays weekly predictions data', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
      expect(screen.getByText('75.0%')).toBeInTheDocument();
    });

    expect(mockApiService.apiService.getWeeklyPredictions).toHaveBeenCalledWith(1);
  });

  it('handles API errors correctly', async () => {
    const errorMessage = 'API connection failed';
    mockApiService.apiService.getWeeklyPredictions.mockRejectedValue(new Error(errorMessage));

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText(`⚠️ ${errorMessage}`)).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('allows week selection', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    const weekSelect = screen.getByDisplayValue('Week 1');
    fireEvent.change(weekSelect, { target: { value: '5' } });

    await waitFor(() => {
      expect(mockApiService.apiService.getWeeklyPredictions).toHaveBeenCalledWith(5);
    });

    expect(screen.getByText('NFL 2025 Predictions — Week 5')).toBeInTheDocument();
  });

  it('switches between tabs correctly', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Top 5 Straight-Up Picks')).toBeInTheDocument();
    });

    // Switch to props tab
    fireEvent.click(screen.getByText('Prop Bets'));
    expect(screen.getByText('Top 5 Player Prop Bets')).toBeInTheDocument();
    expect(screen.getByText('Josh Allen')).toBeInTheDocument();

    // Switch to fantasy tab
    fireEvent.click(screen.getByText('Fantasy Picks'));
    expect(screen.getByText('Top 5 Fantasy Value Picks')).toBeInTheDocument();

    // Switch to lineup tab
    fireEvent.click(screen.getByText('Classic Lineup'));
    expect(screen.getByText('Classic Lineup')).toBeInTheDocument();
  });

  it('displays notifications from API response', async () => {
    const responseWithNotifications = {
      ...mockApiResponse,
      notifications: [
        { type: 'warning' as const, message: 'API rate limit approaching', retryable: false }
      ]
    };

    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(responseWithNotifications);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/API rate limit approaching/)).toBeInTheDocument();
    });
  });

  it('handles retry functionality', async () => {
    mockApiService.apiService.getWeeklyPredictions
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('⚠️ Network error')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    expect(mockApiService.apiService.getWeeklyPredictions).toHaveBeenCalledTimes(2);
  });

  it('handles refresh functionality', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('🔄 Refresh');
    fireEvent.click(refreshButton);

    expect(mockApiService.apiService.getWeeklyPredictions).toHaveBeenCalledTimes(2);
  });

  it('handles JSON download', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);
    mockApiService.apiService.downloadData.mockResolvedValue(new Blob(['{}'], { type: 'application/json' }));

    // Mock document methods
    const mockCreateElement = vi.spyOn(document, 'createElement');
    const mockAppendChild = vi.spyOn(document.body, 'appendChild');
    const mockRemoveChild = vi.spyOn(document.body, 'removeChild');
    const mockClick = vi.fn();

    mockCreateElement.mockReturnValue({
      href: '',
      download: '',
      click: mockClick
    } as any);

    mockAppendChild.mockImplementation(() => null as any);
    mockRemoveChild.mockImplementation(() => null as any);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download JSON');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(mockApiService.apiService.downloadData).toHaveBeenCalledWith(1, 'json');
    });

    expect(mockClick).toHaveBeenCalled();

    mockCreateElement.mockRestore();
    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
  });

  it('handles CSV download', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);
    mockApiService.apiService.downloadData.mockResolvedValue(new Blob(['header1,header2'], { type: 'text/csv' }));

    const mockCreateElement = vi.spyOn(document, 'createElement');
    const mockAppendChild = vi.spyOn(document.body, 'appendChild');
    const mockRemoveChild = vi.spyOn(document.body, 'removeChild');
    const mockClick = vi.fn();

    mockCreateElement.mockReturnValue({
      href: '',
      download: '',
      click: mockClick
    } as any);

    mockAppendChild.mockImplementation(() => null as any);
    mockRemoveChild.mockImplementation(() => null as any);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download CSV');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(mockApiService.apiService.downloadData).toHaveBeenCalledWith(1, 'csv');
    });

    mockCreateElement.mockRestore();
    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
  });

  it('handles PDF download', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);
    mockApiService.apiService.downloadData.mockResolvedValue(new Blob(['%PDF'], { type: 'application/pdf' }));

    const mockCreateElement = vi.spyOn(document, 'createElement');
    const mockAppendChild = vi.spyOn(document.body, 'appendChild');
    const mockRemoveChild = vi.spyOn(document.body, 'removeChild');
    const mockClick = vi.fn();

    mockCreateElement.mockReturnValue({
      href: '',
      download: '',
      click: mockClick
    } as any);

    mockAppendChild.mockImplementation(() => null as any);
    mockRemoveChild.mockImplementation(() => null as any);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download PDF');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(mockApiService.apiService.downloadData).toHaveBeenCalledWith(1, 'pdf');
    });

    mockCreateElement.mockRestore();
    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
  });

  it('handles download errors', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);
    mockApiService.apiService.downloadData.mockRejectedValue(new Error('Download failed'));

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download JSON');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByText(/Download failed: Download failed/)).toBeInTheDocument();
    });
  });

  it('disables controls during loading', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<NFLDashboard />);

    const weekSelect = screen.getByDisplayValue('Week 1');
    const refreshButton = screen.getByText('🔄 Refresh');
    const downloadButtons = screen.getAllByText(/Download/);

    expect(weekSelect).toBeDisabled();
    expect(refreshButton).toBeDisabled();
    downloadButtons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('shows data freshness information', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    // Should show data freshness component (mocked in actual implementation)
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  it('implements auto-refresh for live data', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    // Fast-forward 5 minutes to trigger auto-refresh
    vi.advanceTimersByTime(5 * 60 * 1000);

    await waitFor(() => {
      expect(mockApiService.apiService.getWeeklyPredictions).toHaveBeenCalledTimes(2);
    });
  });

  it('does not auto-refresh for mock data', async () => {
    const mockDataResponse = {
      ...mockApiResponse,
      source: DataSource.MOCK
    };

    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockDataResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    // Fast-forward 5 minutes
    vi.advanceTimersByTime(5 * 60 * 1000);

    // Should not have made additional calls for mock data
    expect(mockApiService.apiService.getWeeklyPredictions).toHaveBeenCalledTimes(1);
  });

  it('displays empty state when no data available', async () => {
    const emptyDataResponse = {
      ...mockApiResponse,
      data: {
        best_picks: [],
        ats_picks: [],
        totals_picks: [],
        prop_bets: [],
        fantasy_picks: [],
        classic_lineup: []
      }
    };

    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(emptyDataResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('No data.')).toBeInTheDocument();
    });
  });

  it('handles missing classic lineup data', async () => {
    const dataWithoutLineup = {
      ...mockApiResponse,
      data: {
        ...mockWeeklyData,
        classic_lineup: []
      }
    };

    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(dataWithoutLineup);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    // Switch to lineup tab
    fireEvent.click(screen.getByText('Classic Lineup'));
    expect(screen.getByText('Classic lineup data not available for this week.')).toBeInTheDocument();
  });

  it('formats percentage values correctly', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('75.0%')).toBeInTheDocument(); // 0.75 * 100
      expect(screen.getByText('68.0%')).toBeInTheDocument(); // 0.68 * 100
    });
  });

  it('formats money values correctly', async () => {
    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(mockApiResponse);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });

    // Switch to fantasy tab
    fireEvent.click(screen.getByText('Fantasy Picks'));
    expect(screen.getByText('8,800')).toBeInTheDocument(); // Formatted salary
  });

  it('dismisses notifications correctly', async () => {
    const responseWithNotifications = {
      ...mockApiResponse,
      notifications: [
        { type: 'warning' as const, message: 'Test notification', retryable: false }
      ]
    };

    mockApiService.apiService.getWeeklyPredictions.mockResolvedValue(responseWithNotifications);

    render(<NFLDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Test notification/)).toBeInTheDocument();
    });

    const dismissButton = screen.getByLabelText('Dismiss notification');
    fireEvent.click(dismissButton);

    expect(screen.queryByText(/Test notification/)).not.toBeInTheDocument();
  });
});