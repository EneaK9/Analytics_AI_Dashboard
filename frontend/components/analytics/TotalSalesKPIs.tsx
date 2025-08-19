"use client";

import React, { useState, useMemo, useCallback } from "react";
import { DollarSign, TrendingUp, Store, ShoppingBag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, {
	DateRange,
	getDateRange,
} from "../ui/CompactDatePicker";
import { useGlobalDataStore } from "../../store/globalDataStore";
import api from "../../lib/axios";

interface TotalSalesKPIsProps {
	clientData?: any[];
	className?: string;
}

type Platform = "shopify" | "amazon" | "all";

interface SalesData {
	value: number;
	trend: {
		value: string;
		isPositive: boolean;
		label: string;
	};
	subtitle: string;
}

const TotalSalesKPIs = React.memo(function TotalSalesKPIs({
	clientData,
	className = "",
}: TotalSalesKPIsProps) {
	// Use global store directly instead of useInventoryData hook
	const inventoryData = useGlobalDataStore((state) => state.inventoryData);
	const loading = useGlobalDataStore((state) => state.loading.inventoryData);
	const error = useGlobalDataStore((state) => state.errors.inventoryData);
	const fetchInventoryData = useGlobalDataStore((state) => state.fetchInventoryData);
	
	// Trigger data fetch on mount if no data
	React.useEffect(() => {
		if (!inventoryData && !loading) {
			fetchInventoryData();
		}
	}, [inventoryData, loading, fetchInventoryData]);

	// Date range states for each platform
	const [shopifyDateRange, setShopifyDateRange] = useState<DateRange>(
		getDateRange("month")
	);
	const [amazonDateRange, setAmazonDateRange] = useState<DateRange>(
		getDateRange("month")
	);
	const [allDateRange, setAllDateRange] = useState<DateRange>(
		getDateRange("month")
	);

	// Component-specific data states for date-filtered data
	const [shopifyCustomData, setShopifyCustomData] = useState<any>(null);
	const [amazonCustomData, setAmazonCustomData] = useState<any>(null);
	const [allCustomData, setAllCustomData] = useState<any>(null);
	const [shopifyCustomLoading, setShopifyCustomLoading] = useState<boolean>(false);
	const [amazonCustomLoading, setAmazonCustomLoading] = useState<boolean>(false);
	const [allCustomLoading, setAllCustomLoading] = useState<boolean>(false);

	// Track which components are using custom date filtering
	const [shopifyUseCustomDate, setShopifyUseCustomDate] = useState<boolean>(false);
	const [amazonUseCustomDate, setAmazonUseCustomDate] = useState<boolean>(false);
	const [allUseCustomDate, setAllUseCustomDate] = useState<boolean>(false);

	// Format date for API
	const formatDateForAPI = (date: Date): string => {
		return date.toISOString().split('T')[0]; // YYYY-MM-DD format
	};

	// Fetch functions for date-filtered data
	const fetchShopifySalesData = useCallback(async (dateRange: DateRange) => {
		setShopifyCustomLoading(true);
		try {
			const params = {
				component_type: "total_sales",
				platform: "shopify",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setShopifyCustomData(response.data.data);
			console.log('✅ Shopify sales data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch Shopify sales data:', error);
		} finally {
			setShopifyCustomLoading(false);
		}
	}, []);

	const fetchAmazonSalesData = useCallback(async (dateRange: DateRange) => {
		setAmazonCustomLoading(true);
		try {
			const params = {
				component_type: "total_sales",
				platform: "amazon",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setAmazonCustomData(response.data.data);
			console.log('✅ Amazon sales data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch Amazon sales data:', error);
		} finally {
			setAmazonCustomLoading(false);
		}
	}, []);

	const fetchAllSalesData = useCallback(async (dateRange: DateRange) => {
		setAllCustomLoading(true);
		try {
			const params = {
				component_type: "total_sales",
				platform: "combined",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setAllCustomData(response.data.data);
			console.log('✅ Combined sales data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch combined sales data:', error);
		} finally {
			setAllCustomLoading(false);
		}
	}, []);

	// Handle date range changes
	const handleShopifyDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ Shopify sales date changed to:', newDateRange.label);
		setShopifyDateRange(newDateRange);
		setShopifyUseCustomDate(true);
		await fetchShopifySalesData(newDateRange);
	}, [fetchShopifySalesData]);

	const handleAmazonDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ Amazon sales date changed to:', newDateRange.label);
		setAmazonDateRange(newDateRange);
		setAmazonUseCustomDate(true);
		await fetchAmazonSalesData(newDateRange);
	}, [fetchAmazonSalesData]);

	const handleAllDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ All platforms sales date changed to:', newDateRange.label);
		setAllDateRange(newDateRange);
		setAllUseCustomDate(true);
		await fetchAllSalesData(newDateRange);
	}, [fetchAllSalesData]);

	// Calculate sales data for each platform
	const calculateSalesData = (
		data: any,
		dateRange: DateRange,
		platform: Platform,
		usingCustomDate: boolean = false
	): SalesData => {
		if (!data) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "No data available",
			};
		}

		// Handle custom date API response format
		if (usingCustomDate) {
			// For combined platform, use the combined data
			if (platform === "all" && data.combined) {
				const currentRevenue = data.combined.total_revenue || 0;
				const currentOrders = data.combined.total_orders || 0;
				
				// Calculate within-period trend from combined sales comparison data if available
				const trendData = data.combined.sales_comparison;
				const trendValue = trendData && trendData.first_half_avg_revenue > 0 ? 
					((trendData.second_half_avg_revenue - trendData.first_half_avg_revenue) / trendData.first_half_avg_revenue) * 100 : 0;

				const isPositive = trendValue >= 0;
				const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;
				
				return {
					value: currentRevenue,
					trend: {
						value: trendFormatted,
						isPositive,
						label: `trend within period`,
					},
					subtitle: `Combined total sales (${currentOrders} orders)`,
				};
			}
			
			// For specific platforms (shopify/amazon)
			const platformKey = platform === "all" ? "shopify" : platform;
			const platformData = data[platformKey] || data;
			
			if (!platformData) {
				return {
					value: 0,
					trend: {
						value: "0%",
						isPositive: true,
						label: "vs previous period",
					},
					subtitle: "No data available",
				};
			}

			// Get revenue from the component data structure
			const currentRevenue = platformData.total_sales_30_days?.revenue || 0;
			const currentOrders = platformData.total_sales_30_days?.orders || 0;
			
			// Calculate trend if available (within-period growth) - handle both naming conventions
			const trendData = platformData.sales_comparison;
			const firstHalf = trendData?.first_half_avg_revenue || trendData?.current_period_avg_revenue || 0;
			const secondHalf = trendData?.second_half_avg_revenue || trendData?.historical_avg_revenue || 0;
			const trendValue = firstHalf > 0 ? 
				((secondHalf - firstHalf) / firstHalf) * 100 : 0;

			const isPositive = trendValue >= 0;
			const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

			return {
				value: currentRevenue,
				trend: {
					value: trendFormatted,
					isPositive,
					label: `trend within period`,
				},
				subtitle: `${
					platform === "all"
						? "Combined"
						: platform.charAt(0).toUpperCase() + platform.slice(1)
				} total sales (${currentOrders} orders)`,
			};
		}

		// Handle default inventory analytics data format
		if (!data?.sales_kpis?.total_sales_30_days) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "No data available",
			};
		}

		// Get 30-day sales data (default to 30 days as requested)
		const salesData = data.sales_kpis.total_sales_30_days;
		const currentRevenue = salesData.revenue || 0;
		const currentOrders = salesData.orders || 0;
		
		// Get trend data from multiple possible sources (handle both naming conventions)
		const trendData = data.trend_analysis?.sales_comparison || data.sales_comparison;
		
		// Handle different field naming conventions
		const firstHalfRevenue = trendData?.first_half_avg_revenue || 
								trendData?.current_period_avg_revenue || 0;
		const secondHalfRevenue = trendData?.second_half_avg_revenue || 
								 trendData?.historical_avg_revenue || 0;

		// Calculate trend percentage (within-period growth)
		const trendValue =
			firstHalfRevenue > 0
				? ((secondHalfRevenue - firstHalfRevenue) / firstHalfRevenue) * 100
				: 0;

		const isPositive = trendValue >= 0;
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		return {
			value: currentRevenue, // Use total revenue for selected period
			trend: {
				value: trendFormatted,
				isPositive,
				label: `trend within ${dateRange.label.toLowerCase()}`,
			},
			subtitle: `${
				platform === "all"
					? "Combined"
					: platform.charAt(0).toUpperCase() + platform.slice(1)
			} total sales (${currentOrders || 'N/A'} orders)`,
		};
	};

	// Memoized sales data for each platform - uses either default or custom date data
	const shopifySales = useMemo(() => {
		// Use custom data if date picker was used, otherwise use default inventory data
		if (shopifyUseCustomDate && shopifyCustomData) {
			return calculateSalesData(shopifyCustomData, shopifyDateRange, "shopify", true);
		}
		// Extract Shopify data from the correct nested path
		const shopifyData = inventoryData?.inventory_analytics?.platforms?.shopify;
		return calculateSalesData(shopifyData, shopifyDateRange, "shopify", false);
	}, [inventoryData, shopifyDateRange, shopifyUseCustomDate, shopifyCustomData]);

	const amazonSales = useMemo(() => {
		// Use custom data if date picker was used, otherwise use default inventory data
		if (amazonUseCustomDate && amazonCustomData) {
			return calculateSalesData(amazonCustomData, amazonDateRange, "amazon", true);
		}
		// Extract Amazon data from the correct nested path
		const amazonData = inventoryData?.inventory_analytics?.platforms?.amazon;
		return calculateSalesData(amazonData, amazonDateRange, "amazon", false);
	}, [inventoryData, amazonDateRange, amazonUseCustomDate, amazonCustomData]);

	const allSales = useMemo(() => {
		// Use custom data if date picker was used, otherwise use default inventory data
		if (allUseCustomDate && allCustomData) {
			return calculateSalesData(allCustomData, allDateRange, "all", true);
		}

		if (!inventoryData?.inventory_analytics?.platforms) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "Combined sales data unavailable",
			};
		}

		// Use the combined platform data which already aggregates both platforms
		const combinedData = inventoryData.inventory_analytics.platforms.combined;
		return calculateSalesData(combinedData, allDateRange, "all", false);
	}, [inventoryData, allDateRange, allUseCustomDate, allCustomData]);

	// Format currency
	const formatCurrency = (value: number) => {
		return new Intl.NumberFormat("en-US", {
			style: "currency",
			currency: "USD",
			minimumFractionDigits: 0,
			maximumFractionDigits: 0,
		}).format(value);
	};

	// Individual KPI Card Component (memoized for performance)
	const SalesKPICard = React.memo(
		({
			title,
			data,
			dateRange,
			onDateRangeChange,
			loading,
			error,
			icon,
			iconColor,
			iconBgColor,
		}: {
			title: string;
			data: SalesData;
			dateRange: DateRange;
			onDateRangeChange: (range: DateRange) => void;
			loading: boolean;
			error: string | null;
			icon: React.ReactNode;
			iconColor: string;
			iconBgColor: string;
		}) => {
			if (loading) {
				return (
					<Card className="bg-gray-100 border-gray-300 hover:shadow-md transition-all duration-300">
						<CardHeader className="pb-3">
							<div className="flex items-center justify-between">
								<CardTitle className="text-sm font-medium text-gray-600">
									{title}
								</CardTitle>
								<div className="w-24 h-6 bg-gray-200 rounded animate-pulse"></div>
							</div>
						</CardHeader>
						<CardContent>
							<div className="animate-pulse">
								<div className="flex items-center justify-between mb-3">
									<div className="h-10 w-10 bg-gray-200 rounded-lg"></div>
									<div className="w-12 h-5 bg-gray-200 rounded"></div>
								</div>
								<div className="space-y-2">
									<div className="h-6 bg-gray-200 rounded"></div>
									<div className="h-3 bg-gray-200 rounded w-2/3"></div>
								</div>
							</div>
						</CardContent>
					</Card>
				);
			}

			if (error) {
				return (
					<Card className="bg-gray-100 border-red-200 hover:shadow-md transition-all duration-300">
						<CardHeader className="pb-3">
							<div className="flex items-center justify-between">
								<CardTitle className="text-sm font-medium text-gray-600">
									{title}
								</CardTitle>
								<CompactDatePicker
									value={dateRange}
									onChange={onDateRangeChange}
								/>
							</div>
						</CardHeader>
						<CardContent>
							<div className="flex items-center justify-center h-20 text-red-600">
								<p className="text-sm">Error loading data</p>
							</div>
						</CardContent>
					</Card>
				);
			}

			return (
				<Card className="bg-gray-100 border-gray-300 hover:shadow-md hover:bg-gray-200 transition-all duration-300">
					<CardHeader className="pb-3">
						<div className="flex items-center justify-between">
							<CardTitle className="text-sm font-medium text-gray-600">
								{title}
							</CardTitle>
							<CompactDatePicker
								value={dateRange}
								onChange={onDateRangeChange}
							/>
						</div>
					</CardHeader>
					<CardContent>
						{/* Header with Trend */}
						<div className="flex items-center justify-between mb-3">
							<div
								className="h-10 w-10 rounded-lg flex items-center justify-center"
								style={{ backgroundColor: iconBgColor }}>
								{icon}
							</div>

							<div
								className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${
									data.trend.isPositive
										? "text-green-700 bg-green-100"
										: "text-red-700 bg-red-100"
								}`}>
								<TrendingUp
									className={`h-3 w-3 ${
										data.trend.isPositive ? "" : "rotate-180"
									}`}
								/>
								{data.trend.value}
							</div>
						</div>

						{/* Value and Subtitle */}
						<div className="space-y-1">
							<h3 className="text-2xl font-bold text-gray-900">
								{formatCurrency(data.value)}
							</h3>
							<p className="text-xs text-gray-500">{data.subtitle}</p>
						</div>

						{/* Trend Label */}
						<div className="mt-2 pt-2 border-t border-gray-300">
							<p className="text-xs text-gray-400">{data.trend.label}</p>
						</div>
					</CardContent>
				</Card>
			);
		}
	);

	SalesKPICard.displayName = "SalesKPICard";

	return (
		<div className={`space-y-4 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">Total Sales</h2>
				<p className="text-sm text-gray-600">
					Revenue metrics across all platforms
				</p>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Shopify Sales KPI */}
				<SalesKPICard
					title="Shopify Sales"
					data={shopifySales}
					dateRange={shopifyDateRange}
					onDateRangeChange={handleShopifyDateChange}
					loading={shopifyUseCustomDate ? shopifyCustomLoading : loading}
					error={error}
					icon={<Store className="h-4 w-4" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Sales KPI */}
				<SalesKPICard
					title="Amazon Sales"
					data={amazonSales}
					dateRange={amazonDateRange}
					onDateRangeChange={handleAmazonDateChange}
					loading={amazonUseCustomDate ? amazonCustomLoading : loading}
					error={error}
					icon={
						<ShoppingBag className="h-4 w-4" style={{ color: "#f59e0b" }} />
					}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Sales KPI */}
				<SalesKPICard
					title="All Platforms"
					data={allSales}
					dateRange={allDateRange}
					onDateRangeChange={handleAllDateChange}
					loading={allUseCustomDate ? allCustomLoading : loading}
					error={error}
					icon={<DollarSign className="h-4 w-4" style={{ color: "#3b82f6" }} />}
					iconColor="#3b82f6"
					iconBgColor="#eff6ff"
				/>
			</div>
		</div>
	);
});

export default TotalSalesKPIs;
