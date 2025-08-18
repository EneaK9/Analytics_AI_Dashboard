"use client";

import React, { useState, useEffect, useMemo } from "react";
import { DollarSign, TrendingUp, Store, ShoppingBag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import DateRangePicker, { DateRange, getDateRange } from "../ui/DateRangePicker";
import useInventoryData from "../../hooks/useInventoryData";

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

export default function TotalSalesKPIs({
	clientData,
	className = "",
}: TotalSalesKPIsProps) {
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

	// Memoized sales data for each platform
	const shopifySales = useMemo(
		() => calculateSalesData(shopifyData, shopifyDateRange, "shopify"),
		[shopifyData, shopifyDateRange]
	);

	const amazonSales = useMemo(
		() => calculateSalesData(amazonData, amazonDateRange, "amazon"),
		[amazonData, amazonDateRange]
	);

	const allSales = useMemo(() => {
		if (!shopifyData || !amazonData) {
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

		// Combine both platforms
		const shopifyRevenue =
			shopifyData.sales_comparison?.current_period_avg_revenue || 0;
		const amazonRevenue =
			amazonData.sales_comparison?.current_period_avg_revenue || 0;
		const combinedRevenue = shopifyRevenue + amazonRevenue;

		const shopifyHistorical =
			shopifyData.sales_comparison?.historical_avg_revenue || 0;
		const amazonHistorical =
			amazonData.sales_comparison?.historical_avg_revenue || 0;
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
	}, [shopifyData, amazonData, allDateRange]);

	// Format currency
	const formatCurrency = (value: number) => {
		return new Intl.NumberFormat("en-US", {
			style: "currency",
			currency: "USD",
			minimumFractionDigits: 0,
			maximumFractionDigits: 0,
		}).format(value);
	};

	// Individual KPI Card Component
	const SalesKPICard = ({
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
				<Card className="group hover:shadow-lg transition-all duration-300">
					<CardHeader className="pb-3">
						<div className="flex items-center justify-between">
							<CardTitle className="text-base font-semibold">{title}</CardTitle>
							<div className="w-32 h-8 bg-gray-200 rounded animate-pulse"></div>
						</div>
					</CardHeader>
					<CardContent>
						<div className="animate-pulse">
							<div className="flex items-center justify-between mb-4">
								<div className="h-12 w-12 bg-gray-200 rounded-xl"></div>
								<div className="w-16 h-6 bg-gray-200 rounded"></div>
							</div>
							<div className="space-y-2">
								<div className="h-8 bg-gray-200 rounded"></div>
								<div className="h-4 bg-gray-200 rounded w-3/4"></div>
							</div>
						</div>
					</CardContent>
				</Card>
			);
		}

		if (error) {
			return (
				<Card className="group hover:shadow-lg transition-all duration-300 border-red-200">
					<CardHeader className="pb-3">
						<div className="flex items-center justify-between">
							<CardTitle className="text-base font-semibold">{title}</CardTitle>
							<DateRangePicker
								value={dateRange}
								onChange={onDateRangeChange}
								className="w-32"
							/>
						</div>
					</CardHeader>
					<CardContent>
						<div className="flex items-center justify-center h-24 text-red-600">
							<p className="text-sm">Error loading data</p>
						</div>
					</CardContent>
				</Card>
			);
		}

		return (
			<Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="text-base font-semibold">{title}</CardTitle>
						<DateRangePicker
							value={dateRange}
							onChange={onDateRangeChange}
							className="w-32"
						/>
					</div>
				</CardHeader>
				<CardContent>
					{/* Header with Icon and Trend */}
					<div className="flex items-center justify-between mb-4">
						<div
							className="h-12 w-12 rounded-xl flex items-center justify-center shadow-sm"
							style={{ backgroundColor: iconBgColor }}>
							{icon}
						</div>

						<div
							className={`flex items-center gap-1 px-3 py-1 rounded-lg font-semibold text-sm ${
								data.trend.isPositive
									? "text-green-700 bg-green-100 border border-green-200"
									: "text-red-700 bg-red-100 border border-red-200"
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
					<div className="space-y-2">
						<h3 className="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
							{formatCurrency(data.value)}
						</h3>
						<p className="text-sm text-gray-500">{data.subtitle}</p>
					</div>

					{/* Trend Label */}
					<div className="mt-3 pt-3 border-t border-gray-100">
						<p className="text-sm text-gray-500">{data.trend.label}</p>
					</div>
				</CardContent>
			</Card>
		);
	};

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
					loading={shopifyLoading}
					error={shopifyError}
					icon={<Store className="h-6 w-6" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Sales KPI */}
				<SalesKPICard
					title="Amazon Sales"
					data={amazonSales}
					dateRange={amazonDateRange}
					onDateRangeChange={setAmazonDateRange}
					loading={amazonLoading}
					error={amazonError}
					icon={<ShoppingBag className="h-6 w-6" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Sales KPI */}
				<SalesKPICard
					title="All Platforms"
					data={allSales}
					dateRange={allDateRange}
					onDateRangeChange={setAllDateRange}
					loading={shopifyLoading || amazonLoading}
					error={shopifyError || amazonError}
					icon={<DollarSign className="h-6 w-6" style={{ color: "#3b82f6" }} />}
					iconColor="#3b82f6"
					iconBgColor="#eff6ff"
				/>
			</div>
		</div>
	);
}
