/**
 * Comprehensive Inventory Data Hook
 * Handles all inventory-related API calls in a single, optimized request
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import api from "../lib/axios";
import {
	InventoryAnalyticsResponse,
	SKUData,
	SKUSummaryStats,
	SalesKPIs,
	TrendAnalysis,
	AlertsSummary,
} from "../lib/inventoryService";
import { useGlobalDataStore } from "../store/globalDataStore";

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

	// Use global store data instead of local state - prevents duplicate API calls
	const inventoryAnalytics = useGlobalDataStore(
		(state: any) => state.inventoryData
	);
	const skuData = useGlobalDataStore((state: any) => state.skuData || []); // Ensure always an array
	const loading = useGlobalDataStore(
		(state: any) => state.loading.inventoryData || state.loading.skuData
	);
	const error = useGlobalDataStore(
		(state: any) => state.errors.inventoryData || state.errors.skuData
	);

	// Extract nested data from inventoryAnalytics
	const salesKPIs = inventoryAnalytics?.inventory_analytics?.sales_kpis || null;
	const trendAnalysis =
		inventoryAnalytics?.inventory_analytics?.trend_analysis || null;
	const alertsSummary =
		inventoryAnalytics?.inventory_analytics?.alerts_summary || null;

	// Generate summary stats from SKU data if not provided
	const summaryStats = useMemo(() => {
		// Ensure skuData is an array before using array methods
		if (!skuData || !Array.isArray(skuData) || skuData.length === 0)
			return null;

		return {
			total_skus: skuData.length,
			total_inventory_value: skuData.reduce(
				(sum: number, sku: any) => sum + (sku.total_value || 0),
				0
			),
			low_stock_count: skuData.filter(
				(sku: any) =>
					sku.current_availability > 0 && sku.current_availability < 10
			).length,
			out_of_stock_count: skuData.filter(
				(sku: any) => sku.current_availability <= 0
			).length,
			overstock_count: skuData.filter(
				(sku: any) => sku.current_availability > 100
			).length,
		};
	}, [skuData]);

	const [lastUpdated] = useState<Date | null>(new Date());
	const pagination = null; // Will be handled by global store later
	const cached = false; // Will be handled by global store later

	// Simple refresh functions that delegate to global store
	const refresh = useCallback(
		async (forceRefresh: boolean = false): Promise<void> => {
			const store = useGlobalDataStore.getState();
			await store.fetchInventoryData(forceRefresh);
		},
		[]
	);

	const loadPage = useCallback(async (page: number): Promise<void> => {
		const store = useGlobalDataStore.getState();
		await store.fetchSKUData(page, false);
	}, []);

	const clearCache = useCallback(async (): Promise<void> => {
		try {
			await api.delete("/dashboard/sku-cache");
			const store = useGlobalDataStore.getState();
			await store.fetchInventoryData(true);
		} catch (err: any) {
			console.error("❌ Failed to clear cache:", err);
		}
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
