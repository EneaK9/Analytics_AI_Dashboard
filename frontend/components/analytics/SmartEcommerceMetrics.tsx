"use client";

import React, { useMemo } from "react";
import {
	TrendingUp,
	TrendingDown,
	Users,
	DollarSign,
	Package,
} from "lucide-react";
import { type SalesKPIs } from "../../lib/inventoryService";
import useInventoryData from "../../hooks/useInventoryData";

interface SmartEcommerceMetricsProps {
	clientData?: any[];
	refreshInterval?: number;
	platform?: "shopify" | "amazon";
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
	platform = "shopify",
}: SmartEcommerceMetricsProps) {
	// Use shared inventory data hook - no more duplicate API calls!
	const { loading, error, salesKPIs, lastUpdated, refresh } = useInventoryData({
		refreshInterval,
		fastMode: true,
		platform,
	});

	// Convert backend KPIs to frontend MetricData format
	const convertKPIsToMetrics = (kpis: any): MetricData[] => {
		const metrics: MetricData[] = [];

		// Total Sales (7 Days)
		if (kpis.total_sales_7_days) {
			const revenue7d = kpis.total_sales_7_days.revenue || 0;
			const units7d = kpis.total_sales_7_days.units || 0;
			const orders7d = kpis.total_sales_7_days.orders || 0;
			metrics.push({
				title: "Total Sales (7 Days)",
				value: `$${revenue7d.toLocaleString()}`,
				change: `${units7d} units, ${orders7d} orders`,
				changeType: "increase",
				icon: DollarSign,
				color: "text-green-600",
			});
		}

		// Total Sales (30 Days)
		if (kpis.total_sales_30_days) {
			const revenue30d = kpis.total_sales_30_days.revenue || 0;
			const units30d = kpis.total_sales_30_days.units || 0;
			const orders30d = kpis.total_sales_30_days.orders || 0;

			// Calculate growth vs 7 days (daily average comparison)
			const avgDaily7d = kpis.total_sales_7_days
				? (kpis.total_sales_7_days.revenue || 0) / 7
				: 0;
			const avgDaily30d = revenue30d / 30;
			const growth =
				avgDaily30d > 0 && avgDaily7d > 0
					? ((avgDaily7d - avgDaily30d) / avgDaily30d) * 100
					: 0;

			metrics.push({
				title: "Total Sales (30 Days)",
				value: `$${revenue30d.toLocaleString()}`,
				change: `${units30d} units, ${orders30d} orders`,
				changeType: growth >= 0 ? "increase" : "decrease",
				icon: TrendingUp,
				color: "text-blue-600",
			});
		}

		// Inventory Turnover Rate
		if (kpis.inventory_turnover_rate !== undefined) {
			const turnover = Number(kpis.inventory_turnover_rate) || 0;
			metrics.push({
				title: "Inventory Turnover",
				value: `${turnover.toFixed(2)}x`,
				change: turnover > 1 ? "Healthy" : "Slow",
				changeType: turnover > 1 ? "increase" : "decrease",
				icon: Package,
				color: "text-purple-600",
			});
		}

		// Days Stock Remaining
		if (kpis.days_stock_remaining !== undefined) {
			const daysStock = Number(kpis.days_stock_remaining) || 0;
			const isHealthy = daysStock >= 7 && daysStock <= 60; // 1 week to 2 months is healthy
			const displayValue =
				daysStock > 999 ? "999+" : `${Math.round(daysStock)}`;
			metrics.push({
				title: "Days Stock Remaining",
				value: `${displayValue} days`,
				change: isHealthy
					? "Optimal"
					: daysStock < 7
					? "Low Stock"
					: "High Stock",
				changeType: isHealthy ? "increase" : "decrease",
				icon: TrendingDown,
				color: "text-orange-600",
			});
		}

		return metrics;
	};

	// Compute metrics based on KPI data
	const metrics = useMemo(() => {
		if (!salesKPIs) return [];
		return convertKPIsToMetrics(salesKPIs);
	}, [salesKPIs]);

	// Only show loading if we have NO data at all - show data immediately if available
	if (loading && !salesKPIs) {
		return (
			<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
				{[...Array(4)].map((_, i) => (
					<div
						key={i}
						className="rounded-sm border border-stroke bg-white py-6 px-7.5 shadow-default animate-pulse">
						<div className="h-11.5 w-11.5 bg-gray-200 rounded-full"></div>
						<div className="mt-4 space-y-2">
							<div className="h-6 bg-gray-200 rounded w-20"></div>
							<div className="h-4 bg-gray-200 rounded w-16"></div>
						</div>
					</div>
				))}
			</div>
		);
	}

	if (error) {
		return (
			<div className="text-center py-8">
				<div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
					<TrendingDown className="h-8 w-8 text-red-600" />
				</div>
				<h3 className="text-lg font-semibold text-gray-900 mb-2">
					Metrics Error
				</h3>
				<p className="text-gray-600 mb-4">{error}</p>
				<button
					onClick={() => refresh(true)}
					className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
					Retry
				</button>
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
							<IconComponent />
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
						{platform === "shopify" ? "Shopify" : "Amazon"} metrics • Last
						updated: {lastUpdated.toLocaleTimeString()}
					</p>
				</div>
			)}
		</div>
	);
}
