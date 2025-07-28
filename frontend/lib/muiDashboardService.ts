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

		// For table type
		table_data?: any[][];
		table_columns?: string[];
		table_config?: {
			sortable?: boolean;
			filterable?: boolean;
			pagination?: boolean;
		};

		// For kpi type
		value?: string;
		trend?: {
			value: string;
			isPositive: boolean;
			percentage?: string;
			direction?: string;
		};
		kpi_id?: string;
	};
	metric_type: "chart_data" | "kpi" | "table";
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

export interface MUITableData {
	id: string;
	title: string;
	subtitle: string;
	data: any[][];
	columns: string[];
	config?: {
		sortable?: boolean;
		filterable?: boolean;
		pagination?: boolean;
	};
}

export interface MUIBusinessInsights {
	insights: string[];
	recommendations: string[];
	dataQualityScore: number;
	confidenceLevel: number;
	businessType: string;
	industrySector: string;
}

export interface MUIDashboardData {
	kpis: MUIStatCardData[];
	pieCharts: MUIChartData[];
	barCharts: MUIChartData[];
	lineCharts: MUIChartData[];
	radarCharts: MUIChartData[];
	radialCharts: MUIChartData[];
	areaCharts: MUIChartData[];
	tables: MUITableData[];
	businessInsights?: MUIBusinessInsights;
	totalMetrics: number;
	lastUpdated: string;
}

// Simple mapping for available MUI chart types
const MUI_CHART_MAP: Record<string, string> = {
	// Backend chart types to MUI chart types
	"pie": "PieChart",
	"bar": "BarChart", 
	"line": "LineChart",
	"area": "AreaChart",
	"radar": "RadarChart",
	"radial": "RadialChart",
	
	// Legacy chart types
	BarChartOne: "BarChart",
	LineChartOne: "LineChart",
};

class MUIDashboardService {
	private cache: Map<string, { data: BackendMetric[]; timestamp: number }> =
		new Map();
	private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

	// Fetch metrics from backend (NEW STANDARDIZED FORMAT)
	async fetchMetrics(): Promise<{ metrics: BackendMetric[]; originalResponse: any }> {
		const cacheKey = "dashboard_metrics";
		const cached = this.cache.get(cacheKey);

		if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
			console.log("📊 Using cached dashboard metrics");
			return { metrics: cached.data, originalResponse: null };
		}

