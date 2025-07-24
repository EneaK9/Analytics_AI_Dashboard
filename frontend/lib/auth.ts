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

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
	return getCurrentToken() !== null;
};

// Logout current user and redirect to appropriate login page
export const logout = (): void => {
	if (typeof window === "undefined") return;

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

	localStorage.removeItem("access_token");
	window.location.href = "/login";
};

export const logoutSuperadmin = (): void => {
	if (typeof window === "undefined") return;

	localStorage.removeItem("superadmin_token");
	window.location.href = "/superadmin/login";
};

// Clear all auth tokens (useful for complete logout)
export const clearAllAuthTokens = (): void => {
	if (typeof window === "undefined") return;

	localStorage.removeItem("access_token");
	localStorage.removeItem("superadmin_token");
};
