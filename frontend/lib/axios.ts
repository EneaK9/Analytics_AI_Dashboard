import axios from "axios";
import { getCurrentToken, logout, isSuperadminRoute } from "./auth";

const api = axios.create({
	baseURL: process.env.NEXT_PUBLIC_API_URL
		? `${process.env.NEXT_PUBLIC_API_URL}/api`
		: "http://localhost:8000/api",
	timeout: 30000, // 30 seconds - increased for metrics processing
	headers: {
		"Content-Type": "application/json",
	},
});

// Debug function to test timeout configuration
export const testTimeoutConfig = async () => {
	console.log("🧪 Testing timeout configuration...");
	
	// Test 1: Check default timeout
	const defaultConfig = api.defaults;
	console.log("🔧 Default timeout:", defaultConfig.timeout);
	
	// Test 2: Check request interceptor
	const testConfig = { url: '/dashboard/metrics', timeout: 15000 };
	const processedConfig = await new Promise((resolve) => {
		api.interceptors.request.handlers[0].fulfilled(testConfig);
		resolve(testConfig);
	});
	console.log("🔧 Processed config timeout:", processedConfig.timeout);
	
	return processedConfig;
};

// Add request interceptor to add auth token if available
api.interceptors.request.use(
	(config) => {
		const token = getCurrentToken();

		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		// Set longer timeout for metrics endpoint
		if (config.url?.includes('/dashboard/metrics')) {
			config.timeout = 60000; // 60 seconds for metrics
			console.log("🔧 Setting 60s timeout for metrics endpoint:", config.url);
		}
		
		console.log("🔧 Request config timeout:", config.timeout, "for URL:", config.url);

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
			console.warn("Timeout details:", {
				url: error.config?.url,
				timeout: error.config?.timeout,
				message: error.message
			});
		} else if (error.code === "ERR_NETWORK") {
			console.warn("Network error - server may be down, real data unavailable");
		}

		// Reject the promise - components will handle empty data states
		return Promise.reject(error);
	}
);

export default api;
