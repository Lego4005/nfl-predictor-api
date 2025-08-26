import { Notification } from './api.types';
import { DataSource } from './nfl.types';

// Loading states
export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

// Component props
export interface NotificationBannerProps {
  notifications: Notification[];
  onDismiss?: (index: number) => void;
  maxVisible?: number;
}

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorBoundaryState>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export interface LoadingIndicatorProps {
  isLoading: boolean;
  message?: string;
  progress?: number;
  size?: 'small' | 'medium' | 'large';
}

// Data freshness indicator
export interface DataFreshnessProps {
  timestamp: string;
  source: DataSource;
  cached: boolean;
}

// Retry button props
export interface RetryButtonProps {
  onRetry: () => void;
  isRetrying: boolean;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

// Notification types for UI
export type NotificationType = 'error' | 'warning' | 'info' | 'success';

export interface UINotification extends Notification {
  id: string;
  timestamp: string;
  dismissed?: boolean;
}