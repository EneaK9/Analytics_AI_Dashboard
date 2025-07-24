# Session Management System

This document explains the automatic session expiration and logout system implemented for both client and superadmin users.

## Overview

The system automatically detects when a user's session has expired (401 Unauthorized responses) and redirects them to the appropriate login page while clearing their authentication tokens.

## Files Added/Modified

### 1. `lib/auth.ts` (NEW)

Contains authentication utility functions:

- `isSuperadminRoute()` - Detects if user is on superadmin pages
- `getCurrentToken()` - Gets the appropriate token based on current route
- `isAuthenticated()` - Checks if user is authenticated
- `logout()` - Logs out current user and redirects to appropriate login page
- `logoutClient()` - Specifically logs out client users
- `logoutSuperadmin()` - Specifically logs out superadmin users
- `clearAllAuthTokens()` - Clears all authentication tokens

### 2. `lib/useAuth.ts` (NEW)

React hook for authentication management:

- Provides authentication state (`isLoggedIn`, `userType`, `token`)
- Automatic session monitoring
- Multi-tab synchronization via localStorage events
- Easy logout functionality

### 3. `lib/axios.ts` (MODIFIED)

Enhanced axios configuration:

- Automatic 401 error detection
- Session expiration handling in response interceptor
- Automatic logout and redirect on session expiration
- Uses auth utilities for cleaner code

### 4. `pages/dashboard.tsx` (MODIFIED)

Updated client dashboard:

- Uses `useAuth()` hook
- Updated logout handler to use auth utilities

### 5. `pages/superadmin/dashboard.tsx` (MODIFIED)

Updated superadmin dashboard:

- Uses `useAuth()` hook
- Updated logout handler to use auth utilities

### 6. `lib/sessionTest.ts` (NEW)

Development utilities for testing session expiration:

- `simulateSessionExpiration()` - Triggers session expiration for testing
- `clearTokensForTesting()` - Manually clears tokens
- `checkAuthState()` - Logs current authentication state

## How It Works

### Automatic Session Expiration Detection

1. **API Request Flow**:

   - User makes API request
   - Axios automatically adds appropriate token (client or superadmin)
   - If server responds with 401 (Unauthorized), axios interceptor catches it
   - System automatically clears tokens and redirects to login page

2. **Route-Based Token Management**:

   - System detects if user is on `/superadmin/*` routes
   - Uses `superadmin_token` for superadmin pages
   - Uses `access_token` for client pages
   - Redirects to appropriate login page based on route

3. **Multi-Tab Synchronization**:
   - `useAuth` hook listens for localStorage changes
   - When tokens are cleared in one tab, all tabs update automatically
   - Prevents inconsistent authentication states across tabs

## Usage Examples

### In Components

```typescript
import { useAuth } from "../lib/useAuth";

const MyComponent = () => {
	const { isLoggedIn, userType, logout } = useAuth();

	if (!isLoggedIn) {
		return <div>Please log in</div>;
	}

	return (
		<div>
			<p>Welcome, {userType} user!</p>
			<button onClick={logout}>Logout</button>
		</div>
	);
};
```

### Manual Logout

```typescript
import { logout, logoutClient, logoutSuperadmin } from "../lib/auth";

// Auto-detect and logout current user
logout();

// Specific logout functions
logoutClient(); // Always redirects to /login
logoutSuperadmin(); // Always redirects to /superadmin/login
```

### Testing Session Expiration (Development)

```typescript
import { simulateSessionExpiration, checkAuthState } from "../lib/sessionTest";

// Check current auth state
checkAuthState();

// Simulate session expiration
await simulateSessionExpiration();
```

## User Experience

### For Client Users:

- When session expires during any API call, automatically redirected to `/login`
- Manual logout via dashboard also goes to `/login`
- Token is completely cleared from localStorage

### For Superadmin Users:

- When session expires during any API call, automatically redirected to `/superadmin/login`
- Manual logout via dashboard also goes to `/superadmin/login`
- Token is completely cleared from localStorage

### Multi-Tab Behavior:

- Logout in one tab automatically updates all other tabs
- No inconsistent states across browser tabs
- Seamless user experience

## Security Features

- **Immediate Token Clearance**: Tokens are removed immediately on session expiration
- **Route-Specific Handling**: Different tokens for different user types
- **No Token Leakage**: Proper cleanup prevents token reuse
- **Automatic Redirect**: Users can't remain on protected pages without valid sessions

## Testing

To test the session expiration functionality:

1. **Natural Expiration**: Wait for JWT token to expire (depends on backend configuration)

2. **Simulated Expiration** (Development):

   ```javascript
   // In browser console
   import("/lib/sessionTest.js").then(({ simulateSessionExpiration }) => {
   	simulateSessionExpiration();
   });
   ```

3. **Manual Testing**: Clear tokens manually and make an API request

The system will automatically redirect to the appropriate login page and clear all authentication data.
