# Authentication Service Usage Examples

This document provides examples of how to use the Supabase authentication service in your NFL Predictor API application.

## Setup

```javascript
import authService from '../src/services/authService.js';
// or for Node.js server-side
import authServiceNode from '../src/services/authServiceNode.js';
```

## User Registration

```javascript
// Basic registration
const signUpResult = await authService.signUp('user@example.com', 'password123');

if (signUpResult.success) {
  if (signUpResult.requiresConfirmation) {
    console.log('Please check your email to confirm your account');
  } else {
    console.log('User registered successfully:', signUpResult.user);
  }
} else {
  console.error('Registration failed:', signUpResult.error);
}

// Registration with metadata
const signUpWithMetadata = await authService.signUp(
  'user@example.com',
  'password123',
  {
    name: 'John Doe',
    preferredTeam: 'KC',
    subscriptionTier: 'free'
  }
);
```

## User Login

```javascript
// Email/password login
const signInResult = await authService.signIn('user@example.com', 'password123');

if (signInResult.success) {
  console.log('User signed in:', signInResult.user);
  console.log('Session token:', signInResult.session.access_token);
} else {
  console.error('Sign in failed:', signInResult.error);
}

// OAuth login (Google, GitHub, etc.)
const oauthResult = await authService.signInWithOAuth('google', {
  redirectTo: 'https://yourapp.com/auth/callback'
});

if (oauthResult.success) {
  // User will be redirected to OAuth provider
  console.log('Redirecting to OAuth provider...');
} else {
  console.error('OAuth sign in failed:', oauthResult.error);
}
```

## Session Management

```javascript
// Check if user is authenticated
if (authService.isAuthenticated()) {
  console.log('User is logged in');
  const currentUser = authService.getCurrentUser();
  console.log('Current user:', currentUser);
} else {
  console.log('User is not authenticated');
}

// Get current session details
const sessionResult = await authService.getCurrentSession();
if (sessionResult.success) {
  console.log('Session:', sessionResult.session);
  console.log('User:', sessionResult.user);
}

// Get access token for API calls
const token = await authService.getAccessToken();
if (token) {
  // Use token in API requests
  const apiResponse = await fetch('/api/protected-endpoint', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
}
```

## Profile Management

```javascript
// Update user profile
const updateResult = await authService.updateProfile({
  name: 'John Updated',
  avatar_url: 'https://example.com/avatar.jpg',
  preferredTeam: 'BUF'
});

if (updateResult.success) {
  console.log('Profile updated:', updateResult.user);
} else {
  console.error('Profile update failed:', updateResult.error);
}

// Update password
const passwordResult = await authService.updatePassword('newpassword123');

if (passwordResult.success) {
  console.log('Password updated successfully');
} else {
  console.error('Password update failed:', passwordResult.error);
}
```

## Password Reset

```javascript
// Send password reset email
const resetResult = await authService.resetPassword('user@example.com');

if (resetResult.success) {
  console.log('Password reset email sent');
} else {
  console.error('Password reset failed:', resetResult.error);
}
```

## Auth State Listeners

```javascript
// Listen for authentication state changes
const unsubscribe = authService.onAuthStateChange((event, session, user) => {
  console.log('Auth state changed:', event);

  switch (event) {
    case 'SIGNED_IN':
      console.log('User signed in:', user);
      // Update UI to show authenticated state
      break;

    case 'SIGNED_OUT':
      console.log('User signed out');
      // Update UI to show unauthenticated state
      break;

    case 'TOKEN_REFRESHED':
      console.log('Token refreshed for user:', user);
      // Token was automatically refreshed
      break;

    case 'USER_UPDATED':
      console.log('User profile updated:', user);
      // User profile was updated
      break;
  }
});

// Don't forget to unsubscribe when component unmounts
// unsubscribe();
```

## React Component Example

