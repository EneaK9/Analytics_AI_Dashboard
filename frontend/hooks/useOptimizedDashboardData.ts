/**
 * Optimized Dashboard Data Hooks with React Query
 *
 * Features:
 * - Independent caching per platform and date range
 * - No duplicate API calls
 * - Background data refresh
 * - Independent component state management
 */

import {
	useQuery,
	useQueryClient,
	UseQueryOptions,
} from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import api from "../lib/axios";

// Types
export interface DateRange {
	startDate: string;
	endDate: string;
	preset?: "7d" | "30d" | "90d" | "custom";
}

export interface DashboardFilters {
	platform: "shopify" | "amazon" | "combined";
	dateRange: DateRange;
	refreshInterval?: number;
}

export interface SalesMetrics {
	total_sales_7_days?: {
		revenue: number;
		units: number;
		orders: number;
	};
	total_sales_30_days?: {
		revenue: number;
		units: number;
		orders: number;
	};
	inventory_turnover_rate?: number;
	days_stock_remaining?: number;
}

export interface TrendData {
	inventory_levels_chart?: Array<{
		date: string;
		inventory_level: number;
	}>;
	units_sold_chart?: Array<{
		date: string;
		units_sold: number;
	}>;
	sales_comparison?: {
		historical_avg_revenue: number;
		current_period_avg_revenue: number;
	};
}

export interface AlertsData {
	summary?: {
		total_alerts: number;
		critical_alerts: number;
	};
	low_stock_alerts?: any[];
	overstock_alerts?: any[];
	sales_spike_alerts?: any[];
	sales_slowdown_alerts?: any[];
}

export interface SKUData {
	skus: any[];
	summary_stats?: {
		total_skus: number;
		total_inventory_value: number;
		low_stock_count: number;
		out_of_stock_count: number;
	};
	pagination?: {
		current_page: number;
		page_size: number;
		total_count: number;
		total_pages: number;
		has_next: boolean;
		has_previous: boolean;
	};
}

// Helper functions
const createQueryKey = (
	type: string,
	platform: string,
	dateRange: DateRange,
	additionalParams?: Record<string, any>
) => {
	const key = [
		type,
		platform,
		dateRange.preset || "custom",
		dateRange.startDate,
		dateRange.endDate,
	];
	if (additionalParams) {
		key.push(JSON.stringify(additionalParams));
	}
	return key;
};

const formatDateForAPI = (date: Date): string => {
	return date.toISOString().split("T")[0];
};

const getDateRangeFromPreset = (preset: "7d" | "30d" | "90d"): DateRange => {
	const endDate = new Date();
	const startDate = new Date();

	switch (preset) {
		case "7d":
			startDate.setDate(endDate.getDate() - 7);
			break;
		case "30d":
			startDate.setDate(endDate.getDate() - 30);
			break;
		case "90d":
			startDate.setDate(endDate.getDate() - 90);
			break;
	}

	return {
		startDate: formatDateForAPI(startDate),
		endDate: formatDateForAPI(endDate),
		preset,
	};
};

// Custom hooks for different data types

/**
 * Hook for fetching sales metrics with independent caching
 */
export const useSalesMetrics = (filters: DashboardFilters) => {
	const queryKey = createQueryKey("sales", filters.platform, filters.dateRange);

	return useQuery({
		queryKey,
		queryFn: async (): Promise<SalesMetrics> => {
			const params: Record<string, any> = {
				platform: filters.platform === "combined" ? "all" : filters.platform,
				start_date: filters.dateRange.startDate,
				end_date: filters.dateRange.endDate,
				fast_mode: true,
			};

			const response = await api.get("/dashboard/inventory-analytics", {
				params,
			});

			// Handle multi-platform response (when platform=all)
			if (response.data?.platforms && filters.platform === "combined") {
				return response.data.platforms.combined?.sales_kpis || {};
			}

			// Handle single platform response or extract specific platform from multi-platform
			if (response.data?.platforms && filters.platform !== "combined") {
				return response.data.platforms[filters.platform]?.sales_kpis || {};
			}

			// Fallback to single platform response structure
			return response.data?.inventory_analytics?.sales_kpis || {};
		},
		staleTime: filters.refreshInterval || 5 * 60 * 1000, // 5 minutes default
		enabled: Boolean(filters.platform && filters.dateRange),
		retry: (failureCount, error: any) => {
			// Don't retry on auth errors - let axios interceptor handle logout
			if (error?.response?.status === 401 || error?.response?.status === 403) {
				return false;
			}
			return failureCount < 3;
		},
	});
};

