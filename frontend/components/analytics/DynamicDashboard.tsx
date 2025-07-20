/**
 * Dynamic Dashboard Component
 *
 * This component renders AI-generated dashboard configurations with:
 * - Dynamic widget types (charts, metrics, tables)
 * - Responsive grid layout
 * - Real-time data updates
 * - AI-powered insights
 */

"use client";

import React, { useState, useEffect } from "react";
import { dashboardService } from "../../lib/dashboardService";
import { clientDataService } from "../../lib/clientDataService";

// Import all available Shadcn chart components
import ShadcnAreaChart from "../charts/ShadcnAreaChart";
import ShadcnBarChart from "../charts/ShadcnBarChart";
import ShadcnLineChart from "../charts/ShadcnLineChart";
import ShadcnPieChart from "../charts/ShadcnPieChart";
import ShadcnInteractiveBar from "../charts/ShadcnInteractiveBar";
import ShadcnInteractiveDonut from "../charts/ShadcnInteractiveDonut";
import ShadcnMultipleArea from "../charts/ShadcnMultipleArea";

// Import KPI components
import SmartEcommerceMetrics from "./SmartEcommerceMetrics";

interface DynamicDashboardProps {
	clientId?: string;
	refreshInterval?: number;
}

interface AIChartConfig {
	id: string;
	title: string;
	subtitle: string;
	chart_type: string; // This will be the Shadcn component name
	data_source: string;
	config: {
		component: string;
		props: any;
		responsive: boolean;
		real_data_columns: string[];
	};
	position: { row: number; col: number };
	size: { width: number; height: number };
}

interface DashboardConfig {
	client_id: string;
	title: string;
	subtitle?: string;
	kpi_widgets: any[];
	chart_widgets: AIChartConfig[];
	theme: string;
	last_generated: string;
	version: string;
}