```javascript
import React, { useState, useEffect } from 'react';
import authService from '../services/authService.js';

function AuthComponent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Wait for auth service to initialize
    authService.waitForInitialization().then(() => {
      setUser(authService.getCurrentUser());
      setLoading(false);
    });

    // Listen for auth state changes
    const unsubscribe = authService.onAuthStateChange((event, session, currentUser) => {
      setUser(currentUser);
    });

    return unsubscribe; // Cleanup listener
  }, []);

  const handleSignIn = async (email, password) => {
    const result = await authService.signIn(email, password);
    if (!result.success) {
      alert(result.error);
    }
  };

  const handleSignOut = async () => {
    await authService.signOut();
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (user) {
    return (
      <div>
        <h2>Welcome, {user.email}!</h2>
        <p>User ID: {user.id}</p>
        <p>Email confirmed: {authService.isEmailConfirmed() ? 'Yes' : 'No'}</p>
        <button onClick={handleSignOut}>Sign Out</button>
      </div>
    );
  }

  return (
    <div>
      <h2>Please sign in</h2>
      <LoginForm onSignIn={handleSignIn} />
    </div>
  );
}
```

## Server-Side Usage (Node.js)

```javascript
import authServiceNode from '../src/services/authServiceNode.js';

// Admin: Create user server-side
const createUserResult = await authServiceNode.signUp(
  'admin@example.com',
  'securepassword',
  { role: 'admin', name: 'Admin User' }
);

// Verify user credentials
const verifyResult = await authServiceNode.verifyCredentials(
  'user@example.com',
  'password123'
);

if (verifyResult.success) {
  console.log('Credentials are valid for user:', verifyResult.user);
}

// Get user by ID (admin function)
const userResult = await authServiceNode.getUserById('user-uuid-123');

// List all users (admin function)
const usersResult = await authServiceNode.listUsers({ page: 1, perPage: 50 });

if (usersResult.success) {
  console.log(`Found ${usersResult.total} users`);
  usersResult.users.forEach(user => {
    console.log(`User: ${user.email}, Created: ${user.created_at}`);
  });
}

// Verify JWT token
const tokenResult = await authServiceNode.verifyToken('jwt-token-here');

if (tokenResult.success && tokenResult.isValid) {
  console.log('Token is valid for user:', tokenResult.user);
} else {
  console.log('Token is invalid');
}
```

## Error Handling Best Practices

```javascript
// Always check for success before using data
const result = await authService.signIn(email, password);

if (result.success) {
  // Success - use result.user, result.session
  console.log('Signed in successfully');
} else {
  // Handle specific error codes
  switch (result.code) {
    case 400:
      console.error('Invalid credentials');
      break;
    case 422:
      console.error('Email already registered');
      break;
    case 429:
      console.error('Too many attempts, please try again later');
      break;
    default:
      console.error('Sign in failed:', result.error);
  }
}
```

## Integration with Protected Routes

```javascript
// Middleware to protect API routes
export async function authenticateRequest(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No authorization token provided' });
  }

  const token = authHeader.substring(7); // Remove 'Bearer ' prefix

  const verifyResult = await authServiceNode.verifyToken(token);

  if (!verifyResult.success || !verifyResult.isValid) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  req.user = verifyResult.user;
  next();
}

// Usage in Express route
app.get('/api/protected', authenticateRequest, (req, res) => {
  res.json({
    message: 'This is a protected endpoint',
    user: req.user
  });
});
```

## NFL Predictor Specific Features

```javascript
// Save user's game prediction
if (authService.isAuthenticated()) {
  const userPick = {
    user_id: authService.getCurrentUser().id,
    game_id: 'game-123',
    predicted_winner: 'KC',
    predicted_spread: -3.5,
    predicted_total: 52.5,
    confidence_level: 'high'
  };

  // This would be implemented in your game service
  const result = await gameService.saveUserPick(userPick);
}

// Get user's prediction history
const userStats = await userService.getUserPredictionHistory(
  authService.getCurrentUser().id
);
```

## Environment Configuration

Make sure your `.env` file contains the required Supabase credentials:

```env
VITE_SUPABASE_URL=your-supabase-project-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Important Notes

1. **Session Persistence**: Browser version persists sessions automatically, Node.js version does not
2. **Error Handling**: Always check `result.success` before using data
3. **Token Management**: Tokens are automatically refreshed in browser environments
4. **Security**: Never expose service role keys in client-side code
5. **Testing**: Use the provided test file as a reference for testing patterns