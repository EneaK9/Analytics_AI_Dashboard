/**
 * Global Data Store using Zustand
 * Centralized state management for dashboard data with API call deduplication
 */

import React from "react";
import { create } from "zustand";
import api from "../lib/axios";

// Cache duration (5 minutes)
const CACHE_DURATION = 5 * 60 * 1000;

// Helper to check if data is stale
const isDataStale = (lastFetched: number | null): boolean => {
	if (!lastFetched) return true;
	return Date.now() - lastFetched > CACHE_DURATION;
};

// Types for available tables
interface AvailableTable {
	data_type: string;
	table_name: string;
	display_name: string;
	count: number;
}

interface AvailableTablesResponse {
	client_id: string;
	available_tables: {
		shopify: AvailableTable[];
		amazon: AvailableTable[];
	};
	total_platforms: number;
	total_tables: number;
	message: string;
}

// Types for raw data tables (updated for pagination)
interface RawDataResponse {
	client_id: string;
	table_key: string;
	display_name: string;
	table_name: string;
	platform: "shopify" | "amazon";
	data_type: "products" | "orders";
	columns: string[];
	data: any[];
	pagination: {
		current_page: number;
		page_size: number;
		total_records: number;
		total_pages: number;
		has_next: boolean;
		has_prev: boolean;
	};
	search?: string;
	search_fallback?: boolean;
	message: string;
}

interface GlobalDataState {
	// Main data from the two endpoints we actually use
	inventoryData: any | null;
	skuData: any[]; // Always an array, never null
	dashboardAnalytics: any | null;

	// Available tables for building dynamic tabs
	availableTables: AvailableTablesResponse | null;

	// Raw data tables for DataTables component
	rawDataTables: RawDataResponse | null;

	// Loading states
	loading: {
		inventoryData: boolean;
		skuData: boolean;
		dashboardAnalytics: boolean;
		availableTables: boolean;
		rawDataTables: boolean;
		rawDataTablesPagination: boolean; // Separate loading for pagination
	};

	// Error states
	errors: {
		inventoryData: string | null;
		skuData: string | null;
		dashboardAnalytics: string | null;
		availableTables: string | null;
		rawDataTables: string | null;
	};

	// Cache metadata
	lastFetched: {
		inventoryData: number | null;
		skuData: number | null;
		dashboardAnalytics: number | null;
		availableTables: number | null;
		rawDataTables: number | null;
	};

	// Request tracking to prevent duplicate calls
	activeRequests: Set<string>;

	// Filters
	filters: {
		platform: "shopify" | "amazon" | "combined";
		dateRange: "7d" | "30d" | "90d" | "custom";
		startDate?: string;
		endDate?: string;
	};

	// Raw data filters (both platform and dataType are required now)
	rawDataFilters: {
		platform: "shopify" | "amazon";
		dataType: "products" | "orders";
		page: number;
		pageSize: number;
		search: string;
	};

	// Actions
	setFilters: (filters: Partial<GlobalDataState["filters"]>) => void;
	setRawDataFilters: (
		filters: Partial<GlobalDataState["rawDataFilters"]>
	) => void;
	setSmartDefaultFilters: () => void;
	fetchInventoryData: (forceRefresh?: boolean) => Promise<void>;
	fetchSKUData: (page?: number, forceRefresh?: boolean) => Promise<void>;
	fetchDashboardAnalytics: (forceRefresh?: boolean) => Promise<void>;
	fetchAvailableTables: (
		clientId: string,
		forceRefresh?: boolean
	) => Promise<void>;
	fetchRawDataTables: (
		clientId: string,
		forceRefresh?: boolean
	) => Promise<void>;
	fetchAllData: (forceRefresh?: boolean) => Promise<void>;
	clearError: (dataType: keyof GlobalDataState["errors"]) => void;
}

