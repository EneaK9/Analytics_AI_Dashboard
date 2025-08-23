"use client";

import React, { useState, useMemo, useCallback } from "react";
import {
	BarChart3,
	Store,
	ShoppingBag,
	TrendingUp,
	Calendar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, {
	DateRange,
	getDateRange,
} from "../ui/CompactDatePicker";
import SimpleBarChart from "../charts/SimpleBarChart";
import useMultiPlatformData from "../../hooks/useMultiPlatformData";
import api from "../../lib/axios";

// Helper function to format dates for API
const formatDateForAPI = (date: Date): string => {
	return date.toISOString().split('T')[0];
};

interface UnitsSoldChartsProps {
	clientData?: any[];
	className?: string;
}

type Platform = "shopify" | "amazon" | "all";

export default function UnitsSoldCharts({
	clientData,
	className = "",
}: UnitsSoldChartsProps) {
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

	// ⚡ OPTIMIZED: Single API call for ALL platforms - NO re-rendering!
	const {
		loading: multiLoading,
		error: multiError,
		shopifyData: shopifyPlatformData,
		amazonData: amazonPlatformData,
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

	// Fetch functions for custom date ranges
	const fetchShopifyUnitsData = useCallback(async (dateRange: DateRange) => {
		setShopifyCustomLoading(true);
		try {
			const params = {
				component_type: "units_sold",
				platform: "shopify",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setShopifyCustomData(response.data.data);
			console.log('✅ Shopify units sold data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch Shopify units sold data:', error);
		} finally {
			setShopifyCustomLoading(false);
		}
	}, []);

	const fetchAmazonUnitsData = useCallback(async (dateRange: DateRange) => {
		setAmazonCustomLoading(true);
		try {
			const params = {
				component_type: "units_sold",
				platform: "amazon",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setAmazonCustomData(response.data.data);
			console.log('✅ Amazon units sold data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch Amazon units sold data:', error);
		} finally {
			setAmazonCustomLoading(false);
		}
	}, []);

	const fetchAllUnitsData = useCallback(async (dateRange: DateRange) => {
		setAllCustomLoading(true);
		try {
			const params = {
				component_type: "units_sold",
				platform: "combined",
				start_date: formatDateForAPI(dateRange.start),
				end_date: formatDateForAPI(dateRange.end)
			};
			
			const response = await api.get('/dashboard/component-data', { params });
			setAllCustomData(response.data.data);
			console.log('✅ Combined units sold data fetched for date range');
		} catch (error) {
			console.error('❌ Failed to fetch combined units sold data:', error);
		} finally {
			setAllCustomLoading(false);
		}
	}, []);

	// Handle date range changes
	const handleShopifyDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ Shopify units sold date changed to:', newDateRange.label);
		setShopifyDateRange(newDateRange);
		setShopifyUseCustomDate(true);
		await fetchShopifyUnitsData(newDateRange);
	}, [fetchShopifyUnitsData]);

	const handleAmazonDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ Amazon units sold date changed to:', newDateRange.label);
		setAmazonDateRange(newDateRange);
		setAmazonUseCustomDate(true);
		await fetchAmazonUnitsData(newDateRange);
	}, [fetchAmazonUnitsData]);

	const handleAllDateChange = useCallback(async (newDateRange: DateRange) => {
		console.log('🗓️ All platforms units sold date changed to:', newDateRange.label);
		setAllDateRange(newDateRange);
		setAllUseCustomDate(true);
		await fetchAllUnitsData(newDateRange);
	}, [fetchAllUnitsData]);

	// Extract trend analysis from platform data - MEMOIZED
	const shopifyData = useMemo(
		() => shopifyUseCustomDate ? shopifyCustomData : shopifyPlatformData?.trend_analysis,
		[shopifyPlatformData, shopifyCustomData, shopifyUseCustomDate]
	);
	const amazonData = useMemo(
		() => amazonUseCustomDate ? amazonCustomData : amazonPlatformData?.trend_analysis,
		[amazonPlatformData, amazonCustomData, amazonUseCustomDate]
	);

	// Derived loading/error states
	const shopifyLoading = shopifyUseCustomDate ? shopifyCustomLoading : multiLoading;
	const amazonLoading = amazonUseCustomDate ? amazonCustomLoading : multiLoading;
	const allLoading = allUseCustomDate ? allCustomLoading : (multiLoading || shopifyLoading || amazonLoading);
	const shopifyError = multiError;
	const amazonError = multiError;

	// Process units sold data for a specific platform and date range
	const processUnitsSoldData = (data: any, dateRange: DateRange) => {
		if (!data?.units_sold_chart) return [];

		// Normalize dates to compare only date parts (ignore time components)
		const startDateStr = dateRange.start.toISOString().split('T')[0];
		const endDateStr = dateRange.end.toISOString().split('T')[0];

		return data.units_sold_chart
			.filter((item: { date: string; units_sold: number }) => {
				const itemDateStr = item.date.split('T')[0]; // Handle both "2025-08-16" and "2025-08-16T00:00:00Z" formats
				return itemDateStr >= startDateStr && itemDateStr <= endDateStr;
			})
			.map((item: { date: string; units_sold: number }) => ({
				date: new Date(item.date).toLocaleDateString("en-US", {
					month: "short",
					day: "numeric",
				}),
				units: item.units_sold,
				value: item.units_sold,
			}))
			.sort(
				(a: any, b: any) =>
					new Date(a.date).getTime() - new Date(b.date).getTime()
			);
	};

	// Memoized chart data for each platform
	const shopifyChartData = useMemo(() => {
		return processUnitsSoldData(shopifyData, shopifyDateRange);
	}, [shopifyData, shopifyDateRange]);

	const amazonChartData = useMemo(() => {
		return processUnitsSoldData(amazonData, amazonDateRange);
	}, [amazonData, amazonDateRange]);

	const allChartData = useMemo(() => {
		// If using custom combined data (when "All" chart's own date was changed), use it directly
		if (allUseCustomDate && allCustomData?.units_sold_chart) {
			return allCustomData.units_sold_chart.map((item: { date: string; units_sold: number }) => ({
				date: new Date(item.date).toLocaleDateString("en-US", {
					month: "short",
					day: "numeric",
				}),
				units: item.units_sold,
				value: item.units_sold,
			}));
		}

		// Use only the "All" chart's own date range - no automatic syncing with individual platforms
		const effectiveDateRange = allDateRange;

		// Get raw data for both platforms from base platform data (not custom filtered data)
		const shopifyRawData = shopifyPlatformData?.trend_analysis?.units_sold_chart || [];
		const amazonRawData = amazonPlatformData?.trend_analysis?.units_sold_chart || [];

		// Apply the same date filtering logic to both platforms using the effective date range
		const startDateStr = effectiveDateRange.start.toISOString().split('T')[0];
		const endDateStr = effectiveDateRange.end.toISOString().split('T')[0];

		// Filter and format Shopify data
		const filteredShopifyData = shopifyRawData
			.filter((item: { date: string; units_sold: number }) => {
				const itemDateStr = item.date.split('T')[0]; // Handle both "2025-08-16" and "2025-08-16T00:00:00Z" formats
				return itemDateStr >= startDateStr && itemDateStr <= endDateStr;
			})
			.map((item: { date: string; units_sold: number }) => ({
				date: new Date(item.date).toLocaleDateString("en-US", {
					month: "short",
					day: "numeric",
				}),
				units: item.units_sold,
			}));

		// Filter and format Amazon data  
		const filteredAmazonData = amazonRawData
			.filter((item: { date: string; units_sold: number }) => {
				const itemDateStr = item.date.split('T')[0]; // Handle both "2025-08-16" and "2025-08-16T00:00:00Z" formats
				return itemDateStr >= startDateStr && itemDateStr <= endDateStr;
			})
			.map((item: { date: string; units_sold: number }) => ({
				date: new Date(item.date).toLocaleDateString("en-US", {
					month: "short",
					day: "numeric",
				}),
				units: item.units_sold,
			}));

		// Combine the filtered data
		const combinedMap = new Map();

		// Add shopify data
		filteredShopifyData.forEach((item: { date: string; units: number }) => {
			const currentUnits = combinedMap.get(item.date) || 0;
			combinedMap.set(item.date, currentUnits + item.units);
		});

		// Add amazon data
		filteredAmazonData.forEach((item: { date: string; units: number }) => {
			const currentUnits = combinedMap.get(item.date) || 0;
			combinedMap.set(item.date, currentUnits + item.units);
		});

		const result = Array.from(combinedMap.entries())
			.map(([date, units]) => ({
				date,
				units,
				value: units,
			}))
			.sort(
				(a: any, b: any) =>
					new Date(a.date + ", 2024").getTime() - new Date(b.date + ", 2024").getTime()
			);

		return result;
	}, [allUseCustomDate, allCustomData, shopifyPlatformData, amazonPlatformData, allDateRange]);

	// Calculate summary stats for each chart
	const calculateStats = (data: any[]) => {
		if (!data.length) return { total: 0, average: 0, peak: 0 };

		const total = data.reduce(
			(sum, item) => sum + (item.units || item.value),
			0
		);
		const average = total / data.length;
		const peak = Math.max(...data.map((item) => item.units || item.value));

		return { total, average, peak };
	};

	// Individual Chart Component
	const UnitsSoldChart = ({
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
		const stats = calculateStats(data);

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
							<p className="text-sm">Error loading units sold data</p>
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
							{/* Quick Stats */}
							<div className="grid grid-cols-3 gap-2 mb-4 p-3 bg-gray-200 rounded-lg">
								<div className="text-center">
									<p className="text-xs text-gray-600">Total Units</p>
									<p className="text-sm font-semibold text-gray-900">
										{stats.total.toLocaleString()}
									</p>
								</div>
								<div className="text-center">
									<p className="text-xs text-gray-600">Daily Avg</p>
									<p className="text-sm font-semibold text-gray-900">
										{Math.round(stats.average).toLocaleString()}
									</p>
								</div>
								<div className="text-center">
									<p className="text-xs text-gray-600">Peak Day</p>
									<p className="text-sm font-semibold text-gray-900">
										{stats.peak.toLocaleString()}
									</p>
								</div>
							</div>

							{/* Bar Chart */}
							<SimpleBarChart data={data} color={iconColor} height={160} />
						</>
					) : (
						<div className="h-48 flex items-center justify-center text-gray-500">
							<div className="text-center">
								<BarChart3 className="h-4 w-4 mx-auto mb-2 text-gray-400" />
								<p className="text-sm">No sales data available</p>
								<p className="text-xs text-gray-400">
									Try selecting a different date range
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
				<h2 className="text-xl font-semibold text-gray-900">Units Sold</h2>
				<p className="text-sm text-gray-600">
					Daily sales volume across all platforms
				</p>
			</div>

			<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
				{/* Shopify Units Sold */}
				<UnitsSoldChart
					title="Shopify Units Sold"
					data={shopifyChartData}
					dateRange={shopifyDateRange}
					onDateRangeChange={handleShopifyDateChange}
					loading={shopifyLoading}
					error={shopifyError}
					icon={<Store className="h-4 w-4" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Units Sold */}
				<UnitsSoldChart
					title="Amazon Units Sold"
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
				<UnitsSoldChart
					title="All Platforms Combined"
					data={allChartData}
					dateRange={allDateRange}
					onDateRangeChange={handleAllDateChange}
					loading={allLoading}
					error={shopifyError || amazonError}
					icon={<BarChart3 className="h-4 w-4" style={{ color: "#3b82f6" }} />}
					iconColor="#3b82f6"
					iconBgColor="#eff6ff"
				/>
			</div>


		</div>
	);
}
