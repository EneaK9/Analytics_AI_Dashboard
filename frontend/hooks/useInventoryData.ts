/**
 * Comprehensive Inventory Data Hook
 * Handles all inventory-related API calls in a single, optimized request
 */

import { useState, useEffect, useCallback, useRef } from "react";
import api from "../lib/axios";
import requestManager from "../lib/requestManager";
import {
	InventoryAnalyticsResponse,
	SKUData,
	SKUSummaryStats,
	SalesKPIs,
	TrendAnalysis,
	AlertsSummary,
} from "../lib/inventoryService";

interface UseInventoryDataOptions {
	refreshInterval?: number; // Auto-refresh interval in ms (0 to disable)
	fastMode?: boolean; // Use fast mode for analytics
	pageSize?: number; // Page size for SKU data (always paginated)
	platform?: string; // Platform selection: "shopify" or "amazon"
}

interface InventoryDataState {
	// Loading states
	loading: boolean;
	error: string | null;

	// Core data
	inventoryAnalytics: InventoryAnalyticsResponse | null;
	skuData: SKUData[];
	summaryStats: SKUSummaryStats | null;
	salesKPIs: SalesKPIs | null;
	trendAnalysis: TrendAnalysis | null;
	alertsSummary: AlertsSummary | null;

	// Pagination (for SKU data)
	pagination: {
		current_page: number;
		page_size: number;
		total_count: number;
		total_pages: number;
		has_next: boolean;
		has_previous: boolean;
	} | null;

	// Cache info
	cached: boolean;
	lastUpdated: Date | null;

	// Methods
	refresh: (forceRefresh?: boolean) => Promise<void>;
	loadPage: (page: number) => Promise<void>;
	clearCache: () => Promise<void>;
}

