"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Calendar, TrendingUp, BarChart3, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import * as Charts from "../charts";

interface InventoryTrendChartsProps {
	clientData?: any[];
	refreshInterval?: number;
}

type DateRange = "7" | "30" | "90";

export default function InventoryTrendCharts({
	clientData,
	refreshInterval = 300000,
}: InventoryTrendChartsProps) {
	const [selectedRange, setSelectedRange] = useState<DateRange>("30");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// Process data for inventory level trends
	const processInventoryTrends = (data: any[], days: number) => {
		const now = new Date();
		const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
		
		// Group data by date
		const dateGroups = new Map<string, number>();
		
		data.forEach(item => {
			const itemDate = item.created_at || item.updated_at || item.date || new Date().toISOString();
			const date = new Date(itemDate);
			
			if (date >= startDate && date <= now) {
				const dateKey = date.toISOString().split('T')[0]; // YYYY-MM-DD format
				const inventory = parseInt(item.inventory_quantity || item.stock || item.on_hand || 0);
				
				dateGroups.set(dateKey, (dateGroups.get(dateKey) || 0) + inventory);
			}
		});

		// Convert to chart format
		return Array.from(dateGroups.entries())
			.map(([date, inventory]) => ({
				date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
				inventory: inventory,
				value: inventory
			}))
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
			.slice(-30); // Limit to last 30 data points
	};

	// Process data for sales trends
	const processSalesTrends = (data: any[], days: number) => {
		const now = new Date();
		const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
		
		const dateGroups = new Map<string, { units: number, revenue: number }>();
		
		data.forEach(item => {
			const itemDate = item.created_at || item.order_date || item.date || new Date().toISOString();
			const date = new Date(itemDate);
			
			if (date >= startDate && date <= now) {
				const dateKey = date.toISOString().split('T')[0];
				const units = parseInt(item.quantity || item.units_sold || item.qty || 1);
				const revenue = parseFloat(item.total_price || item.amount || item.revenue || item.value || 0);
				
				const existing = dateGroups.get(dateKey) || { units: 0, revenue: 0 };
				dateGroups.set(dateKey, {
					units: existing.units + units,
					revenue: existing.revenue + revenue
				});
			}
		});

		return Array.from(dateGroups.entries())
			.map(([date, sales]) => ({
				date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
				units: sales.units,
				revenue: sales.revenue,
				value: sales.units
			}))
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
			.slice(-30);
	};

	// Process data for sales comparison (current vs historical)
	const processSalesComparison = (data: any[]) => {
		const now = new Date();
		const days = parseInt(selectedRange);
		const currentStart = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
		const historicalStart = new Date(currentStart.getTime() - days * 24 * 60 * 60 * 1000);
		const historicalEnd = currentStart;

		// Calculate current period sales
		const currentSales = data
			.filter(item => {
				const itemDate = new Date(item.created_at || item.order_date || item.date || new Date());
				return itemDate >= currentStart && itemDate <= now;
			})
			.reduce((sum, item) => sum + parseFloat(item.total_price || item.amount || item.revenue || 0), 0);

		// Calculate historical period sales
		const historicalSales = data
			.filter(item => {
				const itemDate = new Date(item.created_at || item.order_date || item.date || new Date());
				return itemDate >= historicalStart && itemDate < historicalEnd;
			})
			.reduce((sum, item) => sum + parseFloat(item.total_price || item.amount || item.revenue || 0), 0);

		return [
			{
				name: `Previous ${days} Days`,
				value: historicalSales,
				revenue: historicalSales
			},
			{
				name: `Current ${days} Days`,
				value: currentSales,
				revenue: currentSales
			}
		];
	};

	// Memoized chart data
	const chartData = useMemo(() => {
		if (!clientData || clientData.length === 0) {
			return {
				inventoryTrends: [],
				salesTrends: [],
				salesComparison: []
			};
		}

		const days = parseInt(selectedRange);
		
		return {
			inventoryTrends: processInventoryTrends(clientData, days),
			salesTrends: processSalesTrends(clientData, days),
			salesComparison: processSalesComparison(clientData)
		};
	}, [clientData, selectedRange]);

	// Update data when clientData changes
	useEffect(() => {
		setLoading(true);
		setError(null);

		try {
			if (clientData && clientData.length > 0) {
				// Data processing is handled by useMemo
				setError(null);
			} else {
				setError("No data available for trend analysis");
			}
			setLastUpdated(new Date());
		} catch (err: any) {
			console.error("Error processing trend data:", err);
			setError(`Failed to process trend data: ${err.message}`);
		} finally {
			setLoading(false);
		}
	}, [clientData]);

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
						}`}
					>
						{range}d
					</button>
				))}
			</div>
		</div>
	);

	if (loading) {
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
					<h3 className="text-lg font-semibold text-gray-900 mb-2">Trend Analysis Error</h3>
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
					<h2 className="text-2xl font-semibold text-gray-900">Inventory & Sales Trends</h2>
					<p className="text-gray-600">Real-time trend analysis with customizable date ranges</p>
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
					Last updated: {lastUpdated.toLocaleTimeString()} • 
					Showing {chartData.inventoryTrends.length} inventory data points, {chartData.salesTrends.length} sales data points
				</div>
			)}
		</div>
	);
}
