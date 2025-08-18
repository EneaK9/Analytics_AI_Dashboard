/**
 * Optimized SmartEcommerceMetrics Component
 *
 * Features:
 * - Independent date range and platform state
 * - React Query for optimized caching
 * - React.memo for preventing unnecessary re-renders
 * - No shared state affecting other components
 */

import React, { memo, useState, useCallback, useMemo } from "react";
import {
	TrendingUp,
	TrendingDown,
	Users,
	DollarSign,
	Package,
	RefreshCw,
} from "lucide-react";
import {
	useSalesMetrics,
	DateRange,
	DashboardFilters,
} from "../../hooks/useOptimizedDashboardData";
import IndependentDatePicker from "../ui/IndependentDatePicker";

interface OptimizedSmartEcommerceMetricsProps {
	initialPlatform?: "shopify" | "amazon" | "combined";
	initialDatePreset?: "7d" | "30d" | "90d";
	refreshInterval?: number;
	className?: string;
	showDatePicker?: boolean;
}

interface MetricData {
	title: string;
	value: string;
	change: string;
	changeType: "increase" | "decrease";
	icon: React.ComponentType;
	color: string;
}

// Helper function to format date range
const getDateRangeFromPreset = (preset: "7d" | "30d" | "90d"): DateRange => {
	const endDate = new Date();
	const startDate = new Date();

	switch (preset) {
		case "7d":
			startDate.setDate(endDate.getDate() - 7);
			break;
		case "30d":
			startDate.setDate(endDate.getDate() - 30);
			break;
		case "90d":
			startDate.setDate(endDate.getDate() - 90);
			break;
	}

	return {
		startDate: startDate.toISOString().split("T")[0],
		endDate: endDate.toISOString().split("T")[0],
		preset,
	};
};