export const useInventoryData = (
	options: UseInventoryDataOptions = {}
): InventoryDataState => {
	const {
		refreshInterval = 0,
		fastMode = true,
		pageSize = 50,
		platform = "shopify",
	} = options;

	// State management
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [inventoryAnalytics, setInventoryAnalytics] =
		useState<InventoryAnalyticsResponse | null>(null);
	const [skuData, setSKUData] = useState<SKUData[]>([]);
	const [summaryStats, setSummaryStats] = useState<SKUSummaryStats | null>(
		null
	);
	const [salesKPIs, setSalesKPIs] = useState<SalesKPIs | null>(null);
	const [trendAnalysis, setTrendAnalysis] = useState<TrendAnalysis | null>(
		null
	);
	const [alertsSummary, setAlertsSummary] = useState<AlertsSummary | null>(
		null
	);
	const [pagination, setPagination] =
		useState<InventoryDataState["pagination"]>(null);
	const [cached, setCached] = useState(false);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
	const [currentPage, setCurrentPage] = useState(1);

	// Refs for cleanup and request management
	const intervalRef = useRef<NodeJS.Timeout | null>(null);
	const abortControllerRef = useRef<AbortController | null>(null);
	const isRequestInProgressRef = useRef<boolean>(false);

	/**
	 * Comprehensive data fetcher - gets all inventory data in optimized calls
	 */
	const fetchInventoryData = useCallback(
		async (page: number = 1, forceRefresh: boolean = false): Promise<void> => {
			// Prevent multiple simultaneous requests unless forced
			if (isRequestInProgressRef.current && !forceRefresh) {
				console.log("⏳ Request already in progress, skipping...");
				return;
			}

			try {
				isRequestInProgressRef.current = true;
				setLoading(true);
				setError(null);

				// Only abort if there's a genuine conflict (forced refresh)
				if (forceRefresh && abortControllerRef.current) {
					abortControllerRef.current.abort();
				}
				abortControllerRef.current = new AbortController();

				console.log("🔍 Fetching comprehensive inventory data...", {
					platform,
					page,
					forceRefresh,
				});

				// Use request manager for deduplication and caching with platform support
				const [skuResponse, analyticsResponse] = await Promise.all([
					requestManager.executeRequest(
						`sku-inventory-${platform}-${page}-${pageSize}`,
						async (signal: AbortSignal) => {
							return await api.get("/dashboard/sku-inventory", {
								params: {
									page,
									page_size: pageSize,
									use_cache: !forceRefresh,
									force_refresh: forceRefresh,
									platform: platform,
								},
								signal,
							});
						},
						{
							cacheTTL: 30000, // 30 seconds
							forceRefresh,
						}
					),
					requestManager.executeRequest(
						`inventory-analytics-${platform}-${fastMode}`,
						async (signal: AbortSignal) => {
							return await api.get("/dashboard/inventory-analytics", {
								params: {
									fast_mode: fastMode,
									force_refresh: forceRefresh,
									platform: platform,
								},
								signal,
							});
						},
						{
							cacheTTL: 60000, // 1 minute
							forceRefresh,
						}
					),
				]);

				// Process SKU data with robust error handling
				if (skuResponse.data?.success) {
					console.log("🔍 SKU Response Debug:", {
						success: skuResponse.data.success,
						hasSkuInventory: !!skuResponse.data.sku_inventory,
						skuInventoryKeys: skuResponse.data.sku_inventory
							? Object.keys(skuResponse.data.sku_inventory)
							: "null",
						platform,
					});

					const skuInventory = skuResponse.data.sku_inventory || {};
					setSKUData(skuInventory.skus || []);
					setPagination(
						skuResponse.data.pagination || {
							page: 1,
							page_size: 50,
							total_pages: 1,
							total_count: 0,
						}
					);
					setSummaryStats(skuInventory.summary_stats || null);
					setCached(skuResponse.data.cached || false);
				} else {
					console.log("🚨 SKU Response Failed:", skuResponse.data);
					setSKUData([]);
				}

				// Process analytics data - handle nested structure
				if (analyticsResponse.data?.success) {
					setInventoryAnalytics(analyticsResponse.data);

					// Handle nested inventory_analytics structure
					const inventoryData =
						analyticsResponse.data.inventory_analytics ||
						analyticsResponse.data;
					setSalesKPIs(inventoryData.sales_kpis || null);
					setTrendAnalysis(inventoryData.trend_analysis || null);
					setAlertsSummary(inventoryData.alerts_summary || null);

					console.log("🔍 Analytics Data Debug:", {
						hasInventoryAnalytics: !!analyticsResponse.data.inventory_analytics,
						hasSalesKPIs: !!inventoryData.sales_kpis,
						hasAlertsummary: !!inventoryData.alerts_summary,
						salesKPIsKeys: inventoryData.sales_kpis
							? Object.keys(inventoryData.sales_kpis)
							: [],
						alertsKeys: inventoryData.alerts_summary
							? Object.keys(inventoryData.alerts_summary)
							: [],
					});
				}

				setCurrentPage(page);
				setLastUpdated(new Date());
				setError(null);

				console.log("✅ Inventory data fetched successfully");
			} catch (err: unknown) {
				// Handle request cancellation (both native AbortError and axios CanceledError)
				const error = err as any; // Type assertion for error handling
				if (
					error.name === "AbortError" ||
					error.name === "CanceledError" ||
					error.code === "ERR_CANCELED"
				) {
					console.log("🚫 Request aborted");
					return;
				}

				console.error("❌ Failed to fetch inventory data:", err);
				setError(
					error.response?.data?.detail ||
						error.message ||
						"Failed to fetch inventory data"
				);

				// Reset data on error
				setSKUData([]);
				setSummaryStats(null);
				setSalesKPIs(null);
				setTrendAnalysis(null);
				setAlertsSummary(null);
				setPagination(null);
				setInventoryAnalytics(null);
			} finally {
				isRequestInProgressRef.current = false;
				setLoading(false);
			}
		},
		[pageSize, fastMode, platform]
	);

	/**
	 * Refresh data with optional force refresh
	 */
	const refresh = useCallback(
		async (forceRefresh: boolean = false): Promise<void> => {
			await fetchInventoryData(currentPage, forceRefresh);
		},
		[fetchInventoryData, currentPage]
	);

	/**
	 * Load specific page (for pagination)
	 */
	const loadPage = useCallback(
		async (page: number): Promise<void> => {
			if (page >= 1 && pagination && page <= pagination.total_pages) {
				await fetchInventoryData(page, false);
			}
		},
		[fetchInventoryData, pagination]
	);

	/**
	 * Clear cache and refresh
	 */
	const clearCache = useCallback(async (): Promise<void> => {
		try {
			// Clear both API cache and request manager cache
			await api.delete("/dashboard/sku-cache");
			requestManager.clearCache();
			await refresh(true);
		} catch (err: any) {
			// Handle request cancellation silently
			if (
				err.name === "AbortError" ||
				err.name === "CanceledError" ||
				err.code === "ERR_CANCELED"
			) {
				console.log("🚫 Cache clear request aborted");
				return;
			}

			console.error("❌ Failed to clear cache:", err);
			// Still refresh even if cache clear fails - clear local cache at least
			requestManager.clearCache();
			await refresh(true);
		}
	}, [refresh]);

	// Initial data load and platform change handling
	useEffect(() => {
		fetchInventoryData(1, false);
	}, [fetchInventoryData, platform]); // Include platform to trigger reload on platform change

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

			// Cancel all requests handled by request manager
			requestManager.cancelAllRequests();
		};
	}, []);

	return {
		// Loading states
		loading,
		error,

		// Core data
		inventoryAnalytics,
		skuData,
		summaryStats,
		salesKPIs,
		trendAnalysis,
		alertsSummary,

		// Pagination
		pagination,

		// Cache info
		cached,
		lastUpdated,

		// Methods
		refresh,
		loadPage,
		clearCache,
	};
};

export default useInventoryData;