		// Simple timeout handling with fallback
		try {
			console.log("🔄 Fetching fresh dashboard metrics from backend (NEW FORMAT)");
			console.log("🌐 API call to:", "/dashboard/metrics");
			
			// Use a simple timeout promise
			const timeoutPromise = new Promise((_, reject) => {
				setTimeout(() => reject(new Error("Request timeout")), 450000); // 45 seconds
			});
			
			const fetchPromise = api.get("/dashboard/metrics", {
				timeout: 6000000 // 60 seconds explicitly set
			});
			
			const response = await Promise.race([fetchPromise, timeoutPromise]) as any;
			console.log("📡 API Response status:", response.status);

			// Handle new standardized response format
			const standardizedResponse = response.data;
			console.log(
				"📊 Received standardized response:",
				standardizedResponse.client_id,
				standardizedResponse.total_records
			);

			// Check if we have the expected data structure
			if (!standardizedResponse.llm_analysis) {
				console.warn(
					"⚠️ Backend returned response without llm_analysis"
				);
				return { metrics: [], originalResponse: standardizedResponse };
			}

			// Convert standardized format back to legacy format for compatibility
			const metrics = this.convertStandardizedToLegacy(standardizedResponse);

			// Cache the results
			this.cache.set(cacheKey, {
				data: metrics,
				timestamp: Date.now(),
			});

			console.log(
				`✅ Successfully processed ${metrics.length} metrics from backend`
			);

			return { metrics, originalResponse: standardizedResponse };
		} catch (error) {
			console.error("❌ Failed to fetch dashboard metrics:", error);
			throw error;
		}
	}

	// Convert new standardized format to legacy format for compatibility
	private convertStandardizedToLegacy(
		standardizedResponse: any
	): BackendMetric[] {
		const metrics: BackendMetric[] = [];
		
		// Handle the new response format with llm_analysis
		const llmAnalysis = standardizedResponse.llm_analysis;
		if (!llmAnalysis) {
			console.warn("⚠️ No llm_analysis found in response");
			return [];
		}

		try {
			// Convert KPIs to legacy format
			if (llmAnalysis.kpis) {
				console.log(`🔄 Converting ${llmAnalysis.kpis.length} KPIs from standardized format`);
				
				for (const kpi of llmAnalysis.kpis) {
					console.log(`📊 Processing KPI: "${kpi.display_name}"`, {
						value: kpi.value,
						trend: kpi.trend,
						format: kpi.format
					});

					// Map trend direction from backend to frontend format
					const mapTrendDirection = (direction: string): "up" | "down" | "neutral" => {
						switch (direction.toLowerCase()) {
							case "up":
							case "increasing":
								return "up";
							case "down":
							case "decreasing":
								return "down";
							case "stable":
							case "neutral":
							default:
								return "neutral";
						}
					};

					// Format trend value based on percentage
					const formatTrendValue = (trend: any): string => {
						if (trend.percentage === 0) {
							return "0%";
						}
						const sign = trend.percentage > 0 ? "+" : "";
						return `${sign}${trend.percentage}%`;
					};

					// Format the KPI value based on its format type
					const formatKPIValue = (value: string, format: string): string => {
						const numValue = parseFloat(value);
						if (isNaN(numValue)) return value;
						
						switch (format) {
							case "currency":
								return `$${numValue.toLocaleString()}`;
							case "percentage":
								return `${numValue}%`;
							case "number":
							default:
								return numValue.toLocaleString();
						}
					};

					metrics.push({
						metric_id: kpi.id,
						client_id: standardizedResponse.client_id,
						metric_name: kpi.display_name,
						metric_type: "kpi",
						metric_value: {
							value: formatKPIValue(kpi.value, kpi.format),
							title: kpi.display_name,
							trend: {
								value: formatTrendValue(kpi.trend),
								isPositive: kpi.trend.direction === "up" || kpi.trend.percentage > 0,
								percentage: kpi.trend.percentage,
								direction: kpi.trend.direction
							},
							source: "standardized",
						},
						calculated_at: llmAnalysis.metadata?.generated_at || new Date().toISOString(),
					});
				}
			}

			// Convert Charts to legacy format
			if (llmAnalysis.charts) {
				console.log(`🔄 Converting ${llmAnalysis.charts.length} charts from standardized format`);
				
				for (const chart of llmAnalysis.charts) {
					console.log(`📊 Processing chart: "${chart.display_name}"`, {
						chartType: chart.chart_type,
						dataLength: chart.data?.length || 0,
						dataSample: chart.data?.slice(0, 2)
					});

					// Map chart types to MUI chart types
					const mapChartType = (chartType: string): string => {
						switch (chartType.toLowerCase()) {
							case "pie":
								return "PieChart";
							case "bar":
								return "BarChart";
							case "line":
								return "LineChart";
							case "area":
								return "AreaChart";
							default:
								return "BarChart"; // Default fallback
						}
					};

					// Transform chart data to MUI format
					const transformChartData = (data: any[], chartType: string): any[] => {
						if (!data || !Array.isArray(data)) {
							console.warn(`⚠️ Invalid chart data for "${chart.display_name}"`);
							return [];
						}

						console.log(`🔄 Transforming ${data.length} data points for ${chartType} chart`);

						if (chartType.toLowerCase() === "pie") {
							return data.map((item, index) => ({
								id: index,
								value: Number(item.value) || 0,
								label: item.name || `Item ${index}`,
								name: item.name || `Item ${index}`,
								color: this.extractColor(`color-${index}`, index),
							}));
						} else if (chartType.toLowerCase() === "bar") {
							return data.map((item, index) => ({
								name: item.name || `Item ${index}`,
								value: Number(item.value) || 0,
								id: index,
							}));
						} else if (chartType.toLowerCase() === "line") {
							return data.map((item, index) => ({
								name: item.name || `Month ${index}`,
								value: Number(item.value) || 0,
								id: index,
							}));
						} else {
							// Default transformation for other chart types
							return data.map((item, index) => ({
								name: item.name || `Item ${index}`,
								value: Number(item.value) || 0,
								id: index,
							}));
						}
					};

					// Process dropdown options if available
					const processDropdownOptions = (config: any): Array<{ label: string; value: string }> => {
						if (!config?.filters) return [];
						
						const options: Array<{ label: string; value: string }> = [];
						Object.values(config.filters).forEach((filterArray: any) => {
							if (Array.isArray(filterArray)) {
								options.push(...filterArray);
							}
						});
						
						return options;
					};

					const transformedData = transformChartData(chart.data, chart.chart_type);
					const dropdownOptions = processDropdownOptions(chart.config);

					console.log(`✅ Transformed chart data:`, {
						title: chart.display_name,
						type: chart.chart_type,
						dataPoints: transformedData.length,
						dropdownOptions: dropdownOptions.length
					});

					metrics.push({
						metric_id: chart.id,
						client_id: standardizedResponse.client_id,
						metric_name: chart.display_name,
						metric_type: "chart_data",
						metric_value: {
							data: transformedData,
							chart_type: chart.chart_type,
							title: chart.display_name,
							subtitle: `${chart.config?.x_axis?.display_name || "X"} vs ${
								chart.config?.y_axis?.display_name || "Y"
							}`,
							dropdown_options: dropdownOptions,
							has_dropdown: dropdownOptions.length > 0,
							source: "standardized",
						},
						calculated_at: llmAnalysis.metadata?.generated_at || new Date().toISOString(),
					});
				}
			}

			// Convert Tables to legacy format
			if (llmAnalysis.tables) {
				for (const table of llmAnalysis.tables) {
					metrics.push({
						metric_id: table.id,
						client_id: standardizedResponse.client_id,
						metric_name: table.display_name,
						metric_type: "table",
						metric_value: {
							table_data: table.data,
							table_columns: table.columns,
							table_config: table.config,
							title: table.display_name,
							subtitle: `Data table with ${table.data?.length || 0} rows`,
							source: "standardized",
						},
						calculated_at: llmAnalysis.metadata?.generated_at || new Date().toISOString(),
					});
				}
			}

			console.log(
				`🔄 Converted standardized format: ${
					llmAnalysis.kpis?.length || 0
				} KPIs + ${llmAnalysis.charts?.length || 0} charts + ${llmAnalysis.tables?.length || 0} tables = ${
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
				trendPercentage: trend?.percentage,
				trendDirection: trend?.direction,
				isPositive: trend?.isPositive,
				fullMetric: metric,
			});

			// Map trend direction from backend to frontend format
			const mapTrendDirection = (direction: string): "up" | "down" | "neutral" => {
				switch (direction.toLowerCase()) {
					case "up":
					case "increasing":
						return "up";
					case "down":
					case "decreasing":
						return "down";
					case "stable":
					case "neutral":
					default:
						return "neutral";
				}
			};

			// Format trend value based on the trend data from response
			const formatTrendValue = (trend: any): string => {
				if (!trend) return "0%";
				
				// If trend.value is already formatted (like "0%"), use it directly
				if (typeof trend.value === 'string' && trend.value.includes('%')) {
					return trend.value;
				}
				
				// If trend.percentage exists, format it
				if (trend.percentage !== undefined) {
					if (trend.percentage === 0) return "0%";
					const sign = trend.percentage > 0 ? "+" : "";
					return `${sign}${trend.percentage}%`;
				}
				
				return "0%";
			};

			// Use REAL trend data from your backend response
			const trendValue = formatTrendValue(trend);
			const trendDirection = mapTrendDirection(trend?.direction || "stable");

			console.log(
				`🎯 Final KPI result for "${metric.metric_name}":`, {
					value: value,
					trendValue: trendValue,
					trendDirection: trendDirection,
					trendData: trend
				}
			);

			// Generate realistic trend data based on the actual value
			const baseValue = parseFloat(value?.replace(/[$,]/g, "") || "0") || 100;
			const trendPercentage = parseFloat(trend?.percentage?.toString() || "0") || 0;
			
			const trendData = Array.from({ length: 30 }, (_, i) => {
				// Create realistic progression over 30 days
				const dailyChange = 1 + (trendPercentage / 100) * (i / 30);
				const randomFactor = 0.95 + Math.random() * 0.1; // ±5% daily variation
				return Math.round(baseValue * dailyChange * randomFactor);
			});

			return {
				title: metric.metric_name,
				value: value || "0",
				interval: "Current period",
				trend: trendDirection,
				trendValue: trendValue,
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
			const muiChartType = MUI_CHART_MAP[chartType] || "BarChart";

			console.log(`📊 Processing chart: "${metric.metric_value.title}" - Type: ${chartType} -> MUI: ${muiChartType}`);
			console.log(`📊 Chart data:`, metric.metric_value.data);

			const chartData: MUIChartData = {
				id: metric.metric_id,
				title: metric.metric_value.title || "Chart",
				subtitle: metric.metric_value.subtitle || "",
				muiChartType,
				originalChartType: chartType,
				data: metric.metric_value.data || [], // Use data directly - already transformed
				config: this.generateMUIConfig(chartType, muiChartType),
				hasDropdown: metric.metric_value.has_dropdown,
				dropdownOptions: metric.metric_value.dropdown_options,
			};

			console.log(`📊 Final chart data:`, chartData);

			// Categorize charts based on MUI type
			if (muiChartType === "PieChart") {
				categorizedCharts.pieCharts.push(chartData);
				console.log(`✅ Added to pieCharts: ${chartData.title}`);
			} else if (muiChartType === "BarChart") {
				categorizedCharts.barCharts.push(chartData);
				console.log(`✅ Added to barCharts: ${chartData.title}`);
			} else if (muiChartType === "LineChart") {
				categorizedCharts.lineCharts.push(chartData);
				console.log(`✅ Added to lineCharts: ${chartData.title}`);
			} else if (muiChartType === "AreaChart") {
				categorizedCharts.areaCharts.push(chartData);
				console.log(`✅ Added to areaCharts: ${chartData.title}`);
			} else if (muiChartType === "RadarChart") {
				categorizedCharts.radarCharts.push(chartData);
				console.log(`✅ Added to radarCharts: ${chartData.title}`);
			} else if (muiChartType === "RadialChart") {
				categorizedCharts.radialCharts.push(chartData);
				console.log(`✅ Added to radialCharts: ${chartData.title}`);
			}
		});

		console.log(`📊 Final categorized charts:`, {
			pieCharts: categorizedCharts.pieCharts.length,
			barCharts: categorizedCharts.barCharts.length,
			lineCharts: categorizedCharts.lineCharts.length,
			areaCharts: categorizedCharts.areaCharts.length,
			radarCharts: categorizedCharts.radarCharts.length,
			radialCharts: categorizedCharts.radialCharts.length,
		});

		return categorizedCharts;
	}

	// Convert backend table metrics to MUI table format
	convertToMUITables(metrics: BackendMetric[]): MUITableData[] {
		const tableMetrics = metrics.filter((m) => m.metric_type === "table");
		console.log(`📋 Converting ${tableMetrics.length} table metrics to MUI format`);

		return tableMetrics.map((metric) => {
			console.log(`📊 Processing table: "${metric.metric_name}"`, {
				rows: metric.metric_value.table_data?.length || 0,
				columns: metric.metric_value.table_columns?.length || 0,
			});

			return {
				id: metric.metric_id,
				title: metric.metric_value.title || metric.metric_name,
				subtitle: metric.metric_value.subtitle || "",
				data: metric.metric_value.table_data || [],
				columns: metric.metric_value.table_columns || [],
				config: metric.metric_value.table_config || {
					sortable: true,
					filterable: true,
					pagination: true,
				},
			};
		});
	}

	// Extract business insights from the response
	extractBusinessInsights(standardizedResponse: any): MUIBusinessInsights | undefined {
		const businessAnalysis = standardizedResponse.llm_analysis?.business_analysis;
		if (!businessAnalysis) {
			console.log("⚠️ No business analysis found in response");
			return undefined;
		}

		console.log("📊 Extracting business insights:", {
			businessType: businessAnalysis.business_type,
			industrySector: businessAnalysis.industry_sector,
			insightsCount: businessAnalysis.business_insights?.length || 0,
			recommendationsCount: businessAnalysis.recommendations?.length || 0,
		});

		return {
			insights: businessAnalysis.business_insights || [],
			recommendations: businessAnalysis.recommendations || [],
			dataQualityScore: businessAnalysis.data_quality_score || 0,
			confidenceLevel: businessAnalysis.confidence_level || 0,
			businessType: businessAnalysis.business_type || "unknown",
			industrySector: businessAnalysis.industry_sector || "unknown",
		};
	}

	// Transform backend data format to MUI chart format
	private transformDataForMUI(
		data: any[],
		muiChartType: string,
		title: string
	): any[] {
		if (!data || data.length === 0) return [];

		console.log(`🔄 Transforming data for ${muiChartType}:`, data);

		// For the new response format, data is already in the correct format
		// Just ensure we have the right field names for MUI charts
		switch (muiChartType) {
			case "PieChart":
				return data.map((item, index) => ({
					id: index,
					value: Number(item.value) || 0,
					label: item.name || `Item ${index}`,
					color: this.extractColor(`color-${index}`, index),
				}));

			case "BarChart":
				return data.map((item, index) => ({
					name: item.name || `Item ${index}`,
					value: Number(item.value) || 0,
					id: index,
				}));

			case "LineChart":
				return data.map((item, index) => ({
					month: item.name || `Month ${index}`,
					value: Number(item.value) || 0,
					id: index,
				}));

			case "AreaChart":
				return data.map((item, index) => ({
					name: item.name || `Item ${index}`,
					value: Number(item.value) || 0,
					id: index,
				}));

			default:
				return data.map((item, index) => ({
					...item,
					value: Number(item.value) || 0,
					name: item.name || `Item ${index}`,
				}));
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
			tables: [], // No fake tables
			totalMetrics: 0,
			lastUpdated: "No data available",
		};
	}

	// Main function to process all metrics into MUI dashboard format
	async processMUIMetrics(): Promise<MUIDashboardData> {
		try {
			console.log("🚀 Starting MUI dashboard data processing");
			const { metrics, originalResponse } = await this.fetchMetrics();

			console.log("🚨 CRITICAL DEBUG - Raw metrics received:", {
				totalMetrics: metrics.length,
				hasOriginalResponse: !!originalResponse,
				originalResponseKeys: originalResponse ? Object.keys(originalResponse) : []
			});

			if (metrics.length === 0) {
				console.warn("⚠️ No metrics found, using fallback data");
				return this.generateFallbackData();
			}

			// Debug each metric type
			const kpiMetrics = metrics.filter((m) => m.metric_type === "kpi");
			const chartMetrics = metrics.filter((m) => m.metric_type === "chart_data");
			const tableMetrics = metrics.filter((m) => m.metric_type === "table");

			console.log("🚨 CRITICAL DEBUG - Metric breakdown:", {
				kpis: kpiMetrics.length,
				charts: chartMetrics.length,
				tables: tableMetrics.length
			});

			// Debug KPI metrics
			if (kpiMetrics.length > 0) {
				console.log("🚨 CRITICAL DEBUG - KPI Metrics:", kpiMetrics.map(kpi => ({
					id: kpi.metric_id,
					name: kpi.metric_name,
					value: kpi.metric_value.value,
					trend: kpi.metric_value.trend
				})));
			}

			// Debug Chart metrics
			if (chartMetrics.length > 0) {
				console.log("🚨 CRITICAL DEBUG - Chart Metrics:", chartMetrics.map(chart => ({
					id: chart.metric_id,
					name: chart.metric_name,
					type: chart.metric_value.chart_type,
					dataLength: chart.metric_value.data?.length || 0
				})));
			}

			const kpis = this.convertToStatCards(metrics);
			const charts = this.convertToMUICharts(metrics);
			const tables = this.convertToMUITables(metrics);
			const businessInsights = this.extractBusinessInsights(originalResponse);

			const result = {
				kpis,
				...charts,
				tables,
				businessInsights,
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
				tables: result.tables.length,
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
		totalTables: number;
		lastUpdated: string;
		chartTypes: Record<string, number>;
	} {
		const chartMetrics = metrics.filter((m) => m.metric_type === "chart_data");
		const kpiMetrics = metrics.filter((m) => m.metric_type === "kpi");
		const tableMetrics = metrics.filter((m) => m.metric_type === "table");

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
			totalTables: tableMetrics.length,
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
