import { supabase } from './supabaseClientNode.js';

/**
 * Server-side authentication service for user management using Supabase
 * Optimized for Node.js environments (no session persistence)
 */
class AuthServiceNode {
  constructor() {
    this.isInitialized = true; // Server-side doesn't need session restoration
  }

  /**
   * Sign up a new user (server-side)
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

      const { data, error } = await supabase.auth.admin.createUser({
        email: email.trim().toLowerCase(),
        password,
        user_metadata: metadata,
        email_confirm: false // Auto-confirm for server-side creation
      });

      if (error) {
        return {
          success: false,
          error: error.message,
          code: error.status
        };
      }

      return {
        success: true,
        user: data.user,
        message: 'User created successfully'
      };

    } catch (error) {
      console.error('Server sign up error:', error);
      return {
        success: false,
        error: error.message || 'An unexpected error occurred during sign up'
      };
    }
  }

  /**
   * Authenticate user credentials (server-side verification)
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} - Result object with user data or error
   */
  async verifyCredentials(email, password) {
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

      return {
        success: true,
        user: data.user,
        session: data.session,
        message: 'Credentials verified successfully'
      };

    } catch (error) {
      console.error('Server credential verification error:', error);
      return {
        success: false,
        error: error.message || 'An unexpected error occurred during verification'
      };
    }
  }

  /**
   * Get user by ID (admin function)
   * @param {string} userId - User ID
   * @returns {Promise<Object>} - Result object with user data
   */
  async getUserById(userId) {
    try {
      if (!userId) {
        throw new Error('User ID is required');
      }

      const { data, error } = await supabase.auth.admin.getUserById(userId);

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        user: data.user
      };

    } catch (error) {
      console.error('Get user by ID error:', error);
      return {
        success: false,
        error: error.message || 'Failed to get user'
      };
    }
  }

  /**
   * Get user by email (admin function)
   * @param {string} email - User email
   * @returns {Promise<Object>} - Result object with user data
   */
  async getUserByEmail(email) {
    try {
      if (!email) {
        throw new Error('Email is required');
      }

      const { data, error } = await supabase.auth.admin.listUsers();

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      const user = data.users.find(u => u.email === email.trim().toLowerCase());

      if (!user) {
        return {
          success: false,
          error: 'User not found'
        };
      }

      return {
        success: true,
        user
      };

    } catch (error) {
      console.error('Get user by email error:', error);
      return {
        success: false,
        error: error.message || 'Failed to get user'
      };
    }
  }

  /**
   * Update user (admin function)
   * @param {string} userId - User ID
   * @param {Object} updates - User updates
   * @returns {Promise<Object>} - Result object
   */
  async updateUser(userId, updates) {
    try {
      if (!userId) {
        throw new Error('User ID is required');
      }

      const { data, error } = await supabase.auth.admin.updateUserById(userId, updates);

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        user: data.user,
        message: 'User updated successfully'
      };

    } catch (error) {
      console.error('Update user error:', error);
      return {
        success: false,
        error: error.message || 'Failed to update user'
      };
    }
  }

  /**
   * Delete user (admin function)
   * @param {string} userId - User ID
   * @returns {Promise<Object>} - Result object
   */
  async deleteUser(userId) {
    try {
      if (!userId) {
        throw new Error('User ID is required');
      }

      const { error } = await supabase.auth.admin.deleteUser(userId);

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        message: 'User deleted successfully'
      };

    } catch (error) {
      console.error('Delete user error:', error);
      return {
        success: false,
        error: error.message || 'Failed to delete user'
      };
    }
  }

  /**
   * List all users (admin function)
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Result object with users list
   */
  async listUsers(options = {}) {
    try {
      const { page = 1, perPage = 50 } = options;

      const { data, error } = await supabase.auth.admin.listUsers({
        page: page,
        perPage: Math.min(perPage, 1000) // Supabase limit
      });

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        users: data.users,
        total: data.total || data.users.length,
        page,
        perPage
      };

    } catch (error) {
      console.error('List users error:', error);
      return {
        success: false,
        error: error.message || 'Failed to list users'
      };
    }
  }

  /**
   * Generate access token for user (admin function)
   * @param {string} userId - User ID
   * @returns {Promise<Object>} - Result object with access token
   */
  async generateAccessToken(userId) {
    try {
      if (!userId) {
        throw new Error('User ID is required');
      }

      const { data, error } = await supabase.auth.admin.generateLink({
        type: 'magiclink',
        email: '', // Will be filled by Supabase based on user ID
        options: {
          data: { userId }
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
        accessToken: data.properties?.access_token,
        refreshToken: data.properties?.refresh_token
      };

    } catch (error) {
      console.error('Generate access token error:', error);
      return {
        success: false,
        error: error.message || 'Failed to generate access token'
      };
    }
  }

  /**
   * Verify JWT token
   * @param {string} token - JWT token to verify
   * @returns {Promise<Object>} - Result object with user data if valid
   */
  async verifyToken(token) {
    try {
      if (!token) {
        throw new Error('Token is required');
      }

      const { data, error } = await supabase.auth.getUser(token);

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      return {
        success: true,
        user: data.user,
        isValid: !!data.user
      };

    } catch (error) {
      console.error('Verify token error:', error);
      return {
        success: false,
        error: error.message || 'Failed to verify token'
      };
    }
  }

  /**
   * Reset user password (admin function)
   * @param {string} userId - User ID
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} - Result object
   */
  async resetUserPassword(userId, newPassword) {
    try {
      if (!userId || !newPassword) {
        throw new Error('User ID and new password are required');
      }

      if (newPassword.length < 6) {
        throw new Error('Password must be at least 6 characters long');
      }

      const { data, error } = await supabase.auth.admin.updateUserById(userId, {
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
        message: 'Password reset successfully'
      };

    } catch (error) {
      console.error('Reset user password error:', error);
      return {
        success: false,
        error: error.message || 'Failed to reset password'
      };
    }
  }

  /**
   * Bulk operations for user management
   */
  async bulkCreateUsers(users) {
    try {
      const results = [];

      for (const userData of users) {
        const result = await this.signUp(
          userData.email,
          userData.password,
          userData.metadata
        );
        results.push({
          email: userData.email,
          ...result
        });
      }

      return {
        success: true,
        results,
        successCount: results.filter(r => r.success).length,
        failureCount: results.filter(r => !r.success).length
      };

    } catch (error) {
      console.error('Bulk create users error:', error);
      return {
        success: false,
        error: error.message || 'Failed to bulk create users'
      };
    }
  }

  /**
   * Get user analytics/stats
   * @returns {Promise<Object>} - User statistics
   */
  async getUserStats() {
    try {
      const { data, error } = await supabase.auth.admin.listUsers();

      if (error) {
        return {
          success: false,
          error: error.message
        };
      }

      const stats = {
        totalUsers: data.users.length,
        confirmedUsers: data.users.filter(u => u.email_confirmed_at).length,
        unconfirmedUsers: data.users.filter(u => !u.email_confirmed_at).length,
        recentUsers: data.users.filter(u => {
          const createdAt = new Date(u.created_at);
          const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
          return createdAt > dayAgo;
        }).length
      };

      return {
        success: true,
        stats
      };

    } catch (error) {
      console.error('Get user stats error:', error);
      return {
        success: false,
        error: error.message || 'Failed to get user stats'
      };
    }
  }
}

// Create and export singleton instance
const authServiceNode = new AuthServiceNode();

export default authServiceNode;

// Named exports for convenience
export {
  authServiceNode,
  AuthServiceNode
};