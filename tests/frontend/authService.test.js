import { jest } from '@jest/globals';
import authService from '../../src/services/authService.js';

// Mock Supabase client
const mockSupabaseAuth = {
  signUp: jest.fn(),
  signInWithPassword: jest.fn(),
  signInWithOAuth: jest.fn(),
  signOut: jest.fn(),
  getSession: jest.fn(),
  getUser: jest.fn(),
  updateUser: jest.fn(),
  resetPasswordForEmail: jest.fn(),
  refreshSession: jest.fn(),
  resend: jest.fn(),
  onAuthStateChange: jest.fn()
};

const mockSupabase = {
  auth: mockSupabaseAuth
};

// Mock the supabaseClient module
jest.unstable_mockModule('../../src/services/supabaseClient.js', () => ({
  supabase: mockSupabase
}));

describe('AuthService', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();

    // Reset auth service state
    authService.currentUser = null;
    authService.isInitialized = false;
    authService.authListeners.clear();
  });

  describe('signUp', () => {
    test('should successfully sign up a new user', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        user_metadata: { name: 'Test User' }
      };

      const mockSession = {
        access_token: 'mock-token',
        user: mockUser
      };

      mockSupabaseAuth.signUp.mockResolvedValue({
        data: { user: mockUser, session: mockSession },
        error: null
      });

      const result = await authService.signUp('test@example.com', 'password123', { name: 'Test User' });

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(result.session).toEqual(mockSession);
      expect(mockSupabaseAuth.signUp).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        options: {
          data: { name: 'Test User' }
        }
      });
    });

    test('should handle signup requiring email confirmation', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com'
      };

      mockSupabaseAuth.signUp.mockResolvedValue({
        data: { user: mockUser, session: null },
        error: null
      });

      const result = await authService.signUp('test@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.requiresConfirmation).toBe(true);
      expect(result.message).toBe('Please check your email to confirm your account');
    });

    test('should handle signup errors', async () => {
      mockSupabaseAuth.signUp.mockResolvedValue({
        data: null,
        error: { message: 'Email already registered', status: 422 }
      });

      const result = await authService.signUp('test@example.com', 'password123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Email already registered');
      expect(result.code).toBe(422);
    });

    test('should validate required fields', async () => {
      const result1 = await authService.signUp('', 'password123');
      expect(result1.success).toBe(false);
      expect(result1.error).toBe('Email and password are required');

      const result2 = await authService.signUp('test@example.com', '');
      expect(result2.success).toBe(false);
      expect(result2.error).toBe('Email and password are required');
    });

    test('should validate password length', async () => {
      const result = await authService.signUp('test@example.com', '123');
      expect(result.success).toBe(false);
      expect(result.error).toBe('Password must be at least 6 characters long');
    });
  });

  describe('signIn', () => {
    test('should successfully sign in a user', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com'
      };

      const mockSession = {
        access_token: 'mock-token',
        user: mockUser
      };

      mockSupabaseAuth.signInWithPassword.mockResolvedValue({
        data: { user: mockUser, session: mockSession },
        error: null
      });

      const result = await authService.signIn('test@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(result.session).toEqual(mockSession);
      expect(authService.currentUser).toEqual(mockUser);
      expect(mockSupabaseAuth.signInWithPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });

    test('should handle signin errors', async () => {
      mockSupabaseAuth.signInWithPassword.mockResolvedValue({
        data: null,
        error: { message: 'Invalid credentials', status: 400 }
      });

      const result = await authService.signIn('test@example.com', 'wrongpassword');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
      expect(result.code).toBe(400);
    });

    test('should validate required fields', async () => {
      const result1 = await authService.signIn('', 'password123');
      expect(result1.success).toBe(false);
      expect(result1.error).toBe('Email and password are required');

      const result2 = await authService.signIn('test@example.com', '');
      expect(result2.success).toBe(false);
      expect(result2.error).toBe('Email and password are required');
    });
  });

  describe('signOut', () => {
    test('should successfully sign out a user', async () => {
      authService.currentUser = { id: '123', email: 'test@example.com' };

      mockSupabaseAuth.signOut.mockResolvedValue({
        error: null
      });

      const result = await authService.signOut();

      expect(result.success).toBe(true);
      expect(result.message).toBe('Signed out successfully');
      expect(authService.currentUser).toBeNull();
      expect(mockSupabaseAuth.signOut).toHaveBeenCalled();
    });

    test('should handle signout errors', async () => {
      mockSupabaseAuth.signOut.mockResolvedValue({
        error: { message: 'Sign out failed' }
      });

      const result = await authService.signOut();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Sign out failed');
    });
  });

  describe('getCurrentUser', () => {
    test('should return current user', () => {
      const mockUser = { id: '123', email: 'test@example.com' };
      authService.currentUser = mockUser;

      const result = authService.getCurrentUser();

      expect(result).toEqual(mockUser);
    });

    test('should return null when no user', () => {
      authService.currentUser = null;

      const result = authService.getCurrentUser();

      expect(result).toBeNull();
    });
  });

  describe('getCurrentSession', () => {
    test('should successfully get current session', async () => {
      const mockSession = {
        access_token: 'mock-token',
        user: { id: '123', email: 'test@example.com' }
      };

      mockSupabaseAuth.getSession.mockResolvedValue({
        data: { session: mockSession },
        error: null
      });

      const result = await authService.getCurrentSession();

      expect(result.success).toBe(true);
      expect(result.session).toEqual(mockSession);
      expect(result.user).toEqual(mockSession.user);
    });

    test('should handle session errors', async () => {
      mockSupabaseAuth.getSession.mockResolvedValue({
        data: { session: null },
        error: { message: 'Session not found' }
      });

      const result = await authService.getCurrentSession();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Session not found');
      expect(result.session).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    test('should return true when user is authenticated', () => {
      authService.currentUser = { id: '123', email: 'test@example.com' };

      expect(authService.isAuthenticated()).toBe(true);
    });

    test('should return false when user is not authenticated', () => {
      authService.currentUser = null;

      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('resetPassword', () => {
    test('should successfully send reset password email', async () => {
      mockSupabaseAuth.resetPasswordForEmail.mockResolvedValue({
        data: {},
        error: null
      });

      const result = await authService.resetPassword('test@example.com');

      expect(result.success).toBe(true);
      expect(result.message).toBe('Password reset email sent');
      expect(mockSupabaseAuth.resetPasswordForEmail).toHaveBeenCalledWith(
        'test@example.com',
        expect.any(Object)
      );
    });

    test('should handle reset password errors', async () => {
      mockSupabaseAuth.resetPasswordForEmail.mockResolvedValue({
        data: null,
        error: { message: 'Email not found' }
      });

      const result = await authService.resetPassword('test@example.com');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Email not found');
    });

    test('should validate email requirement', async () => {
      const result = await authService.resetPassword('');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Email is required');
    });
  });

  describe('updatePassword', () => {
    test('should successfully update password', async () => {
      const mockUser = { id: '123', email: 'test@example.com' };

      mockSupabaseAuth.updateUser.mockResolvedValue({
        data: { user: mockUser },
        error: null
      });

      const result = await authService.updatePassword('newpassword123');

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(result.message).toBe('Password updated successfully');
      expect(mockSupabaseAuth.updateUser).toHaveBeenCalledWith({
        password: 'newpassword123'
      });
    });

    test('should validate password length', async () => {
      const result = await authService.updatePassword('123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Password must be at least 6 characters long');
    });
  });

  describe('updateProfile', () => {
    test('should successfully update user profile', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        user_metadata: { name: 'Updated Name' }
      };

      authService.currentUser = { id: '123', email: 'test@example.com' };

      mockSupabaseAuth.updateUser.mockResolvedValue({
        data: { user: mockUser },
        error: null
      });

      const result = await authService.updateProfile({ name: 'Updated Name' });

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(result.message).toBe('Profile updated successfully');
      expect(authService.currentUser).toEqual(mockUser);
      expect(mockSupabaseAuth.updateUser).toHaveBeenCalledWith({
        data: { name: 'Updated Name' }
      });
    });

    test('should require authenticated user', async () => {
      authService.currentUser = null;

      const result = await authService.updateProfile({ name: 'Updated Name' });

      expect(result.success).toBe(false);
      expect(result.error).toBe('User must be authenticated to update profile');
    });
  });

  describe('OAuth signin', () => {
    test('should successfully initiate OAuth signin', async () => {
      mockSupabaseAuth.signInWithOAuth.mockResolvedValue({
        data: { url: 'https://oauth.url' },
        error: null
      });

      const result = await authService.signInWithOAuth('google');

      expect(result.success).toBe(true);
      expect(result.data).toEqual({ url: 'https://oauth.url' });
      expect(mockSupabaseAuth.signInWithOAuth).toHaveBeenCalledWith({
        provider: 'google',
        options: {
          redirectTo: undefined
        }
      });
    });

    test('should handle OAuth signin errors', async () => {
      mockSupabaseAuth.signInWithOAuth.mockResolvedValue({
        data: null,
        error: { message: 'OAuth provider not configured' }
      });

      const result = await authService.signInWithOAuth('google');

      expect(result.success).toBe(false);
      expect(result.error).toBe('OAuth provider not configured');
    });
  });

  describe('Auth state management', () => {
    test('should handle auth state listeners', () => {
      const mockListener = jest.fn();

      const unsubscribe = authService.onAuthStateChange(mockListener);

      // Test listener addition
      expect(authService.authListeners.has(mockListener)).toBe(true);

      // Test notification
      authService.notifyAuthStateChange('SIGNED_IN', { user: { id: '123' } });
      expect(mockListener).toHaveBeenCalledWith('SIGNED_IN', { user: { id: '123' } }, authService.currentUser);

      // Test unsubscribe
      unsubscribe();
      expect(authService.authListeners.has(mockListener)).toBe(false);
    });

    test('should handle auth state change events', () => {
      const mockUser = { id: '123', email: 'test@example.com' };
      const mockSession = { user: mockUser };

      // Test SIGNED_IN
      authService.handleAuthStateChange('SIGNED_IN', mockSession);
      expect(authService.currentUser).toEqual(mockUser);

      // Test SIGNED_OUT
      authService.handleAuthStateChange('SIGNED_OUT', null);
      expect(authService.currentUser).toBeNull();

      // Test TOKEN_REFRESHED
      authService.handleAuthStateChange('TOKEN_REFRESHED', mockSession);
      expect(authService.currentUser).toEqual(mockUser);
    });
  });

  describe('Utility methods', () => {
    test('should get access token', async () => {
      const mockSession = {
        access_token: 'mock-access-token',
        user: { id: '123' }
      };

      mockSupabaseAuth.getSession.mockResolvedValue({
        data: { session: mockSession },
        error: null
      });

      const token = await authService.getAccessToken();

      expect(token).toBe('mock-access-token');
    });

    test('should return null when no session', async () => {
      mockSupabaseAuth.getSession.mockResolvedValue({
        data: { session: null },
        error: null
      });

      const token = await authService.getAccessToken();

      expect(token).toBeNull();
    });

    test('should check email confirmation status', () => {
      authService.currentUser = {
        id: '123',
        email: 'test@example.com',
        email_confirmed_at: '2023-01-01T00:00:00.000Z'
      };

      expect(authService.isEmailConfirmed()).toBe(true);

      authService.currentUser.email_confirmed_at = null;
      expect(authService.isEmailConfirmed()).toBe(false);
    });
  });
});