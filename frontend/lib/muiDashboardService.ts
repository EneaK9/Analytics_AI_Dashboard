import api from "./axios";

// Backend metric types exactly matching your API response
export interface BackendMetric {
	metric_id: string;
	client_id: string;
	metric_name: string;
	metric_value: {
		// For chart_data type
		data?: Array<{
			fill: string;
			name: string;
			count: number;
			month: string;
			value: number;
			mobile: number;
			browser: string;
			desktop: number;
			visitors: number;
			total?: number;
			amount?: number;
		}>;
		title?: string;
		source?: string;
		subtitle?: string;
		timestamp?: string;
		chart_type?: string;
		has_dropdown?: boolean;
		dropdown_options?: Array<{ label: string; value: string }>;

		// For kpi type
		value?: string;
		trend?: {
			value: string;
			isPositive: boolean;
		};
		kpi_id?: string;
	};
	metric_type: "chart_data" | "kpi";
	calculated_at: string;
}

// MUI Chart Data Interfaces
export interface MUIStatCardData {
	title: string;
	value: string;
	interval: string;
	trend: "up" | "down" | "neutral";
	trendValue: string; // Real percentage like "-34.6%" or "+5.2%"
	data: number[];
}

export interface MUIChartData {
	id: string;
	title: string;
	subtitle: string;
	muiChartType: string;
	originalChartType: string;
	data: any[];
	config?: any;
	hasDropdown?: boolean;
	dropdownOptions?: Array<{ label: string; value: string }>;
}

export interface MUIDashboardData {
	kpis: MUIStatCardData[];
	pieCharts: MUIChartData[];
	barCharts: MUIChartData[];
	lineCharts: MUIChartData[];
	radarCharts: MUIChartData[];
	radialCharts: MUIChartData[];
	areaCharts: MUIChartData[];
	totalMetrics: number;
	lastUpdated: string;
}

// Comprehensive mapping from Shadcn chart types to MUI equivalents
const SHADCN_TO_MUI_CHART_MAP: Record<string, string> = {
	// Bar Charts -> MUI BarChart
	ShadcnBarDefault: "BarChart",
	ShadcnBarHorizontal: "BarChart",
	ShadcnBarStacked: "BarChart",
	ShadcnBarActive: "BarChart",
	ShadcnBarNegative: "BarChart",
	ShadcnBarMultiple: "BarChart",
	ShadcnBarMixed: "BarChart",
	ShadcnBarLabel: "BarChart",
	ShadcnBarLabelCustom: "BarChart",
	ShadcnBarCustom: "BarChart",

	// Pie Charts -> MUI PieChart
	ShadcnPieChart: "PieChart",
	ShadcnPieSimple: "PieChart",
	ShadcnPieInteractive: "PieChart",
	ShadcnPieLegend: "PieChart",
	ShadcnPieChartLabel: "PieChart",
	ShadcnPieDonutText: "PieChart",
	ShadcnPieStacked: "PieChart",

	// Area Charts -> MUI LineChart with area prop
	ShadcnAreaChart: "LineChart",
	ShadcnAreaLinear: "LineChart",
	ShadcnAreaInteractive: "LineChart",
	ShadcnAreaStacked: "LineChart",
	ShadcnAreaStep: "LineChart",

	// Radial Charts -> MUI PieChart with custom styling
	ShadcnRadialChart: "PieChart",
	ShadcnRadialStacked: "PieChart",
	ShadcnRadialShape: "PieChart",
	ShadcnRadialText: "PieChart",
	ShadcnRadialLabel: "PieChart",
	ShadcnRadialGrid: "PieChart",

	// Radar Charts -> Custom Radar (using recharts/nivo)
	ShadcnRadarDefault: "RadarChart",
	ShadcnRadarCustom: "RadarChart",
	ShadcnRadarFilled: "RadarChart",
	ShadcnRadarLines: "RadarChart",
	ShadcnRadarLinesOnly: "RadarChart",
	ShadcnRadarMultiple: "RadarChart",
	ShadcnRadarGrid: "RadarChart",
	ShadcnRadarGridFill: "RadarChart",
	ShadcnRadarLegend: "RadarChart",
};

class MUIDashboardService {
	private cache: Map<string, { data: BackendMetric[]; timestamp: number }> =
		new Map();
	private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

