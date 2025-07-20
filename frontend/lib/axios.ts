import axios from "axios";

const api = axios.create({
	baseURL: "http://localhost:8000/api",
	timeout: 15000, // 15 seconds - client creation should be instant now
	headers: {
		"Content-Type": "application/json",
	},
});

// Add request interceptor to add auth token if available
api.interceptors.request.use(
	(config) => {
		// Check if we're on a superadmin page
		const isSuperadminPage =
			typeof window !== "undefined" &&
			window.location.pathname.startsWith("/superadmin");

		// Get appropriate token
		const token = isSuperadminPage
			? localStorage.getItem("superadmin_token")
			: localStorage.getItem("access_token");

		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}
		return config;
	},
	(error) => {
		return Promise.reject(error);
	}
);

// Add response interceptor for better error handling
api.interceptors.response.use(
	(response) => {
		return response;
	},
	(error) => {
		// Handle network errors and timeouts gracefully
		if (error.code === "ECONNABORTED") {
			console.warn(
				"Request timeout - server may be processing, will use fallback data"
			);
		} else if (error.code === "ERR_NETWORK") {
			console.warn(
				"Network error - server may be down, will use fallback data"
			);
		}

		// Don't reject the promise for certain errors, let components handle fallbacks
		return Promise.reject(error);
	}
);

export default api;
