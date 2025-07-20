/**
 * Dashboard Service - Gets ONLY REAL DATA from database
 *
 * This service handles:
 * - Loading pre-generated dashboard configs
 * - Loading pre-calculated metrics
 * - Processing real data for AI-selected Shadcn charts
 * - NO AI ANALYSIS (already done during client creation)
 * - NO FAKE DATA - only real database data or null
 */

import api from "./axios";

// Types for the orchestrated data
export interface DashboardConfig {
	client_id: string;
	title: string;
	subtitle?: string;
	layout: any;
	kpi_widgets: any[];
	chart_widgets: AIChartConfig[];
	theme: string;
	last_generated: string;
	version: string;
}

export interface AIChartConfig {
	id: string;
	title: string;
	subtitle: string;
	chart_type: string; // Shadcn component name
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

export interface DashboardMetric {
	metric_id: string;
	client_id: string;
	metric_name: string;
	metric_value: any;
	metric_type: string;
	calculated_at: string;
}

export interface DataValidation {
	isValid: boolean;
	errors: string[];
	dataType: string;
	recordCount: number;
}

export interface ProcessedChartData {
	component: string;
	data: any[];
	props: any;
	error?: string;
}

class DashboardService {
	/**
	 * Get ONLY real dashboard configuration from database
	 * Returns null if no config exists
	 */
	async getDashboardConfig(): Promise<DashboardConfig | null> {
		try {
			const response = await api.get("/dashboard/config");
			return response.data || null;
		} catch (error) {
			console.error("Failed to get dashboard config:", error);
			return null;
		}
	}

	/**
	 * Get ONLY real dashboard metrics from database
	 * Returns empty array if no metrics exist
	 */
	async getDashboardMetrics(): Promise<DashboardMetric[]> {
		try {
			const response = await api.get("/dashboard/metrics");
			return Array.isArray(response.data) ? response.data : [];
		} catch (error) {
			console.error("Failed to get dashboard metrics:", error);
			return [];
		}
	}

	/**
	 * Get ONLY real client data from database
	 * Returns empty array if no data exists
	 */
	async getClientData(): Promise<any[]> {
		try {
			const response = await api.get("/data");
			return Array.isArray(response.data) ? response.data : [];
		} catch (error) {
			console.error("Failed to get client data:", error);
			return [];
		}
	}

	/**
	 * 🧠 AI CHART DATA PROCESSOR: Get processed data for specific AI-selected Shadcn charts
	 * This method takes the AI configuration and returns properly formatted data for each chart
	 */
	async getProcessedChartData(
		chartConfig: AIChartConfig,
		rawData?: any[]
	): Promise<ProcessedChartData> {
		try {
			// Get raw data if not provided
			const clientData = rawData || (await this.getClientData());

			if (!clientData || clientData.length === 0) {
				return {
					component: chartConfig.config.component,
					data: [],
					props: chartConfig.config.props,
					error: "No client data available",
				};
			}

			// Process data based on AI-selected component
			const processedData = this.processDataForShadcnComponent(
				chartConfig.config.component,
				clientData,
				chartConfig.config.real_data_columns
			);

			return {
				component: chartConfig.config.component,
				data: processedData,
				props: {
					...chartConfig.config.props,
					data: processedData,
					title: chartConfig.title,
					description: chartConfig.subtitle,
				},
			};
		} catch (error: any) {
			console.error(
				`Failed to process chart data for ${chartConfig.config.component}:`,
				error
			);
			return {
				component: chartConfig.config.component,
				data: [],
				props: chartConfig.config.props,
				error: error.message,
			};
		}
	}

	/**
	 * 📊 SHADCN COMPONENT DATA PROCESSOR
	 * Processes raw client data specifically for different Shadcn chart components
	 */
	private processDataForShadcnComponent(
		component: string,
		rawData: any[],
		dataColumns: string[]
	): any[] {
		try {
			switch (component) {
				case "ShadcnAreaChart":
				case "ShadcnLineChart":
					return this.processTimeSeriesData(rawData, dataColumns);

				case "ShadcnBarChart":
				case "ShadcnInteractiveBar":
					return this.processCategoricalData(rawData, dataColumns);

				case "ShadcnPieChart":
				case "ShadcnInteractiveDonut":
					return this.processPieChartData(rawData, dataColumns);

				case "ShadcnMultipleArea":
					return this.processMultiSeriesData(rawData, dataColumns);

				default:
					console.warn(`Unknown Shadcn component: ${component}`);
					return this.processGenericData(rawData, dataColumns);
			}
		} catch (error) {
			console.error(`Error processing data for ${component}:`, error);
			return [];
		}
	}

	/**
	 * 📈 Time Series Data Processing for Area/Line Charts
	 */
	private processTimeSeriesData(data: any[], columns: string[]): any[] {
		if (!columns || columns.length < 2) return [];

		const [dateCol, valueCol] = columns;

		return data
			.filter(
				(item) =>
					item[dateCol] &&
					item[valueCol] !== null &&
					item[valueCol] !== undefined
			)
			.slice(0, 100) // Limit for performance
			.map((item) => ({
				name: this.formatDateForChart(item[dateCol]),
				value: Number(item[valueCol]) || 0,
				[valueCol]: Number(item[valueCol]) || 0,
				date: item[dateCol],
				originalIndex: data.indexOf(item),
			}))
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
			.slice(0, 50); // Final limit for optimal chart performance
	}

