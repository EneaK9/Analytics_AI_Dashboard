"use client";

import React, { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, Users, DollarSign } from "lucide-react";
import { dashboardService } from "../../lib/dashboardService";

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

	// Fetch ONLY real orchestrated metrics - NO FALLBACKS!
	const fetchMetrics = async () => {
		try {
			setLoading(true);
			setError(null);

			// Get ONLY pre-calculated metrics from database
			const orchestratedMetrics = await dashboardService.getDashboardMetrics();

			if (!orchestratedMetrics || orchestratedMetrics.length === 0) {
				// NO DATA = NO METRICS
				setMetrics([]);
				setError("No metrics data available");
				setLoading(false);
				return;
			}

			// Process ONLY real orchestrated metrics
			const realMetrics = processRealMetricsOnly(orchestratedMetrics);

			if (realMetrics.length === 0) {
				setMetrics([]);
				setError("No KPI metrics found in database");
			} else {
				setMetrics(realMetrics);
				setError(null);
			}

			setLastUpdated(new Date());
			setLoading(false);
		} catch (err: any) {
			console.error("Error fetching metrics:", err);

			// NO FALLBACKS - just show error
			setMetrics([]);
			setError(`Failed to load metrics: ${err.message}`);
			setLoading(false);
		}
	};

	// Process ONLY real orchestrated metrics from database
	const processRealMetricsOnly = (orchestratedMetrics: any[]): MetricData[] => {
		// Find ONLY KPI metrics from orchestrated data
		const kpiMetrics = orchestratedMetrics.filter(
			(m) =>
				m.metric_type === "kpi" &&
				m.metric_value !== null &&
				m.metric_value !== undefined
		);

		if (kpiMetrics.length === 0) {
			return [];
		}

		// Convert real database metrics to display format
		return kpiMetrics.slice(0, 4).map((metric, index) => {
			const icons = [DollarSign, Users, TrendingUp, TrendingDown];
			const colors = [
				"text-primary",
				"text-secondary",
				"text-meta-3",
				"text-meta-1",
			];

			return {
				title: metric.metric_name || "Unknown Metric",
				value: formatRealMetricValue(metric.metric_value),
				change: extractRealChange(metric.metric_value),
				changeType: determineChangeType(metric.metric_value),
				icon: icons[index] || DollarSign,
				color: colors[index] || "text-primary",
			};
		});
	};

	// Format ONLY real metric values - no fake data
	const formatRealMetricValue = (value: any): string => {
		if (value === null || value === undefined) {
			return "No Data";
		}

		if (typeof value === "object" && value.value !== undefined) {
			return formatRealMetricValue(value.value);
		}

		if (typeof value === "number") {
			return value > 1000
				? `$${(value / 1000).toFixed(1)}k`
				: `$${value.toFixed(0)}`;
		}

		if (typeof value === "string") {
			return value;
		}

		return "Invalid Data";
	};

	// Extract real change percentage from metric value
	const extractRealChange = (value: any): string => {
		if (value && typeof value === "object") {
			if (value.change) return value.change;
			if (value.trend && value.trend.change) return value.trend.change;
		}
		return "N/A";
	};

	// Determine change type from real data
	const determineChangeType = (value: any): "increase" | "decrease" => {
		if (value && typeof value === "object") {
			if (value.trend && value.trend.direction === "down") return "decrease";
			if (value.change && value.change.startsWith("-")) return "decrease";
		}
		return "increase";
	};

	// Load metrics on component mount
	useEffect(() => {
		fetchMetrics();
	}, [clientData]);

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
								className={`fill-primary h-6 w-6 ${metric.color}`}
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
