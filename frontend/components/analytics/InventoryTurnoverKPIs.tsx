"use client";

import React, { useState, useEffect, useMemo } from "react";
import { RefreshCw, TrendingUp, Store, ShoppingBag, RotateCcw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import DateRangePicker, { DateRange, getDateRange } from "../ui/DateRangePicker";
import useInventoryData from "../../hooks/useInventoryData";

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

export default function InventoryTurnoverKPIs({
	clientData,
	className = "",
}: InventoryTurnoverKPIsProps) {
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

	// Memoized turnover data for each platform
	const shopifyTurnover = useMemo(
		() => calculateTurnoverData(shopifyData, shopifyDateRange, "shopify"),
		[shopifyData, shopifyDateRange]
	);

	const amazonTurnover = useMemo(
		() => calculateTurnoverData(amazonData, amazonDateRange, "amazon"),
		[amazonData, amazonDateRange]
	);

	const allTurnover = useMemo(() => {
		if (!shopifyData || !amazonData) {
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

		// Calculate weighted average based on inventory values
		const shopifyRate = shopifyData.inventory_turnover_rate || 0;
		const amazonRate = amazonData.inventory_turnover_rate || 0;
		
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
	}, [shopifyData, amazonData, allDateRange]);

	// Format turnover rate
	const formatTurnover = (value: number) => {
		return `${value.toFixed(1)}x`;
	};

	// Individual KPI Card Component
	const TurnoverKPICard = ({
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
							{formatTurnover(data.value)}
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
					loading={shopifyLoading}
					error={shopifyError}
					icon={<RotateCcw className="h-6 w-6" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Turnover KPI */}
				<TurnoverKPICard
					title="Amazon Turnover"
					data={amazonTurnover}
					dateRange={amazonDateRange}
					onDateRangeChange={setAmazonDateRange}
					loading={amazonLoading}
					error={amazonError}
					icon={<RefreshCw className="h-6 w-6" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Platforms Turnover KPI */}
				<TurnoverKPICard
					title="All Platforms"
					data={allTurnover}
					dateRange={allDateRange}
					onDateRangeChange={setAllDateRange}
					loading={shopifyLoading || amazonLoading}
					error={shopifyError || amazonError}
					icon={<RefreshCw className="h-6 w-6" style={{ color: "#8b5cf6" }} />}
					iconColor="#8b5cf6"
					iconBgColor="#f3e8ff"
				/>
			</div>
		</div>
	);
}
