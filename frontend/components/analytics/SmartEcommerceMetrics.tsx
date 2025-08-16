"use client";

import React, { useMemo } from "react";
import { TrendingUp, TrendingDown, Users, DollarSign, Package } from "lucide-react";
import { type SalesKPIs } from "../../lib/inventoryService";
import useInventoryData from "../../hooks/useInventoryData";

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
	// Use shared inventory data hook - no more duplicate API calls!
	const {
		loading,
		error,
		salesKPIs,
		lastUpdated,
		refresh
	} = useInventoryData({
		refreshInterval,
		fastMode: true
	});

	// Convert backend KPIs to frontend MetricData format
	const convertKPIsToMetrics = (kpis: SalesKPIs): MetricData[] => {
		const metrics: MetricData[] = [];

		// Total Sales (7 Days)
		if (kpis.total_sales_7_days) {
			metrics.push({
				title: "Total Sales (7 Days)",
				value: kpis.total_sales_7_days.display_value,
				change: kpis.total_sales_7_days.change_percentage || "N/A",
				changeType: kpis.total_sales_7_days.trend === "up" ? "increase" : "decrease",
				icon: DollarSign,
				color: "text-green-600",
			});
		}

		// Total Sales (30 Days)
		if (kpis.total_sales_30_days) {
			metrics.push({
				title: "Total Sales (30 Days)",
				value: kpis.total_sales_30_days.display_value,
				change: kpis.total_sales_30_days.change_percentage || "N/A",
				changeType: kpis.total_sales_30_days.trend === "up" ? "increase" : "decrease",
				icon: TrendingUp,
				color: "text-blue-600",
			});
		}

		// Inventory Turnover Rate
		if (kpis.inventory_turnover_rate) {
			metrics.push({
				title: "Inventory Turnover Rate",
				value: kpis.inventory_turnover_rate.display_value,
				change: kpis.inventory_turnover_rate.change_percentage || "N/A",
				changeType: kpis.inventory_turnover_rate.trend === "up" ? "increase" : "decrease",
				icon: Package,
				color: "text-purple-600",
			});
		}

		// Days of Stock Remaining
		if (kpis.days_of_stock_remaining) {
			const isLowStock = kpis.days_of_stock_remaining.status === "critical" || 
			                  kpis.days_of_stock_remaining.status === "warning";
			metrics.push({
				title: "Days of Stock Remaining",
				value: kpis.days_of_stock_remaining.display_value,
				change: kpis.days_of_stock_remaining.status === "critical" ? "Critical" : 
				        kpis.days_of_stock_remaining.status === "warning" ? "Low Stock" : "Healthy",
				changeType: isLowStock ? "decrease" : "increase",
				icon: Users,
				color: isLowStock ? "text-red-600" : "text-green-600",
			});
		}

		return metrics;
	};

	// Convert KPIs to metrics format using useMemo for performance
	const metrics = useMemo(() => {
		if (!salesKPIs) return [];
		return convertKPIsToMetrics(salesKPIs);
	}, [salesKPIs]);

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
						Last updated: {lastUpdated.toLocaleTimeString()}
					</p>
				</div>
			)}
		</div>
	);
}