/**
 * Hook for fetching trend analysis with independent caching
 */
export const useTrendAnalysis = (filters: DashboardFilters) => {
	const queryKey = createQueryKey(
		"trends",
		filters.platform,
		filters.dateRange
	);

	return useQuery({
		queryKey,
		queryFn: async (): Promise<TrendData> => {
			const params: Record<string, any> = {
				platform: filters.platform === "combined" ? "all" : filters.platform,
				start_date: filters.dateRange.startDate,
				end_date: filters.dateRange.endDate,
				fast_mode: true,
			};

			const response = await api.get("/dashboard/inventory-analytics", {
				params,
			});

			// Handle multi-platform response (when platform=all)
			if (response.data?.platforms && filters.platform === "combined") {
				return response.data.platforms.combined?.trend_analysis || {};
			}

			// Handle single platform response or extract specific platform from multi-platform
			if (response.data?.platforms && filters.platform !== "combined") {
				return response.data.platforms[filters.platform]?.trend_analysis || {};
			}

			// Fallback to single platform response structure
			return response.data?.inventory_analytics?.trend_analysis || {};
		},
		staleTime: filters.refreshInterval || 5 * 60 * 1000,
		enabled: Boolean(filters.platform && filters.dateRange),
		retry: (failureCount, error: any) => {
			// Don't retry on auth errors - let axios interceptor handle logout
			if (error?.response?.status === 401 || error?.response?.status === 403) {
				return false;
			}
			return failureCount < 3;
		},
	});
};

/**
 * Hook for fetching alerts with independent caching
 */
export const useAlertsData = (filters: DashboardFilters) => {
	const queryKey = createQueryKey(
		"alerts",
		filters.platform,
		filters.dateRange
	);

	return useQuery({
		queryKey,
		queryFn: async (): Promise<AlertsData> => {
			const params: Record<string, any> = {
				platform: filters.platform === "combined" ? "all" : filters.platform,
				start_date: filters.dateRange.startDate,
				end_date: filters.dateRange.endDate,
				fast_mode: true,
			};

			const response = await api.get("/dashboard/inventory-analytics", {
				params,
			});

			let alertsData;

			// Handle multi-platform response (when platform=all)
			if (response.data?.platforms && filters.platform === "combined") {
				alertsData = response.data.platforms.combined?.alerts_summary;
			}
			// Handle single platform response or extract specific platform from multi-platform
			else if (response.data?.platforms && filters.platform !== "combined") {
				alertsData = response.data.platforms[filters.platform]?.alerts_summary;
			}
			// Fallback to single platform response structure
			else {
				alertsData = response.data?.inventory_analytics?.alerts_summary;
			}

			return alertsData || {};
		},
		staleTime: filters.refreshInterval || 3 * 60 * 1000, // 3 minutes for alerts (more frequent)
		enabled: Boolean(filters.platform && filters.dateRange),
		retry: (failureCount, error: any) => {
			// Don't retry on auth errors - let axios interceptor handle logout
			if (error?.response?.status === 401 || error?.response?.status === 403) {
				return false;
			}
			return failureCount < 3;
		},
	});
};

/**
 * Hook for fetching SKU data with independent caching and pagination
 */
export const useSKUData = (
	filters: DashboardFilters,
	page: number = 1,
	pageSize: number = 2000 // 🔥 FIXED: Show ALL data by default, not just 50!
) => {
	const queryKey = createQueryKey("sku", filters.platform, filters.dateRange, {
		page,
		pageSize,
	});

	return useQuery({
		queryKey,
		queryFn: async (): Promise<SKUData> => {
			const params: Record<string, any> = {
				platform: filters.platform === "combined" ? "all" : filters.platform,
				page,
				page_size: pageSize,
				use_cache: true,
			};

			const response = await api.get("/dashboard/sku-inventory", { params });

			// SKU data doesn't use multi-platform structure, keep existing logic
			return {
				skus: response.data?.skus || response.data?.sku_inventory?.skus || [],
				summary_stats:
					response.data?.summary_stats ||
					response.data?.sku_inventory?.summary_stats,
				pagination: response.data?.pagination,
			};
		},
		staleTime: filters.refreshInterval || 10 * 60 * 1000, // 10 minutes for SKU data
		enabled: Boolean(filters.platform),
		retry: (failureCount, error: any) => {
			// Don't retry on auth errors - let axios interceptor handle logout
			if (error?.response?.status === 401 || error?.response?.status === 403) {
				return false;
			}
			return failureCount < 3;
		},
	});
};

