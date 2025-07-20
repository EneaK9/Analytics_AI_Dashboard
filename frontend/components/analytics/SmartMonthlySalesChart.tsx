"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { dashboardService } from "../../lib/dashboardService";

const ReactApexChart = dynamic(() => import("react-apexcharts"), {
	ssr: false,
});

interface SmartMonthlySalesChartProps {
	clientData?: any[];
	title?: string;
	refreshInterval?: number;
}

interface ChartData {
	series: any[];
	categories: string[];
}

export default function SmartMonthlySalesChart({
	clientData,
	title = "Sales Overview",
	refreshInterval = 300000, // 5 minutes
}: SmartMonthlySalesChartProps) {
	const [chartData, setChartData] = useState<ChartData | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [insights, setInsights] = useState<string[]>([]);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	const fetchSalesData = async () => {
		try {
			setLoading(true);
			setError(null);

			// Get ONLY pre-generated orchestrated chart data
			const orchestratedMetrics = await dashboardService.getDashboardMetrics();
			
			if (!orchestratedMetrics || orchestratedMetrics.length === 0) {
				// NO DATA = NO CHART
				setChartData(null);
				setError("No chart data available");
				setInsights([]);
				setLoading(false);
				return;
			}

			// Process ONLY real chart data
			const realChartData = extractRealChartData(orchestratedMetrics);
			
			if (!realChartData || !realChartData.series || realChartData.series.length === 0) {
				setChartData(null);
				setError("No chart metrics found in database");
				setInsights([]);
			} else {
				setChartData(realChartData);
				setInsights([
					"📊 Chart loaded from database",
					"💰 Real analytics data",
					"⚡ Live dashboard metrics"
				]);
				setError(null);
			}

			setLastUpdated(new Date());
			setLoading(false);
		} catch (err: any) {
			console.error("Error fetching chart data:", err);
			
			// NO FALLBACKS - just show error
			setChartData(null);
			setInsights([]);
			setError(`Failed to load chart: ${err.message}`);
			setLoading(false);
		}
	};

	// Extract ONLY real chart data from database
	const extractRealChartData = (orchestratedMetrics: any[]): ChartData | null => {
		// Find ONLY chart metrics from orchestrated data
		const chartMetrics = orchestratedMetrics.filter(
			(m) => m.metric_type === "chart_data" && m.metric_value !== null
		);

		if (chartMetrics.length === 0) {
			return null;
		}

		// Use the first available chart metric
		const salesChart = chartMetrics.find(
			(m) =>
				m.metric_name?.includes("sales") ||
				m.metric_name?.includes("revenue") ||
				m.metric_name?.includes("monthly") ||
				m.metric_name?.includes("chart")
		);

		if (!salesChart?.metric_value?.data) {
			return null;
		}

		const chartData = salesChart.metric_value.data;

		// Validate that we have real data structure
		if (!chartData.series || !Array.isArray(chartData.series) || chartData.series.length === 0) {
			return null;
		}

		if (!chartData.categories || !Array.isArray(chartData.categories) || chartData.categories.length === 0) {
			return null;
		}

		return {
			series: chartData.series,
			categories: chartData.categories,
		};
	};

	// Safe chart options - only render if we have real data
	const getChartOptions = () => {
		if (!chartData) return null;

		return {
			legend: {
				show: false,
				position: "top" as const,
				horizontalAlign: "left" as const,
			},
			colors: ["#465FFF", "#9CB9FF"],
			chart: {
				fontFamily: "Satoshi, sans-serif",
				height: 335,
				type: "line" as const,
				dropShadow: {
					enabled: true,
					color: "#623CEA14",
					top: 10,
					blur: 4,
					left: 0,
					opacity: 0.1,
				},
				toolbar: {
					show: false,
				},
			},
			responsive: [
				{
					breakpoint: 1024,
					options: {
						chart: {
							height: 300,
						},
					},
				},
			],
			stroke: {
				width: [2, 2],
				curve: "straight" as const,
			},
			grid: {
				xaxis: {
					lines: {
						show: true,
					},
				},
				yaxis: {
					lines: {
						show: true,
					},
				},
			},
			dataLabels: {
				enabled: false,
			},
			markers: {
				size: 4,
				colors: "#fff",
				strokeColors: ["#465FFF", "#9CB9FF"],
				strokeWidth: 3,
				strokeOpacity: 0.9,
				strokeDashArray: 0,
				fillOpacity: 1,
				hover: {
					size: undefined,
					sizeOffset: 5,
				},
			},
			xaxis: {
				type: "category" as const,
				categories: chartData.categories,
				axisBorder: {
					show: false,
				},
				axisTicks: {
					show: false,
				},
			},
			yaxis: {
				title: {
					style: {
						fontSize: "0px",
					},
				},
				min: 0,
			},
		};
	};

	// Load chart data on component mount
	useEffect(() => {
		fetchSalesData();
	}, [clientData]);

	// Auto-refresh chart data
	useEffect(() => {
		if (refreshInterval > 0) {
			const interval = setInterval(fetchSalesData, refreshInterval);
			return () => clearInterval(interval);
		}
	}, [refreshInterval]);

	// Loading state
	if (loading) {
		return (
			<div className="col-span-12 rounded-sm border border-stroke bg-white px-5 pb-5 pt-7.5 shadow-default xl:col-span-8">
				<div className="flex flex-wrap items-start justify-between gap-3 sm:flex-nowrap">
					<div className="flex w-full flex-wrap gap-3 sm:gap-5">
						<div className="flex min-w-47.5">
							<div className="w-full">
								<div className="h-4 bg-gray-200 rounded w-32 mb-2 animate-pulse"></div>
								<div className="h-6 bg-gray-200 rounded w-20 animate-pulse"></div>
							</div>
						</div>
					</div>
				</div>
				<div className="h-64 bg-gray-100 rounded animate-pulse mt-4"></div>
			</div>
		);
	}

	// No data state
	if (error || !chartData) {
		return (
			<div className="col-span-12 rounded-sm border border-stroke bg-white px-5 pb-5 pt-7.5 shadow-default xl:col-span-8">
				<div className="flex flex-wrap items-start justify-between gap-3 sm:flex-nowrap">
					<div className="flex w-full flex-wrap gap-3 sm:gap-5">
						<div className="flex min-w-47.5">
							<span className="mt-1 mr-2 flex h-4 w-full max-w-4 items-center justify-center rounded-full border border-gray-300">
								<span className="block h-2.5 w-full max-w-2.5 rounded-full bg-gray-300"></span>
							</span>
							<div className="w-full">
								<p className="font-semibold text-gray-700">{title}</p>
								<p className="text-sm font-medium text-gray-500">
									{lastUpdated ? lastUpdated.toLocaleTimeString() : "No data"}
								</p>
							</div>
						</div>
					</div>
				</div>

				<div className="mt-8 flex flex-col items-center justify-center h-64 text-center">
					<div className="mx-auto mb-4 h-16 w-16 rounded-full bg-gray-100 flex items-center justify-center">
						<svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
						</svg>
					</div>
					<h3 className="text-lg font-semibold text-gray-900 mb-2">No Chart Data</h3>
					<p className="text-gray-600 max-w-sm">
						{error || "No chart data has been generated yet. Chart metrics need to be calculated first."}
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

	// Render chart with real data
	const chartOptions = getChartOptions();

	return (
		<div className="col-span-12 rounded-sm border border-stroke bg-white px-5 pb-5 pt-7.5 shadow-default xl:col-span-8">
			<div className="flex flex-wrap items-start justify-between gap-3 sm:flex-nowrap">
				<div className="flex w-full flex-wrap gap-3 sm:gap-5">
					<div className="flex min-w-47.5">
						<span className="mt-1 mr-2 flex h-4 w-full max-w-4 items-center justify-center rounded-full border border-primary">
							<span className="block h-2.5 w-full max-w-2.5 rounded-full bg-primary"></span>
						</span>
						<div className="w-full">
							<p className="font-semibold text-primary">{title}</p>
							<p className="text-sm font-medium">
								{lastUpdated ? lastUpdated.toLocaleTimeString() : "Loading..."}
							</p>
						</div>
					</div>
				</div>
			</div>

			<div className="mt-4">
				<div id="chartOne" className="-ml-5">
					{chartOptions && (
						<ReactApexChart
							options={chartOptions}
							series={chartData.series}
							type="line"
							height={350}
						/>
					)}
				</div>
			</div>

			{insights.length > 0 && (
				<div className="mt-4 space-y-1">
					{insights.map((insight, index) => (
						<p key={index} className="text-xs text-gray-600">
							{insight}
						</p>
					))}
				</div>
			)}
		</div>
	);
}
