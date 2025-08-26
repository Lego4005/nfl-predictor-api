import { DataSource } from './nfl.types';

// API Response wrapper
export interface APIResponse<T> {
  data: T;
  source: DataSource;
  cached: boolean;
  timestamp: string;
  notifications?: Notification[];
}

// Error and notification types
export interface Notification {
  type: 'error' | 'warning' | 'info' | 'success';
  message: string;
  source?: DataSource;
  retryable: boolean;
}

export enum ErrorType {
  API_UNAVAILABLE = 'api_unavailable',
  RATE_LIMITED = 'rate_limited',
  INVALID_DATA = 'invalid_data',
  NETWORK_ERROR = 'network_error',
  AUTHENTICATION_ERROR = 'authentication_error',
  CACHE_ERROR = 'cache_error'
}

export interface ErrorContext {
  source: DataSource;
  endpoint: string;
  week: number;
  retry_count: number;
  timestamp: string;
}

// API Configuration
export interface APIConfig {
  baseUrl: string;
  timeout: number;
  maxRetries: number;
  retryDelay: number;
}

// HTTP Client types
export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: string;
  timeout?: number;
}

export interface RetryOptions {
  maxRetries: number;
  retryDelay: number;
  backoffFactor: number;
}