/**
 * Combined hook for all dashboard data - use when you need everything at once
 */
export const useDashboardData = (filters: DashboardFilters) => {
	const salesMetrics = useSalesMetrics(filters);
	const trendAnalysis = useTrendAnalysis(filters);
	const alertsData = useAlertsData(filters);
	const skuData = useSKUData(filters);

	const isLoading =
		salesMetrics.isLoading ||
		trendAnalysis.isLoading ||
		alertsData.isLoading ||
		skuData.isLoading;
	const error =
		salesMetrics.error ||
		trendAnalysis.error ||
		alertsData.error ||
		skuData.error;

	return {
		salesMetrics: salesMetrics.data,
		trendAnalysis: trendAnalysis.data,
		alertsData: alertsData.data,
		skuData: skuData.data,
		isLoading,
		error,
		refetch: useCallback(() => {
			salesMetrics.refetch();
			trendAnalysis.refetch();
			alertsData.refetch();
			skuData.refetch();
		}, [
			salesMetrics.refetch,
			trendAnalysis.refetch,
			alertsData.refetch,
			skuData.refetch,
		]),
	};
};

/**
 * Utility hook for managing date ranges
 */
export const useDateRange = (initialPreset: "7d" | "30d" | "90d" = "7d") => {
	const dateRange = useMemo(
		() => getDateRangeFromPreset(initialPreset),
		[initialPreset]
	);

	const setPreset = useCallback((preset: "7d" | "30d" | "90d") => {
		return getDateRangeFromPreset(preset);
	}, []);

	const setCustomRange = useCallback(
		(startDate: string, endDate: string): DateRange => {
			return {
				startDate,
				endDate,
				preset: "custom",
			};
		},
		[]
	);

	return {
		dateRange,
		setPreset,
		setCustomRange,
	};
};

/**
 * Prefetch hook for background data loading
 */
export const usePrefetchDashboardData = () => {
	const queryClient = useQueryClient();

	const prefetchPlatformData = useCallback(
		async (
			platform: "shopify" | "amazon",
			preset: "7d" | "30d" | "90d" = "7d"
		) => {
			const dateRange = getDateRangeFromPreset(preset);
			const filters: DashboardFilters = { platform, dateRange };

			const queries = [
				queryClient.prefetchQuery({
					queryKey: createQueryKey("sales", platform, dateRange),
					queryFn: async () => {
						const response = await api.get("/dashboard/inventory-analytics", {
							params: {
								platform,
								start_date: dateRange.startDate,
								end_date: dateRange.endDate,
								fast_mode: true,
							},
						});
						return response.data?.inventory_analytics?.sales_kpis || {};
					},
				}),
				queryClient.prefetchQuery({
					queryKey: createQueryKey("trends", platform, dateRange),
					queryFn: async () => {
						const response = await api.get("/dashboard/inventory-analytics", {
							params: {
								platform,
								start_date: dateRange.startDate,
								end_date: dateRange.endDate,
								fast_mode: true,
							},
						});
						return response.data?.inventory_analytics?.trend_analysis || {};
					},
				}),
				queryClient.prefetchQuery({
					queryKey: createQueryKey("alerts", platform, dateRange),
					queryFn: async () => {
						const response = await api.get("/dashboard/inventory-analytics", {
							params: {
								platform,
								start_date: dateRange.startDate,
								end_date: dateRange.endDate,
								fast_mode: true,
							},
						});
						return response.data?.inventory_analytics?.alerts_summary || {};
					},
				}),
			];

			await Promise.all(queries);
		},
		[queryClient]
	);

	return { prefetchPlatformData };
};
