"use client";

import React, { useState, useMemo } from "react";
import { Calendar, TrendingUp, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, {
	DateRange,
	getDateRange,
} from "../ui/CompactDatePicker";
import { useGlobalDataStore } from "../../store/globalDataStore";

interface DaysOfStockKPIsProps {
	clientData?: any[];
	className?: string;
}

type Platform = "shopify" | "amazon" | "all";

interface StockDaysData {
	value: number;
	trend: {
		value: string;
		isPositive: boolean;
		label: string;
	};
	subtitle: string;
}

const DaysOfStockKPIs = React.memo(function DaysOfStockKPIs({
	clientData,
	className = "",
}: DaysOfStockKPIsProps) {
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

	// Calculate days of stock data for each platform
	const calculateStockDaysData = (
		data: any,
		dateRange: DateRange,
		platform: Platform
	): StockDaysData => {
		if (!data?.sales_kpis?.days_stock_remaining) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "No stock data available",
			};
		}

		const stockDays = data.sales_kpis.days_stock_remaining || 0;

		// Calculate trend based on historical comparison if available
		// For demo purposes, we'll generate a reasonable trend based on typical stock patterns
		const historicalDays = stockDays * (0.9 + Math.random() * 0.2); // Simulate historical data
		const trendValue =
			historicalDays > 0
				? ((stockDays - historicalDays) / historicalDays) * 100
				: 0;

		// For stock days, lower values might be concerning (trending toward stockout)
		// Higher values might indicate overstocking
		const isPositive = stockDays > 30 ? trendValue <= 0 : trendValue >= 0; // Optimal range is around 30-60 days
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		// Determine health status based on stock days
		let subtitle = `${
			platform === "all"
				? "Combined"
				: platform.charAt(0).toUpperCase() + platform.slice(1)
		} average stock days`;
		if (stockDays > 90) {
			subtitle += " • Overstock risk";
		} else if (stockDays > 60) {
			subtitle += " • High stock";
		} else if (stockDays > 30) {
			subtitle += " • Optimal";
		} else if (stockDays > 14) {
			subtitle += " • Low stock";
		} else {
			subtitle += " • Critical";
		}

		return {
			value: stockDays,
			trend: {
				value: trendFormatted,
				isPositive,
				label: `vs ${dateRange.label.toLowerCase()}`,
			},
			subtitle,
		};
	};

	// Memoized stock days data for each platform using global state
	const shopifyStockDays = useMemo(() => {
		const shopifyData = inventoryData?.inventory_analytics?.platforms?.shopify;
		return calculateStockDaysData(shopifyData, shopifyDateRange, "shopify");
	}, [inventoryData, shopifyDateRange]);

	const amazonStockDays = useMemo(() => {
		const amazonData = inventoryData?.inventory_analytics?.platforms?.amazon;
		return calculateStockDaysData(amazonData, amazonDateRange, "amazon");
	}, [inventoryData, amazonDateRange]);

	const allStockDays = useMemo(() => {
		if (!inventoryData?.inventory_analytics?.platforms) {
			return {
				value: 0,
				trend: {
					value: "0%",
					isPositive: true,
					label: "vs previous period",
				},
				subtitle: "Combined stock data unavailable",
			};
		}

		// Use the combined platform data which already aggregates both platforms
		const combinedData = inventoryData.inventory_analytics.platforms.combined;
		return calculateStockDaysData(combinedData, allDateRange, "all");
	}, [inventoryData, allDateRange]);

	// Format stock days
	const formatStockDays = (value: number) => {
		return `${Math.round(value)} days`;
	};

	// Individual KPI Card Component (memoized for performance)
	const StockDaysKPICard = React.memo(
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
			data: StockDaysData;
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
								{formatStockDays(data.value)}
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

	StockDaysKPICard.displayName = "StockDaysKPICard";

	return (
		<div className={`space-y-4 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">
					Days of Stock Remaining
				</h2>
				<p className="text-sm text-gray-600">
					Estimated time until inventory runs out
				</p>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Shopify Stock Days KPI */}
				<StockDaysKPICard
					title="Shopify Stock"
					data={shopifyStockDays}
					dateRange={shopifyDateRange}
					onDateRangeChange={setShopifyDateRange}
					loading={loading}
					error={error}
					icon={<Calendar className="h-4 w-4" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Stock Days KPI */}
				<StockDaysKPICard
					title="Amazon Stock"
					data={amazonStockDays}
					dateRange={amazonDateRange}
					onDateRangeChange={setAmazonDateRange}
					loading={loading}
					error={error}
					icon={<Calendar className="h-4 w-4" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Platforms Stock Days KPI */}
				<StockDaysKPICard
					title="All Platforms"
					data={allStockDays}
					dateRange={allDateRange}
					onDateRangeChange={setAllDateRange}
					loading={loading}
					error={error}
					icon={<Clock className="h-4 w-4" style={{ color: "#dc2626" }} />}
					iconColor="#dc2626"
					iconBgColor="#fef2f2"
				/>
			</div>
		</div>
	);
});

export default DaysOfStockKPIs;
