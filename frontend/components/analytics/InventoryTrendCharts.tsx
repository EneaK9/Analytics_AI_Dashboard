"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Calendar, TrendingUp, BarChart3, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import * as Charts from "../charts";
import { type TrendAnalysis } from "../../lib/inventoryService";
import useInventoryData from "../../hooks/useInventoryData";

interface InventoryTrendChartsProps {
	clientData?: any[];
	refreshInterval?: number;
	platform?: "shopify" | "amazon";
}

type DateRange = "7" | "30" | "90";

export default function InventoryTrendCharts({
	clientData,
	refreshInterval = 300000,
	platform = "shopify",
}: InventoryTrendChartsProps) {
	const [selectedRange, setSelectedRange] = useState<DateRange>("30");

	// Use shared inventory data hook to get trend analysis
	const { loading, error, trendAnalysis, lastUpdated, refresh } =
		useInventoryData({
			refreshInterval,
			fastMode: true,
			platform: platform,
		});

	// Process inventory levels from API trend data
	const processInventoryTrends = (days: number) => {
		if (!(trendAnalysis as any)?.inventory_levels_chart) return [];

		const now = new Date();
		const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

		return (trendAnalysis as any).inventory_levels_chart
			.filter((item: { date: string; inventory_level: number }) => {
				const itemDate = new Date(item.date);
				return itemDate >= startDate && itemDate <= now;
			})
			.map((item: { date: string; inventory_level: number }) => ({
				date: new Date(item.date).toLocaleDateString("en-US", {
					month: "short",
					day: "numeric",
				}),
				inventory: item.inventory_level,
				value: item.inventory_level,
			}))
			.sort(
				(a: any, b: any) =>
					new Date(a.date).getTime() - new Date(b.date).getTime()
			);
	};

	// Process sales trends from API trend data
	const processSalesTrends = (days: number) => {
		if (!(trendAnalysis as any)?.units_sold_chart) return [];

		const now = new Date();
		const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

		return (trendAnalysis as any).units_sold_chart
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
				revenue: 0, // We don't have daily revenue in units_sold_chart, use weekly data if needed
				value: item.units_sold,
			}))
			.sort(
				(a: any, b: any) =>
					new Date(a.date).getTime() - new Date(b.date).getTime()
			);
	};

	// Process sales comparison from API trend data
	const processSalesComparison = () => {
		if (!(trendAnalysis as any)?.sales_comparison) return [];

		const comparison = (trendAnalysis as any).sales_comparison;

		return [
			{
				name: "Historical Average",
				value: (comparison as any).historical_avg_revenue,
				revenue: (comparison as any).historical_avg_revenue,
			},
			{
				name: "Current Period",
				value: (comparison as any).current_period_avg_revenue,
				revenue: (comparison as any).current_period_avg_revenue,
			},
		];
	};

	// Memoized chart data
	const chartData = useMemo(() => {
		if (!trendAnalysis) {
			return {
				inventoryTrends: [],
				salesTrends: [],
				salesComparison: [],
			};
		}

		const days = parseInt(selectedRange);

		return {
			inventoryTrends: processInventoryTrends(days),
			salesTrends: processSalesTrends(days),
			salesComparison: processSalesComparison(),
		};
	}, [trendAnalysis, selectedRange]);

	// Date range selector
	const DateRangeSelector = () => (
		<div className="flex items-center gap-2">
			<Calendar className="h-4 w-4 text-gray-500" />
			<div className="flex rounded-lg border border-gray-300 bg-gray-50">
				{(["7", "30", "90"] as DateRange[]).map((range) => (
					<button
						key={range}
						onClick={() => setSelectedRange(range)}
						className={`px-3 py-1 text-sm font-medium transition-colors ${
							selectedRange === range
								? "bg-blue-500 text-white rounded-md"
								: "text-gray-600 hover:text-gray-900"
						}`}>
						{range}d
					</button>
				))}
			</div>
		</div>
	);

	// Only show loading if we have NO data at all - show data immediately if available
	if (loading && !trendAnalysis) {
		return (
			<div className="space-y-6">
				{/* Loading skeletons */}
				{[...Array(3)].map((_, i) => (
					<Card key={i}>
						<CardHeader>
							<div className="h-6 bg-gray-200 rounded w-48 animate-pulse"></div>
						</CardHeader>
						<CardContent>
							<div className="h-64 bg-gray-200 rounded animate-pulse"></div>
						</CardContent>
					</Card>
				))}
			</div>
		);
	}

	if (error) {
		return (
			<Card>
				<CardContent className="p-8 text-center">
					<div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
						<TrendingUp className="h-8 w-8 text-red-600" />
					</div>
					<h3 className="text-lg font-semibold text-gray-900 mb-2">
						Trend Analysis Error
					</h3>
					<p className="text-gray-600">{error}</p>
				</CardContent>
			</Card>
		);
	}

	return (
		<div className="space-y-6">
			{/* Header with date range selector */}
			<div className="flex items-center justify-between">
				<div>
					{/* <h2 className="text-2xl font-semibold text-gray-900">Inventory & Sales Trends</h2>
					<p className="text-gray-600">Real-time trend analysis with customizable date ranges</p> */}
				</div>
				<DateRangeSelector />
			</div>

			{/* Inventory Levels Time Series */}
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<TrendingUp className="h-5 w-5 text-blue-600" />
						Inventory Levels Over Time ({selectedRange} days)
					</CardTitle>
				</CardHeader>
				<CardContent>
					{chartData.inventoryTrends.length > 0 ? (
						<Charts.LineChartOne
							data={chartData.inventoryTrends}
							title="Inventory Trends"
							description={`Inventory levels over the last ${selectedRange} days`}
							minimal={true}
						/>
					) : (
						<div className="h-64 flex items-center justify-center text-gray-500">
							No inventory trend data available
						</div>
					)}
				</CardContent>
			</Card>

			{/* Units Sold Time Series */}
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<BarChart3 className="h-5 w-5 text-green-600" />
						Units Sold Over Time ({selectedRange} days)
					</CardTitle>
				</CardHeader>
				<CardContent>
					{chartData.salesTrends.length > 0 ? (
						<Charts.LineChartOne
							data={chartData.salesTrends}
							title="Sales Trends"
							description={`Units sold over the last ${selectedRange} days`}
							minimal={true}
						/>
					) : (
						<div className="h-64 flex items-center justify-center text-gray-500">
							No sales trend data available
						</div>
					)}
				</CardContent>
			</Card>

			{/* Sales Comparison Bar Chart */}
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<BarChart3 className="h-5 w-5 text-purple-600" />
						Sales Comparison: Current vs Historical Average
					</CardTitle>
				</CardHeader>
				<CardContent>
					{chartData.salesComparison.length > 0 ? (
						<Charts.BarChartOne
							data={chartData.salesComparison}
							title="Sales Comparison"
							description={`Current ${selectedRange}-day period vs previous ${selectedRange}-day period`}
							minimal={true}
						/>
					) : (
						<div className="h-64 flex items-center justify-center text-gray-500">
							No comparison data available
						</div>
					)}
				</CardContent>
			</Card>

			{/* Data Info */}
			{lastUpdated && (
				<div className="text-center text-sm text-gray-500">
					<RefreshCw className="inline h-4 w-4 mr-1" />
					Last updated: {lastUpdated.toLocaleTimeString()} • Showing{" "}
					{chartData.inventoryTrends.length} inventory data points,{" "}
					{chartData.salesTrends.length} sales data points
				</div>
			)}
		</div>
	);
}