export const useGlobalDataStore = create<GlobalDataState>()((set, get) => ({
	// Initial state
	inventoryData: null,
	skuData: [], // Initialize as empty array instead of null
	dashboardAnalytics: null,
	availableTables: null,
	rawDataTables: null,

	loading: {
		inventoryData: false,
		skuData: false,
		dashboardAnalytics: false,
		availableTables: false,
		rawDataTables: false,
		rawDataTablesPagination: false,
	},

	errors: {
		inventoryData: null,
		skuData: null,
		dashboardAnalytics: null,
		availableTables: null,
		rawDataTables: null,
	},

	lastFetched: {
		inventoryData: null,
		skuData: null,
		dashboardAnalytics: null,
		availableTables: null,
		rawDataTables: null,
	},

	activeRequests: new Set(),

	filters: {
		platform: "combined",
		dateRange: "30d",
	},

	rawDataFilters: {
		platform: "shopify", // Default to shopify
		dataType: "products", // Default to products
		page: 1,
		pageSize: 50,
		search: "",
	},

	// Actions
	setFilters: (newFilters) => {
		set((state) => ({
			filters: { ...state.filters, ...newFilters },
		}));
	},

	setRawDataFilters: (newFilters) => {
		console.log("🔧 Setting raw data filters:", newFilters);
		set((state) => {
			const updatedFilters = { ...state.rawDataFilters, ...newFilters };
			console.log("🔧 Updated filters:", updatedFilters);

			// Smart cache invalidation - only clear cache if platform/dataType/search changes, not for pagination
			const shouldClearCache =
				("platform" in newFilters &&
					newFilters.platform !== state.rawDataFilters.platform) ||
				("dataType" in newFilters &&
					newFilters.dataType !== state.rawDataFilters.dataType) ||
				("search" in newFilters &&
					newFilters.search !== state.rawDataFilters.search);

			return {
				rawDataFilters: updatedFilters,
				// Only clear cache for major filter changes, not pagination
				lastFetched: shouldClearCache
					? { ...state.lastFetched, rawDataTables: null }
					: state.lastFetched,
			};
		});
	},

	setSmartDefaultFilters: () => {
		const state = get();
		if (!state.availableTables) return;

		console.log("🎯 Setting smart default filters based on available tables");

		// Find the first available platform and its first available data type
		const platforms = Object.keys(state.availableTables.available_tables) as (
			| "shopify"
			| "amazon"
		)[];

		if (platforms.length === 0) {
			console.warn("⚠️ No available platforms found");
			return;
		}

		// Prefer shopify if available, otherwise use first available platform
		const preferredPlatform = platforms.includes("shopify")
			? "shopify"
			: platforms[0];
		const availableDataTypes =
			state.availableTables.available_tables[preferredPlatform];

		if (availableDataTypes.length === 0) {
			console.warn(
				`⚠️ No available data types for platform ${preferredPlatform}`
			);
			return;
		}

		// Prefer products if available, otherwise use first available data type
		const preferredDataType =
			availableDataTypes.find((t) => t.data_type === "products")?.data_type ||
			availableDataTypes[0].data_type;

		console.log(
			`🎯 Setting defaults to platform: ${preferredPlatform}, dataType: ${preferredDataType}`
		);

		set((state) => ({
			rawDataFilters: {
				...state.rawDataFilters,
				platform: preferredPlatform,
				dataType: preferredDataType as "products" | "orders",
				page: 1, // Reset to first page
			},
		}));
	},

	fetchInventoryData: async (forceRefresh = false) => {
		const state = get();
		const requestKey = "inventoryData";

		// Check if already loading or cached data is fresh
		if (state.activeRequests.has(requestKey)) return;
		if (!forceRefresh && !isDataStale(state.lastFetched.inventoryData)) return;

		set((state) => ({
			activeRequests: new Set(state.activeRequests).add(requestKey),
			loading: { ...state.loading, inventoryData: true },
			errors: { ...state.errors, inventoryData: null },
		}));

		try {
			const { platform } = state.filters;
			const params = {
				platform: platform === "combined" ? "all" : platform,
				fast_mode: true,
				force_refresh: forceRefresh,
			};

			const response = await api.get("/dashboard/inventory-analytics", {
				params,
			});

			set((state) => ({
				inventoryData: response.data,
				lastFetched: { ...state.lastFetched, inventoryData: Date.now() },
				loading: { ...state.loading, inventoryData: false },
			}));
		} catch (error: any) {
			set((state) => ({
				errors: {
					...state.errors,
					inventoryData: error.message || "Failed to fetch inventory data",
				},
				loading: { ...state.loading, inventoryData: false },
			}));
		} finally {
			set((state) => {
				const newActiveRequests = new Set(state.activeRequests);
				newActiveRequests.delete(requestKey);
				return { activeRequests: newActiveRequests };
			});
		}
	},

	fetchSKUData: async (page = 1, forceRefresh = false) => {
		const state = get();
		const requestKey = `skuData-${page}`;

		if (state.activeRequests.has(requestKey)) return;
		if (!forceRefresh && !isDataStale(state.lastFetched.skuData)) return;

		set((state) => ({
			activeRequests: new Set(state.activeRequests).add(requestKey),
			loading: { ...state.loading, skuData: true },
			errors: { ...state.errors, skuData: null },
		}));

		try {
			const { platform } = state.filters;
			const params = {
				platform: platform === "combined" ? undefined : platform,
				page,
				page_size: 2000, // 🔥 FIXED: Request ALL data, not just 20 items!
				use_cache: !forceRefresh,
				force_refresh: forceRefresh,
			};

			const response = await api.get("/dashboard/sku-inventory", { params });

			// Extract SKU array from response - handle different response structures
			let skuArray = [];
			if (response.data?.success) {
				skuArray =
					response.data.skus || response.data.sku_inventory?.skus || [];
			} else if (Array.isArray(response.data)) {
				skuArray = response.data;
			} else if (response.data?.data && Array.isArray(response.data.data)) {
				skuArray = response.data.data;
			}

			set((state) => ({
				skuData: skuArray, // Ensure it's always an array
				lastFetched: { ...state.lastFetched, skuData: Date.now() },
				loading: { ...state.loading, skuData: false },
			}));
		} catch (error: any) {
			set((state) => ({
				errors: {
					...state.errors,
					skuData: error.message || "Failed to fetch SKU data",
				},
				loading: { ...state.loading, skuData: false },
				skuData: [], // Reset to empty array on error
			}));
		} finally {
			set((state) => {
				const newActiveRequests = new Set(state.activeRequests);
				newActiveRequests.delete(requestKey);
				return { activeRequests: newActiveRequests };
			});
		}
	},

	fetchDashboardAnalytics: async (forceRefresh = false) => {
		const state = get();
		const requestKey = "dashboardAnalytics";

		if (state.activeRequests.has(requestKey)) return;
		if (!forceRefresh && !isDataStale(state.lastFetched.dashboardAnalytics))
			return;

		set((state) => ({
			activeRequests: new Set(state.activeRequests).add(requestKey),
			loading: { ...state.loading, dashboardAnalytics: true },
			errors: { ...state.errors, dashboardAnalytics: null },
		}));

		try {
			const response = await api.get("/dashboard/metrics?fast_mode=true");

			set((state) => ({
				dashboardAnalytics: response.data?.llm_analysis || null,
				lastFetched: { ...state.lastFetched, dashboardAnalytics: Date.now() },
				loading: { ...state.loading, dashboardAnalytics: false },
			}));
		} catch (error: any) {
			set((state) => ({
				errors: {
					...state.errors,
					dashboardAnalytics:
						error.message || "Failed to fetch dashboard analytics",
				},
				loading: { ...state.loading, dashboardAnalytics: false },
			}));
		} finally {
			set((state) => {
				const newActiveRequests = new Set(state.activeRequests);
				newActiveRequests.delete(requestKey);
				return { activeRequests: newActiveRequests };
			});
		}
	},

	fetchAvailableTables: async (clientId: string, forceRefresh = false) => {
		const state = get();
		const requestKey = `availableTables-${clientId}`;

		console.log("📋 fetchAvailableTables called for client:", clientId);

		if (state.activeRequests.has(requestKey)) {
			console.log("⏳ Available tables request already in progress, skipping");
			return;
		}

		if (!forceRefresh && !isDataStale(state.lastFetched.availableTables)) {
			console.log("📋 Using cached available tables");
			return;
		}

		set((state) => ({
			activeRequests: new Set(state.activeRequests).add(requestKey),
			loading: { ...state.loading, availableTables: true },
			errors: { ...state.errors, availableTables: null },
		}));

		try {
			console.log(`🔍 Fetching available tables for client ${clientId}`);

			const response = await api.get(`/data/available-tables/${clientId}`);

			console.log(`✅ Available tables fetched successfully:`, response.data);

			set((state) => ({
				availableTables: response.data,
				lastFetched: { ...state.lastFetched, availableTables: Date.now() },
				loading: { ...state.loading, availableTables: false },
			}));

			// Set smart defaults after fetching available tables
			get().setSmartDefaultFilters();
		} catch (error: any) {
			console.error(
				`❌ Failed to fetch available tables for client ${clientId}:`,
				error
			);
			set((state) => ({
				errors: {
					...state.errors,
					availableTables:
						error.response?.data?.detail ||
						error.message ||
						"Failed to fetch available tables",
				},
				loading: { ...state.loading, availableTables: false },
			}));
		} finally {
			set((state) => {
				const newActiveRequests = new Set(state.activeRequests);
				newActiveRequests.delete(requestKey);
				return { activeRequests: newActiveRequests };
			});
		}
	},

	fetchRawDataTables: async (clientId: string, forceRefresh = false) => {
		const state = get();
		const { platform, dataType, page, pageSize, search } = state.rawDataFilters;
		const requestKey = `rawDataTables-${clientId}-${platform}-${dataType}-${page}-${search}`;

		console.log("🔍 fetchRawDataTables called with:", {
			clientId,
			platform,
			dataType,
			page,
			search,
			forceRefresh,
		});

		if (state.activeRequests.has(requestKey)) {
			console.log("⏳ Request already in progress, skipping");
			return;
		}

		// Check if this is just a page change (same platform, dataType, search)
		const isPlatformOrDataTypeChange =
			!state.rawDataTables ||
			state.rawDataTables.platform !== platform ||
			state.rawDataTables.data_type !== dataType;

		const isSearchChange =
			!state.rawDataTables || (state.rawDataTables.search || "") !== search;

		const isPaginationChange =
			state.rawDataTables &&
			state.rawDataTables.platform === platform &&
			state.rawDataTables.data_type === dataType &&
			(state.rawDataTables.search || "") === search &&
			state.rawDataTables.pagination?.current_page !== page;

		// Skip cache check for platform/dataType/search changes - always fetch fresh data
		if (
			!forceRefresh &&
			!isPlatformOrDataTypeChange &&
			!isSearchChange &&
			!isPaginationChange
		) {
			const cacheKey = `rawDataTables-${platform}-${dataType}-${page}-${search}`;
			const currentCacheKey = state.rawDataTables
				? `rawDataTables-${state.rawDataTables.platform}-${
						state.rawDataTables.data_type
				  }-${state.rawDataTables.pagination?.current_page}-${
						state.rawDataTables.search || ""
				  }`
				: null;

			if (
				currentCacheKey === cacheKey &&
				!isDataStale(state.lastFetched.rawDataTables)
			) {
				console.log("📋 Using cached data for identical request");
				return;
			}
		}

		console.log("🔄 Fetching data:", {
			isPlatformOrDataTypeChange,
			isSearchChange,
			isPaginationChange,
			forceRefresh,
		});

		set((state) => ({
			activeRequests: new Set(state.activeRequests).add(requestKey),
			loading: {
				...state.loading,
				rawDataTables:
					isPlatformOrDataTypeChange || isSearchChange || forceRefresh,
				rawDataTablesPagination: Boolean(
					isPaginationChange && !isPlatformOrDataTypeChange && !isSearchChange
				),
			},
			errors: { ...state.errors, rawDataTables: null },
		}));

		try {
			const params: any = {
				platform,
				data_type: dataType,
				page,
				page_size: pageSize,
			};

			if (search.trim()) {
				params.search = search.trim();
			}

			console.log(
				`🔍 Fetching raw data tables for client ${clientId} with params:`,
				params
			);
			console.log(
				`🌐 API URL: /data/raw/${clientId}?${new URLSearchParams(
					params
				).toString()}`
			);

			const response = await api.get(`/data/raw/${clientId}`, { params });

			console.log(`✅ Raw data tables fetched successfully:`, response.data);

			set((state) => ({
				rawDataTables: response.data,
				lastFetched: { ...state.lastFetched, rawDataTables: Date.now() },
				loading: {
					...state.loading,
					rawDataTables: false,
					rawDataTablesPagination: false,
				},
			}));
		} catch (error: any) {
			console.error(
				`❌ Failed to fetch raw data tables for client ${clientId}:`,
				error
			);
			set((state) => ({
				errors: {
					...state.errors,
					rawDataTables:
						error.response?.data?.detail ||
						error.message ||
						"Failed to fetch raw data tables",
				},
				loading: {
					...state.loading,
					rawDataTables: false,
					rawDataTablesPagination: false,
				},
			}));
		} finally {
			set((state) => {
				const newActiveRequests = new Set(state.activeRequests);
				newActiveRequests.delete(requestKey);
				return { activeRequests: newActiveRequests };
			});
		}
	},

	fetchAllData: async (forceRefresh = false) => {
		// Fetch all data concurrently - SIMPLE AND SAFE
		const promises = [
			get().fetchInventoryData(forceRefresh),
			get().fetchSKUData(1, forceRefresh),
			get().fetchDashboardAnalytics(forceRefresh),
			// Note: rawDataTables is fetched separately when data tables section is accessed
			// to avoid loading unnecessary data for users who don't use it
		];

		await Promise.allSettled(promises);
	},

	clearError: (dataType) => {
		set((state) => ({
			errors: { ...state.errors, [dataType]: null },
		}));
	},
}));

