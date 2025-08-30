"use client";

import React, { useState, useMemo, useCallback } from "react";
import { RefreshCw, TrendingUp, RotateCcw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, {
	DateRange,
	getDateRange,
} from "../ui/CompactDatePicker";
import { useGlobalDataStore } from "../../store/globalDataStore";
import api from "../../lib/axios";

interface InventoryTurnoverKPIsProps {
	clientData?: any[];
	className?: string;
}

type Platform = "shopify" | "amazon" | "all";

interface TurnoverData {
	value: number;
	trend: {
		value: string;
		isPositive: boolean;
		label: string;
	};
	subtitle: string;
}

const InventoryTurnoverKPIs = React.memo(function InventoryTurnoverKPIs({
	clientData,
	className = "",
}: InventoryTurnoverKPIsProps) {
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

	// Custom data states for component-specific API calls
	const [shopifyCustomData, setShopifyCustomData] = useState<any>(null);
	const [amazonCustomData, setAmazonCustomData] = useState<any>(null);
	const [allCustomData, setAllCustomData] = useState<any>(null);

	// Custom loading states
	const [shopifyCustomLoading, setShopifyCustomLoading] = useState(false);
	const [amazonCustomLoading, setAmazonCustomLoading] = useState(false);
	const [allCustomLoading, setAllCustomLoading] = useState(false);

	// Flags to indicate if custom date data should be used
	const [shopifyUseCustomDate, setShopifyUseCustomDate] = useState(false);
	const [amazonUseCustomDate, setAmazonUseCustomDate] = useState(false);
	const [allUseCustomDate, setAllUseCustomDate] = useState(false);

	// Format date for API
	const formatDateForAPI = (date: Date): string => {
		return date.toISOString().split('T')[0]; // YYYY-MM-DD format
	};

	// API fetch functions for component-specific data
	const fetchShopifyTurnoverData = useCallback(async (dateRange: DateRange) => {
		setShopifyCustomLoading(true);
		try {
			const response = await api.get('/dashboard/component-data', {
				params: {
					component_type: 'inventory_turnover',
					platform: 'shopify',
					start_date: formatDateForAPI(dateRange.start),
					end_date: formatDateForAPI(dateRange.end),
				},
			});
			setShopifyCustomData(response.data);
		} catch (error) {
			console.error('Error fetching Shopify turnover data:', error);
		} finally {
			setShopifyCustomLoading(false);
		}
	}, []);

	const fetchAmazonTurnoverData = useCallback(async (dateRange: DateRange) => {
		setAmazonCustomLoading(true);
		try {
			const response = await api.get('/dashboard/component-data', {
				params: {
					component_type: 'inventory_turnover',
					platform: 'amazon',
					start_date: formatDateForAPI(dateRange.start),
					end_date: formatDateForAPI(dateRange.end),
				},
			});
			setAmazonCustomData(response.data);
		} catch (error) {
			console.error('Error fetching Amazon turnover data:', error);
		} finally {
			setAmazonCustomLoading(false);
		}
	}, []);

	const fetchAllTurnoverData = useCallback(async (dateRange: DateRange) => {
		setAllCustomLoading(true);
		try {
			const response = await api.get('/dashboard/component-data', {
				params: {
					component_type: 'inventory_turnover',
					platform: 'combined',
					start_date: formatDateForAPI(dateRange.start),
					end_date: formatDateForAPI(dateRange.end),
				},
			});
			setAllCustomData(response.data);
		} catch (error) {
			console.error('Error fetching combined turnover data:', error);
		} finally {
			setAllCustomLoading(false);
		}
	}, []);

	// Date change handlers that trigger API calls
	const handleShopifyDateChange = useCallback((range: DateRange) => {
		setShopifyDateRange(range);
		setShopifyUseCustomDate(true);
		fetchShopifyTurnoverData(range);
	}, [fetchShopifyTurnoverData]);

	const handleAmazonDateChange = useCallback((range: DateRange) => {
		setAmazonDateRange(range);
		setAmazonUseCustomDate(true);
		fetchAmazonTurnoverData(range);
	}, [fetchAmazonTurnoverData]);

	const handleAllDateChange = useCallback((range: DateRange) => {
		setAllDateRange(range);
		setAllUseCustomDate(true);
		fetchAllTurnoverData(range);
	}, [fetchAllTurnoverData]);

	// Calculate inventory turnover data for each platform
	const calculateTurnoverData = (
		data: any,
		dateRange: DateRange,
		platform: Platform
	): TurnoverData => {
		// Handle component-specific data format (from /dashboard/component-data endpoint)
		if (data?.data && data.data.inventory_turnover_ratio !== undefined) {
			const turnoverData = data.data;
			const turnoverRate = turnoverData.inventory_turnover_ratio || 0;
			
			// Debug logging to see what data we're getting
			console.log('Turnover data received:', turnoverData);
			console.log('Turnover rate extracted:', turnoverRate);
			
			// Calculate trend from within-period comparison if available
			const comparisonData = turnoverData.turnover_comparison;
			
			// Use the growth_rate directly from the API response if available
			let trendValue = 0;
			if (comparisonData && comparisonData.growth_rate !== undefined) {
				trendValue = comparisonData.growth_rate;
			} else if (comparisonData && comparisonData.first_half_turnover_rate > 0) {
				trendValue = ((comparisonData.second_half_turnover_rate - comparisonData.first_half_turnover_rate) / comparisonData.first_half_turnover_rate) * 100;
			}
			
			console.log('Comparison data:', comparisonData);
			console.log('Trend value calculated:', trendValue);

			const isPositive = trendValue >= 0;
			const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

			// Determine health status based on turnover rate
			let subtitle = `${
				platform === "all"
					? "Combined"
					: platform.charAt(0).toUpperCase() + platform.slice(1)
			} turnover rate`;
			if (turnoverRate > 12) {
				subtitle += " • Excellent";
			} else if (turnoverRate > 6) {
				subtitle += " • Good";
			} else if (turnoverRate > 3) {
				subtitle += " • Fair";
			} else {
				subtitle += " • Needs attention";
			}

			return {
				value: turnoverRate,
				trend: {
					value: trendFormatted,
					isPositive,
					label: `trend within period`,
				},
				subtitle,
			};
		}

		// Handle default inventory analytics data format
		if (!data?.sales_kpis?.inventory_turnover_rate && data?.sales_kpis?.inventory_turnover_rate !== 0) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "No turnover data available",
			};
		}

		const turnoverRate = data.sales_kpis.inventory_turnover_rate;

		// Get trend data from multiple possible sources (handle both naming conventions)
		const trendData = data.trend_analysis?.turnover_comparison || data.turnover_comparison;
		
		// Handle different field naming conventions for turnover data
		const firstHalfTurnover = trendData?.first_half_turnover_rate || 
								 trendData?.current_period_turnover_rate || 0;
		const secondHalfTurnover = trendData?.second_half_turnover_rate || 
								  trendData?.historical_turnover_rate || 0;
		
		// Calculate trend from turnover comparison if available
		let trendValue = 0;
		let trendLabel = "vs previous period";
		
		if (firstHalfTurnover > 0) {
			// Use direct turnover comparison
			trendValue = ((secondHalfTurnover - firstHalfTurnover) / firstHalfTurnover) * 100;
			trendLabel = "trend within period";
		} else if (data.trend_analysis?.sales_comparison) {
			// Fallback: Use sales trends as approximate proxy for turnover trend
			const salesComparison = data.trend_analysis.sales_comparison;
			
			// Units sold change is a better proxy for turnover than revenue change
			// because turnover is fundamentally about inventory movement (units), not value
			if (salesComparison.units_change_percent !== undefined) {
				trendValue = salesComparison.units_change_percent;
				trendLabel = "sales velocity trend";
			} else if (salesComparison.revenue_change_percent !== undefined) {
				// Revenue change as secondary fallback (assumes stable inventory levels)
				trendValue = salesComparison.revenue_change_percent;
				trendLabel = "revenue trend (approx)";
			}
		} else if (data.kpi_charts?.inventory_turnover_rate && 
				   data.trend_analysis?.sales_comparison?.current_period_avg_revenue && 
				   data.trend_analysis?.sales_comparison?.historical_avg_revenue) {
			// Calculate a more accurate turnover trend if we have the necessary data
			const salesComparison = data.trend_analysis.sales_comparison;
			const currentTurnover = data.kpi_charts.inventory_turnover_rate;
			
			// Estimate previous turnover using revenue ratio (assuming inventory stayed relatively stable)
			const revenueRatio = salesComparison.historical_avg_revenue / salesComparison.current_period_avg_revenue;
			const estimatedPreviousTurnover = currentTurnover * revenueRatio;
			
			if (estimatedPreviousTurnover > 0) {
				trendValue = ((currentTurnover - estimatedPreviousTurnover) / estimatedPreviousTurnover) * 100;
				trendLabel = "estimated turnover trend";
			}
		}

		const isPositive = trendValue >= 0;
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		// Determine health status based on turnover rate
		let subtitle = `${
			platform === "all"
				? "Combined"
				: platform.charAt(0).toUpperCase() + platform.slice(1)
		} turnover rate`;
		if (turnoverRate > 12) {
			subtitle += " • Excellent";
		} else if (turnoverRate > 6) {
			subtitle += " • Good";
		} else if (turnoverRate > 3) {
			subtitle += " • Fair";
		} else {
			subtitle += " • Needs attention";
		}

		return {
			value: turnoverRate,
			trend: {
				value: trendFormatted,
				isPositive,
				label: trendValue !== 0 ? trendLabel : `vs ${dateRange.label.toLowerCase()}`,
			},
			subtitle,
		};
	};

	// Memoized turnover data for each platform - uses either default or custom date data
	const shopifyTurnover = useMemo(() => {
		if (shopifyUseCustomDate && shopifyCustomData) {
			return calculateTurnoverData(shopifyCustomData, shopifyDateRange, "shopify");
		}
		const shopifyData = inventoryData?.inventory_analytics?.platforms?.shopify;
		return calculateTurnoverData(shopifyData, shopifyDateRange, "shopify");
	}, [inventoryData, shopifyDateRange, shopifyUseCustomDate, shopifyCustomData]);

	const amazonTurnover = useMemo(() => {
		if (amazonUseCustomDate && amazonCustomData) {
			return calculateTurnoverData(amazonCustomData, amazonDateRange, "amazon");
		}
		const amazonData = inventoryData?.inventory_analytics?.platforms?.amazon;
		return calculateTurnoverData(amazonData, amazonDateRange, "amazon");
	}, [inventoryData, amazonDateRange, amazonUseCustomDate, amazonCustomData]);

	const allTurnover = useMemo(() => {
		if (allUseCustomDate && allCustomData) {
			return calculateTurnoverData(allCustomData, allDateRange, "all");
		}
		
		if (!inventoryData?.inventory_analytics?.platforms) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "Combined turnover data unavailable",
			};
		}

		// Use the combined platform data which already aggregates both platforms
		const combinedData = inventoryData.inventory_analytics.platforms.combined;
		return calculateTurnoverData(combinedData, allDateRange, "all");
	}, [inventoryData, allDateRange, allUseCustomDate, allCustomData]);

	// Format turnover rate with proper precision
	const formatTurnover = (value: number) => {
		// Debug logging to see what value is being formatted
		console.log('Formatting turnover value:', value, 'Type:', typeof value);
		
		// Handle very small values with better precision
		if (value < 0.01) {
			return `${value.toFixed(3)}x`;
		} else if (value < 0.1) {
			return `${value.toFixed(2)}x`;
		} else if (value < 1) {
			return `${value.toFixed(1)}x`;
		} else {
			return `${value.toFixed(1)}x`;
		}
	};

	// Individual KPI Card Component (memoized for performance)
	const TurnoverKPICard = React.memo(
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
			data: TurnoverData;
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
								{formatTurnover(data.value)}
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

	TurnoverKPICard.displayName = "TurnoverKPICard";

	return (
		<div className={`space-y-4 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">
					Inventory Turnover
				</h2>
				<p className="text-sm text-gray-600">
					How efficiently inventory is converted to sales
				</p>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Shopify Turnover KPI */}
				<TurnoverKPICard
					title="Shopify Turnover"
					data={shopifyTurnover}
					dateRange={shopifyDateRange}
					onDateRangeChange={handleShopifyDateChange}
					loading={shopifyUseCustomDate ? shopifyCustomLoading : loading}
					error={error}
					icon={<RotateCcw className="h-4 w-4" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Turnover KPI */}
				<TurnoverKPICard
					title="Amazon Turnover"
					data={amazonTurnover}
					dateRange={amazonDateRange}
					onDateRangeChange={handleAmazonDateChange}
					loading={amazonUseCustomDate ? amazonCustomLoading : loading}
					error={error}
					icon={<RefreshCw className="h-4 w-4" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Platforms Turnover KPI */}
				<TurnoverKPICard
					title="All Platforms"
					data={allTurnover}
					dateRange={allDateRange}
					onDateRangeChange={handleAllDateChange}
					loading={allUseCustomDate ? allCustomLoading : loading}
					error={error}
					icon={<RefreshCw className="h-4 w-4" style={{ color: "#8b5cf6" }} />}
					iconColor="#8b5cf6"
					iconBgColor="#f3e8ff"
				/>
			</div>
		</div>
	);
});

export default InventoryTurnoverKPIs;
