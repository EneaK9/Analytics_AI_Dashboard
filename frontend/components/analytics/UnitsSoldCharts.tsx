"use client";

import React, { useState, useMemo } from "react";
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

	// Extract trend analysis from platform data - MEMOIZED
	const shopifyData = useMemo(
		() => shopifyPlatformData?.trend_analysis || null,
		[shopifyPlatformData]
	);
	const amazonData = useMemo(
		() => amazonPlatformData?.trend_analysis || null,
		[amazonPlatformData]
	);

	// Derived loading/error states
	const shopifyLoading = multiLoading;
	const amazonLoading = multiLoading;
	const shopifyError = multiError;
	const amazonError = multiError;

	// Process units sold data for a specific platform and date range
	const processUnitsSoldData = (data: any, days: number) => {
		if (!data?.units_sold_chart) return [];

		const now = new Date();
		const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

		return data.units_sold_chart
			.filter((item: { date: string; units_sold: number }) => {
				const itemDate = new Date(item.date);
				return itemDate >= startDate && itemDate <= now;
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
		const days = Math.floor(
			(shopifyDateRange.end.getTime() - shopifyDateRange.start.getTime()) /
				(1000 * 60 * 60 * 24)
		);
		return processUnitsSoldData(shopifyData, days);
	}, [shopifyData, shopifyDateRange]);

	const amazonChartData = useMemo(() => {
		const days = Math.floor(
			(amazonDateRange.end.getTime() - amazonDateRange.start.getTime()) /
				(1000 * 60 * 60 * 24)
		);
		return processUnitsSoldData(amazonData, days);
	}, [amazonData, amazonDateRange]);

	const allChartData = useMemo(() => {
		if (!shopifyData?.units_sold_chart || !amazonData?.units_sold_chart) {
			return [];
		}

		const days = Math.floor(
			(allDateRange.end.getTime() - allDateRange.start.getTime()) /
				(1000 * 60 * 60 * 24)
		);

		// Combine data from both platforms
		const now = new Date();
		const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

		const shopifyFiltered = shopifyData.units_sold_chart.filter(
			(item: { date: string }) => {
				const itemDate = new Date(item.date);
				return itemDate >= startDate && itemDate <= now;
			}
		);

		const amazonFiltered = amazonData.units_sold_chart.filter(
			(item: { date: string }) => {
				const itemDate = new Date(item.date);
				return itemDate >= startDate && itemDate <= now;
			}
		);

		// Create a map to combine data by date
		const combinedMap = new Map();

		shopifyFiltered.forEach((item: { date: string; units_sold: number }) => {
			const date = new Date(item.date).toLocaleDateString("en-US", {
				month: "short",
				day: "numeric",
			});
			combinedMap.set(date, (combinedMap.get(date) || 0) + item.units_sold);
		});

		amazonFiltered.forEach((item: { date: string; units_sold: number }) => {
			const date = new Date(item.date).toLocaleDateString("en-US", {
				month: "short",
				day: "numeric",
			});
			combinedMap.set(date, (combinedMap.get(date) || 0) + item.units_sold);
		});

		return Array.from(combinedMap.entries())
			.map(([date, units]) => ({
				date,
				units,
				value: units,
			}))
			.sort(
				(a: any, b: any) =>
					new Date(a.date).getTime() - new Date(b.date).getTime()
			);
	}, [shopifyData, amazonData, allDateRange]);

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
					onDateRangeChange={setShopifyDateRange}
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
					onDateRangeChange={setAmazonDateRange}
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
					onDateRangeChange={setAllDateRange}
					loading={shopifyLoading || amazonLoading}
					error={shopifyError || amazonError}
					icon={<BarChart3 className="h-4 w-4" style={{ color: "#3b82f6" }} />}
					iconColor="#3b82f6"
					iconBgColor="#eff6ff"
				/>
			</div>

			{/* Data Info */}
			<div className="text-center text-sm text-gray-500">
				<Calendar className="inline h-4 w-4 mr-1" />
				Showing units sold for selected date ranges • Data updates every 5
				minutes
			</div>
		</div>
	);
}
