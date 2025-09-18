import { supabase } from './supabaseClient.js';

/**
 * Authentication service for user management using Supabase
 * Handles user registration, login, logout, and session management
 */
class AuthService {
  constructor() {
    this.currentUser = null;
    this.isInitialized = false;
    this.authListeners = new Set();

    // Initialize session on service creation
    this.initialize();
  }

  /**
   * Initialize the auth service and restore session
   */
  async initialize() {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) {
        console.warn('Auth initialization error:', error.message);
      } else if (session) {
        this.currentUser = session.user;
        this.notifyAuthStateChange('SIGNED_IN', session);
      }

      // Set up auth state listener
      supabase.auth.onAuthStateChange((event, session) => {
        this.handleAuthStateChange(event, session);
      });

      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize auth service:', error);
      this.isInitialized = true; // Still mark as initialized to prevent hanging
    }
  }

  /**
   * Handle auth state changes from Supabase
   */
  handleAuthStateChange(event, session) {
    switch (event) {
      case 'SIGNED_IN':
        this.currentUser = session?.user || null;
        break;
      case 'SIGNED_OUT':
        this.currentUser = null;
        break;
      case 'TOKEN_REFRESHED':
        this.currentUser = session?.user || null;
        break;
      case 'USER_UPDATED':
        this.currentUser = session?.user || null;
        break;
    }

    this.notifyAuthStateChange(event, session);
  }

  /**
   * Add listener for auth state changes
   * @param {Function} callback - Function to call on auth state change
   * @returns {Function} - Unsubscribe function
   */
  onAuthStateChange(callback) {
    this.authListeners.add(callback);

    // Return unsubscribe function
    return () => {
      this.authListeners.delete(callback);
    };
  }

  /**
   * Notify all auth listeners of state change
   */
  notifyAuthStateChange(event, session) {
    this.authListeners.forEach(listener => {
      try {
        listener(event, session, this.currentUser);
      } catch (error) {
        console.error('Auth listener error:', error);
      }
    });
  }

  /**
   * Sign up a new user
   * @param {string} email - User email
   * @param {string} password - User password
   * @param {Object} metadata - Optional user metadata
   * @returns {Promise<Object>} - Result object with user data or error
   */
  async signUp(email, password, metadata = {}) {
    try {
      if (!email || !password) {
        throw new Error('Email and password are required');
      }

      if (password.length < 6) {
        throw new Error('Password must be at least 6 characters long');
      }

      const { data, error } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          data: metadata
        }
      });

      if (error) {
        return {
          success: false,
          error: error.message,
          code: error.status
        };
      }

      // If user needs email confirmation
      if (data.user && !data.session) {
        return {
          success: true,
          user: data.user,
          message: 'Please check your email to confirm your account',
          requiresConfirmation: true
        };
      }

      return {
        success: true,
        user: data.user,
        session: data.session,
        message: 'Account created successfully'
      };

    } catch (error) {
      console.error('Sign up error:', error);
      return {
        success: false,
        error: error.message || 'An unexpected error occurred during sign up'
      };
    }
  }

  /**
   * Sign in an existing user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} - Result object with user data or error
   */
  async signIn(email, password) {
    try {
      if (!email || !password) {
        throw new Error('Email and password are required');
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password
      });

      if (error) {
        return {
          success: false,
          error: error.message,
          code: error.status
        };
      }

      this.currentUser = data.user;

      return {
        success: true,
        user: data.user,
        session: data.session,
        message: 'Signed in successfully'
      };

    } catch (error) {
      console.error('Sign in error:', error);
      return {
        success: false,
        error: error.message || 'An unexpected error occurred during sign in'
      };
    }
  }

  /**
   * Sign in with OAuth provider
   * @param {string} provider - OAuth provider (google, github, etc.)
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} - Result object
   */
  async signInWithOAuth(provider, options = {}) {
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: options.redirectTo || window?.location?.origin
        }
      });

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        data
      };

    } catch (error) {
      console.error('OAuth sign in error:', error);
      return {
        success: false,
        error: error.message || 'OAuth sign in failed'
      };
    }
  }

  /**
   * Sign out the current user
   * @returns {Promise<Object>} - Result object
   */
  async signOut() {
    try {
      const { error } = await supabase.auth.signOut();

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      this.currentUser = null;

      return {
        success: true,
        message: 'Signed out successfully'
      };

    } catch (error) {
      console.error('Sign out error:', error);
      return {
        success: false,
        error: error.message || 'An unexpected error occurred during sign out'
      };
    }
  }

  /**
   * Get the current user
   * @returns {Object|null} - Current user object or null
   */
  getCurrentUser() {
    return this.currentUser;
  }

  /**
   * Get current session
   * @returns {Promise<Object>} - Current session data
   */
  async getCurrentSession() {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) {
        return {
          success: false,
          error: error.message,
          session: null
        };
      }

      return {
        success: true,
        session,
        user: session?.user || null
      };

    } catch (error) {
      console.error('Get session error:', error);
      return {
        success: false,
        error: error.message || 'Failed to get current session',
        session: null
      };
    }
  }

  /**
   * Check if user is authenticated
   * @returns {boolean} - Whether user is authenticated
   */
  isAuthenticated() {
    return !!this.currentUser;
  }

  /**
   * Reset password for user
   * @param {string} email - User email
   * @returns {Promise<Object>} - Result object
   */
  async resetPassword(email) {
    try {
      if (!email) {
        throw new Error('Email is required');
      }

      const { data, error } = await supabase.auth.resetPasswordForEmail(
        email.trim().toLowerCase(),
        {
          redirectTo: window?.location?.origin ? `${window.location.origin}/reset-password` : undefined
        }
      );

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        message: 'Password reset email sent',
        data
      };

    } catch (error) {
      console.error('Reset password error:', error);
      return {
        success: false,
        error: error.message || 'Failed to send reset password email'
      };
    }
  }

  /**
   * Update user password
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} - Result object
   */
  async updatePassword(newPassword) {
    try {
      if (!newPassword || newPassword.length < 6) {
        throw new Error('Password must be at least 6 characters long');
      }

      const { data, error } = await supabase.auth.updateUser({
        password: newPassword
      });

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        user: data.user,
        message: 'Password updated successfully'
      };

    } catch (error) {
      console.error('Update password error:', error);
      return {
        success: false,
        error: error.message || 'Failed to update password'
      };
    }
  }

  /**
   * Update user profile
   * @param {Object} updates - Profile updates
   * @returns {Promise<Object>} - Result object
   */
  async updateProfile(updates) {
    try {
      if (!this.currentUser) {
        throw new Error('User must be authenticated to update profile');
      }

      const { data, error } = await supabase.auth.updateUser({
        data: updates
      });

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      this.currentUser = data.user;

      return {
        success: true,
        user: data.user,
        message: 'Profile updated successfully'
      };

    } catch (error) {
      console.error('Update profile error:', error);
      return {
        success: false,
        error: error.message || 'Failed to update profile'
      };
    }
  }

  /**
   * Refresh the current session
   * @returns {Promise<Object>} - Result object
   */
  async refreshSession() {
    try {
      const { data, error } = await supabase.auth.refreshSession();

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      this.currentUser = data.user;

      return {
        success: true,
        session: data.session,
        user: data.user
      };

    } catch (error) {
      console.error('Refresh session error:', error);
      return {
        success: false,
        error: error.message || 'Failed to refresh session'
      };
    }
  }

  /**
   * Wait for service to be initialized
   * @returns {Promise<void>}
   */
  async waitForInitialization() {
    if (this.isInitialized) return;

    return new Promise((resolve) => {
      const checkInit = () => {
        if (this.isInitialized) {
          resolve();
        } else {
          setTimeout(checkInit, 100);
        }
      };
      checkInit();
    });
  }

  /**
   * Get user's JWT token
   * @returns {Promise<string|null>} - JWT token or null
   */
  async getAccessToken() {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      return session?.access_token || null;
    } catch (error) {
      console.error('Get access token error:', error);
      return null;
    }
  }

  /**
   * Verify if user's email is confirmed
   * @returns {boolean} - Whether email is confirmed
   */
  isEmailConfirmed() {
    return !!this.currentUser?.email_confirmed_at;
  }

  /**
   * Resend email confirmation
   * @returns {Promise<Object>} - Result object
   */
  async resendConfirmation() {
    try {
      if (!this.currentUser?.email) {
        throw new Error('No user email found');
      }

      const { error } = await supabase.auth.resend({
        type: 'signup',
        email: this.currentUser.email
      });

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        message: 'Confirmation email sent'
      };

    } catch (error) {
      console.error('Resend confirmation error:', error);
      return {
        success: false,
        error: error.message || 'Failed to resend confirmation email'
      };
    }
  }
}

// Create and export singleton instance
const authService = new AuthService();

export default authService;

// Named exports for convenience
export {
  authService,
  AuthService
};