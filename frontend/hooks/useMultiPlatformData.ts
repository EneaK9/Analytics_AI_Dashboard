/**
 * Multi-Platform Inventory Data Hook - PERFORMANCE OPTIMIZED
 * Fetches data for all platforms (Shopify, Amazon, Combined) in a single API call
 * Prevents multiple re-renders and API calls
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import api from "../lib/axios";
import { isAuthenticated } from "../lib/auth";

interface MultiPlatformDataState {
	// Loading states
	loading: boolean;
	error: string | null;

	// Platform-specific data
	shopifyData: any;
	amazonData: any;
	combinedData: any;

	// Cache info
	cached: boolean;
	lastUpdated: Date | null;

	// Methods
	refresh: (forceRefresh?: boolean) => Promise<void>;
}

interface UseMultiPlatformOptions {
	refreshInterval?: number;
	fastMode?: boolean;
}

export const useMultiPlatformData = (
	options: UseMultiPlatformOptions = {}
): MultiPlatformDataState => {
	const { refreshInterval = 0, fastMode = true } = options;

	// State management
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [platformData, setPlatformData] = useState<any>(null);
	const [cached, setCached] = useState(false);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// Refs for cleanup and request management
	const intervalRef = useRef<NodeJS.Timeout | null>(null);
	const abortControllerRef = useRef<AbortController | null>(null);
	const isRequestInProgressRef = useRef<boolean>(false);

	/**
	 * Fetch all platform data in ONE optimized call
	 */
	const fetchAllPlatformData = useCallback(
		async (forceRefresh: boolean = false): Promise<void> => {
			// Check authentication before making API calls
			if (!isAuthenticated()) {
				console.log("🔒 User not authenticated, skipping API call");
				setLoading(false);
				setError(null);
				return;
			}

			// Prevent multiple simultaneous requests unless forced
			if (isRequestInProgressRef.current && !forceRefresh) {
				console.log(
					"⏳ Multi-platform request already in progress, skipping..."
				);
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

				console.log(
					"🚀 Fetching ALL platform data in single optimized call..."
				);

				// Single API call to get ALL platforms data
				const response = await api.get("/dashboard/inventory-analytics", {
					params: {
						fast_mode: fastMode,
						force_refresh: forceRefresh,
						platform: "all", // 🔥 This gets all platforms in one call!
					},
					signal: abortControllerRef.current.signal,
				});

				if (response.data?.success) {
					const analytics = response.data.inventory_analytics;

					if (analytics?.platforms) {
						// NEW multi-platform structure (from _get_multi_platform_analytics)
						setPlatformData(analytics.platforms);
						setCached(response.data.cached || false);
						setLastUpdated(new Date());

						console.log("✅ All platform data loaded successfully:", {
							shopify: analytics.platforms.shopify ? "✓" : "✗",
							amazon: analytics.platforms.amazon ? "✓" : "✗",
							combined: analytics.platforms.combined ? "✓" : "✗",
						});
					} else if (analytics?.sales_kpis || analytics?.success) {
						// ORGANIZED single-platform structure - this is what we're getting!
						console.log(
							"🔄 Converting organized single-platform response to multi-platform format"
						);

						const organizedPlatforms = {
							shopify: {
								sales_kpis: analytics.sales_kpis || analytics,
								trend_analysis: analytics.trend_analysis || analytics,
								alerts_summary: analytics.alerts_summary || analytics,
								data_summary: analytics.data_summary || {},
							},
							amazon: {
								sales_kpis: {},
								trend_analysis: {},
								alerts_summary: {},
								data_summary: {},
							},
							combined: {
								sales_kpis: analytics.sales_kpis || analytics,
								trend_analysis: analytics.trend_analysis || analytics,
								alerts_summary: analytics.alerts_summary || analytics,
								data_summary: analytics.data_summary || {},
							},
						};

						setPlatformData(organizedPlatforms);
						setCached(response.data.cached || false);
						setLastUpdated(new Date());

						console.log("✅ Organized data converted to multi-platform format");
					} else {
						throw new Error(
							"Invalid response structure - no analytics data found"
						);
					}
				} else {
					throw new Error(
						response.data?.message || "Failed to fetch platform data"
					);
				}
			} catch (error: any) {
				// Handle request cancellation silently
				if (
					error.name === "AbortError" ||
					error.name === "CanceledError" ||
					error.code === "ERR_CANCELED"
				) {
					console.log("🚫 Multi-platform request aborted");
					return;
				}

				console.error("❌ Failed to fetch multi-platform data:", error);
				setError(error.message || "Failed to load platform data");
			} finally {
				setLoading(false);
				isRequestInProgressRef.current = false;
			}
		},
		[fastMode]
	);

	/**
	 * Manual refresh function
	 */
	const refresh = useCallback(
		async (forceRefresh: boolean = false): Promise<void> => {
			await fetchAllPlatformData(forceRefresh);
		},
		[fetchAllPlatformData]
	);

	// Initial data load
	useEffect(() => {
		fetchAllPlatformData(false);
	}, [fetchAllPlatformData]);

	// Auto-refresh setup
	useEffect(() => {
		if (refreshInterval > 0) {
			intervalRef.current = setInterval(() => {
				refresh(false);
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
					console.log("Cleanup: Request already aborted or completed");
				}
			}
		};
	}, []);

	// Memoized platform data extraction - PREVENTS RE-RENDERS
	const shopifyData = useMemo(() => {
		return platformData?.shopify || null;
	}, [platformData]);

	const amazonData = useMemo(() => {
		return platformData?.amazon || null;
	}, [platformData]);

	const combinedData = useMemo(() => {
		return platformData?.combined || null;
	}, [platformData]);

	return {
		// Loading states
		loading,
		error,

		// Platform-specific data (memoized)
		shopifyData,
		amazonData,
		combinedData,

		// Cache info
		cached,
		lastUpdated,

		// Methods
		refresh,
	};
};

export default useMultiPlatformData;
