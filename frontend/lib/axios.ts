import axios from "axios";
import { getCurrentToken, logout, isSuperadminRoute } from "./auth";

const api = axios.create({
	baseURL: process.env.NEXT_PUBLIC_API_URL
		? `${process.env.NEXT_PUBLIC_API_URL}/api`
		: "http://localhost:8000/api",
	timeout: 1800000, // 5 hours - increased 100x for heavy processing
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

	// Test 2: Check request interceptor (simplified)
	const testConfig = { url: "/dashboard/metrics", timeout: 120000 };
	console.log("🔧 Test config timeout:", testConfig.timeout);

	return testConfig;
};

// Add request interceptor to add auth token if available
api.interceptors.request.use(
	(config) => {
		const token = getCurrentToken();

		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		// Set longer timeout for LLM-powered endpoints
		if (
			config.url?.includes("/dashboard/metrics") ||
			config.url?.includes("/dashboard/business-insights") ||
			config.url?.includes("/dashboard/performance") ||
			config.url?.includes("/dashboard/generate-template") ||
			config.url?.includes("/dashboard/generate")
		) {
			// Check if force_llm=true for even longer timeout
			config.timeout = 300000; // 30 seconds for LLM endpoints
		}

		// Set reasonable timeout for inventory analytics endpoints
		if (
			config.url?.includes("/dashboard/sku-inventory") ||
			config.url?.includes("/dashboard/inventory-analytics")
		) {
			config.timeout = 150000; // 15 seconds for inventory processing
		}

		// Set reasonable timeout for file uploads
		if (
			config.url?.includes("/superadmin/clients") &&
			config.method?.toLowerCase() === "post"
		) {
			config.timeout = 300000; // 5 minutes for file processing
		}

		console.log(
			"🔧 Request config timeout:",
			config.timeout,
			"for URL:",
			config.url
		);

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
				message: error.message,
			});
		} else if (error.code === "ERR_NETWORK") {
			console.warn("Network error - server may be down, real data unavailable");
		}

		// Reject the promise - components will handle empty data states
		return Promise.reject(error);
	}
);

export default api;
