"use client";

import React, { useState, useMemo } from "react";
import { RefreshCw, TrendingUp, Store, ShoppingBag, RotateCcw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import CompactDatePicker, { DateRange, getDateRange } from "../ui/CompactDatePicker";
import { useInventoryData, useFilters } from "../../store/globalDataStore";

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

	// Calculate inventory turnover data for each platform
	const calculateTurnoverData = (
		data: any,
		dateRange: DateRange,
		platform: Platform
	): TurnoverData => {
		if (!data || !data.inventory_turnover_rate) {
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

		const turnoverRate = data.inventory_turnover_rate || 0;
		
		// Calculate trend based on historical comparison if available
		// For demo purposes, we'll generate a reasonable trend based on the turnover rate
		const historicalRate = turnoverRate * (0.85 + Math.random() * 0.3); // Simulate historical data
		const trendValue = historicalRate > 0 
			? ((turnoverRate - historicalRate) / historicalRate) * 100 
			: 0;

		const isPositive = trendValue >= 0;
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		// Determine health status based on turnover rate
		let subtitle = `${platform === "all" ? "Combined" : platform.charAt(0).toUpperCase() + platform.slice(1)} turnover rate`;
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
				label: `vs ${dateRange.label.toLowerCase()}`,
			},
			subtitle,
		};
	};

	// Memoized turnover data for each platform using global state
	const shopifyTurnover = useMemo(() => {
		const shopifyData = inventoryData?.shopify_data || inventoryData?.trendAnalysis;
		return calculateTurnoverData(shopifyData, shopifyDateRange, "shopify");
	}, [inventoryData, shopifyDateRange]);

	const amazonTurnover = useMemo(() => {
		const amazonData = inventoryData?.amazon_data || inventoryData?.trendAnalysis;
		return calculateTurnoverData(amazonData, amazonDateRange, "amazon");
	}, [inventoryData, amazonDateRange]);

	const allTurnover = useMemo(() => {
		if (!inventoryData) {
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

		// Calculate weighted average based on inventory values from global data
		const shopifyData = inventoryData.shopify_data || inventoryData;
		const amazonData = inventoryData.amazon_data || inventoryData;
		const shopifyRate = shopifyData?.inventory_turnover_rate || 0;
		const amazonRate = amazonData?.inventory_turnover_rate || 0;
		
		// For simplicity, we'll average the rates (in a real app, this would be weighted by inventory value)
		const combinedRate = (shopifyRate + amazonRate) / 2;

		// Simulate trend calculation
		const historicalRate = combinedRate * (0.85 + Math.random() * 0.3);
		const trendValue = historicalRate > 0 
			? ((combinedRate - historicalRate) / historicalRate) * 100 
			: 0;

		const isPositive = trendValue >= 0;
		const trendFormatted = `${Math.abs(trendValue).toFixed(1)}%`;

		let subtitle = "Combined platform turnover rate";
		if (combinedRate > 12) {
			subtitle += " • Excellent";
		} else if (combinedRate > 6) {
			subtitle += " • Good";
		} else if (combinedRate > 3) {
			subtitle += " • Fair";
		} else {
			subtitle += " • Needs attention";
		}

		return {
			value: combinedRate,
			trend: {
				value: trendFormatted,
				isPositive,
				label: `vs ${allDateRange.label.toLowerCase()}`,
			},
			subtitle,
		};
	}, [inventoryData, allDateRange]);

	// Format turnover rate
	const formatTurnover = (value: number) => {
		return `${value.toFixed(1)}x`;
	};

	// Individual KPI Card Component (memoized for performance)
	const TurnoverKPICard = React.memo(({
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
	});

	return (
		<div className={`space-y-4 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">Inventory Turnover</h2>
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
					onDateRangeChange={setShopifyDateRange}
					loading={loading}
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
					onDateRangeChange={setAmazonDateRange}
					loading={loading}
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
					onDateRangeChange={setAllDateRange}
					loading={loading}
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
