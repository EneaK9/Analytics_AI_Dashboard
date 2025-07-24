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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer } from "@/components/ui/chart";

// Import data processing utilities
import { dashboardService } from "../../lib/dashboardService";
import { clientDataService } from "../../lib/clientDataService";

// Import ALL CHART COMPONENTS from the charts index - Clean and reliable
import * as Charts from "../charts";

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

	// 🧠 AI-POWERED CHART COMPONENT SELECTOR - ALL CHARTS AS PRIMARY OPTIONS
	const getShadcnComponent = (componentName: string) => {
		const componentMap = {
			// Area Charts (5)
			ShadcnAreaChart: Charts.ShadcnAreaChart,
			ShadcnAreaInteractive: Charts.ShadcnAreaInteractive,
			ShadcnAreaLinear: Charts.ShadcnAreaLinear,
			ShadcnAreaStacked: Charts.ShadcnAreaStacked,
			ShadcnAreaStep: Charts.ShadcnAreaStep,

			// Bar Charts (11)
			ShadcnBarChart: Charts.ShadcnBarChart,
			ShadcnBarDefault: Charts.ShadcnBarDefault,
			ShadcnBarLabel: Charts.ShadcnBarLabel,
			ShadcnBarLabelCustom: Charts.ShadcnBarLabelCustom,
			ShadcnBarHorizontal: Charts.ShadcnBarHorizontal,
			ShadcnBarMultiple: Charts.ShadcnBarMultiple,
			ShadcnBarStacked: Charts.ShadcnBarStacked,
			ShadcnBarMixed: Charts.ShadcnBarMixed,
			ShadcnBarActive: Charts.ShadcnBarActive,
			ShadcnBarNegative: Charts.ShadcnBarNegative,
			ShadcnBarCustom: Charts.ShadcnBarCustom,

			// Pie Charts (7)
			ShadcnPieChart: Charts.ShadcnPieChart,
			ShadcnPieChartLabel: Charts.ShadcnPieChartLabel,
			ShadcnPieDonutText: Charts.ShadcnPieDonutText,
			ShadcnPieInteractive: Charts.ShadcnPieInteractive,
			ShadcnPieLegend: Charts.ShadcnPieLegend,
			ShadcnPieSimple: Charts.ShadcnPieSimple,
			ShadcnPieStacked: Charts.ShadcnPieStacked,

			// Radar Charts (9)
			ShadcnRadarDefault: Charts.ShadcnRadarDefault,
			ShadcnRadarGridFill: Charts.ShadcnRadarGridFill,
			ShadcnRadarLegend: Charts.ShadcnRadarLegend,
			ShadcnRadarLinesOnly: Charts.ShadcnRadarLinesOnly,
			ShadcnRadarMultiple: Charts.ShadcnRadarMultiple,
			ShadcnRadarCustom: Charts.ShadcnRadarCustom,
			ShadcnRadarFilled: Charts.ShadcnRadarFilled,
			ShadcnRadarLines: Charts.ShadcnRadarLines,
			ShadcnRadarGrid: Charts.ShadcnRadarGrid,

			// Radial Charts (6)
			ShadcnRadialChart: Charts.ShadcnRadialChart,
			ShadcnRadialLabel: Charts.ShadcnRadialLabel,
			ShadcnRadialGrid: Charts.ShadcnRadialGrid,
			ShadcnRadialText: Charts.ShadcnRadialText,
			ShadcnRadialShape: Charts.ShadcnRadialShape,
			ShadcnRadialStacked: Charts.ShadcnRadialStacked,
		};

		const component = componentMap[componentName as keyof typeof componentMap];
		if (!component) {
			console.warn(
				`⚠️ Unknown chart component: ${componentName}, using ShadcnAreaChart as fallback`
			);
			return Charts.ShadcnAreaChart; // Fallback to a reliable default component
		}
		return component;
	};

	// 📊 REAL DATA PROCESSOR: Transform client data ensuring UNIQUE data per chart
	const processDataForChart = (
		chartConfig: AIChartConfig,
		rawData: any[]
	): any[] => {
		try {
			const { real_data_columns, component } = chartConfig.config;
			const chartTitle = chartConfig.title || "Unknown Chart";

			console.log(`🎯 Processing data for "${chartTitle}":`, {
				component,
				columns: real_data_columns,
				dataSize: rawData?.length || 0,
				sampleData: rawData?.slice(0, 2),
			});

			if (!rawData || rawData.length === 0) {
				console.warn(`❌ No data available for chart: ${chartTitle}`);
				return [];
			}

			if (!real_data_columns || real_data_columns.length === 0) {
				console.warn(`❌ No data columns specified for chart: ${chartTitle}`);
				return [];
			}

			let processedData: any[] = [];

			// 🚀 Process data for ALL chart types with VALIDATION - ALL SHADCN CHARTS SUPPORTED
			switch (component) {
				// Area Charts - Time Series Data
				case "ShadcnAreaChart":
				case "ShadcnAreaInteractive":
				case "ShadcnAreaLinear":
				case "ShadcnAreaStacked":
				case "ShadcnAreaStep":
					processedData = processTimeSeriesData(rawData, real_data_columns);
					break;

				// Bar Charts - Categorical Data - ALL BAR CHART TYPES
				case "ShadcnBarChart":
				case "ShadcnBarDefault":
				case "ShadcnBarLabel":
				case "ShadcnBarLabelCustom":
				case "ShadcnBarHorizontal":
				case "ShadcnBarMultiple":
				case "ShadcnBarStacked":
				case "ShadcnBarMixed":
				case "ShadcnBarActive":
				case "ShadcnBarNegative":
				case "ShadcnBarCustom":
					processedData = processCategoricalData(rawData, real_data_columns);
					break;

				// Pie Charts - Part-to-Whole Data - ALL PIE CHART TYPES
				case "ShadcnPieChart":
				case "ShadcnPieChartLabel":
				case "ShadcnPieDonutText":
				case "ShadcnPieInteractive":
				case "ShadcnPieLegend":
				case "ShadcnPieSimple":
				case "ShadcnPieStacked":
					processedData = processPieChartData(rawData, real_data_columns);
					break;

				// Radar Charts - Multi-dimensional Data - ALL RADAR CHART TYPES
				case "ShadcnRadarDefault":
				case "ShadcnRadarGridFill":
				case "ShadcnRadarLegend":
				case "ShadcnRadarLinesOnly":
				case "ShadcnRadarMultiple":
				case "ShadcnRadarCustom":
				case "ShadcnRadarFilled":
				case "ShadcnRadarLines":
				case "ShadcnRadarGrid":
					processedData = processRadarData(rawData, real_data_columns);
					break;

				// Radial Charts - Progress/Percentage Data - ALL RADIAL CHART TYPES
				case "ShadcnRadialChart":
				case "ShadcnRadialLabel":
				case "ShadcnRadialGrid":
				case "ShadcnRadialText":
				case "ShadcnRadialShape":
				case "ShadcnRadialStacked":
					processedData = processRadialData(rawData, real_data_columns);
					break;

				default:
					console.warn(
						`Unknown chart type: ${component}, using default time series processing`
					);
					processedData = processTimeSeriesData(rawData, real_data_columns);
					break;
			}

			console.log(`✅ Processed data for "${chartTitle}":`, {
				originalSize: rawData.length,
				processedSize: processedData.length,
				sampleProcessed: processedData.slice(0, 2),
			});

			// 🔍 VALIDATION: Ensure processed data is valid
			if (!processedData || processedData.length === 0) {
				console.error(
					`❌ Chart "${chartTitle}" resulted in empty data after processing`
				);
				return [];
			}

			return processedData;
		} catch (error) {
			console.error(
				`❌ Error processing data for chart "${chartConfig.title}":`,
				error
			);
			return [];
		}
	};

	// 📈 Time Series Data Processing - ENHANCED for real Shopify dates
	const processTimeSeriesData = (data: any[], columns: string[]): any[] => {
		console.log("🔍 Processing time series data:", {
			data: data.slice(0, 3),
			columns,
		});

		const [dateCol, valueCol] = columns;

		const processedData = data
			.filter(
				(item) =>
					item[dateCol] &&
					item[valueCol] !== null &&
					item[valueCol] !== undefined
			)
			.map((item) => {
				// 🔧 BETTER DATE FORMATTING: Convert Shopify dates to readable format
				let formattedDate = item[dateCol];
				if (typeof formattedDate === "string") {
					const date = new Date(formattedDate);
					if (!isNaN(date.getTime())) {
						formattedDate = date.toLocaleDateString("en-US", {
							month: "short",
							day: "numeric",
							year:
								date.getFullYear() !== new Date().getFullYear()
									? "numeric"
									: undefined,
						});
					}
				}

				return {
					...item,
					[dateCol]: formattedDate,
					[valueCol]: Number(item[valueCol]) || 0,
				};
			})
			.sort(
				(a, b) =>
					new Date(a[dateCol]).getTime() - new Date(b[dateCol]).getTime()
			)
			.slice(0, 30); // Limit for performance but show more data points

		console.log("✅ Processed time series result:", processedData.slice(0, 3));
		return processedData;
	};

	// 📊 Categorical Data Processing - ENHANCED for real Shopify data
	const processCategoricalData = (data: any[], columns: string[]): any[] => {
		console.log("🔍 Processing categorical data:", {
			data: data.slice(0, 3),
			columns,
		});

		const [categoryCol, valueCol] = columns;

		// Group by category and sum/count values
		const groupedData: { [key: string]: number } = {};

		data.forEach((item) => {
			// 🔧 BETTER CATEGORY EXTRACTION: Handle product titles, vendors, tags properly
			let category = String(item[categoryCol] || "Unknown");

			// Truncate long product names for readability
			if (categoryCol === "title" && category.length > 25) {
				category = category.substring(0, 25) + "...";
			}

			// Handle empty vendors
			if (
				categoryCol === "vendor" &&
				(!category || category === "null" || category === "")
			) {
				category = "No Brand";
			}

			// Handle product types
			if (
				categoryCol === "product_type" &&
				(!category || category === "null" || category === "")
			) {
				category = "Uncategorized";
			}

			// Handle tags (might be arrays or comma-separated)
			if (categoryCol === "tags") {
				if (Array.isArray(item[categoryCol])) {
					// If tags is an array, use the first tag
					category = item[categoryCol][0] || "No Tags";
				} else if (
					typeof item[categoryCol] === "string" &&
					item[categoryCol].includes(",")
				) {
					// If tags is comma-separated, use the first tag
					category = item[categoryCol].split(",")[0].trim() || "No Tags";
				}
			}

			const value = Number(item[valueCol]) || 0;
			groupedData[category] = (groupedData[category] || 0) + value;
		});

		// Convert to chart format and limit to top 12 for better readability
		const result = Object.entries(groupedData)
			.map(([category, value]) => ({
				name: category,
				value: value,
				[valueCol]: value,
			}))
			.sort((a, b) => b.value - a.value)
			.slice(0, 12);

		console.log("✅ Processed categorical result:", result);
		return result;
	};

	// 🥧 Pie Chart Data Processing - FIXED to handle real Shopify data
	const processPieChartData = (data: any[], columns: string[]): any[] => {
		console.log("🔍 Processing pie chart data:", {
			data: data.slice(0, 3),
			columns,
		});

		const [categoryCol, valueCol] = columns;

		// 🔧 SPECIAL HANDLING: If valueCol is "count", we need to count categories
		if (valueCol === "count" || !valueCol) {
			// Count occurrences of each category
			const counts: { [key: string]: number } = {};

			data.forEach((item) => {
				const category = String(item[categoryCol] || "Unknown");
				counts[category] = (counts[category] || 0) + 1;
			});

			// Convert to pie chart format
			const pieData = Object.entries(counts)
				.map(([category, count]) => ({
					name: category,
					value: count,
					count: count,
					percentage: 0, // Will be calculated below
				}))
				.sort((a, b) => b.value - a.value)
				.slice(0, 8);

			// Calculate percentages
			const total = pieData.reduce((sum, item) => sum + item.value, 0);
			return pieData.map((item) => ({
				...item,
				percentage: total > 0 ? Math.round((item.value / total) * 100) : 0,
			}));
		} else {
			// Use existing logic for numeric values
			const categoricalData = processCategoricalData(data, columns);
			const total = categoricalData.reduce((sum, item) => sum + item.value, 0);

			return categoricalData.slice(0, 8).map((item) => ({
				...item,
				percentage: total > 0 ? Math.round((item.value / total) * 100) : 0,
			}));
		}
	};

	// 🕸️ Radar Chart Data Processing
	const processRadarData = (data: any[], columns: string[]): any[] => {
		const [categoryCol, valueCol] = columns;

		// Group and aggregate data for radar chart
		const groupedData: { [key: string]: number } = {};

		data.forEach((item) => {
			const category = String(item[categoryCol] || "Unknown");
			const value = Number(item[valueCol]) || 0;
			groupedData[category] = (groupedData[category] || 0) + value;
		});

		// Convert to radar format (limit to 6 categories for readability)
		return Object.entries(groupedData)
			.map(([category, value]) => ({
				category,
				value,
				[valueCol]: value,
			}))
			.sort((a, b) => b.value - a.value)
			.slice(0, 6);
	};

	// 📊 Radial Chart Data Processing - NEW FOR RADIAL CHARTS
	const processRadialData = (data: any[], columns: string[]): any[] => {
		console.log("🔍 Processing radial data:", {
			data: data.slice(0, 3),
			columns,
		});

		const [categoryCol, valueCol] = columns;

		// Calculate progress/percentage values for radial charts
		const groupedData: { [key: string]: number } = {};

		data.forEach((item) => {
			const category = String(item[categoryCol] || "Unknown");
			const value = Number(item[valueCol]) || 0;
			groupedData[category] = (groupedData[category] || 0) + value;
		});

		const maxValue = Math.max(...Object.values(groupedData));

		// Convert to radial format with percentage calculations
		return Object.entries(groupedData)
			.map(([category, value]) => ({
				name: category,
				value: value,
				percentage: Math.round((value / maxValue) * 100),
				fill: `hsl(var(--chart-${
					(Object.keys(groupedData).indexOf(category) % 5) + 1
				}))`,
			}))
			.sort((a, b) => b.value - a.value)
			.slice(0, 5); // Limit to 5 for radial charts
	};

	// 📈 Multi-Series Data Processing - ENHANCED for real Shopify data
	const processMultiSeriesData = (data: any[], columns: string[]): any[] => {
		console.log("🔍 Processing multi-series data:", {
			data: data.slice(0, 3),
			columns,
		});

		// Handle different column configurations
		if (columns.length === 2) {
			// Two columns: X-axis and category grouping
			const [xCol, categoryCol] = columns;

			// Group data by category and X value
			const groupedData: { [key: string]: { [category: string]: number } } = {};

			data.forEach((item) => {
				const xValue = String(item[xCol] || "Unknown");
				const category = String(item[categoryCol] || "Other");

				if (!groupedData[xValue]) {
					groupedData[xValue] = {};
				}
				groupedData[xValue][category] =
					(groupedData[xValue][category] || 0) + 1;
			});

			// Convert to chart format
			const result = Object.entries(groupedData)
				.map(([xValue, categories]) => ({
					[xCol]: xValue,
					...categories,
				}))
				.sort(
					(a, b) => new Date(a[xCol]).getTime() - new Date(b[xCol]).getTime()
				)
				.slice(0, 20);

			console.log("✅ Processed multi-series result:", result.slice(0, 3));
			return result;
		} else if (columns.length >= 3) {
			// Three+ columns: X-axis and multiple Y values
			const [dateCol, value1Col, value2Col] = columns;

			const processedData = data
				.filter(
					(item) =>
						item[dateCol] &&
						(item[value1Col] !== null || item[value2Col] !== null)
				)
				.map((item) => {
					// Format date for better display
					let formattedDate = item[dateCol];
					if (typeof formattedDate === "string") {
						const date = new Date(formattedDate);
						if (!isNaN(date.getTime())) {
							formattedDate = date.toLocaleDateString("en-US", {
								month: "short",
								day: "numeric",
							});
						}
					}

					return {
						[dateCol]: formattedDate,
						[value1Col]: Number(item[value1Col]) || 0,
						[value2Col]: Number(item[value2Col]) || 0,
					};
				})
				.sort(
					(a, b) =>
						new Date(a[dateCol]).getTime() - new Date(b[dateCol]).getTime()
				)
				.slice(0, 30);

			console.log(
				"✅ Processed multi-series result:",
				processedData.slice(0, 3)
			);
			return processedData;
		}

		// Fallback
		return data.slice(0, 20);
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
			const processedData = await clientDataService.fetchClientData();

			setDashboardConfig(config);
			setClientData(processedData.rawData); // Extract the array from ProcessedClientData
			setLastUpdated(new Date());
			setError(null);
		} catch (err: any) {
			console.error("Error fetching dashboard data:", err);
			setError(`Failed to load dashboard: ${err.message}`);
		} finally {
			setLoading(false);
		}
	};

	// 🎨 Render AI-Selected Shadcn Chart with Enhanced Layout
	const renderAIChart = (chartConfig: AIChartConfig) => {
		const ChartComponent = getShadcnComponent(chartConfig.config.component);

		if (!ChartComponent) {
			return (
				<div className="p-6 border-2 border-dashed border-red-300 rounded-xl bg-red-50">
					<div className="text-center">
						<div className="text-red-600 font-medium mb-2">⚠️ Chart Error</div>
						<p className="text-red-500 text-sm">
							Unknown chart type: {chartConfig.config.component}
						</p>
					</div>
				</div>
			);
		}

		// Process real data for this specific chart
		const processedData = processDataForChart(chartConfig, clientData);

		// Check if we have data to display
		if (!processedData || processedData.length === 0) {
			return (
				<div className="p-6 border-2 border-dashed border-yellow-300 rounded-xl bg-yellow-50">
					<div className="text-center">
						<div className="text-yellow-600 font-medium mb-2">
							📊 No Data Available
						</div>
						<p className="text-yellow-600 text-sm">
							{chartConfig.title} - Waiting for data
						</p>
					</div>
				</div>
			);
		}

		// Enhanced chart props with better styling
		const chartProps = {
			...chartConfig.config.props,
			data: processedData,
			title: chartConfig.title,
			description: chartConfig.subtitle,
			className: "w-full h-full",
		};

		// Responsive column spanning based on screen size
		const getResponsiveClasses = () => {
			const { width, height } = chartConfig.size;

			// Mobile (sm): Most charts full width
			// Tablet (md): Half width for smaller charts
			// Desktop (lg): Use configured width
			if (width >= 3) {
				return `col-span-4 md:col-span-4 lg:col-span-${width} row-span-${height}`;
			} else if (width === 2) {
				return `col-span-4 md:col-span-2 lg:col-span-2 row-span-${height}`;
			} else {
				return `col-span-2 md:col-span-1 lg:col-span-1 row-span-${height}`;
			}
		};

		return (
			<div
				className={`${getResponsiveClasses()} min-h-[300px]`}
				key={chartConfig.id}>
				<div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-300 h-full">
					<div className="p-6 h-full flex flex-col">
						{/* Chart Header */}
						<div className="mb-4">
							<h3 className="text-lg font-semibold text-gray-900 mb-1">
								{chartConfig.title}
							</h3>
							{chartConfig.subtitle && (
								<p className="text-sm text-gray-600">{chartConfig.subtitle}</p>
							)}
						</div>

						{/* Chart Content */}
						<div className="flex-1 min-h-0">
							<ChartComponent {...chartProps} />
						</div>

						{/* Chart Footer with Data Count */}
						<div className="mt-4 pt-3 border-t border-gray-100">
							<p className="text-xs text-gray-500 text-center">
								{processedData.length} data points • Real-time data
							</p>
						</div>
					</div>
				</div>
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
		<div className="space-y-8">
			{/* 📊 Dashboard Header - Enhanced */}
			<div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
				<div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
					<div className="flex-1">
						<h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
							{dashboardConfig.title}
						</h1>
						{dashboardConfig.subtitle && (
							<p className="text-lg text-gray-700 mb-3">
								{dashboardConfig.subtitle}
							</p>
						)}
						<div className="flex flex-wrap gap-4 text-sm text-gray-600">
							<span className="inline-flex items-center gap-1">
								🤖 AI-Generated Dashboard
							</span>
							<span className="inline-flex items-center gap-1">
								🕒 Last updated: {lastUpdated?.toLocaleTimeString()}
							</span>
							<span className="inline-flex items-center gap-1">
								📊 {clientData.length} data points
							</span>
						</div>
					</div>
					<div className="flex gap-3">
						<button
							onClick={fetchDashboardData}
							className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
							disabled={loading}>
							{loading ? (
								<span className="flex items-center gap-2">
									<div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
									Refreshing...
								</span>
							) : (
								<span className="flex items-center gap-2">🔄 Refresh Data</span>
							)}
						</button>
					</div>
				</div>
			</div>

			{/* 📈 KPI Metrics Section - Enhanced */}
			{dashboardConfig.kpi_widgets &&
				dashboardConfig.kpi_widgets.length > 0 && (
					<div>
						<div className="mb-6">
							<h2 className="text-2xl font-semibold text-gray-900 mb-2">
								Key Performance Indicators
							</h2>
							<p className="text-gray-600">
								Real-time insights from your business data
							</p>
						</div>
						<SmartEcommerceMetrics clientData={clientData} />
					</div>
				)}

			{/* 🎨 AI-Selected Charts Grid - Enhanced Responsive Layout */}
			{dashboardConfig.chart_widgets &&
			dashboardConfig.chart_widgets.length > 0 ? (
				<div>
					<div className="mb-6">
						<h2 className="text-2xl font-semibold text-gray-900 mb-2">
							Analytics Dashboard
						</h2>
						<p className="text-gray-600">
							AI-generated visualizations based on your data patterns
						</p>
					</div>
					<div className="grid grid-cols-4 gap-6 auto-rows-min">
						{dashboardConfig.chart_widgets.map((chartConfig) =>
							renderAIChart(chartConfig)
						)}
					</div>
				</div>
			) : (
				<div className="text-center p-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
					<div className="max-w-md mx-auto">
						<div className="text-6xl mb-4">📊</div>
						<h3 className="text-xl font-medium text-gray-900 mb-2">
							No Charts Available
						</h3>
						<p className="text-gray-600 mb-6">
							No charts configured for this dashboard. Try refreshing your data
							or check if you have sufficient data for chart generation.
						</p>
						<button
							onClick={fetchDashboardData}
							className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
							🔄 Regenerate Dashboard
						</button>
					</div>
				</div>
			)}

			{/* 📊 Dashboard Info - Enhanced */}
			<div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
				<div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 text-sm">
					<div className="flex flex-wrap gap-4 text-blue-800">
						<span className="font-medium">
							Dashboard Version: {dashboardConfig.version}
						</span>
						<span>
							Generated:{" "}
							{new Date(dashboardConfig.last_generated).toLocaleString()}
						</span>
						<span>Charts: {dashboardConfig.chart_widgets?.length || 0}</span>
						<span>Data Points: {clientData.length}</span>
					</div>
					<div className="flex items-center gap-2 text-blue-800 font-medium">
						<span className="text-lg">🤖</span>
						<span>AI-Orchestrated Dashboard</span>
					</div>
				</div>
			</div>
		</div>
	);
}