	/**
	 * 📊 Categorical Data Processing for Bar Charts
	 */
	private processCategoricalData(data: any[], columns: string[]): any[] {
		if (!columns || columns.length < 2) return [];

		const [categoryCol, valueCol] = columns;

		// Group by category and aggregate values
		const groupedData: { [key: string]: number } = {};

		data.forEach((item) => {
			const category = String(item[categoryCol] || "Unknown");
			const value = Number(item[valueCol]) || 0;
			groupedData[category] = (groupedData[category] || 0) + value;
		});

		// Convert to chart format
		return Object.entries(groupedData)
			.map(([category, value]) => ({
				name: category,
				value: value,
				[valueCol]: value,
				category: category,
			}))
			.sort((a, b) => b.value - a.value)
			.slice(0, 20); // Limit for readability
	}

	/**
	 * 🥧 Pie Chart Data Processing
	 */
	private processPieChartData(data: any[], columns: string[]): any[] {
		const categoricalData = this.processCategoricalData(data, columns);

		// Calculate percentages
		const total = categoricalData.reduce((sum, item) => sum + item.value, 0);

		return categoricalData
			.slice(0, 10) // Limit for pie chart readability
			.map((item, index) => ({
				...item,
				percentage: total > 0 ? Math.round((item.value / total) * 100) : 0,
				fill: this.getChartColor(index),
			}));
	}

	/**
	 * 📈 Multi-Series Data Processing for Multiple Area Charts
	 */
	private processMultiSeriesData(data: any[], columns: string[]): any[] {
		if (!columns || columns.length < 3) return [];

		const [dateCol, value1Col, value2Col] = columns;

		return data
			.filter(
				(item) =>
					item[dateCol] &&
					(item[value1Col] !== null || item[value2Col] !== null)
			)
			.slice(0, 50) // Limit for performance
			.map((item) => ({
				name: this.formatDateForChart(item[dateCol]),
				[value1Col]: Number(item[value1Col]) || 0,
				[value2Col]: Number(item[value2Col]) || 0,
				date: item[dateCol],
			}))
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
	}

	/**
	 * 📊 Generic Data Processing (fallback)
	 */
	private processGenericData(data: any[], columns: string[]): any[] {
		if (!columns || columns.length === 0) return data.slice(0, 20);

		return data.slice(0, 20).map((item, index) => ({
			name: `Item ${index + 1}`,
			value: Number(item[columns[0]]) || 0,
			...item,
		}));
	}

	/**
	 * 📅 Date Formatter for Charts
	 */
	private formatDateForChart(dateString: string): string {
		try {
			const date = new Date(dateString);
			if (isNaN(date.getTime())) {
				return String(dateString).slice(0, 10);
			}

			return date.toLocaleDateString("en-US", {
				month: "short",
				day: "numeric",
				year:
					date.getFullYear() !== new Date().getFullYear()
						? "2-digit"
						: undefined,
			});
		} catch {
			return String(dateString).slice(0, 10);
		}
	}

	/**
	 * 🎨 Chart Color Generator
	 */
	private getChartColor(index: number): string {
		const colors = [
			"#465FFF",
			"#00C49F",
			"#FFBB28",
			"#FF8042",
			"#8884d8",
			"#82ca9d",
			"#ffc658",
			"#ff7300",
			"#9CB9FF",
			"#4ECDC4",
			"#45B7D1",
			"#FF6B6B",
		];
		return colors[index % colors.length];
	}

	/**
	 * 📊 Bulk Process All Dashboard Charts
	 * Processes data for all AI-selected charts in a dashboard configuration
	 */
	async processDashboardCharts(
		dashboardConfig: DashboardConfig
	): Promise<ProcessedChartData[]> {
		try {
			// Get client data once
			const clientData = await this.getClientData();

			if (!clientData || clientData.length === 0) {
				console.warn("No client data available for chart processing");
				return [];
			}

			// Process all charts concurrently
			const chartPromises = dashboardConfig.chart_widgets.map((chartConfig) =>
				this.getProcessedChartData(chartConfig, clientData)
			);

			const processedCharts = await Promise.all(chartPromises);

			console.log(
				`Processed ${processedCharts.length} AI-selected charts with real data`
			);
			return processedCharts;
		} catch (error: any) {
			console.error("Failed to process dashboard charts:", error);
			return [];
		}
	}

	/**
	 * Validate data structure - NO PROCESSING, just validation
	 */
	validateData(data: any[]): DataValidation {
		try {
			if (!Array.isArray(data)) {
				return {
					isValid: false,
					errors: ["Data must be an array"],
					dataType: "unknown",
					recordCount: 0,
				};
			}

			if (data.length === 0) {
				return {
					isValid: false,
					errors: ["Data array is empty"],
					dataType: "empty",
					recordCount: 0,
				};
			}

			// Basic validation only
			const errors: string[] = [];
			let dataType = "unknown";

			// Check if all items are objects
			const allObjects = data.every(
				(item) => typeof item === "object" && item !== null
			);
			if (!allObjects) {
				errors.push("All data items must be objects");
			}

			// Determine basic data type
			if (data.length > 0 && typeof data[0] === "object") {
				const firstItem = data[0];
				if (firstItem.revenue || firstItem.sales || firstItem.amount) {
					dataType = "financial";
				} else if (firstItem.user_id || firstItem.customer_id) {
					dataType = "user";
				} else if (firstItem.product_id || firstItem.item) {
					dataType = "product";
				} else {
					dataType = "general";
				}
			}

			return {
				isValid: errors.length === 0,
				errors,
				dataType,
				recordCount: data.length,
			};
		} catch (error) {
			return {
				isValid: false,
				errors: [`Validation error: ${error}`],
				dataType: "error",
				recordCount: 0,
			};
		}
	}

	/**
	 * Get user info - ONLY real data from token
	 */
	async getUserInfo(): Promise<any | null> {
		try {
			const response = await api.get("/auth/me");
			return response.data || null;
		} catch (error) {
			console.error("Failed to get user info:", error);
			return null;
		}
	}
}

export const dashboardService = new DashboardService();
export default dashboardService;
