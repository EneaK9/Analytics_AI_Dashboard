import axios from "axios";
import { getCurrentToken, logout, isSuperadminRoute } from "./auth";

const api = axios.create({
	baseURL: process.env.NEXT_PUBLIC_API_URL
		? `${process.env.NEXT_PUBLIC_API_URL}/api`
		: "http://localhost:8000/api",
	timeout: 15000, // 15 seconds - client creation should be instant now
	headers: {
		"Content-Type": "application/json",
	},
});

// Add request interceptor to add auth token if available
api.interceptors.request.use(
	(config) => {
		const token = getCurrentToken();

		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}
		return config;
	},
	(error) => {
		return Promise.reject(error);
	}
);

// Add response interceptor for better error handling and session management
api.interceptors.response.use(
	(response) => {
		return response;
	},
	(error) => {
		// Handle session expiration (401 Unauthorized)
		if (error.response?.status === 401) {
			// Only handle automatic logout if we're in the browser
			if (typeof window !== "undefined") {
				console.warn("Session expired - redirecting to login");
				logout();
				return Promise.reject(new Error("Session expired"));
			}
		}

		// Handle network errors and timeouts gracefully - NO FALLBACK DATA
		if (error.code === "ECONNABORTED") {
			console.warn(
				"Request timeout - server may be processing, real data unavailable"
			);
		} else if (error.code === "ERR_NETWORK") {
			console.warn("Network error - server may be down, real data unavailable");
		}

		// Reject the promise - components will handle empty data states
		return Promise.reject(error);
	}
);

export default api;