	// Fetch metrics from backend (NEW STANDARDIZED FORMAT)
	async fetchMetrics(): Promise<BackendMetric[]> {
		const cacheKey = "dashboard_metrics";
		const cached = this.cache.get(cacheKey);

		if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
			console.log("📊 Using cached dashboard metrics");
			return cached.data;
		}

		try {
			console.log(
				"🔄 Fetching fresh dashboard metrics from backend (NEW FORMAT)"
			);
			console.log("🌐 API call to:", "/dashboard/metrics");
			const response = await api.get("/dashboard/metrics");
			console.log("📡 API Response status:", response.status);

			// Handle new standardized response format
			const standardizedResponse = response.data;
			console.log(
				"📊 Received standardized response:",
				standardizedResponse.success,
				standardizedResponse.message
			);

			if (
				!standardizedResponse.success ||
				!standardizedResponse.dashboard_data
			) {
				console.warn(
					"⚠️ Backend returned unsuccessful response or no dashboard data"
				);
				return [];
			}

			// Convert standardized format back to legacy format for compatibility
			const metrics: BackendMetric[] =
				this.convertStandardizedToLegacy(standardizedResponse);

			console.log(
				`✅ Fetched and converted ${metrics.length} metrics from backend`
			);

			// DEBUG: Log sample data to see what we're actually getting
			if (metrics.length > 0) {
				console.log("📋 Sample converted metric data:", metrics[0]);
				const chartData = metrics.find((m) => m.metric_type === "chart_data");
				if (chartData) {
					console.log("📊 Sample chart data:", chartData.metric_value);
				}
			}

			this.cache.set(cacheKey, { data: metrics, timestamp: Date.now() });
			return metrics;
		} catch (error) {
			console.error("❌ Error fetching dashboard metrics:", error);
			return [];
		}
	}

	// Convert new standardized format to legacy format for compatibility
	private convertStandardizedToLegacy(
		standardizedResponse: any
	): BackendMetric[] {
		const metrics: BackendMetric[] = [];
		const { dashboard_data } = standardizedResponse;

		try {
			// Convert KPIs to legacy format
			if (dashboard_data.kpis) {
				for (const kpi of dashboard_data.kpis) {
					metrics.push({
						metric_id: kpi.id,
						client_id: standardizedResponse.client_id,
						metric_name: kpi.display_name,
						metric_type: "kpi",
						metric_value: {
							value: kpi.value,
							title: kpi.display_name,
							trend: {
								value: `${kpi.trend.percentage}%`,
								isPositive: kpi.trend.direction === "up",
							},
							source: "standardized",
							format: kpi.format,
						},
						calculated_at: dashboard_data.metadata.generated_at,
					});
				}
			}

			// Convert Charts to legacy format
			if (dashboard_data.charts) {
				for (const chart of dashboard_data.charts) {
					metrics.push({
						metric_id: chart.id,
						client_id: standardizedResponse.client_id,
						metric_name: chart.display_name,
						metric_type: "chart_data",
						metric_value: {
							data: chart.data,
							chart_type: chart.chart_type,
							title: chart.display_name,
							subtitle: `${chart.config.x_axis?.display_name || "X"} vs ${
								chart.config.y_axis?.display_name || "Y"
							}`,
							dropdown_options: chart.config.filters
								? Object.values(chart.config.filters).flat()
								: [],
							has_dropdown:
								chart.config.filters &&
								Object.keys(chart.config.filters).length > 0,
							source: "standardized",
						},
						calculated_at: dashboard_data.metadata.generated_at,
					});
				}
			}

			console.log(
				`🔄 Converted standardized format: ${
					dashboard_data.kpis?.length || 0
				} KPIs + ${dashboard_data.charts?.length || 0} charts = ${
					metrics.length
				} legacy metrics`
			);
			return metrics;
		} catch (error) {
			console.error(
				"❌ Error converting standardized format to legacy:",
				error
			);
			return [];
		}
	}

	// Convert backend metrics to MUI StatCard format
	convertToStatCards(metrics: BackendMetric[]): MUIStatCardData[] {
		const kpiMetrics = metrics.filter((m) => m.metric_type === "kpi");
		console.log(`📈 Converting ${kpiMetrics.length} KPI metrics to stat cards`);

		return kpiMetrics.map((metric) => {
			const { value, trend } = metric.metric_value;

			// DEBUG: Log what we're actually getting from the API
			console.log(`🔍 Processing KPI: "${metric.metric_name}"`, {
				value: value,
				trend: trend,
				trendValue: trend?.value,
				isPositive: trend?.isPositive,
				fullMetric: metric,
			});

			// Use REAL trend percentage from your backend data
			const trendValue = trend?.value || "0%";
			const isPositive = trend?.isPositive ?? true;

			console.log(
				`🎯 Final trendValue for "${metric.metric_name}": "${trendValue}"`
			);

			// Validate that we're getting the expected values
			if (
				metric.metric_name === "Total First Variant Price" &&
				trendValue !== "-2.9%"
			) {
				console.warn(`⚠️ Expected -2.9% but got: "${trendValue}"`);
			}

			// Generate realistic trend data based on the actual value and trend
			const baseValue = parseFloat(value?.replace(/[$,]/g, "") || "0") || 100;
			const trendPercentage = parseFloat(trendValue.replace(/[%+-]/g, "")) || 0;
			const trendMultiplier = isPositive
				? 1 + trendPercentage / 100
				: 1 - trendPercentage / 100;

			const trendData = Array.from({ length: 30 }, (_, i) => {
				// Create realistic progression over 30 days using real trend
				const dailyChange = Math.pow(trendMultiplier, i / 30);
				const randomFactor = 0.95 + Math.random() * 0.1; // ±5% daily variation
				return Math.round(baseValue * dailyChange * randomFactor);
			});

			return {
				title: metric.metric_name,
				value: value || "0",
				interval: "Last 30 days", // Remove the trend from interval text
				trend: isPositive ? "up" : "down",
				trendValue: trendValue, // Real percentage from backend like "-34.6%"
				data: trendData,
			};
		});
	}

	// Convert backend chart data to MUI format
	convertToMUICharts(metrics: BackendMetric[]): {
		pieCharts: MUIChartData[];
		barCharts: MUIChartData[];
		lineCharts: MUIChartData[];
		radarCharts: MUIChartData[];
		radialCharts: MUIChartData[];
		areaCharts: MUIChartData[];
	} {
		const chartMetrics = metrics.filter((m) => m.metric_type === "chart_data");
		console.log(
			`📊 Converting ${chartMetrics.length} chart metrics to MUI format`
		);

		// DEBUG: Log all chart titles we're receiving
		chartMetrics.forEach((metric) => {
			console.log(
				`📈 Found chart: "${metric.metric_value.title}" (${metric.metric_value.chart_type})`
			);
			console.log(
				`📊 Chart data sample:`,
				metric.metric_value.data?.slice(0, 2)
			); // First 2 items
		});

		const categorizedCharts = {
			pieCharts: [] as MUIChartData[],
			barCharts: [] as MUIChartData[],
			lineCharts: [] as MUIChartData[],
			radarCharts: [] as MUIChartData[],
			radialCharts: [] as MUIChartData[],
			areaCharts: [] as MUIChartData[],
		};

		chartMetrics.forEach((metric) => {
			const chartType = metric.metric_value.chart_type || "";
			const muiChartType = SHADCN_TO_MUI_CHART_MAP[chartType] || "BarChart";

			const chartData: MUIChartData = {
				id: metric.metric_id,
				title: metric.metric_value.title || "Chart",
				subtitle: metric.metric_value.subtitle || "",
				muiChartType,
				originalChartType: chartType,
				data: this.transformDataForMUI(
					metric.metric_value.data || [],
					muiChartType,
					metric.metric_value.title || ""
				),
				config: this.generateMUIConfig(chartType, muiChartType),
				hasDropdown: metric.metric_value.has_dropdown,
				dropdownOptions: metric.metric_value.dropdown_options,
			};

			// Categorize charts based on MUI type and original type
			if (muiChartType === "PieChart") {
				if (chartType.includes("Radial")) {
					categorizedCharts.radialCharts.push(chartData);
				} else {
					categorizedCharts.pieCharts.push(chartData);
				}
			} else if (muiChartType === "BarChart") {
				categorizedCharts.barCharts.push(chartData);
			} else if (muiChartType === "LineChart") {
				if (chartType.includes("Area")) {
					categorizedCharts.areaCharts.push(chartData);
				} else {
					categorizedCharts.lineCharts.push(chartData);
				}
			} else if (muiChartType === "RadarChart") {
				categorizedCharts.radarCharts.push(chartData);
			}
		});

		return categorizedCharts;
	}

	// Transform backend data format to MUI chart format
	private transformDataForMUI(
		data: any[],
		muiChartType: string,
		title: string
	): any[] {
		if (!data || data.length === 0) return [];

		// Detect if this is a status-related chart based on data content
		const isStatusChart = this.detectStatusChart(data, title);

		// Calculate total for percentage calculations using appropriate fields
		// For status charts, prioritize count fields; for monetary charts, prioritize amount fields
		const totalSum = data.reduce((sum, item) => {
			if (isStatusChart) {
				return (
					sum +
					(item.count ||
						item.visitors ||
						item.value ||
						item.total ||
						item.amount ||
						0)
				);
			} else {
				return (
					sum + (item.amount || item.total || item.value || item.count || 0)
				);
			}
		}, 0);

		console.log(
			`💯 Total sum for percentage calculation: ${totalSum} (isStatusChart: ${isStatusChart})`,
			data.map((item) => ({
				name: item.name,
				amount: item.amount,
				total: item.total,
				value: item.value,
				count: item.count,
				visitors: item.visitors,
			}))
		);

		switch (muiChartType) {
			case "PieChart":
				return data.map((item, index) => {
					// Use appropriate field based on chart type
					const value = isStatusChart
						? item.count ||
						  item.visitors ||
						  item.value ||
						  item.total ||
						  item.amount ||
						  0
						: item.amount || item.total || item.value || item.count || 0;
					const percentage =
						totalSum > 0 ? Math.round((value / totalSum) * 100) : 0;

					console.log(
						`🥧 PieChart item: ${item.name} - value: ${value}, percentage: ${percentage}% (isStatusChart: ${isStatusChart}) (from: amount=${item.amount}, total=${item.total}, value=${item.value}, count=${item.count})`
					);

					return {
						id: item.name,
						value: value,
						label: `${item.name} (${percentage}%)`,
						color: this.extractColor(item.fill, index),
					};
				});

			case "BarChart":
				return data.map((item) => {
					// Use appropriate field based on chart type
					const value = isStatusChart
						? item.count ||
						  item.visitors ||
						  item.value ||
						  item.total ||
						  item.amount ||
						  0
						: item.amount || item.total || item.value || item.count || 0;
					const percentage =
						totalSum > 0 ? Math.round((value / totalSum) * 100) : 0;
					const desktop = item.desktop || value;
					const mobile = item.mobile || value * 0.8;

					console.log(
						`📊 BarChart item: ${item.name} - value: ${value}, desktop: ${desktop}, mobile: ${mobile} (isStatusChart: ${isStatusChart}) (from: amount=${item.amount}, total=${item.total})`
					);

					return {
						name: item.name,
						value: value,
						desktop: desktop,
						mobile: mobile,
						percentage: percentage,
						fill: item.fill,
					};
				});

			case "LineChart":
				return data.map((item, index) => {
					// Use appropriate field based on chart type
					const value = isStatusChart
						? item.count ||
						  item.visitors ||
						  item.value ||
						  item.total ||
						  item.amount ||
						  0
						: item.amount || item.total || item.value || item.count || 0;
					const percentage =
						totalSum > 0 ? Math.round((value / totalSum) * 100) : 0;

					console.log(
						`📈 LineChart item: ${item.name} - value: ${value}, percentage: ${percentage}% (isStatusChart: ${isStatusChart}) (from: amount=${item.amount}, total=${item.total})`
					);

					return {
						name: item.name,
						value: value,
						desktop: item.desktop || value,
						mobile: item.mobile || value * 0.8,
						month: item.month || item.name || `Point ${index + 1}`,
						percentage: percentage,
					};
				});

			case "RadarChart":
				return data.map((item) => {
					// Use appropriate field based on chart type
					const value = isStatusChart
						? item.count ||
						  item.visitors ||
						  item.value ||
						  item.total ||
						  item.amount ||
						  0
						: item.amount || item.total || item.value || item.count || 0;
					const percentage =
						totalSum > 0 ? Math.round((value / totalSum) * 100) : 0;

					console.log(
						`🎯 RadarChart item: ${item.name} - value: ${value}, percentage: ${percentage}% (isStatusChart: ${isStatusChart})`
					);

					return {
						name: item.name,
						value: value,
						desktop: item.desktop || value,
						mobile: item.mobile || value * 0.8,
						count: item.count || value,
						percentage: percentage,
					};
				});

			default:
				return data;
		}
	}

	// Detect if this is a status-related chart based on data content
	private detectStatusChart(data: any[], title: string): boolean {
		if (!data || data.length === 0) return false;

		// Check chart title for status-related keywords
		const titleLower = title.toLowerCase();
		const statusTitleKeywords = ["activity radar", "activity tracking"];
		const hasTitleKeywords = statusTitleKeywords.some((keyword) =>
			titleLower.includes(keyword)
		);

		// Exclude charts that are explicitly about monetary comparisons
		const monetaryKeywords = [
			"revenue",
			"sales",
			"profit",
			"platform share",
			"growth",
			"price",
		];
		const isExplicitlyMonetary = monetaryKeywords.some(
			(keyword) =>
				titleLower.includes(keyword) ||
				(data[0] && typeof data[0].amount === "number" && data[0].amount > 100)
		);

		// Check if the names/categories are status-related terms
		const statusTerms = [
			"active",
			"inactive",
			"archived",
			"draft",
			"pending",
			"approved",
			"rejected",
			"published",
			"unpublished",
			"enabled",
			"disabled",
		];

		const hasStatusTerms = data.some((item) => {
			const name = (item.name || "").toLowerCase();
			return statusTerms.some((term) => name.includes(term));
		});

		// Check if count/visitors fields are present and more meaningful than amount fields
		const hasCountData = data.some((item) => item.count || item.visitors);
		const hasAmountData = data.some((item) => item.amount || item.total);

		// Filter out charts with unrealistic large numbers (likely IDs or timestamps)
		if (hasAmountData) {
			const avgAmount =
				data.reduce((sum, item) => sum + (item.amount || item.total || 0), 0) /
				data.length;
			const avgCount =
				data.reduce(
					(sum, item) => sum + (item.count || item.visitors || 0),
					0
				) / data.length;

			// If amounts are extremely large, treat as status chart (to use count instead)
			if (avgAmount > 1000000) {
				console.log(
					`🔍 Detected unrealistic large values, treating as status chart: avgAmount=${avgAmount}`
				);
				return true;
			}
		}

		// Special cases:
		// 1. If title explicitly mentions monetary terms and has realistic amounts, prefer monetary
		if (isExplicitlyMonetary && hasAmountData) {
			const avgAmount =
				data.reduce((sum, item) => sum + (item.amount || item.total || 0), 0) /
				data.length;
			if (avgAmount > 0 && avgAmount < 100000) {
				// Realistic monetary range
				console.log(
					`🔍 Chart "${title}" has monetary focus with realistic amounts, treating as monetary chart`
				);
				return false;
			}
		}

		// 2. If chart title suggests status analysis but data doesn't contain status terms, it's not a status chart
		if (titleLower.includes("status") && !hasStatusTerms) {
			console.log(
				`🔍 Chart "${title}" has status in title but no status terms in data, treating as regular chart`
			);
			return false;
		}

		// 3. Pure status charts: explicit status keywords in title AND status terms in data
		const isPureStatusChart = hasTitleKeywords && hasStatusTerms;

		const isStatusChart = isPureStatusChart || (hasCountData && !hasAmountData);
		console.log(`🔍 Status chart detection for "${title}": 
		  hasTitleKeywords=${hasTitleKeywords}, 
		  hasStatusTerms=${hasStatusTerms}, 
		  isExplicitlyMonetary=${isExplicitlyMonetary},
		  isPureStatusChart=${isPureStatusChart},
		  result=${isStatusChart}`);

		return isStatusChart;
	}

	// Generate MUI-specific configuration based on chart types
	private generateMUIConfig(originalType: string, muiType: string): any {
		const baseConfig = {
			responsive: true,
			maintainAspectRatio: false,
		};

		switch (muiType) {
			case "BarChart":
				return {
					...baseConfig,
					layout: originalType.includes("Horizontal")
						? "horizontal"
						: "vertical",
					stacked: originalType.includes("Stacked"),
				};

			case "PieChart":
				if (originalType.includes("Donut") || originalType.includes("Radial")) {
					return { ...baseConfig, innerRadius: 40, outerRadius: 80 };
				}
				return { ...baseConfig, innerRadius: 0, outerRadius: 80 };

			case "LineChart":
				return {
					...baseConfig,
					area: originalType.includes("Area"),
					stacked: originalType.includes("Stacked"),
					curve: originalType.includes("Step") ? "step" : "linear",
				};

			default:
				return baseConfig;
		}
	}

	// Extract color from CSS custom property
	private extractColor(fill: string, index: number): string {
		if (fill && fill.includes("hsl(var(--chart-")) {
			const colorMap: Record<string, string> = {
				"--chart-1": "#0088FE",
				"--chart-2": "#00C49F",
				"--chart-3": "#FFBB28",
				"--chart-4": "#FF8042",
				"--chart-5": "#8884D8",
			};

			const match = fill.match(/--chart-(\d+)/);
			if (match) {
				return (
					colorMap[`--chart-${match[1]}`] ||
					`hsl(${(index * 137.5) % 360}, 70%, 50%)`
				);
			}
		}

		return `hsl(${(index * 137.5) % 360}, 70%, 50%)`;
	}

	// Return empty data when backend is unavailable - NO fake data
	private generateFallbackData(): MUIDashboardData {
		console.log(
			"⚠️ No backend data available - returning empty data structure"
		);

		return {
			kpis: [], // No fake KPIs
			pieCharts: [], // No fake pie charts
			barCharts: [], // No fake bar charts
			lineCharts: [], // No fake line charts
			radarCharts: [], // No fake radar charts
			radialCharts: [], // No fake radial charts
			areaCharts: [], // No fake area charts
			totalMetrics: 0,
			lastUpdated: "No data available",
		};
	}

	// Main function to process all metrics into MUI dashboard format
	async processMUIMetrics(): Promise<MUIDashboardData> {
		try {
			console.log("🚀 Starting MUI dashboard data processing");
			const metrics = await this.fetchMetrics();

			if (metrics.length === 0) {
				console.warn("⚠️ No metrics found, using fallback data");
				return this.generateFallbackData();
			}

			const kpis = this.convertToStatCards(metrics);
			const charts = this.convertToMUICharts(metrics);

			const result = {
				kpis,
				...charts,
				totalMetrics: metrics.length,
				lastUpdated: new Date().toLocaleString(),
			};

			console.log("✅ MUI dashboard data processing complete:", {
				totalMetrics: result.totalMetrics,
				kpis: result.kpis.length,
				totalCharts:
					result.pieCharts.length +
					result.barCharts.length +
					result.lineCharts.length +
					result.radarCharts.length,
			});

			return result;
		} catch (error) {
			console.error("❌ Error processing MUI metrics, using fallback:", error);
			return this.generateFallbackData();
		}
	}

	// Helper function to generate summary statistics
	generateSummaryStats(metrics: BackendMetric[]): {
		totalMetrics: number;
		totalCharts: number;
		totalKPIs: number;
		lastUpdated: string;
		chartTypes: Record<string, number>;
	} {
		const chartMetrics = metrics.filter((m) => m.metric_type === "chart_data");
		const kpiMetrics = metrics.filter((m) => m.metric_type === "kpi");

		const chartTypes: Record<string, number> = {};
		chartMetrics.forEach((metric) => {
			const chartType = metric.metric_value.chart_type || "Unknown";
			chartTypes[chartType] = (chartTypes[chartType] || 0) + 1;
		});

		const latestTimestamp = metrics.reduce((latest, metric) => {
			const timestamp = new Date(metric.calculated_at).getTime();
			return timestamp > latest ? timestamp : latest;
		}, 0);

		return {
			totalMetrics: metrics.length,
			totalCharts: chartMetrics.length,
			totalKPIs: kpiMetrics.length,
			lastUpdated:
				latestTimestamp > 0
					? new Date(latestTimestamp).toLocaleString()
					: "Never",
			chartTypes,
		};
	}
}

export const muiDashboardService = new MUIDashboardService();
export default muiDashboardService;
