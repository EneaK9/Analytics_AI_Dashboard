"use client";

import React, { useState, useMemo, memo, useCallback } from "react";
import {
	Store,
	ShoppingBag,
	TrendingUp,
	Calendar,
	GitCompare,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, {
	DateRange,
	getDateRange,
} from "../ui/CompactDatePicker";
import SimpleBarChart from "../charts/SimpleBarChart";
import useMultiPlatformData from "../../hooks/useMultiPlatformData";
import api from "../../lib/axios";

interface HistoricalComparisonChartsProps {
	clientData?: any[];
	className?: string;
}

// Memoize initial date ranges to prevent re-renders
const INITIAL_DATE_RANGE_HIST = getDateRange("month");

const HistoricalComparisonCharts = memo(function HistoricalComparisonCharts({
	clientData,
	className = "",
}: HistoricalComparisonChartsProps) {
	// Date range states for each platform - use memoized initial value
	const [shopifyDateRange, setShopifyDateRange] = useState<DateRange>(
		INITIAL_DATE_RANGE_HIST
	);
	const [amazonDateRange, setAmazonDateRange] = useState<DateRange>(
		INITIAL_DATE_RANGE_HIST
	);
	const [allDateRange, setAllDateRange] = useState<DateRange>(
		INITIAL_DATE_RANGE_HIST
	);

	// ⚡ OPTIMIZED: Single API call for ALL platforms - NO re-rendering!
	const {
		loading: multiLoading,
		error: multiError,
		shopifyData: shopifyPlatformData,
		amazonData: amazonPlatformData,
		combinedData: combinedPlatformData,
	} = useMultiPlatformData({
		fastMode: true,
	});

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

	// Extract trend analysis from platform data - MEMOIZED
	const shopifyData = useMemo(
		() => shopifyUseCustomDate ? shopifyCustomData?.shopify : shopifyPlatformData?.trend_analysis,
		[shopifyPlatformData, shopifyCustomData, shopifyUseCustomDate]
	);
	const amazonData = useMemo(
		() => amazonUseCustomDate ? amazonCustomData?.amazon : amazonPlatformData?.trend_analysis,
		[amazonPlatformData, amazonCustomData, amazonUseCustomDate]
	);

	// Format date for API
	const formatDateForAPI = (date: Date): string => {
		return date.toISOString().split('T')[0]; // YYYY-MM-DD format
	};

	// Fetch functions for date-filtered data
	const fetchShopifyHistoricalData = useCallback(async (dateRange: DateRange) => {
		setShopifyCustomLoading(true);
		try {
			const params = {
				component_type: "historical_comparison",
				platform: "shopify",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setShopifyCustomData(response.data.data);
			console.log('✅ Shopify historical data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch Shopify historical data:', error);
		} finally {
			setShopifyCustomLoading(false);
		}
	}, []);

	const fetchAmazonHistoricalData = useCallback(async (dateRange: DateRange) => {
		setAmazonCustomLoading(true);
		try {
			const params = {
				component_type: "historical_comparison",
				platform: "amazon",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setAmazonCustomData(response.data.data);
			console.log('✅ Amazon historical data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch Amazon historical data:', error);
		} finally {
			setAmazonCustomLoading(false);
		}
	}, []);

	const fetchAllHistoricalData = useCallback(async (dateRange: DateRange) => {
		setAllCustomLoading(true);
		try {
			const params = {
				component_type: "historical_comparison",
				platform: "combined",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setAllCustomData(response.data.data);
			console.log('✅ Combined historical data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch combined historical data:', error);
		} finally {
			setAllCustomLoading(false);
		}
	}, []);

	// Handle date range changes
	const handleShopifyDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ Shopify historical date changed to:', newDateRange.label);
		setShopifyDateRange(newDateRange);
		setShopifyUseCustomDate(true);
		await fetchShopifyHistoricalData(newDateRange);
	}, [fetchShopifyHistoricalData]);

	const handleAmazonDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ Amazon historical date changed to:', newDateRange.label);
		setAmazonDateRange(newDateRange);
		setAmazonUseCustomDate(true);
		await fetchAmazonHistoricalData(newDateRange);
	}, [fetchAmazonHistoricalData]);

	const handleAllDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ All platforms historical date changed to:', newDateRange.label);
		setAllDateRange(newDateRange);
		setAllUseCustomDate(true);
		await fetchAllHistoricalData(newDateRange);
	}, [fetchAllHistoricalData]);

	// Derived loading/error states
	const shopifyLoading = shopifyUseCustomDate ? shopifyCustomLoading : multiLoading;
	const amazonLoading = amazonUseCustomDate ? amazonCustomLoading : multiLoading;
	const allLoading = allUseCustomDate ? allCustomLoading : multiLoading;
	const shopifyError = multiError;
	const amazonError = multiError;

	// Process historical comparison data for a specific platform
	const processComparisonData = (data: any, dateRange: DateRange) => {
		// Handle new API response format with totals at root level
		if (data?.total_current_period !== undefined && data?.total_previous_period !== undefined) {
			return [
				{
					name: "Previous Period",
					value: data.total_previous_period || 0,
					revenue: data.total_previous_period || 0,
					units: 0, // Units data not available in this format
					period: `Previous ${dateRange.label.toLowerCase()}`,
				},
				{
					name: "Current Period",
					value: data.total_current_period || 0,
					revenue: data.total_current_period || 0,
					units: 0, // Units data not available in this format
					period: `Current ${dateRange.label.toLowerCase()}`,
				},
			];
		}

		// Fallback to old format for backward compatibility
		if (!data?.sales_comparison) {
			return [];
		}

		const comparison = data.sales_comparison as any;

		return [
			{
				name: "Previous Period",
				value: comparison.historical_avg_revenue || 0,
				revenue: comparison.historical_avg_revenue || 0,
				units: comparison.historical_avg_units || 0,
				period: `Previous ${dateRange.label.toLowerCase()}`,
			},
			{
				name: "Current Period",
				value: comparison.current_period_avg_revenue || 0,
				revenue: comparison.current_period_avg_revenue || 0,
				units: comparison.current_period_avg_units || 0,
				period: `Current ${dateRange.label.toLowerCase()}`,
			},
		];
	};

	// Memoized chart data for each platform
	const shopifyChartData = useMemo(() => {
		return processComparisonData(shopifyData, shopifyDateRange);
	}, [shopifyData, shopifyDateRange]);

	const amazonChartData = useMemo(() => {
		return processComparisonData(amazonData, amazonDateRange);
	}, [amazonData, amazonDateRange]);

	const allChartData = useMemo(() => {
		// If using custom date filtering, use the combined data directly
		if (allUseCustomDate && allCustomData?.combined) {
			return processComparisonData(allCustomData.combined, allDateRange);
		}

		// Handle new API response format
		if (shopifyData?.total_current_period !== undefined && amazonData?.total_current_period !== undefined) {
			const combinedHistoricalRevenue =
				(shopifyData.total_previous_period || 0) +
				(amazonData.total_previous_period || 0);

			const combinedCurrentRevenue =
				(shopifyData.total_current_period || 0) +
				(amazonData.total_current_period || 0);

			return [
				{
					name: "Previous Period",
					value: combinedHistoricalRevenue,
					revenue: combinedHistoricalRevenue,
					units: 0, // Units data not available in this format
					period: `Previous ${allDateRange.label.toLowerCase()}`,
				},
				{
					name: "Current Period",
					value: combinedCurrentRevenue,
					revenue: combinedCurrentRevenue,
					units: 0, // Units data not available in this format
					period: `Current ${allDateRange.label.toLowerCase()}`,
				},
			];
		}

		// Fallback to combining individual platform data (old format)
		if (!shopifyData?.sales_comparison || !amazonData?.sales_comparison) {
			return [];
		}

		// Combine data from both platforms
		const shopifyComparison = shopifyData.sales_comparison as any;
		const amazonComparison = amazonData.sales_comparison as any;

		const combinedHistoricalRevenue =
			(shopifyComparison.historical_avg_revenue || 0) +
			(amazonComparison.historical_avg_revenue || 0);

		const combinedCurrentRevenue =
			(shopifyComparison.current_period_avg_revenue || 0) +
			(amazonComparison.current_period_avg_revenue || 0);

		const combinedHistoricalUnits =
			(shopifyComparison.historical_avg_units || 0) +
			(amazonComparison.historical_avg_units || 0);

		const combinedCurrentUnits =
			(shopifyComparison.current_period_avg_units || 0) +
			(amazonComparison.current_period_avg_units || 0);

		return [
			{
				name: "Previous Period",
				value: combinedHistoricalRevenue,
				revenue: combinedHistoricalRevenue,
				units: combinedHistoricalUnits,
				period: `Previous ${allDateRange.label.toLowerCase()}`,
			},
			{
				name: "Current Period",
				value: combinedCurrentRevenue,
				revenue: combinedCurrentRevenue,
				units: combinedCurrentUnits,
				period: `Current ${allDateRange.label.toLowerCase()}`,
			},
		];
	}, [shopifyData, amazonData, allDateRange, allUseCustomDate, allCustomData]);

	// Calculate comparison stats
	const calculateComparisonStats = (data: any[]) => {
		if (data.length < 2)
			return { change: 0, changePercent: 0, isPositive: true };

		const previous = data[0].value;
		const current = data[1].value;
		const change = current - previous;
		const changePercent = previous > 0 ? (change / previous) * 100 : 0;

		return {
			change,
			changePercent,
			isPositive: change >= 0,
		};
	};

	// Individual Chart Component
	const ComparisonChart = ({
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
		data: any[];
		dateRange: DateRange;
		onDateRangeChange: (range: DateRange) => void;
		loading: boolean;
		error: string | null;
		icon: React.ReactNode;
		iconColor: string;
		iconBgColor: string;
	}) => {
		const stats = calculateComparisonStats(data);

		if (loading) {
			return (
				<Card className="bg-gray-100 border-gray-300 hover:shadow-md transition-all duration-300">
					<CardHeader className="pb-3">
						<div className="flex items-center justify-between">
							<CardTitle className="flex items-center gap-2 text-sm font-medium text-gray-600">
								{icon}
								{title}
							</CardTitle>
							<div className="w-24 h-6 bg-gray-200 rounded animate-pulse"></div>
						</div>
					</CardHeader>
					<CardContent>
						<div className="h-48 bg-gray-200 rounded animate-pulse"></div>
					</CardContent>
				</Card>
			);
		}

		if (error) {
			return (
				<Card className="bg-gray-100 border-red-200 hover:shadow-md transition-all duration-300">
					<CardHeader className="pb-3">
						<div className="flex items-center justify-between">
							<CardTitle className="flex items-center gap-2 text-sm font-medium text-gray-600">
								{icon}
								{title}
							</CardTitle>
							<CompactDatePicker
								value={dateRange}
								onChange={onDateRangeChange}
							/>
						</div>
					</CardHeader>
					<CardContent>
						<div className="h-48 flex items-center justify-center text-red-600">
							<p className="text-sm">Error loading comparison data</p>
						</div>
					</CardContent>
				</Card>
			);
		}

		return (
			<Card className="bg-gray-100 border-gray-300 hover:shadow-md hover:bg-gray-200 transition-all duration-300">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="flex items-center gap-2 text-sm font-medium text-gray-600">
							{icon}
							{title}
						</CardTitle>
						<CompactDatePicker value={dateRange} onChange={onDateRangeChange} />
					</div>
				</CardHeader>
				<CardContent>
					{data.length > 0 ? (
						<>
							{/* Performance Indicator */}
							<div className="mb-4 p-3 bg-gray-200 rounded-lg">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-xs text-gray-600">Period Comparison</p>
										<p className="text-sm font-semibold text-gray-900">
											{Math.abs(stats.change).toLocaleString("en-US", {
												style: "currency",
												currency: "USD",
												minimumFractionDigits: 0,
											})}
										</p>
									</div>
									<div
										className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${
											stats.isPositive
												? "text-green-700 bg-green-100"
												: "text-red-700 bg-red-100"
										}`}>
										<TrendingUp
											className={`h-3 w-3 ${
												stats.isPositive ? "" : "rotate-180"
											}`}
										/>
										{stats.isPositive ? "+" : ""}
										{(stats.changePercent || 0).toFixed(1)}%
									</div>
								</div>
								<p className="text-xs text-gray-500 mt-1">
									{stats.isPositive ? "Increase" : "Decrease"} from previous
									period
								</p>
							</div>

							{/* Bar Chart */}
							<SimpleBarChart data={data} color={iconColor} height={140} />
						</>
					) : (
						<div className="h-48 flex items-center justify-center text-gray-500">
							<div className="text-center">
								<GitCompare className="h-4 w-4 mx-auto mb-2 text-gray-400" />
								<p className="text-sm">No comparison data available</p>
								<p className="text-xs text-gray-400">
									Need data from multiple periods for comparison
								</p>
							</div>
						</div>
					)}
				</CardContent>
			</Card>
		);
	};

	return (
		<div className={`space-y-6 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">
					Historical Comparison
				</h2>
				<p className="text-sm text-gray-600">
					Current vs previous period performance analysis
				</p>
			</div>

			<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
				{/* Shopify Comparison */}
				<ComparisonChart
					title="Shopify Performance"
					data={shopifyChartData}
					dateRange={shopifyDateRange}
					onDateRangeChange={handleShopifyDateChange}
					loading={shopifyLoading}
					error={shopifyError}
					icon={<Store className="h-4 w-4" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Comparison */}
				<ComparisonChart
					title="Amazon Performance"
					data={amazonChartData}
					dateRange={amazonDateRange}
					onDateRangeChange={handleAmazonDateChange}
					loading={amazonLoading}
					error={amazonError}
					icon={
						<ShoppingBag className="h-4 w-4" style={{ color: "#f59e0b" }} />
					}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Platforms Combined */}
				<ComparisonChart
					title="Combined Performance"
					data={allChartData}
					dateRange={allDateRange}
					onDateRangeChange={handleAllDateChange}
					loading={allLoading}
					error={shopifyError || amazonError}
					icon={<GitCompare className="h-4 w-4" style={{ color: "#3b82f6" }} />}
					iconColor="#3b82f6"
					iconBgColor="#eff6ff"
				/>
			</div>

			
		</div>
	);
});

export default HistoricalComparisonCharts;