// Stable selectors using individual properties to prevent re-renders
export const useInventoryData = () => {
	const data = useGlobalDataStore((state) => state.inventoryData);
	const loading = useGlobalDataStore((state) => state.loading.inventoryData);
	const error = useGlobalDataStore((state) => state.errors.inventoryData);
	const fetch = useGlobalDataStore((state) => state.fetchInventoryData);

	return { data, loading, error, fetch };
};

export const useSKUData = () => {
	const data = useGlobalDataStore((state) => state.skuData);
	const loading = useGlobalDataStore((state) => state.loading.skuData);
	const error = useGlobalDataStore((state) => state.errors.skuData);
	const fetch = useGlobalDataStore((state) => state.fetchSKUData);

	return { data, loading, error, fetch };
};

export const useDashboardAnalytics = () => {
	const data = useGlobalDataStore((state) => state.dashboardAnalytics);
	const loading = useGlobalDataStore(
		(state) => state.loading.dashboardAnalytics
	);
	const error = useGlobalDataStore((state) => state.errors.dashboardAnalytics);
	const fetch = useGlobalDataStore((state) => state.fetchDashboardAnalytics);

	return { data, loading, error, fetch };
};

export const useAvailableTables = () => {
	const data = useGlobalDataStore((state) => state.availableTables);
	const loading = useGlobalDataStore((state) => state.loading.availableTables);
	const error = useGlobalDataStore((state) => state.errors.availableTables);
	const fetch = useGlobalDataStore((state) => state.fetchAvailableTables);

	return { data, loading, error, fetch };
};

export const useFilters = () => {
	const filters = useGlobalDataStore((state) => state.filters);
	const setFilters = useGlobalDataStore((state) => state.setFilters);

	return { filters, setFilters };
};

export const useRawDataTables = () => {
	const data = useGlobalDataStore((state) => state.rawDataTables);
	const loading = useGlobalDataStore((state) => state.loading.rawDataTables);
	const paginationLoading = useGlobalDataStore(
		(state) => state.loading.rawDataTablesPagination
	);
	const error = useGlobalDataStore((state) => state.errors.rawDataTables);
	const fetch = useGlobalDataStore((state) => state.fetchRawDataTables);

	return { data, loading, paginationLoading, error, fetch };
};

export const useRawDataFilters = () => {
	const filters = useGlobalDataStore((state) => state.rawDataFilters);
	const setFilters = useGlobalDataStore((state) => state.setRawDataFilters);

	return { filters, setFilters };
};

export const useGlobalLoading = () => {
	const loadingStates = useGlobalDataStore((state) => state.loading);
	// Use useMemo to prevent recalculation on every render
	const isLoading = React.useMemo(
		() => Object.values(loadingStates).some(Boolean),
		[loadingStates]
	);

	return { isLoading, loadingStates };
};
