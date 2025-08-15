"use client";

import React, { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, Users, DollarSign, Package, BarChart3, Clock } from "lucide-react";
import { inventoryService, type SalesKPIs } from "../../lib/inventoryService";

interface SmartEcommerceMetricsProps {
	clientData?: any[];
	refreshInterval?: number;
}

interface MetricData {
	title: string;
	value: string;
	change: string;
	changeType: "increase" | "decrease";
	icon: React.ComponentType;
	color: string;
}

export default function SmartEcommerceMetrics({
	clientData,
	refreshInterval = 300000, // 5 minutes
}: SmartEcommerceMetricsProps) {
	const [metrics, setMetrics] = useState<MetricData[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// Fetch comprehensive inventory and sales metrics from dedicated endpoint
	const fetchMetrics = async () => {
		try {
			setLoading(true);
			setError(null);

			// Get analytics from dedicated inventory endpoint
			const response = await inventoryService.getInventoryAnalytics();
			
			if (response.success && response.inventory_analytics.sales_kpis) {
				const inventoryMetrics = convertKPIsToMetrics(response.inventory_analytics.sales_kpis);
				setMetrics(inventoryMetrics);
				setError(null);
			} else {
				setMetrics([]);
				setError(response.error || "No inventory analytics available");
			}

			setLastUpdated(new Date());
			setLoading(false);
		} catch (err: any) {
			console.error("Error fetching inventory metrics:", err);
			setMetrics([]);
			setError(`Failed to load inventory metrics: ${err.message}`);
			setLoading(false);
		}
	};

	// Convert backend KPIs to frontend MetricData format
	const convertKPIsToMetrics = (kpis: SalesKPIs): MetricData[] => {
		const metrics: MetricData[] = [];

		// Total Sales (7 Days)
		metrics.push({
			title: "Total Sales (7 Days)",
			value: `$${kpis.total_sales_7_days.revenue.toLocaleString()}`,
			change: `${kpis.total_sales_7_days.units} units • ${kpis.total_sales_7_days.orders} orders`,
			changeType: kpis.total_sales_7_days.revenue > 0 ? "increase" : "neutral",
			icon: DollarSign,
			color: "text-green-600",
		});

		// Total Sales (30 Days)
		metrics.push({
			title: "Total Sales (30 Days)",
			value: `$${kpis.total_sales_30_days.revenue.toLocaleString()}`,
			change: `${kpis.total_sales_30_days.units} units • ${kpis.total_sales_30_days.orders} orders`,
			changeType: kpis.total_sales_30_days.revenue > 0 ? "increase" : "neutral",
			icon: TrendingUp,
			color: "text-blue-600",
		});

		// Total Sales (90 Days)
		metrics.push({
			title: "Total Sales (90 Days)",
			value: `$${kpis.total_sales_90_days.revenue.toLocaleString()}`,
			change: `${kpis.total_sales_90_days.units} units • ${kpis.total_sales_90_days.orders} orders`,
			changeType: kpis.total_sales_90_days.revenue > 0 ? "increase" : "neutral",
			icon: BarChart3,
			color: "text-purple-600",
		});

		// Inventory Turnover Rate
		metrics.push({
			title: "Inventory Turnover Rate",
			value: kpis.inventory_turnover_rate.toFixed(2),
			change: kpis.inventory_turnover_rate > 0 ? "Active" : "No turnover",
			changeType: kpis.inventory_turnover_rate > 1 ? "increase" : "decrease",
			icon: Package,
			color: kpis.inventory_turnover_rate > 1 ? "text-green-600" : "text-orange-600",
		});

		// Days of Stock Remaining
		const isLowStock = kpis.days_stock_remaining < 30;
		metrics.push({
			title: "Days of Stock Remaining",
			value: kpis.days_stock_remaining.toString(),
			change: isLowStock ? "Low Stock" : "Healthy",
			changeType: isLowStock ? "decrease" : "increase",
			icon: Clock,
			color: isLowStock ? "text-red-600" : "text-green-600",
		});

		// Total Inventory Units
		metrics.push({
			title: "Total Inventory Units",
			value: kpis.total_inventory_units.toLocaleString(),
			change: `${kpis.avg_daily_sales.toFixed(1)} avg daily sales`,
			changeType: "neutral",
			icon: Package,
			color: "text-gray-600",
		});

		return metrics;
	};



	// Load metrics on component mount
	useEffect(() => {
		fetchMetrics();
	}, []);

	// Auto-refresh metrics
	useEffect(() => {
		if (refreshInterval > 0) {
			const interval = setInterval(fetchMetrics, refreshInterval);
			return () => clearInterval(interval);
		}
	}, [refreshInterval]);

	// Show loading state
	if (loading) {
		return (
			<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
				{[...Array(4)].map((_, index) => (
					<div
						key={index}
						className="rounded-sm border border-stroke bg-white py-6 px-7.5 shadow-default">
						<div className="flex h-11.5 w-11.5 items-center justify-center rounded-full bg-gray-200 animate-pulse"></div>
						<div className="mt-4 flex items-end justify-between">
							<div>
								<div className="h-4 bg-gray-200 rounded w-24 mb-2 animate-pulse"></div>
								<div className="h-6 bg-gray-200 rounded w-16 animate-pulse"></div>
							</div>
							<div className="h-4 bg-gray-200 rounded w-12 animate-pulse"></div>
						</div>
					</div>
				))}
			</div>
		);
	}

	// Show error or no data state
	if (error || metrics.length === 0) {
		return (
			<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
				<div className="col-span-full rounded-sm border border-stroke bg-white py-12 px-7.5 shadow-default text-center">
					<div className="mx-auto mb-4 h-16 w-16 rounded-full bg-gray-100 flex items-center justify-center">
						<Users className="h-8 w-8 text-gray-400" />
					</div>
					<h3 className="text-lg font-semibold text-gray-900 mb-2">
						No Metrics Data
					</h3>
					<p className="text-gray-600">
						{error ||
							"No metrics have been calculated yet. Data needs to be processed first."}
					</p>
					{lastUpdated && (
						<p className="text-xs text-gray-400 mt-2">
							Last checked: {lastUpdated.toLocaleTimeString()}
						</p>
					)}
				</div>
			</div>
		);
	}

	// Show real metrics data
	return (
		<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
			{metrics.map((metric, index) => {
				const IconComponent = metric.icon;
				return (
					<div
						key={index}
						className="rounded-sm border border-stroke bg-white py-6 px-7.5 shadow-default">
						<div
							className={`flex h-11.5 w-11.5 items-center justify-center rounded-full bg-meta-2`}>
							<IconComponent
								// className={`fill-primary h-6 w-6 ${metric.color}`}
							/>
						</div>

						<div className="mt-4 flex items-end justify-between">
							<div>
								<h4 className="text-title-md font-bold text-black">
									{metric.value}
								</h4>
								<span className="text-sm font-medium">{metric.title}</span>
							</div>

							<span
								className={`flex items-center gap-1 text-sm font-medium ${
									metric.changeType === "increase"
										? "text-meta-3"
										: "text-meta-5"
								}`}>
								{metric.change}
								{metric.changeType === "increase" ? (
									<TrendingUp className="h-4 w-4" />
								) : (
									<TrendingDown className="h-4 w-4" />
								)}
							</span>
						</div>
					</div>
				);
			})}

			{lastUpdated && (
				<div className="col-span-full text-center mt-2">
					<p className="text-xs text-gray-500">
						Last updated: {lastUpdated.toLocaleTimeString()}
					</p>
				</div>
			)}
		</div>
	);
}