export default function DynamicDashboard({
	clientId,
	refreshInterval = 300000, // 5 minutes
}: DynamicDashboardProps) {
	const [dashboardConfig, setDashboardConfig] =
		useState<DashboardConfig | null>(null);
	const [clientData, setClientData] = useState<any[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

	// 🧠 AI-POWERED CHART COMPONENT SELECTOR
	const getShadcnComponent = (componentName: string) => {
		const componentMap = {
			ShadcnAreaChart,
			ShadcnBarChart,
			ShadcnLineChart,
			ShadcnPieChart,
			ShadcnInteractiveBar,
			ShadcnInteractiveDonut,
			ShadcnMultipleArea,
		};

		return componentMap[componentName as keyof typeof componentMap];
	};

	// 📊 REAL DATA PROCESSOR: Transform client data for specific chart requirements
	const processDataForChart = (
		chartConfig: AIChartConfig,
		rawData: any[]
	): any[] => {
		try {
			const { real_data_columns, component } = chartConfig.config;

			if (!rawData || rawData.length === 0) {
				return [];
			}

			// Process data based on chart component requirements
			switch (component) {
				case "ShadcnAreaChart":
				case "ShadcnLineChart":
					return processTimeSeriesData(rawData, real_data_columns);

				case "ShadcnBarChart":
				case "ShadcnInteractiveBar":
					return processCategoricalData(rawData, real_data_columns);

				case "ShadcnPieChart":
				case "ShadcnInteractiveDonut":
					return processPieChartData(rawData, real_data_columns);

				case "ShadcnMultipleArea":
					return processMultiSeriesData(rawData, real_data_columns);

				default:
					return rawData.slice(0, 20); // Fallback
			}
		} catch (error) {
			console.error("Error processing chart data:", error);
			return [];
		}
	};

	// 📈 Time Series Data Processing
	const processTimeSeriesData = (data: any[], columns: string[]): any[] => {
		const [dateCol, valueCol] = columns;
		return data
			.filter((item) => item[dateCol] && item[valueCol] !== null)
			.slice(0, 50) // Limit for performance
			.map((item) => ({
				name: formatDateForChart(item[dateCol]),
				value: Number(item[valueCol]) || 0,
				[valueCol]: Number(item[valueCol]) || 0,
				date: item[dateCol],
			}))
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	};

	// 📊 Categorical Data Processing
	const processCategoricalData = (data: any[], columns: string[]): any[] => {
		const [categoryCol, valueCol] = columns;

		// Group by category and sum values
		const groupedData: { [key: string]: number } = {};

		data.forEach((item) => {
			const category = String(item[categoryCol] || "Unknown");
			const value = Number(item[valueCol]) || 0;
			groupedData[category] = (groupedData[category] || 0) + value;
		});

		// Convert to chart format and limit to top 15
		return Object.entries(groupedData)
			.map(([category, value]) => ({
				name: category,
				value: value,
				[valueCol]: value,
			}))
			.sort((a, b) => b.value - a.value)
			.slice(0, 15);
	};

	// 🥧 Pie Chart Data Processing
	const processPieChartData = (data: any[], columns: string[]): any[] => {
		const categoricalData = processCategoricalData(data, columns);

		// Calculate percentages
		const total = categoricalData.reduce((sum, item) => sum + item.value, 0);

		return categoricalData
			.slice(0, 8) // Limit for readability
			.map((item) => ({
				...item,
				percentage: total > 0 ? Math.round((item.value / total) * 100) : 0,
			}));
	};

	// 📈 Multi-Series Data Processing
	const processMultiSeriesData = (data: any[], columns: string[]): any[] => {
		const [dateCol, value1Col, value2Col] = columns;

		return data
			.filter(
				(item) =>
					item[dateCol] &&
					(item[value1Col] !== null || item[value2Col] !== null)
			)
			.slice(0, 30) // Limit for performance
			.map((item) => ({
				name: formatDateForChart(item[dateCol]),
				[value1Col]: Number(item[value1Col]) || 0,
				[value2Col]: Number(item[value2Col]) || 0,
				date: item[dateCol],
			}))
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	};

	// 📅 Date Formatter for Charts
	const formatDateForChart = (dateString: string): string => {
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString("en-US", {
				month: "short",
				day: "numeric",
				year:
					date.getFullYear() !== new Date().getFullYear()
						? "2-digit"
						: undefined,
			});
		} catch {
			return String(dateString).slice(0, 10); // Fallback
		}
	};

	// 📊 Fetch dashboard configuration and data
	const fetchDashboardData = async () => {
		try {
			setLoading(true);
			setError(null);

			// Get AI-generated dashboard configuration
			const config = await dashboardService.getDashboardConfig();

			if (!config) {
				setError(
					"No dashboard configuration found. Please generate a dashboard first."
				);
				setLoading(false);
				return;
			}

			// Get real client data
			const rawData = await clientDataService.fetchClientData();

			setDashboardConfig(config);
			setClientData(rawData);
			setLastUpdated(new Date());
			setError(null);
		} catch (err: any) {
			console.error("Error fetching dashboard data:", err);
			setError(`Failed to load dashboard: ${err.message}`);
		} finally {
			setLoading(false);
		}
	};

	// 🎨 Render AI-Selected Shadcn Chart
	const renderAIChart = (chartConfig: AIChartConfig) => {
		const ChartComponent = getShadcnComponent(chartConfig.config.component);

		if (!ChartComponent) {
			return (
				<div className="p-4 border rounded-lg bg-red-50">
					<p className="text-red-600">
						Unknown chart type: {chartConfig.config.component}
					</p>
				</div>
			);
		}

		// Process real data for this specific chart
		const processedData = processDataForChart(chartConfig, clientData);

		// Merge AI-generated props with processed data
		const chartProps = {
			...chartConfig.config.props,
			data: processedData,
			title: chartConfig.title,
			description: chartConfig.subtitle,
		};

		return (
			<div
				className={`col-span-${chartConfig.size.width} row-span-${chartConfig.size.height}`}
				key={chartConfig.id}>
				<ChartComponent {...chartProps} />
			</div>
		);
	};

	// Initialize and set up auto-refresh
	useEffect(() => {
		fetchDashboardData();

		const interval = setInterval(fetchDashboardData, refreshInterval);
		return () => clearInterval(interval);
	}, [clientId, refreshInterval]);

	if (loading) {
		return (
			<div className="flex items-center justify-center min-h-96">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
					<p className="text-lg font-medium text-gray-600">
						Loading AI-Powered Dashboard...
					</p>
					<p className="text-sm text-gray-500">
						Fetching real data and configurations
					</p>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex items-center justify-center min-h-96">
				<div className="text-center p-8 bg-red-50 rounded-lg border border-red-200">
					<div className="text-red-600 text-lg font-medium mb-2">
						Dashboard Error
					</div>
					<p className="text-red-700 mb-4">{error}</p>
					<button
						onClick={fetchDashboardData}
						className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
						Retry Loading
					</button>
				</div>
			</div>
		);
	}

	if (!dashboardConfig) {
		return (
			<div className="flex items-center justify-center min-h-96">
				<div className="text-center p-8 bg-yellow-50 rounded-lg border border-yellow-200">
					<div className="text-yellow-800 text-lg font-medium mb-2">
						No Dashboard Found
					</div>
					<p className="text-yellow-700">
						No dashboard configuration available.
					</p>
				</div>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{/* 📊 Dashboard Header */}
			<div className="flex justify-between items-start">
				<div>
					<h1 className="text-3xl font-bold text-gray-900">
						{dashboardConfig.title}
					</h1>
					{dashboardConfig.subtitle && (
						<p className="text-lg text-gray-600 mt-1">
							{dashboardConfig.subtitle}
						</p>
					)}
					<p className="text-sm text-gray-500 mt-2">
						AI-Generated Dashboard • Last updated:{" "}
						{lastUpdated?.toLocaleTimeString()}
					</p>
				</div>
				<button
					onClick={fetchDashboardData}
					className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
					disabled={loading}>
					🔄 Refresh
				</button>
			</div>

			{/* 📈 KPI Metrics Section */}
			{dashboardConfig.kpi_widgets &&
				dashboardConfig.kpi_widgets.length > 0 && (
					<div>
						<SmartEcommerceMetrics clientData={clientData} />
					</div>
				)}

			{/* 🎨 AI-Selected Charts Grid */}
			{dashboardConfig.chart_widgets &&
			dashboardConfig.chart_widgets.length > 0 ? (
				<div className="grid grid-cols-4 gap-6 auto-rows-min">
					{dashboardConfig.chart_widgets.map((chartConfig) =>
						renderAIChart(chartConfig)
					)}
				</div>
			) : (
				<div className="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
					<p className="text-gray-600">
						No charts configured for this dashboard.
					</p>
				</div>
			)}

			{/* 📊 Dashboard Info */}
			<div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
				<div className="flex items-center justify-between text-sm text-blue-800">
					<span>
						Dashboard Version: {dashboardConfig.version} • Generated:{" "}
						{new Date(dashboardConfig.last_generated).toLocaleString()} •
						Charts: {dashboardConfig.chart_widgets?.length || 0} • Data Points:{" "}
						{clientData.length}
					</span>
					<span className="font-medium">🤖 AI-Orchestrated Dashboard</span>
				</div>
			</div>
		</div>
	);
}
