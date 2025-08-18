"use client";

import React, { useState, useEffect, useMemo } from "react";
import { BarChart3, Store, ShoppingBag, TrendingUp, Calendar, GitCompare } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import DateRangePicker, { DateRange, getDateRange } from "../ui/DateRangePicker";
import * as Charts from "../charts";
import useInventoryData from "../../hooks/useInventoryData";

interface HistoricalComparisonChartsProps {
	clientData?: any[];
	className?: string;
}

type Platform = "shopify" | "amazon" | "all";

export default function HistoricalComparisonCharts({
	clientData,
	className = "",
}: HistoricalComparisonChartsProps) {
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

	// Data hooks for each platform
	const {
		loading: shopifyLoading,
		error: shopifyError,
		trendAnalysis: shopifyData,
	} = useInventoryData({
		platform: "shopify",
		fastMode: true,
	});

	const {
		loading: amazonLoading,
		error: amazonError,
		trendAnalysis: amazonData,
	} = useInventoryData({
		platform: "amazon",
		fastMode: true,
	});

	// Process historical comparison data for a specific platform
	const processComparisonData = (data: any, dateRange: DateRange) => {
		if (!data?.sales_comparison) {
			return [];
		}

		const comparison = data.sales_comparison;
		
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
		if (!shopifyData?.sales_comparison || !amazonData?.sales_comparison) {
			return [];
		}

		// Combine data from both platforms
		const shopifyComparison = shopifyData.sales_comparison;
		const amazonComparison = amazonData.sales_comparison;

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
	}, [shopifyData, amazonData, allDateRange]);

	// Calculate comparison stats
	const calculateComparisonStats = (data: any[]) => {
		if (data.length < 2) return { change: 0, changePercent: 0, isPositive: true };
		
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
				<Card className="group hover:shadow-lg transition-all duration-300">
					<CardHeader>
						<div className="flex items-center justify-between">
							<CardTitle className="flex items-center gap-2">
								{icon}
								{title}
							</CardTitle>
							<div className="w-32 h-8 bg-gray-200 rounded animate-pulse"></div>
						</div>
					</CardHeader>
					<CardContent>
						<div className="h-64 bg-gray-200 rounded animate-pulse"></div>
					</CardContent>
				</Card>
			);
		}

		if (error) {
			return (
				<Card className="group hover:shadow-lg transition-all duration-300 border-red-200">
					<CardHeader>
						<div className="flex items-center justify-between">
							<CardTitle className="flex items-center gap-2">
								{icon}
								{title}
							</CardTitle>
							<DateRangePicker
								value={dateRange}
								onChange={onDateRangeChange}
								className="w-32"
							/>
						</div>
					</CardHeader>
					<CardContent>
						<div className="h-64 flex items-center justify-center text-red-600">
							<p className="text-sm">Error loading comparison data</p>
						</div>
					</CardContent>
				</Card>
			);
		}

		return (
			<Card className="group hover:shadow-lg transition-all duration-300">
				<CardHeader>
					<div className="flex items-center justify-between">
						<CardTitle className="flex items-center gap-2">
							{icon}
							{title}
						</CardTitle>
						<DateRangePicker
							value={dateRange}
							onChange={onDateRangeChange}
							className="w-32"
						/>
					</div>
				</CardHeader>
				<CardContent>
					{data.length > 0 ? (
						<>
							{/* Performance Indicator */}
							<div className="mb-6 p-4 bg-gray-50 rounded-lg">
								<div className="flex items-center justify-between">
									<div>
										<p className="text-sm text-gray-600">Period Comparison</p>
										<p className="text-lg font-semibold text-gray-900">
											{Math.abs(stats.change).toLocaleString('en-US', {
												style: 'currency',
												currency: 'USD',
												minimumFractionDigits: 0,
											})}
										</p>
									</div>
									<div className={`flex items-center gap-1 px-3 py-1 rounded-lg font-semibold text-sm ${
										stats.isPositive
											? "text-green-700 bg-green-100 border border-green-200"
											: "text-red-700 bg-red-100 border border-red-200"
									}`}>
										<TrendingUp
											className={`h-3 w-3 ${
												stats.isPositive ? "" : "rotate-180"
											}`}
										/>
										{stats.isPositive ? "+" : ""}{stats.changePercent.toFixed(1)}%
									</div>
								</div>
								<p className="text-xs text-gray-500 mt-1">
									{stats.isPositive ? "Increase" : "Decrease"} from previous period
								</p>
							</div>

							{/* Detailed Comparison */}
							{data.length === 2 && (
								<div className="grid grid-cols-2 gap-4 mb-6">
									<div className="text-center p-3 bg-blue-50 rounded-lg">
										<p className="text-sm text-blue-600">Previous Period</p>
										<p className="text-lg font-semibold text-blue-900">
											{data[0].value.toLocaleString('en-US', {
												style: 'currency',
												currency: 'USD',
												minimumFractionDigits: 0,
											})}
										</p>
										<p className="text-xs text-blue-600">
											{data[0].units?.toLocaleString()} units
										</p>
									</div>
									<div className="text-center p-3 bg-green-50 rounded-lg">
										<p className="text-sm text-green-600">Current Period</p>
										<p className="text-lg font-semibold text-green-900">
											{data[1].value.toLocaleString('en-US', {
												style: 'currency',
												currency: 'USD',
												minimumFractionDigits: 0,
											})}
										</p>
										<p className="text-xs text-green-600">
											{data[1].units?.toLocaleString()} units
										</p>
									</div>
								</div>
							)}

							{/* Bar Chart */}
							<Charts.BarChartOne
								data={data}
								title="Revenue Comparison"
								description={`Comparing ${dateRange.label.toLowerCase()} performance`}
								minimal={true}
							/>
						</>
					) : (
						<div className="h-64 flex items-center justify-center text-gray-500">
							<div className="text-center">
								<GitCompare className="h-8 w-8 mx-auto mb-2 text-gray-400" />
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
				<h2 className="text-xl font-semibold text-gray-900">Historical Comparison</h2>
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
					onDateRangeChange={setShopifyDateRange}
					loading={shopifyLoading}
					error={shopifyError}
					icon={<Store className="h-5 w-5" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Comparison */}
				<ComparisonChart
					title="Amazon Performance"
					data={amazonChartData}
					dateRange={amazonDateRange}
					onDateRangeChange={setAmazonDateRange}
					loading={amazonLoading}
					error={amazonError}
					icon={<ShoppingBag className="h-5 w-5" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Platforms Combined */}
				<ComparisonChart
					title="Combined Performance"
					data={allChartData}
					dateRange={allDateRange}
					onDateRangeChange={setAllDateRange}
					loading={shopifyLoading || amazonLoading}
					error={shopifyError || amazonError}
					icon={<GitCompare className="h-5 w-5" style={{ color: "#3b82f6" }} />}
					iconColor="#3b82f6"
					iconBgColor="#eff6ff"
				/>
			</div>

			{/* Data Info */}
			<div className="text-center text-sm text-gray-500">
				<Calendar className="inline h-4 w-4 mr-1" />
				Comparing selected periods with previous equivalent periods • Data updates every 5 minutes
			</div>
		</div>
	);
}
