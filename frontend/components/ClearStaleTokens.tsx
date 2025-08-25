// Add this to your login page or app initialization
export const clearStaleTokens = () => {
	if (typeof window !== "undefined") {
		// Clear all authentication-related localStorage items
		localStorage.removeItem("access_token");
		localStorage.removeItem("superadmin_token");
		localStorage.removeItem("disable_auth_redirect");

		console.log("✅ Cleared all stale authentication tokens");
	}
};

// Call this on app startup or login page load
export default clearStaleTokens;
