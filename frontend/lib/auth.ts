/**
 * Authentication utilities for session management
 */

// Check if user is on superadmin pages
export const isSuperadminRoute = (): boolean => {
	return (
		typeof window !== "undefined" &&
		window.location.pathname.startsWith("/superadmin")
	);
};

// Get the current user's token based on route
export const getCurrentToken = (): string | null => {
	if (typeof window === "undefined") return null;

	return isSuperadminRoute()
		? localStorage.getItem("superadmin_token")
		: localStorage.getItem("access_token");
};

// Parse JWT token to check expiration
const parseJWTToken = (token: string): { exp?: number } | null => {
	try {
		const base64Url = token.split('.')[1];
		const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
		const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
			return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
		}).join(''));
		return JSON.parse(jsonPayload);
	} catch (error) {
		console.warn('Failed to parse JWT token:', error);
		return null;
	}
};

// Check if token is expired
const isTokenExpired = (token: string): boolean => {
	const payload = parseJWTToken(token);
	if (!payload?.exp) return true;
	
	// Check if token expires within the next 5 minutes (buffer time)
	const expirationTime = payload.exp * 1000; // Convert to milliseconds
	const bufferTime = 5 * 60 * 1000; // 5 minutes buffer
	const currentTime = Date.now();
	
	return currentTime >= (expirationTime - bufferTime);
};

// Cache for token validation to avoid repeated parsing
let tokenValidationCache: { token: string; isValid: boolean; timestamp: number } | null = null;
const VALIDATION_CACHE_TTL = 30000; // 30 seconds

// Check if user is authenticated with valid, non-expired token
export const isAuthenticated = (): boolean => {
	const token = getCurrentToken();
	if (!token) return false;
	
	// For superadmin tokens, we'll do a simple existence check for now
	// (you can enhance this later with superadmin token expiration if needed)
	if (isSuperadminRoute()) {
		return token !== null;
	}
	
	// Check cache first to avoid repeated JWT parsing
	const now = Date.now();
	if (tokenValidationCache && 
		tokenValidationCache.token === token && 
		(now - tokenValidationCache.timestamp) < VALIDATION_CACHE_TTL) {
		return tokenValidationCache.isValid;
	}
	
	// For client tokens, check expiration
	const isValid = !isTokenExpired(token);
	if (!isValid) {
		console.warn('Token is expired, clearing from storage');
		localStorage.removeItem('access_token');
	}
	
	// Cache the result
	tokenValidationCache = {
		token,
		isValid,
		timestamp: now
	};
	
	return isValid;
};

// Logout current user and redirect to appropriate login page
export const logout = (): void => {
	if (typeof window === "undefined") return;

	// Clear validation cache
	tokenValidationCache = null;
	
	if (isSuperadminRoute()) {
		// Clear superadmin token and redirect to superadmin login
		localStorage.removeItem("superadmin_token");
		window.location.href = "/superadmin/login";
	} else {
		// Clear client token and redirect to client login
		localStorage.removeItem("access_token");
		window.location.href = "/login";
	}
};

// Logout specific user type (useful for explicit logout actions)
export const logoutClient = (): void => {
	if (typeof window === "undefined") return;

	tokenValidationCache = null;
	localStorage.removeItem("access_token");
	window.location.href = "/login";
};

export const logoutSuperadmin = (): void => {
	if (typeof window === "undefined") return;

	tokenValidationCache = null;
	localStorage.removeItem("superadmin_token");
	window.location.href = "/superadmin/login";
};

// Clear all auth tokens (useful for complete logout)
export const clearAllAuthTokens = (): void => {
	if (typeof window === "undefined") return;

	tokenValidationCache = null;
	localStorage.removeItem("access_token");
	localStorage.removeItem("superadmin_token");
};

// Debug helper function to check authentication status
export const debugAuthStatus = (): void => {
	if (typeof window === "undefined") {
		console.log("🔍 Auth Debug: Running in server environment");
		return;
	}
	
	const isSuperadmin = isSuperadminRoute();
	const token = getCurrentToken();
	const authenticated = isAuthenticated();
	
	console.log("🔍 Authentication Debug Status:");
	console.log(`- Route Type: ${isSuperadmin ? 'Superadmin' : 'Client'}`);
	console.log(`- Token Exists: ${token ? 'Yes' : 'No'}`);
	console.log(`- Token Preview: ${token ? token.substring(0, 20) + '...' : 'None'}`);
	console.log(`- Is Authenticated: ${authenticated ? 'Yes' : 'No'}`);
	
	if (token && !isSuperadmin) {
		const payload = parseJWTToken(token);
		if (payload?.exp) {
			const expirationTime = new Date(payload.exp * 1000);
			const isExpired = isTokenExpired(token);
			console.log(`- Token Expires: ${expirationTime.toLocaleString()}`);
			console.log(`- Token Expired: ${isExpired ? 'Yes' : 'No'}`);
		}
	}
	
	console.log(`- Redirect Disabled: ${localStorage.getItem("disable_auth_redirect") === "true" ? 'Yes' : 'No'}`);
};
