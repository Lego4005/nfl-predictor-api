/**
 * Tests for NotificationBanner component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import '@testing-library/jest-dom';
import NotificationBanner from '../../../src/components/NotificationBanner';
import { DataSource } from '../../../src/types/nfl.types';
import { Notification } from '../../../src/types/api.types';

describe('NotificationBanner', () => {
  const mockNotifications: Notification[] = [
    {
      type: 'error',
      message: 'API connection failed',
      source: DataSource.ODDS_API,
      retryable: true
    },
    {
      type: 'warning',
      message: 'Rate limit approaching',
      source: DataSource.SPORTSDATA_IO,
      retryable: false
    },
    {
      type: 'info',
      message: 'Using cached data',
      source: DataSource.CACHE,
      retryable: false
    },
    {
      type: 'success',
      message: 'Data updated successfully',
      retryable: false
    }
  ];

  const mockOnDismiss = vi.fn();

  beforeEach(() => {
    mockOnDismiss.mockClear();
  });

  it('renders nothing when no notifications provided', () => {
    const { container } = render(<NotificationBanner notifications={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when notifications array is empty', () => {
    const { container } = render(<NotificationBanner notifications={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders single notification correctly', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[0]]} 
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText(/The Odds API: API connection failed/)).toBeInTheDocument();
    expect(screen.getByText('⚠️')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
    expect(screen.getByLabelText('Dismiss notification')).toBeInTheDocument();
  });

  it('renders multiple notifications correctly', () => {
    render(
      <NotificationBanner 
        notifications={mockNotifications.slice(0, 3)} 
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText(/The Odds API: API connection failed/)).toBeInTheDocument();
    expect(screen.getByText(/SportsDataIO: Rate limit approaching/)).toBeInTheDocument();
    expect(screen.getByText(/Cache: Using cached data/)).toBeInTheDocument();
  });

  it('respects maxVisible prop', () => {
    render(
      <NotificationBanner 
        notifications={mockNotifications} 
        onDismiss={mockOnDismiss}
        maxVisible={2}
      />
    );

    // Should show first 2 notifications
    expect(screen.getByText(/The Odds API: API connection failed/)).toBeInTheDocument();
    expect(screen.getByText(/SportsDataIO: Rate limit approaching/)).toBeInTheDocument();
    
    // Should not show the 3rd and 4th notifications
    expect(screen.queryByText(/Cache: Using cached data/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Data updated successfully/)).not.toBeInTheDocument();

    // Should show "more notifications" indicator
    expect(screen.getByText('+2 more notifications')).toBeInTheDocument();
  });

  it('displays correct icons for different notification types', () => {
    render(
      <NotificationBanner 
        notifications={mockNotifications} 
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('⚠️')).toBeInTheDocument(); // error
    expect(screen.getByText('⚡')).toBeInTheDocument(); // warning
    expect(screen.getByText('ℹ️')).toBeInTheDocument(); // info
    expect(screen.getByText('✅')).toBeInTheDocument(); // success
  });

  it('shows retry button only for retryable notifications', () => {
    render(
      <NotificationBanner 
        notifications={mockNotifications} 
        onDismiss={mockOnDismiss}
      />
    );

    const retryButtons = screen.getAllByText('Retry');
    expect(retryButtons).toHaveLength(1); // Only the first notification is retryable
  });

  it('calls onDismiss when dismiss button is clicked', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[0]]} 
        onDismiss={mockOnDismiss}
      />
    );

    const dismissButton = screen.getByLabelText('Dismiss notification');
    fireEvent.click(dismissButton);

    expect(mockOnDismiss).toHaveBeenCalledWith(0);
  });

  it('handles notifications without source correctly', () => {
    const notificationWithoutSource: Notification = {
      type: 'info',
      message: 'General information',
      retryable: false
    };

    render(
      <NotificationBanner 
        notifications={[notificationWithoutSource]} 
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('General information')).toBeInTheDocument();
    expect(screen.queryByText(':')).not.toBeInTheDocument(); // No source prefix
  });

  it('applies correct styling for error notifications', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[0]]} 
        onDismiss={mockOnDismiss}
      />
    );

    const notification = screen.getByText(/The Odds API: API connection failed/).closest('div');
    expect(notification).toHaveStyle({
      backgroundColor: '#fef2f2',
      borderColor: '#fecaca',
      color: '#dc2626'
    });
  });

  it('applies correct styling for warning notifications', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[1]]} 
        onDismiss={mockOnDismiss}
      />
    );

    const notification = screen.getByText(/SportsDataIO: Rate limit approaching/).closest('div');
    expect(notification).toHaveStyle({
      backgroundColor: '#fffbeb',
      borderColor: '#fed7aa',
      color: '#d97706'
    });
  });

  it('applies correct styling for info notifications', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[2]]} 
        onDismiss={mockOnDismiss}
      />
    );

    const notification = screen.getByText(/Cache: Using cached data/).closest('div');
    expect(notification).toHaveStyle({
      backgroundColor: '#eff6ff',
      borderColor: '#bfdbfe',
      color: '#2563eb'
    });
  });

  it('applies correct styling for success notifications', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[3]]} 
        onDismiss={mockOnDismiss}
      />
    );

    const notification = screen.getByText(/Data updated successfully/).closest('div');
    expect(notification).toHaveStyle({
      backgroundColor: '#f0fdf4',
      borderColor: '#bbf7d0',
      color: '#16a34a'
    });
  });

  it('handles retry button click correctly', () => {
    // Mock window.location.reload
    const mockReload = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true
    });

    render(
      <NotificationBanner 
        notifications={[mockNotifications[0]]} 
        onDismiss={mockOnDismiss}
      />
    );

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(mockReload).toHaveBeenCalled();
  });

  it('renders without onDismiss prop', () => {
    render(
      <NotificationBanner 
        notifications={[mockNotifications[0]]} 
      />
    );

    expect(screen.getByText(/The Odds API: API connection failed/)).toBeInTheDocument();
    expect(screen.queryByLabelText('Dismiss notification')).not.toBeInTheDocument();
  });

  it('handles empty message gracefully', () => {
    const notificationWithEmptyMessage: Notification = {
      type: 'info',
      message: '',
      retryable: false
    };

    render(
      <NotificationBanner 
        notifications={[notificationWithEmptyMessage]} 
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('ℹ️')).toBeInTheDocument();
  });

  it('formats source names correctly', () => {
    const notificationsWithDifferentSources: Notification[] = [
      { type: 'info', message: 'Test', source: DataSource.ODDS_API, retryable: false },
      { type: 'info', message: 'Test', source: DataSource.SPORTSDATA_IO, retryable: false },
      { type: 'info', message: 'Test', source: DataSource.ESPN_API, retryable: false },
      { type: 'info', message: 'Test', source: DataSource.NFL_API, retryable: false },
      { type: 'info', message: 'Test', source: DataSource.RAPID_API, retryable: false },
      { type: 'info', message: 'Test', source: DataSource.CACHE, retryable: false }
    ];

    render(
      <NotificationBanner 
        notifications={notificationsWithDifferentSources} 
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('The Odds API: Test')).toBeInTheDocument();
    expect(screen.getByText('SportsDataIO: Test')).toBeInTheDocument();
    expect(screen.getByText('ESPN API: Test')).toBeInTheDocument();
    expect(screen.getByText('NFL.com API: Test')).toBeInTheDocument();
    expect(screen.getByText('RapidAPI: Test')).toBeInTheDocument();
    expect(screen.getByText('Cache: Test')).toBeInTheDocument();
  });
});