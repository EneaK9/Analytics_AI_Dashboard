/**
 * SKU Data Hook - Gets SKU inventory data from dedicated endpoint
 * Uses the correct /api/dashboard/sku-inventory endpoint for actual SKU lists
 */

import { useState, useEffect, useCallback, useRef } from "react";
import api from "../lib/axios";
import { isAuthenticated } from "../lib/auth";

interface SKUDataState {
	// Loading states
	loading: boolean;
	error: string | null;

	// SKU data for each platform
	shopifySKUs: any[];
	amazonSKUs: any[];

	// Summary stats
	shopifyStats: any;
	amazonStats: any;

	// Cache info
	cached: boolean;
	lastUpdated: Date | null;

	// Methods
	refresh: (platform?: string, forceRefresh?: boolean) => Promise<void>;
}

interface UseSKUDataOptions {
	refreshInterval?: number;
	fastMode?: boolean;
}

export const useSKUData = (options: UseSKUDataOptions = {}): SKUDataState => {
	const { refreshInterval = 0, fastMode = true } = options;

	// State management
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [shopifySKUs, setShopifySKUs] = useState<any[]>([]);
	const [amazonSKUs, setAmazonSKUs] = useState<any[]>([]);
	const [shopifyStats, setShopifyStats] = useState<any>(null);
	const [amazonStats, setAmazonStats] = useState<any>(null);
	const [cached, setCached] = useState(false);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// Refs for cleanup and request management
	const intervalRef = useRef<NodeJS.Timeout | null>(null);
	const abortControllerRef = useRef<AbortController | null>(null);
	const isRequestInProgressRef = useRef<boolean>(false);

	/**
	 * Fetch SKU data for a specific platform
	 */
	const fetchPlatformSKUs = useCallback(
		async (platform: string, forceRefresh: boolean = false): Promise<void> => {
			try {
				console.log(
					`🚀 Fetching ${platform} SKU data from dedicated endpoint...`
				);

				// Call the dedicated SKU inventory endpoint
				const response = await api.get("/dashboard/sku-inventory", {
					params: {
						platform: platform,
						page: 1,
						page_size: 1000, // Get all data, no pagination in UI
						use_cache: !forceRefresh,
						force_refresh: forceRefresh,
					},
					signal: abortControllerRef.current?.signal,
				});

				if (response.data?.success) {
					const skuData = response.data.sku_inventory?.skus || [];
					const summaryStats = response.data.sku_inventory?.summary_stats || {};

					console.log(`🔍 ${platform} SKU Response:`, {
						success: response.data.success,
						skuCount: skuData.length,
						hasStats: !!summaryStats,
						responseStructure: Object.keys(response.data),
					});

					if (platform === "shopify") {
						console.log(`📦 Setting ${skuData.length} Shopify SKUs`);
						setShopifySKUs(skuData);
						setShopifyStats(summaryStats);
					} else if (platform === "amazon") {
						console.log(`📦 Setting ${skuData.length} Amazon SKUs`);
						setAmazonSKUs(skuData);
						setAmazonStats(summaryStats);
					}

					setCached(response.data.cached || false);
					setLastUpdated(new Date());

					console.log(
						`✅ ${platform} SKU data loaded: ${skuData.length} items`
					);
				} else {
					console.error(`❌ ${platform} SKU API returned unsuccessful:`, {
						success: response.data?.success,
						message: response.data?.message,
						error: response.data?.error,
						fullResponse: response.data,
					});
					throw new Error(
						response.data?.message || `Failed to fetch ${platform} SKU data`
					);
				}
			} catch (error: any) {
				// Handle request cancellation silently
				if (
					error.name === "AbortError" ||
					error.name === "CanceledError" ||
					error.code === "ERR_CANCELED"
				) {
					console.log(`🚫 ${platform} SKU request aborted`);
					return;
				}

				console.error(`❌ Failed to fetch ${platform} SKU data:`, {
					errorName: error.name,
					errorMessage: error.message,
					errorCode: error.code,
					responseStatus: error.response?.status,
					responseData: error.response?.data,
				});
				throw error;
			}
		},
		[fastMode]
	);

	/**
	 * Fetch SKU data for all platforms
	 */
	const fetchAllSKUData = useCallback(
		async (forceRefresh: boolean = false): Promise<void> => {
			// Check authentication before making API calls
			if (!isAuthenticated()) {
				console.log("🔒 User not authenticated, skipping SKU data fetch");
				setLoading(false);
				setError(null);
				return;
			}

			// Prevent multiple simultaneous requests unless forced
			if (isRequestInProgressRef.current && !forceRefresh) {
				console.log("⏳ SKU data request already in progress, skipping...");
				return;
			}

			try {
				isRequestInProgressRef.current = true;
				setLoading(true);
				setError(null);

				// Abort any existing requests if forced
				if (forceRefresh && abortControllerRef.current) {
					abortControllerRef.current.abort();
				}
				abortControllerRef.current = new AbortController();

				// Fetch both platforms in parallel - FORCE REFRESH for debugging
				await Promise.all([
					fetchPlatformSKUs("shopify", true), // Force refresh for Shopify
					fetchPlatformSKUs("amazon", forceRefresh),
				]);
			} catch (error: any) {
				// Handle request cancellation silently
				if (
					error.name === "AbortError" ||
					error.name === "CanceledError" ||
					error.code === "ERR_CANCELED"
				) {
					console.log("🚫 SKU data requests aborted");
					return;
				}

				console.error("❌ Failed to fetch SKU data:", {
					errorMessage: error.message,
					platforms: "shopify and amazon",
					errorDetails: error,
				});
				setError(error.message || "Failed to load SKU data");
			} finally {
				setLoading(false);
				isRequestInProgressRef.current = false;
			}
		},
		[fetchPlatformSKUs]
	);

	/**
	 * Manual refresh function
	 */
	const refresh = useCallback(
		async (platform?: string, forceRefresh: boolean = false): Promise<void> => {
			if (platform) {
				// Refresh specific platform
				try {
					setLoading(true);
					await fetchPlatformSKUs(platform, forceRefresh);
				} finally {
					setLoading(false);
				}
			} else {
				// Refresh all platforms
				await fetchAllSKUData(forceRefresh);
			}
		},
		[fetchAllSKUData, fetchPlatformSKUs]
	);

	// Initial data load
	useEffect(() => {
		fetchAllSKUData(false);
	}, [fetchAllSKUData]);

	// Auto-refresh setup
	useEffect(() => {
		if (refreshInterval > 0) {
			intervalRef.current = setInterval(() => {
				refresh();
			}, refreshInterval);

			return () => {
				if (intervalRef.current) {
					clearInterval(intervalRef.current);
				}
			};
		}
	}, [refresh, refreshInterval]);

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			// Clear any intervals
			if (intervalRef.current) {
				clearInterval(intervalRef.current);
			}

			// Reset request progress flag
			isRequestInProgressRef.current = false;

			// Abort any ongoing requests
			if (abortControllerRef.current) {
				try {
					abortControllerRef.current.abort();
				} catch (error) {
					// Ignore cleanup errors
					console.log("Cleanup: SKU requests already aborted or completed");
				}
			}
		};
	}, []);

	return {
		// Loading states
		loading,
		error,

		// Platform-specific SKU data
		shopifySKUs,
		amazonSKUs,

		// Summary stats
		shopifyStats,
		amazonStats,

		// Cache info
		cached,
		lastUpdated,

		// Methods
		refresh,
	};
};

export default useSKUData;
