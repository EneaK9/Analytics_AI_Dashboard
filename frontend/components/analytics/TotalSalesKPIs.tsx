"use client";

import React, { useState, useMemo } from "react";
import { DollarSign, TrendingUp, Store, ShoppingBag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, { DateRange, getDateRange } from "../ui/CompactDatePicker";
import { useInventoryData, useFilters } from "../../store/globalDataStore";

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
	// Use global state for data - no manual fetching needed
	const { data: inventoryData, loading, error } = useInventoryData();
	// Remove filters for now to prevent any potential issues
	// const { filters, setFilters } = useFilters();

	// No manual fetching - GlobalDataProvider handles this

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

	// Calculate sales data for each platform
	const calculateSalesData = (
		data: any,
		dateRange: DateRange,
		platform: Platform
	): SalesData => {
		if (!data || !data.sales_comparison) {
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

		const salesComparison = data.sales_comparison;
		const currentRevenue = salesComparison.current_period_avg_revenue || 0;
		const historicalRevenue = salesComparison.historical_avg_revenue || 0;

		// Calculate trend percentage
		const trendValue =
			historicalRevenue > 0
				? ((currentRevenue - historicalRevenue) / historicalRevenue) * 100
				: 0;

		const isPositive = trendValue >= 0;
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		return {
			value: currentRevenue,
			trend: {
				value: trendFormatted,
				isPositive,
				label: `vs ${dateRange.label.toLowerCase()}`,
			},
			subtitle: `${platform === "all" ? "Combined" : platform.charAt(0).toUpperCase() + platform.slice(1)} total sales`,
		};
	};

	// Memoized sales data for each platform using global state
	const shopifySales = useMemo(() => {
		// Extract Shopify data from global inventory data
		const shopifyData = inventoryData?.shopify_data || inventoryData?.trendAnalysis;
		return calculateSalesData(shopifyData, shopifyDateRange, "shopify");
	}, [inventoryData, shopifyDateRange]);

	const amazonSales = useMemo(() => {
		// Extract Amazon data from global inventory data
		const amazonData = inventoryData?.amazon_data || inventoryData?.trendAnalysis;
		return calculateSalesData(amazonData, amazonDateRange, "amazon");
	}, [inventoryData, amazonDateRange]);

	const allSales = useMemo(() => {
		if (!inventoryData) {
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

		// Combine both platforms from global data
		const shopifyData = inventoryData.shopify_data || inventoryData;
		const amazonData = inventoryData.amazon_data || inventoryData;

		const shopifyRevenue =
			shopifyData?.sales_comparison?.current_period_avg_revenue || 0;
		const amazonRevenue =
			amazonData?.sales_comparison?.current_period_avg_revenue || 0;
		const combinedRevenue = shopifyRevenue + amazonRevenue;

		const shopifyHistorical =
			shopifyData?.sales_comparison?.historical_avg_revenue || 0;
		const amazonHistorical =
			amazonData?.sales_comparison?.historical_avg_revenue || 0;
		const combinedHistorical = shopifyHistorical + amazonHistorical;

		const trendValue =
			combinedHistorical > 0
				? ((combinedRevenue - combinedHistorical) / combinedHistorical) * 100
				: 0;

		const isPositive = trendValue >= 0;
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		return {
			value: combinedRevenue,
			trend: {
				value: trendFormatted,
				isPositive,
				label: `vs ${allDateRange.label.toLowerCase()}`,
			},
			subtitle: "Combined Shopify + Amazon sales",
		};
	}, [inventoryData, allDateRange]);

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
	const SalesKPICard = React.memo(({
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
							<CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
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
							<CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
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
						<CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
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
	});

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
					onDateRangeChange={setShopifyDateRange}
					loading={loading}
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
					onDateRangeChange={setAmazonDateRange}
					loading={loading}
					error={error}
					icon={<ShoppingBag className="h-4 w-4" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Sales KPI */}
				<SalesKPICard
					title="All Platforms"
					data={allSales}
					dateRange={allDateRange}
					onDateRangeChange={setAllDateRange}
					loading={loading}
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