const OptimizedSmartEcommerceMetrics: React.FC<OptimizedSmartEcommerceMetricsProps> =
	memo(
		({
			initialPlatform = "shopify",
			initialDatePreset = "7d",
			refreshInterval = 5 * 60 * 1000, // 5 minutes
			className = "",
			showDatePicker = true,
		}) => {
			// Independent state - changes here don't affect other components
			const [platform, setPlatform] = useState<
				"shopify" | "amazon" | "combined"
			>(initialPlatform);
			const [dateRange, setDateRange] = useState<DateRange>(() =>
				getDateRangeFromPreset(initialDatePreset)
			);

			// Memoized filters to prevent unnecessary re-renders
			const filters = useMemo<DashboardFilters>(
				() => ({
					platform,
					dateRange,
					refreshInterval,
				}),
				[platform, dateRange, refreshInterval]
			);

			// React Query hook with independent caching
			const {
				data: salesKPIs,
				isLoading,
				error,
				refetch,
				isRefetching,
			} = useSalesMetrics(filters);

			// Memoized metric conversion to prevent unnecessary calculations
			const metrics = useMemo((): MetricData[] => {
				if (!salesKPIs) return [];

				const metricsList: MetricData[] = [];

				// Total Sales (7 Days)
				if (salesKPIs.total_sales_7_days) {
					const revenue7d = salesKPIs.total_sales_7_days.revenue || 0;
					const units7d = salesKPIs.total_sales_7_days.units || 0;
					const orders7d = salesKPIs.total_sales_7_days.orders || 0;
					metricsList.push({
						title: "Total Sales (7 Days)",
						value: `$${revenue7d.toLocaleString()}`,
						change: `${units7d} units, ${orders7d} orders`,
						changeType: "increase",
						icon: DollarSign,
						color: "text-green-600",
					});
				}

				// Total Sales (30 Days)
				if (salesKPIs.total_sales_30_days) {
					const revenue30d = salesKPIs.total_sales_30_days.revenue || 0;
					const units30d = salesKPIs.total_sales_30_days.units || 0;
					const orders30d = salesKPIs.total_sales_30_days.orders || 0;

					// Calculate growth vs 7 days (daily average comparison)
					const avgDaily7d = salesKPIs.total_sales_7_days
						? (salesKPIs.total_sales_7_days.revenue || 0) / 7
						: 0;
					const avgDaily30d = revenue30d / 30;
					const growth =
						avgDaily30d > 0 && avgDaily7d > 0
							? ((avgDaily7d - avgDaily30d) / avgDaily30d) * 100
							: 0;

					metricsList.push({
						title: "Total Sales (30 Days)",
						value: `$${revenue30d.toLocaleString()}`,
						change: `${units30d} units, ${orders30d} orders`,
						changeType: growth >= 0 ? "increase" : "decrease",
						icon: TrendingUp,
						color: "text-blue-600",
					});
				}

				// Inventory Turnover Rate
				if (salesKPIs.inventory_turnover_rate !== undefined) {
					const turnover = Number(salesKPIs.inventory_turnover_rate) || 0;
					metricsList.push({
						title: "Inventory Turnover",
						value: `${(turnover || 0).toFixed(2)}x`,
						change: turnover > 1 ? "Healthy" : "Slow",
						changeType: turnover > 1 ? "increase" : "decrease",
						icon: Package,
						color: "text-purple-600",
					});
				}

				// Days Stock Remaining
				if (salesKPIs.days_stock_remaining !== undefined) {
					const daysStock = Number(salesKPIs.days_stock_remaining) || 0;
					const isHealthy = daysStock >= 7 && daysStock <= 60;
					const displayValue =
						daysStock > 999 ? "999+" : `${Math.round(daysStock)}`;
					metricsList.push({
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

				return metricsList;
			}, [salesKPIs]);

			// Callbacks to prevent child re-renders
			const handleDateRangeChange = useCallback((newDateRange: DateRange) => {
				setDateRange(newDateRange);
			}, []);

			const handlePlatformChange = useCallback(
				(newPlatform: "shopify" | "amazon" | "combined") => {
					setPlatform(newPlatform);
				},
				[]
			);

			const handleRefresh = useCallback(() => {
				refetch();
			}, [refetch]);

			// Only show loading if we have NO data at all - show data immediately if available
			if (isLoading && !salesKPIs) {
				return (
					<div className={`space-y-4 ${className}`}>
						{/* Date picker skeleton */}
						{showDatePicker && (
							<div className="h-12 bg-gray-200 rounded animate-pulse"></div>
						)}

						{/* Metrics skeleton */}
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
					</div>
				);
			}

			if (error) {
				return (
					<div className={`text-center py-8 ${className}`}>
						<div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
							<TrendingDown className="h-8 w-8 text-red-600" />
						</div>
						<h3 className="text-lg font-semibold text-gray-900 mb-2">
							Metrics Error
						</h3>
						<p className="text-gray-600 mb-4">{error.message}</p>
						<button
							onClick={handleRefresh}
							disabled={isRefetching}
							className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 mx-auto">
							<RefreshCw
								className={`h-4 w-4 ${isRefetching ? "animate-spin" : ""}`}
							/>
							Retry
						</button>
					</div>
				);
			}

			return (
				<div className={`space-y-4 ${className}`}>
					{/* Independent Date & Platform Picker */}
					{showDatePicker && (
						<div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
							<IndependentDatePicker
								dateRange={dateRange}
								onDateRangeChange={handleDateRangeChange}
								platform={platform}
								disabled={isLoading}
							/>

							{/* Platform selector */}
							<div className="flex items-center gap-2">
								<span className="text-sm font-medium text-gray-700">
									Platform:
								</span>
								<select
									value={platform}
									onChange={(e) =>
										handlePlatformChange(
											e.target.value as "shopify" | "amazon" | "combined"
										)
									}
									disabled={isLoading}
									className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed">
									<option value="shopify">Shopify</option>
									<option value="amazon">Amazon</option>
									<option value="combined">Combined</option>
								</select>
							</div>
						</div>
					)}

					{/* Metrics Grid */}
					<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
						{metrics.map((metric, index) => {
							const IconComponent = metric.icon;
							return (
								<div
									key={`${platform}-${metric.title}-${index}`}
									className="rounded-sm border border-stroke bg-white py-6 px-7.5 shadow-default relative">
									{/* Loading overlay */}
									{isRefetching && (
										<div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
											<RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
										</div>
									)}

									<div className="flex h-11.5 w-11.5 items-center justify-center rounded-full bg-meta-2">
										<IconComponent />
									</div>

									<div className="mt-4 flex items-end justify-between">
										<div>
											<h4 className="text-title-md font-bold text-black">
												{metric.value}
											</h4>
											<span className="text-sm font-medium">
												{metric.title}
											</span>
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
					</div>

					{/* Footer with last updated info */}
					<div className="text-center mt-4">
						<p className="text-xs text-gray-500">
							{platform === "combined"
								? "All Platforms"
								: platform.charAt(0).toUpperCase() + platform.slice(1)}{" "}
							metrics • Date range: {dateRange.startDate} to {dateRange.endDate}
							{isRefetching && (
								<span className="ml-2 inline-flex items-center gap-1">
									<RefreshCw className="h-3 w-3 animate-spin" />
									Refreshing...
								</span>
							)}
						</p>
					</div>
				</div>
			);
		}
	);

OptimizedSmartEcommerceMetrics.displayName = "OptimizedSmartEcommerceMetrics";

export default OptimizedSmartEcommerceMetrics;
