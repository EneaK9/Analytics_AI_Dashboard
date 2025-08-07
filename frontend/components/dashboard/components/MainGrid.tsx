import * as React from "react";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Copyright from "../internals/components/Copyright";
import ChartUserByCountry from "./ChartUserByCountry";
import BusinessDataTable from "./BusinessDataTable";
import HighlightedCard from "./HighlightedCard";
import RevenueTrendsChart from "./RevenueTrendsChart";
import SalesCategoryChart from "./SalesCategoryChart";
import StatCard, { StatCardProps } from "./StatCard";
import { DateRange } from "./CustomDatePicker";
import api from "../../../lib/axios";
import {
	MUIDashboardData,
	BackendMetric,
	MUITableData,
} from "../../../lib/muiDashboardService";

// Import various chart components
import * as Charts from "../../charts";

// Import MUI X Charts
import { LineChart } from "@mui/x-charts/LineChart";
import { PieChart } from "@mui/x-charts/PieChart";
import { BarChart } from "@mui/x-charts/BarChart";

// Chart data validation function for LLM response format
// Helper function to format KPI values based on format type (shared between components)
const formatKPIValue = (value: any, format: string): string => {
	// Handle object format (e.g., status distributions, breakdowns)
	if (format === "object" && typeof value === "object" && value !== null) {
		const entries = Object.entries(value);

		// Calculate total if all values are numbers
		const total = entries.reduce((sum, [key, val]) => {
			const num = typeof val === "number" ? val : parseFloat(String(val));
			return !isNaN(num) ? sum + num : sum;
		}, 0);

		// Show total with breakdown hint
		const breakdown = entries.map(([key, val]) => `${key}: ${val}`).join(", ");
		return `${total} total (${breakdown})`;
	}

	const numValue = parseFloat(value);
	if (
		isNaN(numValue) ||
		numValue === null ||
		numValue === undefined ||
		value === null ||
		value === undefined
	) {
		// Return safe string representation if value can't be parsed as number
		return String(value || "0");
	}

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

const isValidChartData = (chartData: any) => {
	if (!chartData) {
		console.log("❌ isValidChartData: No chartData provided");
		return false;
	}

	console.log("🔍 isValidChartData checking:", {
		hasData: !!chartData.data,
		dataType: Array.isArray(chartData.data) ? "array" : typeof chartData.data,
		dataLength: chartData.data?.length,
		hasLabels: !!chartData.labels,
		labelsType: Array.isArray(chartData.labels)
			? "array"
			: typeof chartData.labels,
		labelsLength: chartData.labels?.length,
		firstDataItem: chartData.data?.[0],
		firstLabel: chartData.labels?.[0],
		hasConfig: !!chartData.config,
	});

	// Check for transformed format first (labels + data arrays)
	if (
		chartData.labels &&
		Array.isArray(chartData.labels) &&
		chartData.data &&
		Array.isArray(chartData.data)
	) {
		const hasValidLabels =
			chartData.labels.length > 0 &&
			chartData.labels.every((label: any) => label != null);

		const hasValidData =
			chartData.data.length > 0 &&
			chartData.data.every(
				(value: any) => value != null && !isNaN(Number(value))
			);

		const sameLength = chartData.labels.length === chartData.data.length;

		const isValid = hasValidLabels && hasValidData && sameLength;
		console.log("✅ Transformed format validation:", {
			hasValidLabels,
			hasValidData,
			sameLength,
			isValid,
		});
		return isValid;
	}

	// Check if it's LLM format with data array of objects
	if (
		chartData.data &&
		Array.isArray(chartData.data) &&
		chartData.data.length > 0
	) {
		// For LLM format: validate that data array contains objects with field values
		const hasValidDataObjects = chartData.data.every((item: any) => {
			if (!item || typeof item !== "object") return false;

			// Get field names from config or use defaults
			const xField = chartData.config?.x_axis?.field || "name";
			const yField = chartData.config?.y_axis?.field || "value";

			// Check if the item has the required fields
			const hasXField = item[xField] != null;
			const hasYField = item[yField] != null && !isNaN(Number(item[yField]));

			return hasXField && hasYField;
		});

		console.log("✅ LLM format validation:", { hasValidDataObjects });
		return hasValidDataObjects;
	}

	console.log("❌ No valid format detected");
	return false;
};

// Default data for main dashboard (fallback when no dynamic data is provided)
const defaultData: StatCardProps[] = [
	{
		title: "Users",
		value: "14k",
		interval: "Last 30 days",
		trend: "up",
		data: [
			200, 24, 220, 260, 240, 380, 100, 240, 280, 240, 300, 340, 320, 360, 340,
			380, 360, 400, 380, 420, 400, 640, 340, 460, 440, 480, 460, 600, 880, 920,
		],
	},
	{
		title: "Conversions",
		value: "325",
		interval: "Last 30 days",
		trend: "down",
		data: [
			1640, 1250, 970, 1130, 1050, 900, 720, 1080, 900, 450, 920, 820, 840, 600,
			820, 780, 800, 760, 380, 740, 660, 620, 840, 500, 520, 480, 400, 360, 300,
			220,
		],
	},
	{
		title: "Event count",
		value: "200k",
		interval: "Last 30 days",
		trend: "neutral",
		data: [
			500, 400, 510, 530, 520, 600, 530, 520, 510, 730, 520, 510, 530, 620, 510,
			530, 520, 410, 530, 520, 610, 530, 520, 610, 530, 420, 510, 430, 520, 510,
		],
	},
];

interface MainGridProps {
	dashboardData?: {
		users: number;
		conversions: number;
		eventCount: number;
		sessions: number;
		pageViews?: number;
		// New fields for real client data
		totalRecords?: number;
		dataPoints?: number;
		processingRate?: string;
		lastUpdated?: string;
	};
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
	dashboardType?: string;
	dateRange?: DateRange;
}

interface DashboardConfig {
	title: string;
	subtitle: string;
	kpi_widgets: KPIWidget[];
	chart_widgets: ChartWidget[];
}

interface KPIWidget {
	id: string;
	title: string;
	value: string;
	subtitle: string;
	trend: "up" | "down" | "stable";
	data: number[];
	position: { row: number; col: number };
	size: { width: number; height: number };
}

interface ChartWidget {
	id: string;
	title: string;
	subtitle: string;
	chart_type: string;
	position: { row: number; col: number };
	size: { width: number; height: number };
	config: any;
}

export default function MainGrid({
	dashboardData,
	user,
	dashboardType = "main",
	dateRange,
}: MainGridProps) {
	// Route to the appropriate dashboard template
	// Main dashboard uses the original OriginalMainGrid with rich LLM analysis
	if (dashboardType === "main") {
		return (
			<OriginalMainGrid
				dashboardData={dashboardData}
				user={user}
				dateRange={dateRange}
			/>
		);
	}

	// For other dashboard types, use the dynamic template system
	return (
		<TemplateDashboard
			dashboardData={dashboardData}
			user={user}
			dashboardType={dashboardType}
			dateRange={dateRange}
		/>
	);
}

// Original Main Dashboard Component - Uses REAL BACKEND DATA
function OriginalMainGrid({
	dashboardData,
	user,
	dateRange,
}: {
	dashboardData?: MainGridProps["dashboardData"];
	user?: { client_id: string; company_name: string; email: string };
	dateRange?: { start: any; end: any; label?: string };
}) {
	const [llmAnalysis, setLlmAnalysis] = React.useState<any>(null);
	const [clientData, setClientData] = React.useState<any[]>([]);
	const [dataColumns, setDataColumns] = React.useState<any[]>([]);
	const [loading, setLoading] = React.useState(true);
	const [error, setError] = React.useState<string | null>(null);
	const [isLoadingDateFilter, setIsLoadingDateFilter] = React.useState(false);

	// State for chart dropdown selections
	const [chartDropdownSelections, setChartDropdownSelections] = React.useState<{
		[chartId: string]: string;
	}>({});

	// Date filtering for main dashboard
	const loadDateFilteredData = React.useCallback(async () => {
		if (
			!user?.client_id ||
			!dateRange ||
			(!dateRange.start && !dateRange.end)
		) {
			console.log("🏠 No date filter applied - using regular data");
			return;
		}

		console.log("📅 Loading date-filtered data for main dashboard:", {
			start: dateRange.start?.format
				? dateRange.start.format("YYYY-MM-DD")
				: dateRange.start,
			end: dateRange.end?.format
				? dateRange.end.format("YYYY-MM-DD")
				: dateRange.end,
			label: dateRange.label,
		});

		setIsLoadingDateFilter(true);

		try {
			const params = new URLSearchParams();
			params.append("fast_mode", "true");

			if (dateRange.start) {
				const startDate = dateRange.start?.format
					? dateRange.start.format("YYYY-MM-DD")
					: dateRange.start;
				params.append("start_date", startDate);
			}
			if (dateRange.end) {
				const endDate = dateRange.end?.format
					? dateRange.end.format("YYYY-MM-DD")
					: dateRange.end;
				params.append("end_date", endDate);
			}

			const response = await api.get(`/dashboard/metrics?${params.toString()}`);

			if (response.data && response.data.llm_analysis) {
				console.log("✅ Date-filtered main dashboard data loaded");
				setLlmAnalysis(response.data.llm_analysis);
			} else {
				console.error("❌ No LLM analysis in date-filtered response");
			}
		} catch (error) {
			console.error("❌ Error loading date-filtered data:", error);
			setError("Failed to load date-filtered data");
		} finally {
			setIsLoadingDateFilter(false);
		}
	}, [user?.client_id, dateRange]);

	// Trigger date filtering when dateRange changes
	React.useEffect(() => {
		if (dateRange && (dateRange.start || dateRange.end)) {
			console.log(
				"🗓️ Main dashboard: Date range changed, loading filtered data"
			);
			loadDateFilteredData();
		}
	}, [dateRange, loadDateFilteredData]);

	// Helper function to get trend direction icon and color
	const getTrendDisplay = (trend: any) => {
		if (!trend || !trend.direction) return null;

		const direction = trend.direction.toLowerCase();
		const percentage = trend.percentage || "0%";

		switch (direction) {
			case "up":
			case "increasing":
				return { icon: "↗️", color: "success.main", direction: "up" as const };
			case "down":
			case "decreasing":
				return { icon: "↘️", color: "error.main", direction: "down" as const };
			case "stable":
			case "neutral":
			default:
				return {
					icon: "→",
					color: "text.secondary",
					direction: "neutral" as const,
				};
		}
	};

	// Handle dropdown change for charts
	const handleDropdownChange = (chartId: string, value: string) => {
		setChartDropdownSelections((prev) => ({
			...prev,
			[chartId]: value,
		}));
	};

	// Fetch client data using the EXACT same approach as template dashboard
	const loadClientData = React.useCallback(async () => {
		if (!user?.client_id) return;

		try {
			setLoading(true);

			// Use the SAME API call as template dashboard
			const clientDataResponse = await api.post(
				`/dashboard/generate-template?template_type=main&force_regenerate=false`
			);

			if (clientDataResponse.data.success) {
				setClientData(clientDataResponse.data.client_data || []);
				setDataColumns(clientDataResponse.data.data_columns || []);
				console.log("✅ Client data loaded for main dashboard:", {
					records: clientDataResponse.data.client_data?.length || 0,
					columns: clientDataResponse.data.data_columns?.length || 0,
				});
			}
		} catch (error) {
			console.error("❌ Error loading client data, trying fallback:", error);
			// Use EXACT same fallback as template dashboard
			try {
				const fallbackResponse = await api.get(`/data/${user.client_id}`);
				if (fallbackResponse.data) {
					// Handle different response structures
					const responseData =
						fallbackResponse.data.data || fallbackResponse.data;
					if (Array.isArray(responseData)) {
						setClientData(responseData.slice(0, 100));
						if (responseData.length > 0) {
							setDataColumns(Object.keys(responseData[0]));
						}
						console.log(
							"✅ Fallback client data loaded for main dashboard:",
							responseData.length,
							"rows"
						);
					}
				}
			} catch (fallbackError) {
				console.error("❌ Fallback failed:", fallbackError);
				setClientData([]);
				setDataColumns([]);
			}
		}
	}, [user?.client_id]);

	// Fetch REAL BACKEND DATA for main dashboard with AI-POWERED CUSTOM TEMPLATES
	React.useEffect(() => {
		const fetchRealData = async () => {
			try {
				console.log(
					"🚀 Loading AI-POWERED custom dashboard with intelligent analysis"
				);

				// 🚀 Load rich LLM analysis for main dashboard (with fallback)
				console.log("🔗 Loading main dashboard with rich LLM analysis");

				// Load rich LLM analysis for main dashboard (cached when possible)
				const endpoint = "/dashboard/metrics?fast_mode=true";
				console.log(`🔗 Calling LLM endpoint: ${endpoint}`);
				const response = await api.get(endpoint);

				if (response.data && response.data.llm_analysis) {
					const analysis = response.data.llm_analysis;

					console.log("🚨 CRITICAL DEBUG - LLM Analysis received:", {
						hasKpis: !!analysis.kpis,
						kpisCount: analysis.kpis?.length || 0,
						hasCharts: !!analysis.charts,
						chartsCount: analysis.charts?.length || 0,
						hasTables: !!analysis.tables,
						tablesCount: analysis.tables?.length || 0,
						hasBusinessAnalysis: !!analysis.business_analysis,
					});

					// Debug KPIs
					if (analysis.kpis && analysis.kpis.length > 0) {
						console.log(
							"📈 KPI Data:",
							analysis.kpis.map((kpi: any) => ({
								display_name: kpi.display_name,
								value: kpi.value,
								format: kpi.format,
								trend: kpi.trend,
							}))
						);
					} else {
						console.warn("⚠️ NO KPIs found in llm_analysis!");
					}

					// Debug Charts
					if (analysis.charts && analysis.charts.length > 0) {
						console.log(
							"📊 Chart Data:",
							analysis.charts.map((chart: any) => ({
								display_name: chart.display_name,
								chart_type: chart.chart_type,
								dataLength: chart.data?.length || 0,
								dataSample: chart.data?.slice(0, 2),
							}))
						);
					} else {
						console.warn("⚠️ NO Charts found in llm_analysis!");
					}

					// Debug Tables
					if (analysis.tables && analysis.tables.length > 0) {
						console.log(
							"📋 Table Data:",
							analysis.tables.map((table: any) => ({
								display_name: table.display_name,
								columnsCount: table.columns?.length || 0,
								rowsCount: table.data?.length || 0,
							}))
						);
					} else {
						console.warn("⚠️ NO Tables found in llm_analysis!");
					}

					setLlmAnalysis(analysis);
					setError(null);
				} else {
					console.error("❌ No llm_analysis found in response");
					setError("No analysis data available");
					setLlmAnalysis(null);
				}

				// Load client data using the SAME method as template dashboard
				await loadClientData();
			} catch (error) {
				console.error("❌ CRITICAL ERROR loading dashboard data:", error);
				setError("Failed to load dashboard data");
				setLlmAnalysis(null);
			} finally {
				setLoading(false);
			}
		};

		fetchRealData();
	}, [loadClientData]);

	if (loading) {
		return (
			<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
				<Typography component="h2" variant="h6" sx={{ mb: 2 }}>
					Loading Analytics Dashboard...
				</Typography>
				<Grid container spacing={2} columns={12}>
					{Array.from({ length: 4 }).map((_, index) => (
						<Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
							<Card sx={{ height: 150, bgcolor: "grey.100" }}>
								<CardContent>
									<Typography>Loading...</Typography>
								</CardContent>
							</Card>
						</Grid>
					))}
				</Grid>
			</Box>
		);
	}

	if (error) {
		return (
			<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
				<Card sx={{ bgcolor: "error.light", color: "error.contrastText" }}>
					<CardContent sx={{ textAlign: "center", py: 4 }}>
						<Typography variant="h6" sx={{ mb: 1 }}>
							❌ Dashboard Error
						</Typography>
						<Typography variant="body2">{error}</Typography>
					</CardContent>
				</Card>
			</Box>
		);
	}

	return (
		<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
			{/* Date Filter Indicators for Main Dashboard */}
			{isLoadingDateFilter && (
				<Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
					<Typography
						variant="caption"
						color="primary"
						sx={{ fontWeight: 500 }}>
						🗓️ Loading data for selected date range...
					</Typography>
				</Box>
			)}

			{dateRange && (dateRange.start || dateRange.end) && (
				<Box sx={{ mb: 3 }}>
					<Typography
						variant="caption"
						sx={{
							color: "info.main",
							bgcolor: "info.light",
							px: 1.5,
							py: 0.5,
							borderRadius: 1,
							fontWeight: 500,
						}}>
						📅 Data Filtered: {dateRange.label || "Custom Range"}
						{dateRange.start && dateRange.end && (
							<span style={{ opacity: 0.8 }}>
								{" "}
								(
								{dateRange.start?.format
									? dateRange.start.format("MMM DD")
									: dateRange.start}{" "}
								-{" "}
								{dateRange.end?.format
									? dateRange.end.format("MMM DD, YYYY")
									: dateRange.end}
								)
							</span>
						)}
					</Typography>
				</Box>
			)}

			{/* Business Insights Section - Only if available */}
			{llmAnalysis?.business_analysis && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					<Grid size={{ xs: 12 }}>
						<Card
							sx={{
								background:
									"linear-gradient(135deg,rgb(134, 136, 139) 0%,rgb(140, 180, 213) 100%)",
								color: "white",
								boxShadow: "0 4px 20px rgba(25, 118, 210, 0.3)",
							}}>
							<CardHeader
								title={
									<Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
										<Typography variant="h5" sx={{ fontWeight: 600 }}>
											💡 Business Insights & Recommendations
										</Typography>
									</Box>
								}
								sx={{ color: "inherit", pb: 1 }}
							/>
							<CardContent sx={{ pt: 0 }}>
								<Grid container spacing={3}>
									{llmAnalysis.business_analysis.business_insights && (
										<Grid size={{ xs: 12, md: 6 }}>
											<Card
												sx={{
													bgcolor: "rgba(255, 255, 255, 0.1)",
													backdropFilter: "blur(10px)",
													border: "1px solid rgba(255, 255, 255, 0.2)",
												}}>
												<CardHeader
													title={
														<Typography
															variant="h6"
															sx={{ color: "white", fontWeight: 600 }}>
															🔍 Key Insights
														</Typography>
													}
													sx={{ pb: 1 }}
												/>
												<CardContent sx={{ pt: 0 }}>
													<Box component="ul" sx={{ pl: 2, m: 0 }}>
														{llmAnalysis.business_analysis.business_insights.map(
															(insight: string, index: number) => (
																<Typography
																	key={index}
																	component="li"
																	variant="body2"
																	sx={{
																		mb: 2,
																		color: "white",
																		opacity: 0.95,
																		lineHeight: 1.6,
																		padding: "8px 12px",
																		borderRadius: "6px",
																		bgcolor: "rgba(255, 255, 255, 0.05)",
																		border:
																			"1px solid rgba(255, 255, 255, 0.1)",
																		"&::marker": {
																			color: "rgba(255, 255, 255, 0.8)",
																			fontWeight: "bold",
																		},
																		"&:hover": {
																			bgcolor: "rgba(255, 255, 255, 0.1)",
																			transition: "background-color 0.2s ease",
																		},
																	}}>
																	{insight}
																</Typography>
															)
														)}
													</Box>
												</CardContent>
											</Card>
										</Grid>
									)}
									{llmAnalysis.business_analysis.recommendations && (
										<Grid size={{ xs: 12, md: 6 }}>
											<Card
												sx={{
													bgcolor: "rgba(255, 255, 255, 0.1)",
													backdropFilter: "blur(10px)",
													border: "1px solid rgba(255, 255, 255, 0.2)",
												}}>
												<CardHeader
													title={
														<Typography
															variant="h6"
															sx={{ color: "white", fontWeight: 600 }}>
															🚀 Recommendations
														</Typography>
													}
													sx={{ pb: 1 }}
												/>
												<CardContent sx={{ pt: 0 }}>
													<Box component="ul" sx={{ pl: 2, m: 0 }}>
														{llmAnalysis.business_analysis.recommendations.map(
															(recommendation: string, index: number) => (
																<Typography
																	key={index}
																	component="li"
																	variant="body2"
																	sx={{
																		mb: 2,
																		color: "white",
																		opacity: 0.95,
																		lineHeight: 1.6,
																		padding: "8px 12px",
																		borderRadius: "6px",
																		bgcolor: "rgba(255, 255, 255, 0.05)",
																		border:
																			"1px solid rgba(255, 255, 255, 0.1)",
																		"&::marker": {
																			color: "rgba(255, 255, 255, 0.8)",
																			fontWeight: "bold",
																		},
																		"&:hover": {
																			bgcolor: "rgba(255, 255, 255, 0.1)",
																			transition: "background-color 0.2s ease",
																		},
																	}}>
																	{recommendation}
																</Typography>
															)
														)}
													</Box>
												</CardContent>
											</Card>
										</Grid>
									)}
								</Grid>
							</CardContent>
						</Card>
					</Grid>
				</Grid>
			)}

			{/* KPI Cards - Only render if kpis array exists and has items */}
			{llmAnalysis?.kpis && llmAnalysis.kpis.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{llmAnalysis.kpis.map((kpi: any, index: number) => {
						const trendDisplay = getTrendDisplay(kpi.trend);

						return (
							<Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
								<StatCard
									title={kpi.display_name}
									value={formatKPIValue(kpi.value, kpi.format)}
									interval={kpi.trend.description}
									trend={kpi.trend.direction || "neutral"}
									trendValue={
										kpi.trend?.percentage ? `${kpi.trend.percentage}%` : "0%"
									}
									data={Array.from(
										{ length: 30 },
										() => parseFloat(kpi.value) || 0
									)}
								/>
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* Charts - Only render if charts array exists and has items */}
			{llmAnalysis?.charts && llmAnalysis.charts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{llmAnalysis.charts.map((chart: any, index: number) => {
						// Skip if no data or invalid chart type
						if (
							!chart.data ||
							!Array.isArray(chart.data) ||
							chart.data.length === 0
						) {
							return null;
						}

						const chartId = `chart-${index}`;
						const selectedValue = chartDropdownSelections[chartId] || "all";

						// Filter data based on dropdown selection if filters exist
						let filteredData = chart.data;
						if (chart.config?.filters && selectedValue !== "all") {
							filteredData = chart.data.filter((item: any) => {
								const itemName = item.name || item.id || "";
								return (
									itemName
										.toLowerCase()
										.includes(selectedValue.toLowerCase()) ||
									itemName === selectedValue ||
									item.id === selectedValue
								);
							});
						}

						// Render based on chart type
						switch (chart.chart_type?.toLowerCase()) {
							case "pie":
								return (
									<Grid key={index} size={{ xs: 12, md: 4 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle={
													chart.config?.x_axis?.display_name &&
													chart.config?.y_axis?.display_name
														? `${chart.config.x_axis.display_name} vs ${chart.config.y_axis.display_name}`
														: "Data visualization"
												}
												action={
													chart.config?.filters && (
														<FormControl size="small" sx={{ minWidth: 120 }}>
															<InputLabel id={`chart-dropdown-${chartId}`}>
																Filter
															</InputLabel>
															<Select
																labelId={`chart-dropdown-${chartId}`}
																value={selectedValue}
																label="Filter"
																onChange={(e) =>
																	handleDropdownChange(chartId, e.target.value)
																}>
																<MenuItem value="all">All</MenuItem>
																{Object.values(chart.config.filters)
																	.flat()
																	.map((option: any) => (
																		<MenuItem
																			key={option.value}
																			value={option.value}>
																			{option.label}
																		</MenuItem>
																	))}
															</Select>
														</FormControl>
													)
												}
											/>
											<CardContent>
												<Box
													sx={{
														height: 300,
														display: "flex",
														justifyContent: "center",
														alignItems: "center",
													}}>
													<PieChart
														series={[
															{
																data: filteredData.map(
																	(item: any, idx: number) => {
																		// Get the actual field names from chart config
																		const xField =
																			chart.config?.x_axis?.field || "name";
																		const yField =
																			chart.config?.y_axis?.field || "value";

																		return {
																			id: item.id || idx,
																			value: Number(
																				item[yField] || item.value || 0
																			),
																			label: String(
																				item[xField] ||
																					item.name ||
																					`Item ${idx}`
																			),
																		};
																	}
																),
																valueFormatter: (value: any) => {
																	// Handle case where value might be an object
																	const actualValue =
																		typeof value === "object" && value !== null
																			? value.value || value
																			: value;

																	if (actualValue == null) return "0";
																	if (
																		typeof actualValue === "number" &&
																		actualValue > 100
																	) {
																		return `$${actualValue.toLocaleString()}`;
																	}
																	return actualValue.toString();
																},
															},
														]}
														width={300}
														height={300}
														margin={{
															top: 40,
															bottom: 40,
															left: 40,
															right: 40,
														}}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "bar":
								return (
									<Grid key={index} size={{ xs: 12, md: 6 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle={
													chart.config?.x_axis?.display_name &&
													chart.config?.y_axis?.display_name
														? `${chart.config.x_axis.display_name} vs ${chart.config.y_axis.display_name}`
														: "Data visualization"
												}
												action={
													chart.config?.filters && (
														<FormControl size="small" sx={{ minWidth: 120 }}>
															<InputLabel id={`bar-chart-dropdown-${chartId}`}>
																Filter
															</InputLabel>
															<Select
																labelId={`bar-chart-dropdown-${chartId}`}
																value={selectedValue}
																label="Filter"
																onChange={(e) =>
																	handleDropdownChange(chartId, e.target.value)
																}>
																<MenuItem value="all">All</MenuItem>
																{Object.values(chart.config.filters)
																	.flat()
																	.map((option: any) => (
																		<MenuItem
																			key={option.value}
																			value={option.value}>
																			{option.label}
																		</MenuItem>
																	))}
															</Select>
														</FormControl>
													)
												}
											/>
											<CardContent>
												<Box sx={{ height: 300 }}>
													<BarChart
														dataset={filteredData.map((item: any) => {
															// Get the actual field names from chart config
															const xField =
																chart.config?.x_axis?.field || "name";
															const yField =
																chart.config?.y_axis?.field || "value";

															// Create normalized object with both original and normalized fields
															const normalizedItem = { ...item };
															normalizedItem[xField] = String(
																item[xField] ||
																	item.name ||
																	item.id ||
																	"Unknown"
															);
															normalizedItem[yField] = Number(
																item[yField] || item.value || 0
															);

															return normalizedItem;
														})}
														xAxis={[
															{
																scaleType: "band",
																dataKey: chart.config?.x_axis?.field || "name",
																tickPlacement: "middle",
																tickLabelPlacement: "middle",
															},
														]}
														series={[
															{
																dataKey: chart.config?.y_axis?.field || "value",
																label:
																	chart.config?.y_axis?.display_name || "Value",
																valueFormatter: (value: any) => {
																	// Handle case where value might be an object
																	const actualValue =
																		typeof value === "object" && value !== null
																			? value.value || value
																			: value;

																	if (actualValue == null) return "0";
																	if (
																		typeof actualValue === "number" &&
																		actualValue > 100
																	) {
																		return `$${actualValue.toLocaleString()}`;
																	}
																	return actualValue.toString();
																},
															},
														]}
														width={500}
														height={300}
														margin={{
															top: 20,
															bottom: 60,
															left: 70,
															right: 20,
														}}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "line":
								return (
									<Grid key={index} size={{ xs: 12, md: 6 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle={
													chart.config?.x_axis?.display_name &&
													chart.config?.y_axis?.display_name
														? `${chart.config.x_axis.display_name} vs ${chart.config.y_axis.display_name}`
														: "Data visualization"
												}
												action={
													chart.config?.filters && (
														<FormControl size="small" sx={{ minWidth: 120 }}>
															<InputLabel id={`line-chart-dropdown-${chartId}`}>
																Filter
															</InputLabel>
															<Select
																labelId={`line-chart-dropdown-${chartId}`}
																value={selectedValue}
																label="Filter"
																onChange={(e) =>
																	handleDropdownChange(chartId, e.target.value)
																}>
																<MenuItem value="all">All</MenuItem>
																{Object.values(chart.config.filters)
																	.flat()
																	.map((option: any) => (
																		<MenuItem
																			key={option.value}
																			value={option.value}>
																			{option.label}
																		</MenuItem>
																	))}
															</Select>
														</FormControl>
													)
												}
											/>
											<CardContent>
												<Box sx={{ height: 300 }}>
													<LineChart
														dataset={filteredData.map((item: any) => {
															// Get the actual field names from chart config
															const xField =
																chart.config?.x_axis?.field || "name";
															const yField =
																chart.config?.y_axis?.field || "value";

															// Create normalized object with both original and normalized fields
															const normalizedItem = { ...item };
															normalizedItem[xField] = String(
																item[xField] ||
																	item.name ||
																	item.id ||
																	"Unknown"
															);
															normalizedItem[yField] = Number(
																item[yField] || item.value || 0
															);

															return normalizedItem;
														})}
														xAxis={[
															{
																scaleType: "point",
																dataKey: chart.config?.x_axis?.field || "name",
															},
														]}
														series={[
															{
																dataKey: chart.config?.y_axis?.field || "value",
																label:
																	chart.config?.y_axis?.display_name || "Value",
																curve: "linear",
																valueFormatter: (value: any) => {
																	// Handle case where value might be an object
																	const actualValue =
																		typeof value === "object" && value !== null
																			? value.value || value
																			: value;

																	if (actualValue == null) return "0";
																	if (
																		typeof actualValue === "number" &&
																		actualValue > 100
																	) {
																		return `$${actualValue.toLocaleString()}`;
																	}
																	return actualValue.toString();
																},
															},
														]}
														width={500}
														height={300}
														margin={{
															top: 20,
															bottom: 60,
															left: 70,
															right: 20,
														}}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "radar":
								return (
									<Grid key={index} size={{ xs: 12, md: 6 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle="Multi-dimensional performance analysis"
											/>
											<CardContent>
												<Box sx={{ height: 300 }}>
													<Charts.RadarChart
														data={filteredData}
														title={chart.display_name}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "scatter":
								return (
									<Grid key={index} size={{ xs: 12, md: 6 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle="Correlation and relationship analysis"
											/>
											<CardContent>
												<Box sx={{ height: 300 }}>
													<Charts.ScatterChart
														data={filteredData}
														title={chart.display_name}
														xAxisLabel={
															chart.config?.x_axis?.display_name || "X Axis"
														}
														yAxisLabel={
															chart.config?.y_axis?.display_name || "Y Axis"
														}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "heatmap":
								return (
									<Grid key={index} size={{ xs: 12, md: 8 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle="Pattern and intensity visualization"
											/>
											<CardContent>
												<Box sx={{ height: 300 }}>
													<Charts.HeatmapChart
														data={filteredData}
														title={chart.display_name}
														xAxisLabel={
															chart.config?.x_axis?.display_name || "Categories"
														}
														yAxisLabel={
															chart.config?.y_axis?.display_name || "Metrics"
														}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "radial":
								return (
									<Grid key={index} size={{ xs: 12, md: 4 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle="Progress and completion tracking"
											/>
											<CardContent>
												<Box
													sx={{
														height: 300,
														display: "flex",
														justifyContent: "center",
														alignItems: "center",
													}}>
													<PieChart
														series={[
															{
																data: filteredData
																	.slice(0, 6)
																	.map((item: any, i: number) => {
																		const value = Number(
																			item.value ||
																				item.count ||
																				item.total ||
																				0
																		);
																		return {
																			id: i,
																			value: isNaN(value) ? 0 : value,
																			label: String(
																				item.name ||
																					item.label ||
																					item.category ||
																					`Item ${i + 1}`
																			),
																		};
																	})
																	.filter((item: any) => item.value > 0),
																highlightScope: {
																	fade: "global",
																	highlight: "item",
																} as const,
																innerRadius: 50,
																outerRadius: 100,
															},
														]}
														height={280}
														width={400}
														skipAnimation={true}
														slotProps={{
															noDataOverlay: { message: "No data available" },
														}}
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							case "donut":
								return (
									<Grid key={index} size={{ xs: 12, md: 4 }}>
										<Card>
											<CardHeader
												title={chart.display_name}
												subtitle="Donut chart visualization"
											/>
											<CardContent>
												<Box sx={{ height: 300 }}>
													<Charts.PieChart
														data={filteredData}
														title={chart.display_name}
														chartType="donut"
													/>
												</Box>
											</CardContent>
										</Card>
									</Grid>
								);

							default:
								console.warn(`⚠️ Unknown chart type: ${chart.chart_type}`);
								return null;
						}
					})}
				</Grid>
			)}

			{/* Tables - Only render if tables array exists and has items */}
			{llmAnalysis?.tables && llmAnalysis.tables.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{llmAnalysis.tables.map((table: any, index: number) => {
						// Skip if no columns or data
						if (
							!table.columns ||
							!Array.isArray(table.columns) ||
							!table.data ||
							!Array.isArray(table.data)
						) {
							return null;
						}

						return (
							<Grid key={index} size={{ xs: 12 }}>
								<Card>
									<CardHeader
										title={table.display_name}
										subheader={`${table.data.length} rows of data`}
									/>
									<CardContent>
										<Box sx={{ overflow: "auto", maxHeight: 400 }}>
											<table
												style={{ width: "100%", borderCollapse: "collapse" }}>
												<thead>
													<tr style={{ backgroundColor: "#f5f5f5" }}>
														{table.columns.map(
															(column: string, colIndex: number) => (
																<th
																	key={colIndex}
																	style={{
																		padding: "12px",
																		textAlign: "left",
																		borderBottom: "1px solid #ddd",
																		fontWeight: "bold",
																	}}>
																	{column}
																</th>
															)
														)}
													</tr>
												</thead>
												<tbody>
													{table.data.map((row: any, rowIndex: number) => (
														<tr key={rowIndex}>
															{Array.isArray(row)
																? // Handle array format (row is an array)
																  row.map((cell: any, cellIndex: number) => (
																		<td
																			key={cellIndex}
																			style={{
																				padding: "12px",
																				borderBottom: "1px solid #eee",
																			}}>
																			{String(cell || "-")}
																		</td>
																  ))
																: // Handle object format (row is an object)
																  table.columns.map(
																		(column: string, cellIndex: number) => (
																			<td
																				key={cellIndex}
																				style={{
																					padding: "12px",
																					borderBottom: "1px solid #eee",
																				}}>
																				{String(row[column] || "-")}
																			</td>
																		)
																  )}
														</tr>
													))}
												</tbody>
											</table>
										</Box>
									</CardContent>
								</Card>
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* No Data Message - Only show if no data at all */}
			{(!llmAnalysis ||
				((!llmAnalysis.kpis || llmAnalysis.kpis.length === 0) &&
					(!llmAnalysis.charts || llmAnalysis.charts.length === 0) &&
					(!llmAnalysis.tables || llmAnalysis.tables.length === 0))) && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					<Grid size={{ xs: 12 }}>
						<Card
							sx={{
								bgcolor: "grey.50",
								border: "2px dashed #ccc",
							}}>
							<CardContent sx={{ textAlign: "center", py: 4 }}>
								<Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
									📊 Dashboard Data
								</Typography>
								<Typography variant="body2" color="text.secondary">
									No KPIs, charts, or tables available in the current analysis
								</Typography>
							</CardContent>
						</Card>
					</Grid>
				</Grid>
			)}

			<Copyright sx={{ my: 4 }} />
		</Box>
	);
}

// Template Dashboard Component (for non-main dashboards)
function TemplateDashboard({
	dashboardData,
	user,
	dashboardType,
	dateRange,
}: MainGridProps) {
	const [loading, setLoading] = React.useState(true);
	const [clientData, setClientData] = React.useState<any[]>([]);
	const [dataColumns, setDataColumns] = React.useState<string[]>([]);
	const [aiMetrics, setAiMetrics] = React.useState<any[]>([]);
	const [specializedData, setSpecializedData] = React.useState<any>(null);

	// Frontend cache for date-filtered analyses
	const [analysisCache, setAnalysisCache] = React.useState<Map<string, any>>(
		new Map()
	);
	const [isLoadingWithDateFilter, setIsLoadingWithDateFilter] =
		React.useState(false);

	// Convert new standardized format to legacy format for compatibility
	const convertStandardizedToLegacyFormat = (
		standardizedResponse: any
	): any[] => {
		const metrics: any[] = [];
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
				`🔄 Template - Converted standardized format: ${
					dashboard_data.kpis?.length || 0
				} KPIs + ${dashboard_data.charts?.length || 0} charts = ${
					metrics.length
				} legacy metrics`
			);
			return metrics;
		} catch (error) {
			console.error(
				"❌ Template - Error converting standardized format to legacy:",
				error
			);
			return [];
		}
	};

	const loadClientData = React.useCallback(async () => {
		if (!user?.client_id) return;

		try {
			setLoading(true);

			// Use specialized LLM-powered endpoints for business and performance templates
			if (dashboardType === "business") {
				console.log(
					"🤖 Loading Business Intelligence data with LLM analysis..."
				);
				// Load rich business insights (cached when possible)
				const businessResponse = await api.get(
					"/dashboard/business-insights?fast_mode=true"
				);

				if (businessResponse.data && businessResponse.data.llm_analysis) {
					// Process the LLM analysis data directly
					const analysis = businessResponse.data.llm_analysis;

					// Store specialized business data from LLM analysis
					setSpecializedData({
						type: "business_intelligence",
						config: businessResponse.data.dashboard_config,
						kpis: analysis.kpis || [],
						charts: analysis.charts || [],
						insights: analysis.business_analysis || analysis.insights || {},
						tables: analysis.tables || [],
						llm_analysis: analysis,
					});

					console.log("✅ Business Intelligence LLM data loaded:", {
						kpis: analysis.kpis?.length || 0,
						charts: analysis.charts?.length || 0,
						tables: analysis.tables?.length || 0,
						business_analysis: !!analysis.business_analysis,
					});
				} else {
					console.error("❌ Business Intelligence LLM analysis not available");
				}
			} else if (dashboardType === "performance") {
				console.log("⚡ Loading Performance Hub data with LLM analysis...");
				// Load rich performance insights (cached when possible)
				const performanceResponse = await api.get(
					"/dashboard/performance?fast_mode=true"
				);

				if (performanceResponse.data && performanceResponse.data.llm_analysis) {
					// Process the LLM analysis data directly
					const analysis = performanceResponse.data.llm_analysis;

					// Store specialized performance data from LLM analysis
					setSpecializedData({
						type: "performance_hub",
						config: performanceResponse.data.dashboard_config,
						kpis: analysis.kpis || [],
						charts: analysis.charts || [],
						insights: analysis.business_analysis || analysis.insights || {},
						tables: analysis.tables || [],
						llm_analysis: analysis,
					});

					console.log("✅ Performance Hub LLM data loaded:", {
						kpis: analysis.kpis?.length || 0,
						charts: analysis.charts?.length || 0,
						tables: analysis.tables?.length || 0,
						business_analysis: !!analysis.business_analysis,
					});
				} else {
					console.error("❌ Performance Hub LLM analysis not available");
				}
			} else {
				// Main dashboard - use existing logic
				console.log("🏠 Loading Main dashboard data...");

				// Fetch real client data with proper query parameters
				const clientDataResponse = await api.post(
					`/dashboard/generate-template?template_type=${dashboardType}&force_regenerate=false`
				);

				if (clientDataResponse.data.success) {
					setClientData(clientDataResponse.data.client_data || []);
					setDataColumns(clientDataResponse.data.data_columns || []);
					console.log("✅ Client data loaded:", {
						records: clientDataResponse.data.client_data?.length || 0,
						columns: clientDataResponse.data.data_columns?.length || 0,
						dashboardType,
					});
				}

				// Fetch AI-generated metrics and charts (NEW STANDARDIZED FORMAT)
				try {
					// Call appropriate endpoint based on dashboard type
					let endpoint = "/dashboard/metrics"; // default
					if (dashboardType === "business") {
						endpoint = "/dashboard/business-insights?fast_mode=true";
					} else if (dashboardType === "performance") {
						endpoint = "/dashboard/performance?fast_mode=true";
					}

					console.log(
						`🔗 Calling endpoint: ${endpoint} for dashboard type: ${dashboardType}`
					);
					const metricsResponse = await api.get(endpoint);
					if (metricsResponse.data) {
						// Handle new standardized response format
						const standardizedResponse = metricsResponse.data;

						if (
							standardizedResponse.success &&
							standardizedResponse.dashboard_data
						) {
							// Convert standardized format to legacy format for compatibility
							const legacyMetrics =
								convertStandardizedToLegacyFormat(standardizedResponse);
							setAiMetrics(legacyMetrics);
							console.log(
								"🤖 AI Metrics loaded and converted:",
								legacyMetrics.length
							);
						} else {
							console.warn(
								"⚠️ Backend returned unsuccessful response or no dashboard data"
							);
							setAiMetrics([]);
						}
					}
				} catch (error) {
					console.warn("⚠️ AI metrics not available:", error);
					setAiMetrics([]);
				}
			}
		} catch (error) {
			console.error("❌ Error loading client data:", error);
			// Fallback to basic client data
			try {
				const fallbackResponse = await api.get(`/data/${user.client_id}`);
				if (fallbackResponse.data) {
					// Handle different response structures
					const responseData =
						fallbackResponse.data.data || fallbackResponse.data;
					if (Array.isArray(responseData)) {
						setClientData(responseData.slice(0, 100));
						if (responseData.length > 0) {
							setDataColumns(Object.keys(responseData[0]));
						}
					} else if (responseData && typeof responseData === "object") {
						setClientData([responseData]);
						setDataColumns(Object.keys(responseData));
					}
				}
			} catch (fallbackError) {
				console.error("❌ Fallback data loading failed:", fallbackError);
			}
		} finally {
			setLoading(false);
			console.log("🔄 Loading finished, data state:", {
				clientDataLength: clientData.length,
				dataColumnsLength: dataColumns.length,
				aiMetricsLength: aiMetrics.length,
				loading: false,
			});
		}
	}, [user?.client_id, dashboardType]);

	// Load data on mount and when dependencies change
	React.useEffect(() => {
		loadClientData();
	}, [loadClientData]);

	// Effect to trigger date-filtered analysis when date range changes
	React.useEffect(() => {
		if (dashboardType === "main") {
			// Main dashboard date filtering is handled in OriginalMainGrid
			return;
		}

		if (dateRange && (dateRange.start || dateRange.end)) {
			console.log(
				`📊 ${dashboardType} dashboard: Date filter ignored - showing comprehensive analysis`
			);
		}
	}, [dateRange, dashboardType]);

	// Filter data based on date range
	const getFilteredData = React.useCallback(
		(data: any[]) => {
			if (!dateRange || !data.length) return data;

			return data.filter((item) => {
				const itemDate = new Date(
					item.date || item.created_at || item.timestamp
				);
				const startDate = dateRange.start?.toDate();
				const endDate = dateRange.end?.toDate();

				if (startDate && endDate) {
					return itemDate >= startDate && itemDate <= endDate;
				}
				return true;
			});
		},
		[dateRange]
	);

	// Generate date-aware cache key for analysis caching
	const generateDateAwareCacheKey = React.useCallback(
		(baseKey: string) => {
			if (!dateRange || (!dateRange.start && !dateRange.end)) {
				return `${baseKey}_all_time`;
			}

			const startKey = dateRange.start?.format("YYYY-MM-DD") || "no_start";
			const endKey = dateRange.end?.format("YYYY-MM-DD") || "no_end";
			return `${baseKey}_${startKey}_to_${endKey}`;
		},
		[dateRange]
	);

	// Cache management functions
	const getCachedAnalysis = React.useCallback(
		(cacheKey: string) => {
			const cached = analysisCache.get(cacheKey);
			if (cached && cached.timestamp) {
				// Check if cache is still valid (5 minutes)
				const now = Date.now();
				const cacheAge = now - cached.timestamp;
				const maxAge = 5 * 60 * 1000; // 5 minutes

				if (cacheAge < maxAge) {
					console.log(`⚡ Using cached analysis for key: ${cacheKey}`);
					return cached.data;
				} else {
					console.log(`🕒 Cache expired for key: ${cacheKey}`);
					// Remove expired cache
					setAnalysisCache((prev) => {
						const newCache = new Map(prev);
						newCache.delete(cacheKey);
						return newCache;
					});
				}
			}
			return null;
		},
		[analysisCache]
	);

	const setCachedAnalysis = React.useCallback((cacheKey: string, data: any) => {
		console.log(`💾 Caching analysis for key: ${cacheKey}`);
		setAnalysisCache((prev) => {
			const newCache = new Map(prev);
			newCache.set(cacheKey, {
				data,
				timestamp: Date.now(),
			});
			return newCache;
		});
	}, []);

	// Load date-filtered analysis with smart caching (MAIN DASHBOARD ONLY)
	const loadDateFilteredAnalysis = React.useCallback(async () => {
		// Only apply date filtering to main dashboard
		if (dashboardType !== "main") {
			console.log(
				`📊 ${dashboardType} dashboard shows comprehensive analysis - date filter ignored`
			);
			return;
		}

		if (
			!user?.client_id ||
			!dateRange ||
			(!dateRange.start && !dateRange.end)
		) {
			// No date filter applied, use regular loadClientData
			return;
		}

		const cacheKey = generateDateAwareCacheKey(`main_analysis`);

		// Check cache first
		const cachedResult = getCachedAnalysis(cacheKey);
		if (cachedResult) {
			console.log(`⚡ Using cached date-filtered analysis for main dashboard`);
			setSpecializedData(cachedResult);
			setIsLoadingWithDateFilter(false);
			return;
		}

		console.log(`🗓️ Loading date-filtered analysis for main dashboard:`, {
			start: dateRange.start?.format("YYYY-MM-DD"),
			end: dateRange.end?.format("YYYY-MM-DD"),
		});

		setIsLoadingWithDateFilter(true);

		try {
			// Filter existing client data by date range
			const filteredData = getFilteredData(clientData);

			if (filteredData.length === 0) {
				console.log(`⚠️ No data found for date range`);
				setSpecializedData(null);
				setIsLoadingWithDateFilter(false);
				return;
			}

			// Main dashboard uses metrics endpoint with date parameters
			const params = new URLSearchParams();
			params.append("fast_mode", "true");
			if (dateRange.start) {
				params.append("start_date", dateRange.start.format("YYYY-MM-DD"));
			}
			if (dateRange.end) {
				params.append("end_date", dateRange.end.format("YYYY-MM-DD"));
			}

			const endpointWithParams = `/dashboard/metrics?${params.toString()}`;

			console.log(
				`🔗 Calling date-filtered main dashboard: ${endpointWithParams}`
			);
			const response = await api.get(endpointWithParams);

			if (response.data && response.data.llm_analysis) {
				const analysisData = {
					...response.data,
					dateFiltered: true,
					dateRange: {
						start: dateRange.start?.format("YYYY-MM-DD"),
						end: dateRange.end?.format("YYYY-MM-DD"),
						label: dateRange.label,
					},
				};

				// Cache the result
				setCachedAnalysis(cacheKey, analysisData);
				setSpecializedData(analysisData);

				console.log(
					`✅ Date-filtered main dashboard analysis loaded and cached`
				);
			} else {
				console.error(`❌ Date-filtered main dashboard analysis not available`);
			}
		} catch (error) {
			console.error(
				`❌ Failed to load date-filtered analysis for main dashboard:`,
				error
			);
		} finally {
			setIsLoadingWithDateFilter(false);
		}
	}, [
		user?.client_id,
		dateRange,
		generateDateAwareCacheKey,
		getCachedAnalysis,
		setCachedAnalysis,
		getFilteredData,
		clientData,
	]);

	// Helper function to get AI-generated chart data
	const getAIChartData = (chartName: string) => {
		const chartMetric = aiMetrics.find(
			(metric) =>
				metric.metric_type === "chart_data" &&
				metric.metric_name.toLowerCase().includes(chartName.toLowerCase())
		);
		return chartMetric?.metric_value || null;
	};

	// Helper function to get AI-generated KPI data
	const getAIKPI = (kpiName: string) => {
		const kpiMetric = aiMetrics.find(
			(metric) =>
				metric.metric_type === "kpi" &&
				metric.metric_name.toLowerCase().includes(kpiName.toLowerCase())
		);
		return kpiMetric?.metric_value || null;
	};

	// Helper function to create chart data from any data structure
	const createDynamicChartData = (
		data: any[],
		xField: string,
		yField: string,
		limit = 10
	) => {
		if (!data || data.length === 0) return [];

		// Group data by xField and aggregate yField values
		const grouped = data.reduce((acc, record) => {
			const key = record[xField] || "Unknown";
			const value = parseFloat(record[yField]) || 0;

			if (!acc[key]) {
				acc[key] = { sum: 0, count: 0 };
			}
			acc[key].sum += value;
			acc[key].count += 1;
			return acc;
		}, {});

		// Convert to chart format and limit results
		return Object.entries(grouped)
			.map(([key, data]: [string, any]) => ({
				name: key,
				value: Math.round((data.sum / data.count) * 100) / 100, // Average value
				count: data.count,
			}))
			.sort((a, b) => b.value - a.value)
			.slice(0, limit);
	};

	// 🚀 NEW: Get specialized template configuration
	const getTemplateConfig = () => {
		const filteredData = getFilteredData(clientData);
		// Use LLM response total_records if available, otherwise fall back to filtered data length
		const totalRecords =
			specializedData?.total_records ||
			specializedData?.llm_analysis?.total_records ||
			filteredData.length;

		// Handle Business Intelligence template with LLM Analysis
		if (dashboardType === "business" && specializedData?.llm_analysis?.charts) {
			// Transform LLM charts to UI format using actual field names from config
			const transformedCharts: any = {};
			if (
				specializedData.llm_analysis.charts &&
				Array.isArray(specializedData.llm_analysis.charts)
			) {
				specializedData.llm_analysis.charts.forEach((chart: any) => {
					// Get actual field names from chart config
					const xField = chart.config?.x_axis?.field || "name";
					const yField = chart.config?.y_axis?.field || "value";

					if (chart.chart_type === "pie" || chart.chart_type === "radial") {
						transformedCharts[chart.id] = {
							title: chart.display_name,
							type: chart.chart_type,
							data: chart.data.map(
								(item: any) => item[yField] || item.value || 0
							),
							labels: chart.data.map(
								(item: any) => item[xField] || item.name || "Unknown"
							),
							insights:
								chart.insights || `${chart.display_name} analysis from AI`,
							config: chart.config,
						};
					} else if (
						chart.chart_type === "line" ||
						chart.chart_type === "bar"
					) {
						transformedCharts[chart.id] = {
							title: chart.display_name,
							type: chart.chart_type,
							data: chart.data.map(
								(item: any) => item[yField] || item.value || 0
							),
							labels: chart.data.map(
								(item: any) => item[xField] || item.name || "Unknown"
							),
							insights:
								chart.insights ||
								`${chart.display_name} trends from AI analysis`,
							config: chart.config,
						};
					}
				});
			}

			return {
				title: "Business Intelligence Dashboard",
				subtitle: `AI-Powered Revenue & Growth Analytics • ${totalRecords} records`,
				cards:
					specializedData.llm_analysis.kpis?.map((kpi: any) => ({
						title: kpi.display_name,
						value: kpi.value,
						trend: kpi.trend,
						change: kpi.trend?.percentage + "%",
						icon: "💼",
					})) || [],
				showDataTable: true,
				showCharts: true,
				templateType: "business_intelligence",
				// Map LLM analysis data to UI components
				llm_analysis: specializedData.llm_analysis,
				kpis: specializedData.llm_analysis.kpis || [],
				charts: transformedCharts,
				insights:
					specializedData.llm_analysis?.business_analysis?.business_insights ||
					[],
				tables: specializedData.llm_analysis.tables || [],
				analytics: specializedData.analytics,
				theme: "business",
			};
		}

		// Handle Performance Hub template with LLM Analysis
		if (
			dashboardType === "performance" &&
			specializedData?.llm_analysis?.charts
		) {
			// Transform LLM charts to UI format using actual field names from config
			const transformedCharts: any = {};
			if (
				specializedData.llm_analysis.charts &&
				Array.isArray(specializedData.llm_analysis.charts)
			) {
				specializedData.llm_analysis.charts.forEach((chart: any) => {
					// Get actual field names from chart config
					const xField = chart.config?.x_axis?.field || "name";
					const yField = chart.config?.y_axis?.field || "value";

					if (chart.chart_type === "pie" || chart.chart_type === "radial") {
						transformedCharts[chart.id] = {
							title: chart.display_name,
							type: chart.chart_type,
							data: chart.data.map(
								(item: any) => item[yField] || item.value || 0
							),
							labels: chart.data.map(
								(item: any) => item[xField] || item.name || "Unknown"
							),
							insights:
								chart.insights ||
								`${chart.display_name} performance analysis from AI`,
							config: chart.config,
						};
					} else if (
						chart.chart_type === "line" ||
						chart.chart_type === "bar" ||
						chart.chart_type === "radar"
					) {
						transformedCharts[chart.id] = {
							title: chart.display_name,
							type: chart.chart_type,
							data: chart.data.map(
								(item: any) => item[yField] || item.value || 0
							),
							labels: chart.data.map(
								(item: any) => item[xField] || item.name || "Unknown"
							),
							insights:
								chart.insights ||
								`${chart.display_name} performance trends from AI analysis`,
							config: chart.config,
						};
					}
				});
			}

			return {
				title: "Performance Hub Dashboard",
				subtitle: `AI-Powered Operational Efficiency • ${totalRecords} records`,
				cards:
					specializedData.llm_analysis.kpis?.map((kpi: any) => ({
						title: kpi.display_name,
						value: kpi.value,
						trend: kpi.trend,
						change: kpi.trend?.percentage + "%",
						icon: "⚡",
					})) || [],
				showDataTable: true,
				showCharts: true,
				templateType: "performance_hub",
				// Map LLM analysis data to UI components
				llm_analysis: specializedData.llm_analysis,
				kpis: specializedData.llm_analysis.kpis || [],
				charts: transformedCharts,
				insights:
					specializedData.llm_analysis?.business_analysis?.business_insights ||
					[],
				tables: specializedData.llm_analysis.tables || [],
				analytics: specializedData.analytics,
				theme: "performance",
			};
		}

		// Fallback templates (legacy)
		switch (dashboardType) {
			case "sales":
			case "1":
				return {
					title: `${user?.company_name} Data Analytics Hub`,
					subtitle: `Raw data exploration • ${totalRecords} records • Database analysis`,
					cards: [
						{
							title: "Database Records",
							value: totalRecords.toLocaleString(),
							trend: "neutral",
						},
						{
							title: "Data Columns",
							value: dataColumns.length.toString(),
							trend: "up",
						},
						{
							title: "Data Quality Score",
							value: "96.3%",
							trend: "up",
						},
						{
							title: "Processing Status",
							value: "Active",
							trend: "neutral",
						},
					],
					showDataTable: true,
					showCharts: false,
					templateType: "data_analytics",
				};

			case "operations":
			case "2":
			default:
				return {
					title: `${user?.company_name} Visual Insights Platform`,
					subtitle: `Advanced visualizations • ${totalRecords} data points • AI-powered charts`,
					cards: [
						{
							title: "Chart Visualizations",
							value: "4",
							trend: "up",
						},
						{
							title: "Insights Generated",
							value: "12",
							trend: "up",
						},
						{
							title: "Analysis Accuracy",
							value: "98.7%",
							trend: "up",
						},
						{
							title: "Real-time Updates",
							value: "Live",
							trend: "neutral",
						},
					],
					showDataTable: false,
					showCharts: true,
					chartType: "visual_insights",
					templateType: "visual_analytics",
				};
		}
	};

	// 🚀 Move useMemo BEFORE conditional returns to follow hooks rules
	const config = React.useMemo(() => {
		try {
			return getTemplateConfig();
		} catch (error) {
			console.error("Error in getTemplateConfig:", error);
			return {
				title: "Dashboard",
				subtitle: "Loading...",
				cards: [],
				showDataTable: false,
				showCharts: false,
				templateType: "fallback",
			};
		}
	}, [dashboardType, specializedData, clientData]);

	if (loading) {
		return (
			<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
				<Typography component="h2" variant="h6" sx={{ mb: 2 }}>
					Loading {dashboardType} Dashboard...
				</Typography>
				<Grid container spacing={2} columns={12}>
					{Array.from({ length: 4 }).map((_, index) => (
						<Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
							<Card sx={{ height: 150, bgcolor: "grey.100" }}>
								<CardContent>
									<Typography>Loading...</Typography>
								</CardContent>
							</Card>
						</Grid>
					))}
				</Grid>
			</Box>
		);
	}

	return (
		<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
			{/* Dashboard Header */}
			<Typography component="h1" variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
				{config.title}
			</Typography>
			<Typography variant="body1" sx={{ mb: 1, color: "text.secondary" }}>
				{config.subtitle}
			</Typography>

			{/* Date Range & Loading Indicators */}
			{isLoadingWithDateFilter && dashboardType === "main" && (
				<Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
					<Typography
						variant="caption"
						color="primary"
						sx={{ fontWeight: 500 }}>
						🗓️ Analyzing operational data for selected date range...
					</Typography>
				</Box>
			)}

			{dateRange && (dateRange.start || dateRange.end) && (
				<Box sx={{ mb: 3 }}>
					{dashboardType === "main" ? (
						<Typography
							variant="caption"
							sx={{
								color: "info.main",
								bgcolor: "info.light",
								px: 1.5,
								py: 0.5,
								borderRadius: 1,
								fontWeight: 500,
							}}>
							📅 Data Filtered: {dateRange.label}
							{dateRange.start && dateRange.end && (
								<span style={{ opacity: 0.8 }}>
									{" "}
									({dateRange.start.format("MMM DD")} -{" "}
									{dateRange.end.format("MMM DD, YYYY")})
								</span>
							)}
						</Typography>
					) : (
						<Typography
							variant="caption"
							sx={{
								color: "grey.600",
								bgcolor: "grey.100",
								px: 1.5,
								py: 0.5,
								borderRadius: 1,
								fontWeight: 500,
							}}>
							📊 Comprehensive Analysis - Date filter not applicable for{" "}
							{dashboardType === "business"
								? "strategic insights"
								: "operational excellence"}
						</Typography>
					)}
				</Box>
			)}

			{/* KPI Cards - Commented out for business and performance dashboards */}
			{/* 
			<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
				{config.cards.map((card: any, index: number) => (
					<Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
						<StatCard
							title={card.title}
							value={card.value}
							interval="Current period"
							trend={card.trend as "up" | "down" | "neutral"}
							data={Array.from(
								{ length: 30 },
								() => Math.round(Math.random() * 100) + 50
							)}
						/>
					</Grid>
				))}
			</Grid>
			*/}

			{/* LLM-Generated Business Intelligence Analysis */}
			{(config as any).templateType === "business_intelligence" &&
				(config as any)?.llm_analysis && (
					<>
						{/* Business Intelligence KPIs Grid */}
						<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
							{(config as any).kpis &&
								(config as any).kpis.map((kpi: any, index: number) => (
									<Grid key={kpi.id || index} size={{ xs: 12, sm: 6, md: 4 }}>
										<Card
											sx={{
												height: "100%",
												background:
													"linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
												color: "white",
												transition:
													"transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
												"&:hover": {
													transform: "translateY(-4px)",
													boxShadow: "0 8px 25px rgba(0,0,0,0.15)",
												},
											}}>
											<CardContent sx={{ p: 3 }}>
												<Box
													sx={{
														display: "flex",
														alignItems: "flex-start",
														justifyContent: "space-between",
														mb: 2,
													}}>
													<Box
														sx={{
															width: 48,
															height: 48,
															borderRadius: 2,
															bgcolor: "rgba(255,255,255,0.2)",
															display: "flex",
															alignItems: "center",
															justifyContent: "center",
															backdropFilter: "blur(10px)",
														}}>
														<Typography
															variant="h6"
															color="white"
															sx={{ fontWeight: "bold" }}>
															{kpi.category === "revenue"
																? "💰"
																: kpi.category === "customer"
																? "👥"
																: kpi.category === "growth"
																? "📈"
																: kpi.category === "sales"
																? "🛒"
																: kpi.category === "profitability"
																? "💎"
																: "📊"}
														</Typography>
													</Box>
													{kpi.trend && (
														<Box
															sx={{
																display: "flex",
																alignItems: "center",
																px: 1,
																py: 0.5,
																borderRadius: 1,
																bgcolor:
																	kpi.trend.direction === "upward"
																		? "rgba(76, 175, 80, 0.2)"
																		: kpi.trend.direction === "downward"
																		? "rgba(244, 67, 54, 0.2)"
																		: "rgba(158, 158, 158, 0.2)",
															}}>
															<Typography
																variant="caption"
																sx={{ fontWeight: 600 }}>
																{kpi.trend.direction === "upward"
																	? "↗"
																	: kpi.trend.direction === "downward"
																	? "↘"
																	: "→"}
															</Typography>
														</Box>
													)}
												</Box>

												<Box>
													<Typography
														variant="h3"
														component="div"
														sx={{
															fontWeight: "bold",
															mb: 0.5,
															fontSize: { xs: "1.75rem", sm: "2rem" },
														}}>
														{formatKPIValue(kpi.value, kpi.format)}
													</Typography>
													<Typography
														variant="body1"
														sx={{
															opacity: 0.9,
															fontWeight: 500,
															mb: 1,
														}}>
														{kpi.display_name || kpi.title}
													</Typography>
													{kpi.trend?.percentage && (
														<Typography
															variant="body2"
															sx={{
																fontWeight: 600,
																display: "flex",
																alignItems: "center",
																gap: 0.5,
															}}>
															<Box
																component="span"
																sx={{
																	color:
																		kpi.trend.direction === "upward"
																			? "#4caf50"
																			: kpi.trend.direction === "downward"
																			? "#f44336"
																			: "#9e9e9e",
																}}>
																{kpi.trend.percentage > 0 ? "+" : ""}
																{kpi.trend.percentage}%
															</Box>
															<Box
																component="span"
																sx={{ opacity: 0.7, fontSize: "0.75rem" }}>
																{kpi.trend?.description || "vs last period"}
															</Box>
														</Typography>
													)}
												</Box>
											</CardContent>
										</Card>
									</Grid>
								))}
						</Grid>

						{/* Business Intelligence Insights Section */}
						<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
							<Grid size={{ xs: 12 }}>
								<Card
									sx={{
										background:
											"linear-gradient(135deg, #f8f9ff 0%, #e8f2ff 100%)",
										border: "1px solid #e3f2fd",
										boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
									}}>
									<CardHeader
										title={
											<Box
												sx={{ display: "flex", alignItems: "center", gap: 2 }}>
												<Box
													sx={{
														width: 48,
														height: 48,
														borderRadius: 2,
														background:
															"linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
														display: "flex",
														alignItems: "center",
														justifyContent: "center",
													}}>
													<Typography variant="h6" color="white">
														🤖
													</Typography>
												</Box>
												<Box>
													<Typography
														variant="h5"
														sx={{ fontWeight: "bold", color: "primary.main" }}>
														AI-Powered Business Insights
													</Typography>
													<Typography variant="body2" color="text.secondary">
														{(config as any)?.llm_analysis
															?.business_type_detected ||
															"Sustainable Energy"}{" "}
														Industry Analysis
													</Typography>
												</Box>
											</Box>
										}
										sx={{ pb: 2 }}
									/>
									<CardContent sx={{ pt: 0 }}>
										<Box sx={{ mb: 2 }}>
											{(config as any)?.insights &&
												(config as any).insights.map(
													(insight: string, index: number) => (
														<Box
															key={index}
															sx={{
																display: "flex",
																alignItems: "flex-start",
																mb: 3,
																p: 2,
																borderRadius: 2,
																bgcolor: "white",
																boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
																border: "1px solid #f0f0f0",
																transition: "transform 0.2s ease-in-out",
																"&:hover": {
																	transform: "translateX(4px)",
																	boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
																},
															}}>
															<Box
																sx={{
																	minWidth: 32,
																	height: 32,
																	borderRadius: "50%",
																	background:
																		"linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
																	display: "flex",
																	alignItems: "center",
																	justifyContent: "center",
																	mr: 2,
																	mt: 0.5,
																	boxShadow:
																		"0 2px 8px rgba(102, 126, 234, 0.3)",
																}}>
																<Typography
																	variant="body2"
																	color="white"
																	sx={{ fontWeight: "bold" }}>
																	{index + 1}
																</Typography>
															</Box>
															<Typography
																variant="body1"
																color="text.primary"
																sx={{
																	fontWeight: 500,
																	lineHeight: 1.6,
																	flex: 1,
																}}>
																{insight}
															</Typography>
														</Box>
													)
												)}
										</Box>
									</CardContent>
								</Card>
							</Grid>
						</Grid>

						{/* Business Intelligence Charts */}
						{(config as any)?.charts &&
							Object.keys((config as any).charts).length > 0 && (
								<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
									{Object.entries((config as any).charts).map(
										([chartKey, chartData]: [string, any], index: number) => {
											console.log(`🔍 Rendering business chart ${chartKey}:`, {
												chartKey,
												index,
												chartData: {
													title: chartData.title,
													type: chartData.type,
													hasData: !!chartData.data,
													dataLength: chartData.data?.length,
													dataFirstItem: chartData.data?.[0],
													hasLabels: !!chartData.labels,
													labelsLength: chartData.labels?.length,
													labelsFirstItem: chartData.labels?.[0],
													hasConfig: !!chartData.config,
													fullData: chartData,
												},
											});

											return (
												<Grid
													key={chartKey}
													size={{ xs: 12, md: index === 0 ? 8 : 4 }}>
													<Card sx={{ height: "100%" }}>
														<CardHeader
															title={chartData.title || chartKey}
															subheader={`${
																chartData.type?.toUpperCase() || "CHART"
															} • AI Analysis`}
														/>
														<CardContent>
															<Box
																sx={{
																	height: 300,
																	display: "flex",
																	flexDirection: "column",
																}}>
																{isValidChartData(chartData) ? (
																	<>
																		{/* Render Actual Chart Components */}
																		<Box sx={{ flex: 1, minHeight: 200 }}>
																			{chartData.type === "line" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<LineChart
																						series={[
																							{
																								data: chartData.data.map(
																									(val: any) => {
																										const num = Number(val);
																										return isNaN(num) ? 0 : num;
																									}
																								),
																								label:
																									chartData.title || "Revenue",
																								color: "#1976d2",
																							},
																						]}
																						xAxis={[
																							{
																								data: chartData.labels.map(
																									(label: any) =>
																										String(label || "")
																								),
																								scaleType: "point",
																							},
																						]}
																						height={200}
																						margin={{
																							left: 50,
																							right: 50,
																							top: 20,
																							bottom: 50,
																						}}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "pie" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																						display: "flex",
																						justifyContent: "center",
																					}}>
																					<PieChart
																						series={[
																							{
																								data: chartData.labels
																									.map(
																										(
																											label: string,
																											i: number
																										) => {
																											const value = Number(
																												chartData.data[i]
																											);
																											return {
																												id: i,
																												value: isNaN(value)
																													? 0
																													: value,
																												label: String(
																													label ||
																														`Item ${i + 1}`
																												),
																											};
																										}
																									)
																									.filter(
																										(item: any) =>
																											item.value > 0
																									),
																								highlightScope: {
																									fade: "global",
																									highlight: "item",
																								} as const,
																							},
																						]}
																						height={200}
																						width={400}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "radial" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																						display: "flex",
																						justifyContent: "center",
																					}}>
																					<PieChart
																						series={[
																							{
																								data: chartData.labels
																									.map(
																										(
																											label: string,
																											i: number
																										) => {
																											const value = Number(
																												chartData.data[i]
																											);
																											return {
																												id: i,
																												value: isNaN(value)
																													? 0
																													: value,
																												label: String(
																													label ||
																														`Item ${i + 1}`
																												),
																											};
																										}
																									)
																									.filter(
																										(item: any) =>
																											item.value > 0
																									),
																								highlightScope: {
																									fade: "global",
																									highlight: "item",
																								} as const,
																								innerRadius: 50,
																								outerRadius: 90,
																							},
																						]}
																						height={200}
																						width={400}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "scatter" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<Charts.ScatterChart
																						data={chartData.labels
																							.map(
																								(label: string, i: number) => {
																									const xValue = Number(
																										chartData.data[i]
																									);
																									const yValue =
																										Number(chartData.data[i]) *
																										(Math.random() * 0.5 +
																											0.75); // Add some variation
																									return {
																										x: isNaN(xValue)
																											? i
																											: xValue,
																										y: isNaN(yValue)
																											? i
																											: yValue,
																										label: String(
																											label || `Point ${i + 1}`
																										),
																									};
																								}
																							)
																							.filter(
																								(item: any) =>
																									item.x >= 0 && item.y >= 0
																							)}
																						title={chartData.title}
																						xAxisLabel="X Value"
																						yAxisLabel="Y Value"
																					/>
																				</div>
																			)}

																			{chartData.type === "bar" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<BarChart
																						series={[
																							{
																								data: chartData.data.map(
																									(val: any) => {
																										const num = Number(val);
																										return isNaN(num) ? 0 : num;
																									}
																								),
																								label:
																									chartData.title || "Metrics",
																								color: "#ed6c02",
																							},
																						]}
																						xAxis={[
																							{
																								data: chartData.labels.map(
																									(label: any) =>
																										String(label || "")
																								),
																								scaleType: "band",
																							},
																						]}
																						height={200}
																						margin={{
																							left: 50,
																							right: 50,
																							top: 20,
																							bottom: 50,
																						}}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{/* Handle special chart types that might cause offsetY errors */}
																			{(chartData.type === "radar" ||
																				chartData.type === "heatmap") && (
																				<Box
																					sx={{
																						display: "flex",
																						alignItems: "center",
																						justifyContent: "center",
																						height: 200,
																						bgcolor: "grey.50",
																						borderRadius: 1,
																						border: "1px dashed",
																						borderColor: "grey.300",
																					}}>
																					<Typography
																						variant="body1"
																						color="text.secondary">
																						📊 {chartData.type.toUpperCase()}{" "}
																						Chart: {chartData.title}
																					</Typography>
																				</Box>
																			)}
																		</Box>

																		{/* Chart Insights */}
																		{chartData.insights && (
																			<Box
																				sx={{
																					p: 2,
																					mt: 2,
																					bgcolor: "info.50",
																					borderRadius: 1,
																					border: "1px solid",
																					borderColor: "info.200",
																				}}>
																				<Typography
																					variant="body2"
																					color="info.main"
																					sx={{
																						fontStyle: "italic",
																						lineHeight: 1.5,
																					}}>
																					💡 {chartData.insights}
																				</Typography>
																			</Box>
																		)}
																	</>
																) : (
																	<Box
																		sx={{
																			display: "flex",
																			alignItems: "center",
																			justifyContent: "center",
																			height: 200,
																			bgcolor: "grey.50",
																			borderRadius: 1,
																			border: "1px dashed",
																			borderColor: "grey.300",
																		}}>
																		<Typography
																			variant="body1"
																			color="text.secondary">
																			📊 Chart data is loading or unavailable
																		</Typography>
																	</Box>
																)}
															</Box>
														</CardContent>
													</Card>
												</Grid>
											);
										}
									)}
								</Grid>
							)}

						{/* Business Intelligence Tables */}
						{(config as any)?.tables && (config as any).tables.length > 0 && (
							<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
								{(config as any).tables.map((table: any, index: number) => (
									<Grid key={index} size={{ xs: 12 }}>
										<Card>
											<CardHeader
												title={
													table.display_name ||
													table.title ||
													`Business Analysis ${index + 1}`
												}
												subheader="Data-driven insights from your business metrics"
											/>
											<CardContent>
												{table.columns && table.data && (
													<Box sx={{ overflow: "auto" }}>
														{/* Table Header */}
														<Box
															sx={{
																display: "flex",
																bgcolor: "grey.100",
																p: 1,
																borderRadius: 1,
																mb: 1,
															}}>
															{table.columns.map(
																(column: string, colIndex: number) => (
																	<Typography
																		key={colIndex}
																		variant="subtitle2"
																		sx={{
																			flex: 1,
																			fontWeight: "bold",
																			textAlign:
																				colIndex === 0 ? "left" : "right",
																		}}>
																		{column}
																	</Typography>
																)
															)}
														</Box>

														{/* Table Data */}
														{table.data.map((row: any, rowIndex: number) => (
															<Box
																key={rowIndex}
																sx={{
																	display: "flex",
																	p: 1,
																	borderBottom: "1px solid",
																	borderColor: "grey.200",
																	"&:hover": { bgcolor: "grey.50" },
																}}>
																{Array.isArray(row)
																	? // Handle array format (row is an array)
																	  row.map((cell: any, cellIndex: number) => (
																			<Typography
																				key={cellIndex}
																				variant="body2"
																				sx={{
																					flex: 1,
																					textAlign:
																						cellIndex === 0 ? "left" : "right",
																					fontWeight:
																						cellIndex === 0 ? 500 : 400,
																				}}>
																				{cell}
																			</Typography>
																	  ))
																	: // Handle object format (row is an object)
																	  table.columns.map(
																			(column: string, cellIndex: number) => (
																				<Typography
																					key={cellIndex}
																					variant="body2"
																					sx={{
																						flex: 1,
																						textAlign:
																							cellIndex === 0
																								? "left"
																								: "right",
																						fontWeight:
																							cellIndex === 0 ? 500 : 400,
																					}}>
																					{String(row[column] || "-")}
																				</Typography>
																			)
																	  )}
															</Box>
														))}
													</Box>
												)}
											</CardContent>
										</Card>
									</Grid>
								))}
							</Grid>
						)}
					</>
				)}

			{/* LLM-Generated Performance Hub Analysis */}
			{config.templateType === "performance_hub" &&
				(config as any)?.llm_analysis && (
					<>
						{/* Performance Hub KPIs Grid */}
						<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
							{(config as any).kpis &&
								(config as any).kpis.map((kpi: any, index: number) => (
									<Grid key={kpi.id || index} size={{ xs: 12, sm: 6, md: 4 }}>
										<Card
											sx={{
												height: "100%",
												background:
													"linear-gradient(135deg, #ff9800 0%, #f57c00 100%)",
												color: "white",
												transition:
													"transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
												"&:hover": {
													transform: "translateY(-4px)",
													boxShadow: "0 8px 25px rgba(0,0,0,0.15)",
												},
											}}>
											<CardContent sx={{ p: 3 }}>
												<Box
													sx={{
														display: "flex",
														alignItems: "flex-start",
														justifyContent: "space-between",
														mb: 2,
													}}>
													<Box
														sx={{
															width: 48,
															height: 48,
															borderRadius: 2,
															bgcolor: "rgba(255,255,255,0.2)",
															display: "flex",
															alignItems: "center",
															justifyContent: "center",
															backdropFilter: "blur(10px)",
														}}>
														<Typography
															variant="h6"
															color="white"
															sx={{ fontWeight: "bold" }}>
															{kpi.category === "efficiency"
																? "⚡"
																: kpi.category === "reliability"
																? "🛡️"
																: kpi.category === "quality"
																? "⭐"
																: kpi.category === "speed"
																? "🚀"
																: kpi.category === "performance"
																? "📊"
																: "⚙️"}
														</Typography>
													</Box>
													{kpi.trend && (
														<Box
															sx={{
																display: "flex",
																alignItems: "center",
																px: 1,
																py: 0.5,
																borderRadius: 1,
																bgcolor:
																	kpi.trend.direction === "upward"
																		? "rgba(76, 175, 80, 0.2)"
																		: kpi.trend.direction === "downward"
																		? "rgba(244, 67, 54, 0.2)"
																		: "rgba(158, 158, 158, 0.2)",
															}}>
															<Typography
																variant="caption"
																sx={{ fontWeight: 600 }}>
																{kpi.trend.direction === "upward"
																	? "↗"
																	: kpi.trend.direction === "downward"
																	? "↘"
																	: "→"}
															</Typography>
														</Box>
													)}
												</Box>

												<Box>
													<Typography
														variant="h3"
														component="div"
														sx={{
															fontWeight: "bold",
															mb: 0.5,
															fontSize: { xs: "1.75rem", sm: "2rem" },
														}}>
														{formatKPIValue(kpi.value, kpi.format)}
													</Typography>
													<Typography
														variant="body1"
														sx={{
															opacity: 0.9,
															fontWeight: 500,
															mb: 1,
														}}>
														{kpi.display_name || kpi.title}
													</Typography>
													{kpi.trend?.percentage && (
														<Typography
															variant="body2"
															sx={{
																fontWeight: 600,
																display: "flex",
																alignItems: "center",
																gap: 0.5,
															}}>
															<Box
																component="span"
																sx={{
																	color:
																		kpi.trend.direction === "upward"
																			? "#4caf50"
																			: kpi.trend.direction === "downward"
																			? "#f44336"
																			: "#9e9e9e",
																}}>
																{kpi.trend.percentage > 0 ? "+" : ""}
																{kpi.trend.percentage}%
															</Box>
															<Box
																component="span"
																sx={{ opacity: 0.7, fontSize: "0.75rem" }}>
																{kpi.trend?.description || "vs last period"}
															</Box>
														</Typography>
													)}
												</Box>
											</CardContent>
										</Card>
									</Grid>
								))}
						</Grid>

						{/* Performance Hub Insights Section */}
						<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
							<Grid size={{ xs: 12 }}>
								<Card
									sx={{
										background:
											"linear-gradient(135deg, #fff8e1 0%, #ffe0b2 100%)",
										border: "1px solid #ffcc02",
										boxShadow: "0 4px 20px rgba(255, 152, 0, 0.1)",
									}}>
									<CardHeader
										title={
											<Box
												sx={{ display: "flex", alignItems: "center", gap: 2 }}>
												<Box
													sx={{
														width: 48,
														height: 48,
														borderRadius: 2,
														background:
															"linear-gradient(135deg, #ff9800 0%, #f57c00 100%)",
														display: "flex",
														alignItems: "center",
														justifyContent: "center",
													}}>
													<Typography variant="h6" color="white">
														⚡
													</Typography>
												</Box>
												<Box>
													<Typography
														variant="h5"
														sx={{ fontWeight: "bold", color: "orange.main" }}>
														AI-Powered Performance Analysis
													</Typography>
													<Typography variant="body2" color="text.secondary">
														{(config as any)?.llm_analysis
															?.performance_type_detected ||
															"Operational Efficiency"}{" "}
														Performance Insights
													</Typography>
												</Box>
											</Box>
										}
										sx={{ pb: 2 }}
									/>
									<CardContent sx={{ pt: 0 }}>
										<Box sx={{ mb: 2 }}>
											{(config as any)?.insights &&
												(config as any).insights.map(
													(insight: string, index: number) => (
														<Box
															key={index}
															sx={{
																display: "flex",
																alignItems: "flex-start",
																mb: 3,
																p: 2,
																borderRadius: 2,
																bgcolor: "white",
																boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
																border: "1px solid #ffe0b2",
																transition: "transform 0.2s ease-in-out",
																"&:hover": {
																	transform: "translateX(4px)",
																	boxShadow:
																		"0 4px 12px rgba(255, 152, 0, 0.15)",
																},
															}}>
															<Box
																sx={{
																	minWidth: 32,
																	height: 32,
																	borderRadius: "50%",
																	background:
																		"linear-gradient(135deg, #ff9800 0%, #f57c00 100%)",
																	display: "flex",
																	alignItems: "center",
																	justifyContent: "center",
																	mr: 2,
																	mt: 0.5,
																	boxShadow: "0 2px 8px rgba(255, 152, 0, 0.3)",
																}}>
																<Typography
																	variant="body2"
																	color="white"
																	sx={{ fontWeight: "bold" }}>
																	{index + 1}
																</Typography>
															</Box>
															<Typography
																variant="body1"
																color="text.primary"
																sx={{
																	fontWeight: 500,
																	lineHeight: 1.6,
																	flex: 1,
																}}>
																{insight}
															</Typography>
														</Box>
													)
												)}
										</Box>
									</CardContent>
								</Card>
							</Grid>
						</Grid>

						{/* Performance Hub Charts */}
						{config.templateType === "performance_hub" &&
							(config as any)?.charts &&
							Object.keys((config as any).charts).length > 0 && (
								<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
									{Object.entries((config as any).charts).map(
										([chartKey, chartData]: [string, any], index: number) => {
											console.log(
												`🔍 Rendering performance chart ${chartKey}:`,
												{
													chartKey,
													index,
													chartData: {
														title: chartData.title,
														type: chartData.type,
														hasData: !!chartData.data,
														dataLength: chartData.data?.length,
														dataFirstItem: chartData.data?.[0],
														hasLabels: !!chartData.labels,
														labelsLength: chartData.labels?.length,
														labelsFirstItem: chartData.labels?.[0],
														hasConfig: !!chartData.config,
														fullData: chartData,
													},
												}
											);

											return (
												<Grid
													key={chartKey}
													size={{ xs: 12, md: index === 0 ? 8 : 4 }}>
													<Card sx={{ height: "100%" }}>
														<CardHeader
															title={chartData.title || chartKey}
															subheader={`${
																chartData.type?.toUpperCase() || "CHART"
															} • Performance Analytics`}
														/>
														<CardContent>
															<Box
																sx={{
																	height: 300,
																	display: "flex",
																	flexDirection: "column",
																}}>
																{isValidChartData(chartData) ? (
																	<>
																		{/* Render Actual Chart Components */}
																		<Box sx={{ flex: 1, minHeight: 200 }}>
																			{chartData.type === "line" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<LineChart
																						series={[
																							{
																								data: chartData.data.map(
																									(val: any) => {
																										const num = Number(val);
																										return isNaN(num) ? 0 : num;
																									}
																								),
																								label:
																									chartData.title ||
																									"Performance",
																								color: "#ff9800",
																							},
																						]}
																						xAxis={[
																							{
																								data: chartData.labels.map(
																									(label: any) =>
																										String(label || "")
																								),
																								scaleType: "point",
																							},
																						]}
																						height={200}
																						margin={{
																							left: 50,
																							right: 50,
																							top: 20,
																							bottom: 50,
																						}}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "scatter" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<Charts.ScatterChart
																						data={chartData.labels
																							.map(
																								(label: string, i: number) => {
																									const xValue = Number(
																										chartData.data[i]
																									);
																									const yValue =
																										Number(chartData.data[i]) *
																										(Math.random() * 0.5 +
																											0.75); // Add some variation
																									return {
																										x: isNaN(xValue)
																											? i
																											: xValue,
																										y: isNaN(yValue)
																											? i
																											: yValue,
																										label: String(
																											label || `Point ${i + 1}`
																										),
																									};
																								}
																							)
																							.filter(
																								(item: any) =>
																									item.x >= 0 && item.y >= 0
																							)}
																						title={chartData.title}
																						xAxisLabel="X Value"
																						yAxisLabel="Y Value"
																					/>
																				</div>
																			)}

																			{chartData.type === "bar" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<BarChart
																						series={[
																							{
																								data: chartData.data.map(
																									(val: any) => {
																										const num = Number(val);
																										return isNaN(num) ? 0 : num;
																									}
																								),
																								label:
																									chartData.title ||
																									"Performance",
																								color: "#ff9800",
																							},
																						]}
																						xAxis={[
																							{
																								data: chartData.labels.map(
																									(label: any) =>
																										String(label || "")
																								),
																								scaleType: "band",
																							},
																						]}
																						height={200}
																						margin={{
																							left: 50,
																							right: 50,
																							top: 20,
																							bottom: 50,
																						}}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "pie" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																						display: "flex",
																						justifyContent: "center",
																					}}>
																					<PieChart
																						series={[
																							{
																								data: chartData.labels
																									.map(
																										(
																											label: string,
																											i: number
																										) => {
																											const value = Number(
																												chartData.data[i]
																											);
																											return {
																												id: i,
																												value: isNaN(value)
																													? 0
																													: value,
																												label: String(
																													label ||
																														`Item ${i + 1}`
																												),
																											};
																										}
																									)
																									.filter(
																										(item: any) =>
																											item.value > 0
																									),
																								highlightScope: {
																									fade: "global",
																									highlight: "item",
																								} as const,
																							},
																						]}
																						height={200}
																						width={400}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "radial" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																						display: "flex",
																						justifyContent: "center",
																					}}>
																					<PieChart
																						series={[
																							{
																								data: chartData.labels
																									.map(
																										(
																											label: string,
																											i: number
																										) => {
																											const value = Number(
																												chartData.data[i]
																											);
																											return {
																												id: i,
																												value: isNaN(value)
																													? 0
																													: value,
																												label: String(
																													label ||
																														`Item ${i + 1}`
																												),
																											};
																										}
																									)
																									.filter(
																										(item: any) =>
																											item.value > 0
																									),
																								highlightScope: {
																									fade: "global",
																									highlight: "item",
																								} as const,
																								innerRadius: 40,
																								outerRadius: 80,
																							},
																						]}
																						height={200}
																						width={400}
																						skipAnimation={true}
																						slotProps={{
																							noDataOverlay: {
																								message: "No data available",
																							},
																						}}
																					/>
																				</div>
																			)}

																			{chartData.type === "scatter" && (
																				<div
																					style={{
																						width: "100%",
																						height: "200px",
																					}}>
																					<Charts.ScatterChart
																						data={chartData.labels
																							.map(
																								(label: string, i: number) => {
																									const xValue = Number(
																										chartData.data[i]
																									);
																									const yValue =
																										Number(chartData.data[i]) *
																										(Math.random() * 0.5 +
																											0.75); // Add some variation
																									return {
																										x: isNaN(xValue)
																											? i
																											: xValue,
																										y: isNaN(yValue)
																											? i
																											: yValue,
																										label: String(
																											label || `Point ${i + 1}`
																										),
																									};
																								}
																							)
																							.filter(
																								(item: any) =>
																									item.x >= 0 && item.y >= 0
																							)}
																						title={chartData.title}
																						xAxisLabel="X Value"
																						yAxisLabel="Y Value"
																					/>
																				</div>
																			)}

																			{/* Handle special chart types that might cause offsetY errors */}
																			{(chartData.type === "radar" ||
																				chartData.type === "heatmap") && (
																				<Box
																					sx={{
																						display: "flex",
																						alignItems: "center",
																						justifyContent: "center",
																						height: 200,
																						bgcolor: "orange.50",
																						borderRadius: 1,
																						border: "1px dashed",
																						borderColor: "orange.300",
																					}}>
																					<Typography
																						variant="body1"
																						color="text.secondary">
																						⚡ {chartData.type.toUpperCase()}{" "}
																						Chart: {chartData.title}
																					</Typography>
																				</Box>
																			)}
																		</Box>

																		{/* Chart Insights */}
																		{chartData.insights && (
																			<Box
																				sx={{
																					p: 2,
																					mt: 2,
																					bgcolor: "warning.50",
																					borderRadius: 1,
																					border: "1px solid",
																					borderColor: "warning.200",
																				}}>
																				<Typography
																					variant="body2"
																					color="warning.main"
																					sx={{
																						fontStyle: "italic",
																						lineHeight: 1.5,
																					}}>
																					⚡ {chartData.insights}
																				</Typography>
																			</Box>
																		)}
																	</>
																) : (
																	<Box
																		sx={{
																			display: "flex",
																			alignItems: "center",
																			justifyContent: "center",
																			height: 200,
																			bgcolor: "orange.50",
																			borderRadius: 1,
																			border: "1px dashed",
																			borderColor: "orange.300",
																		}}>
																		<Typography
																			variant="body1"
																			color="text.secondary">
																			⚡ Chart data is loading or unavailable
																		</Typography>
																	</Box>
																)}
															</Box>
														</CardContent>
													</Card>
												</Grid>
											);
										}
									)}
								</Grid>
							)}
						{(config as any)?.charts &&
							Object.keys((config as any).charts).length > 0 && (
								<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
									{Object.entries((config as any).charts).map(
										([chartKey, chartData]: [string, any], index: number) => (
											<Grid
												key={chartKey}
												size={{ xs: 12, md: index === 0 ? 8 : 4 }}>
												<Card sx={{ height: "100%" }}>
													<CardHeader
														title={chartData.title || chartKey}
														subheader={`${
															chartData.type?.toUpperCase() || "PERFORMANCE"
														} • AI Analysis`}
													/>
													<CardContent>
														<Box
															sx={{
																height: 300,
																display: "flex",
																flexDirection: "column",
															}}>
															{isValidChartData(chartData) ? (
																<>
																	{/* Render Actual Chart Components */}
																	<Box sx={{ flex: 1, minHeight: 200 }}>
																		{chartData.type === "line" && (
																			<div
																				style={{
																					width: "100%",
																					height: "200px",
																				}}>
																				<LineChart
																					series={[
																						{
																							data: chartData.data.map(
																								(val: any) => {
																									const num = Number(val);
																									return isNaN(num) ? 0 : num;
																								}
																							),
																							label:
																								chartData.title ||
																								"Performance",
																							color: "#ff9800",
																						},
																					]}
																					xAxis={[
																						{
																							data: chartData.labels.map(
																								(label: any) =>
																									String(label || "")
																							),
																							scaleType: "point",
																						},
																					]}
																					height={200}
																					margin={{
																						left: 50,
																						right: 50,
																						top: 20,
																						bottom: 50,
																					}}
																					skipAnimation={true}
																					slotProps={{
																						noDataOverlay: {
																							message: "No data available",
																						},
																					}}
																				/>
																			</div>
																		)}

																		{chartData.type === "pie" && (
																			<div
																				style={{
																					width: "100%",
																					height: "200px",
																					display: "flex",
																					justifyContent: "center",
																				}}>
																				<PieChart
																					series={[
																						{
																							data: chartData.labels
																								.map(
																									(
																										label: string,
																										i: number
																									) => {
																										const value = Number(
																											chartData.data[i]
																										);
																										return {
																											id: i,
																											value: isNaN(value)
																												? 0
																												: value,
																											label: String(
																												label || `Item ${i + 1}`
																											),
																										};
																									}
																								)
																								.filter(
																									(item: any) => item.value > 0
																								),
																							highlightScope: {
																								fade: "global",
																								highlight: "item",
																							} as const,
																						},
																					]}
																					height={200}
																					width={400}
																					skipAnimation={true}
																					slotProps={{
																						noDataOverlay: {
																							message: "No data available",
																						},
																					}}
																				/>
																			</div>
																		)}

																		{chartData.type === "radial" && (
																			<div
																				style={{
																					width: "100%",
																					height: "200px",
																					display: "flex",
																					justifyContent: "center",
																				}}>
																				<PieChart
																					series={[
																						{
																							data: chartData.labels
																								.map(
																									(
																										label: string,
																										i: number
																									) => {
																										const value = Number(
																											chartData.data[i]
																										);
																										return {
																											id: i,
																											value: isNaN(value)
																												? 0
																												: value,
																											label: String(
																												label || `Item ${i + 1}`
																											),
																										};
																									}
																								)
																								.filter(
																									(item: any) => item.value > 0
																								),
																							highlightScope: {
																								fade: "global",
																								highlight: "item",
																							} as const,
																							innerRadius: 40,
																							outerRadius: 80,
																						},
																					]}
																					height={200}
																					width={400}
																					skipAnimation={true}
																					slotProps={{
																						noDataOverlay: {
																							message: "No data available",
																						},
																					}}
																				/>
																			</div>
																		)}

																		{chartData.type === "radar" && (
																			<div
																				style={{
																					width: "100%",
																					height: "200px",
																				}}>
																				<Charts.RadarChart
																					data={chartData.labels
																						.map((label: string, i: number) => {
																							const value = Number(
																								chartData.data[i]
																							);
																							return {
																								category: String(
																									label || `Category ${i + 1}`
																								),
																								value: isNaN(value) ? 0 : value,
																							};
																						})
																						.filter(
																							(item: any) => item.value > 0
																						)}
																					title={chartData.title}
																					minimal={true}
																				/>
																			</div>
																		)}

																		{chartData.type === "heatmap" && (
																			<div
																				style={{
																					width: "100%",
																					height: "200px",
																				}}>
																				<Charts.HeatmapChart
																					data={chartData.labels
																						.map((label: string, i: number) => {
																							const value = Number(
																								chartData.data[i]
																							);
																							return {
																								name: String(
																									label || `Item ${i + 1}`
																								),
																								value: isNaN(value) ? 0 : value,
																							};
																						})
																						.filter(
																							(item: any) => item.value > 0
																						)}
																					title={chartData.title}
																					minimal={true}
																				/>
																			</div>
																		)}

																		{chartData.type === "bar" && (
																			<div
																				style={{
																					width: "100%",
																					height: "200px",
																				}}>
																				<BarChart
																					series={[
																						{
																							data: chartData.data.map(
																								(val: any) => {
																									const num = Number(val);
																									return isNaN(num) ? 0 : num;
																								}
																							),
																							label:
																								chartData.title ||
																								"Performance",
																							color: "#f44336",
																						},
																					]}
																					xAxis={[
																						{
																							data: chartData.labels.map(
																								(label: any) =>
																									String(label || "")
																							),
																							scaleType: "band",
																						},
																					]}
																					height={200}
																					margin={{
																						left: 50,
																						right: 50,
																						top: 20,
																						bottom: 50,
																					}}
																					skipAnimation={true}
																					slotProps={{
																						noDataOverlay: {
																							message: "No data available",
																						},
																					}}
																				/>
																			</div>
																		)}
																	</Box>

																	{/* Chart Insights */}
																	{chartData.insights && (
																		<Box
																			sx={{
																				p: 2,
																				mt: 2,
																				bgcolor: "warning.50",
																				borderRadius: 1,
																				border: "1px solid",
																				borderColor: "warning.200",
																			}}>
																			<Typography
																				variant="body2"
																				color="warning.main"
																				sx={{
																					fontStyle: "italic",
																					lineHeight: 1.5,
																				}}>
																				⚡ {chartData.insights}
																			</Typography>
																		</Box>
																	)}
																</>
															) : (
																<Box
																	sx={{
																		display: "flex",
																		alignItems: "center",
																		justifyContent: "center",
																		height: 200,
																		bgcolor: "grey.50",
																		borderRadius: 1,
																		border: "1px dashed",
																		borderColor: "grey.300",
																	}}>
																	<Typography
																		variant="body1"
																		color="text.secondary">
																		📊 Chart data is loading or unavailable
																	</Typography>
																</Box>
															)}
														</Box>
													</CardContent>
												</Card>
											</Grid>
										)
									)}
								</Grid>
							)}

						{/* Performance Hub Tables */}
						{(config as any)?.tables && (config as any).tables.length > 0 && (
							<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
								{(config as any).tables.map((table: any, index: number) => (
									<Grid key={index} size={{ xs: 12 }}>
										<Card>
											<CardHeader
												title={
													table.title || `Performance Analysis ${index + 1}`
												}
												subheader="Performance metrics and operational insights"
											/>
											<CardContent>
												{table.columns && table.data && (
													<Box sx={{ overflow: "auto" }}>
														{/* Table Header */}
														<Box
															sx={{
																display: "flex",
																bgcolor: "secondary.100",
																p: 1,
																borderRadius: 1,
																mb: 1,
															}}>
															{table.columns.map(
																(column: string, colIndex: number) => (
																	<Typography
																		key={colIndex}
																		variant="subtitle2"
																		sx={{
																			flex: 1,
																			fontWeight: "bold",
																			textAlign:
																				colIndex === 0 ? "left" : "right",
																		}}>
																		{column}
																	</Typography>
																)
															)}
														</Box>

														{/* Table Data */}
														{table.data.map((row: any, rowIndex: number) => (
															<Box
																key={rowIndex}
																sx={{
																	display: "flex",
																	p: 1,
																	borderBottom: "1px solid",
																	borderColor: "grey.200",
																	"&:hover": { bgcolor: "secondary.50" },
																}}>
																{Array.isArray(row)
																	? // Handle array format (row is an array)
																	  row.map((cell: any, cellIndex: number) => (
																			<Typography
																				key={cellIndex}
																				variant="body2"
																				sx={{
																					flex: 1,
																					textAlign:
																						cellIndex === 0 ? "left" : "right",
																					fontWeight:
																						cellIndex === 0 ? 500 : 400,
																				}}>
																				{cell}
																			</Typography>
																	  ))
																	: // Handle object format (row is an object)
																	  table.columns.map(
																			(column: string, cellIndex: number) => (
																				<Typography
																					key={cellIndex}
																					variant="body2"
																					sx={{
																						flex: 1,
																						textAlign:
																							cellIndex === 0
																								? "left"
																								: "right",
																						fontWeight:
																							cellIndex === 0 ? 500 : 400,
																					}}>
																					{String(row[column] || "-")}
																				</Typography>
																			)
																	  )}
															</Box>
														))}
													</Box>
												)}
											</CardContent>
										</Card>
									</Grid>
								))}
							</Grid>
						)}
					</>
				)}

			{/* Default Charts for Main Template */}
			{config.showCharts &&
				config.templateType !== "business_intelligence" &&
				config.templateType !== "performance_hub" && (
					<>
						{/* First Row - Unique Charts for Visual Analytics */}
						<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
							<Grid size={{ xs: 12, md: 8 }}>
								<Card>
									<CardHeader
										title="Trading Volume Analysis"
										subheader={`Stock trading patterns • ${clientData.length} transactions analyzed`}
									/>
									<CardContent>
										<Box sx={{ height: 300 }}>
											{clientData.length > 0 ? (
												<div style={{ width: "100%", height: "250px" }}>
													<LineChart
														xAxis={[
															{
																data: (() => {
																	// Try to get AI-generated chart labels first
																	const aiData =
																		getAIChartData("volume") ||
																		getAIChartData("trend") ||
																		getAIChartData("quarterly");
																	if (
																		aiData &&
																		aiData.labels &&
																		Array.isArray(aiData.labels)
																	) {
																		return aiData.labels.slice(0, 10);
																	}

																	// Fallback: Create dynamic labels from data
																	const numericFields = dataColumns.filter(
																		(col) => {
																			const values = clientData
																				.map((record) => record[col])
																				.filter((v) => v != null);
																			return (
																				values.length > 0 &&
																				!isNaN(parseFloat(values[0]))
																			);
																		}
																	);

																	if (numericFields.length > 0) {
																		const labelField =
																			dataColumns.find(
																				(col) =>
																					typeof clientData[0][col] === "string"
																			) || dataColumns[0];
																		const chartData = createDynamicChartData(
																			clientData,
																			labelField,
																			numericFields[0],
																			10
																		);
																		return chartData.map(
																			(item, index) =>
																				item.name || `Item ${index + 1}`
																		);
																	}

																	// Last resort: use period labels
																	return [
																		"Period 1",
																		"Period 2",
																		"Period 3",
																		"Period 4",
																		"Period 5",
																		"Period 6",
																		"Period 7",
																		"Period 8",
																		"Period 9",
																		"Period 10",
																	];
																})(),
																scaleType: "point",
															},
														]}
														series={[
															{
																data: (() => {
																	// Try to get AI-generated chart data first
																	const aiData =
																		getAIChartData("volume") ||
																		getAIChartData("trend") ||
																		getAIChartData("quarterly");
																	if (
																		aiData &&
																		aiData.data &&
																		Array.isArray(aiData.data)
																	) {
																		return aiData.data
																			.slice(0, 10)
																			.map(
																				(item: any) =>
																					item.value || item.desktop || 0
																			);
																	}

																	// Fallback: Create dynamic chart from any numeric field
																	const numericFields = dataColumns.filter(
																		(col) => {
																			const values = clientData
																				.map((record) => record[col])
																				.filter((v) => v != null);
																			return (
																				values.length > 0 &&
																				!isNaN(parseFloat(values[0]))
																			);
																		}
																	);

																	if (numericFields.length > 0) {
																		const field = numericFields[0]; // Use first numeric field
																		const chartData = createDynamicChartData(
																			clientData,
																			dataColumns.find(
																				(col) =>
																					typeof clientData[0][col] === "string"
																			) || dataColumns[0],
																			field,
																			10
																		);
																		return chartData.map((item) => item.value);
																	}

																	return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
																})(),
																label: `${dataColumns[0] || "Data"} Analysis`,
																color: "#1976d2",
															},
															{
																data: (() => {
																	// Try to get second AI chart or use second numeric field
																	const aiData =
																		getAIChartData("price") ||
																		getAIChartData("revenue") ||
																		getAIChartData("performance");
																	if (
																		aiData &&
																		aiData.data &&
																		Array.isArray(aiData.data)
																	) {
																		return aiData.data
																			.slice(0, 10)
																			.map(
																				(item: any) =>
																					item.value || item.mobile || 0
																			);
																	}

																	// Fallback: Use second numeric field
																	const numericFields = dataColumns.filter(
																		(col) => {
																			const values = clientData
																				.map((record) => record[col])
																				.filter((v) => v != null);
																			return (
																				values.length > 0 &&
																				!isNaN(parseFloat(values[0]))
																			);
																		}
																	);

																	if (numericFields.length > 1) {
																		const field = numericFields[1]; // Use second numeric field
																		const chartData = createDynamicChartData(
																			clientData,
																			dataColumns.find(
																				(col) =>
																					typeof clientData[0][col] === "string"
																			) || dataColumns[0],
																			field,
																			10
																		);
																		return chartData.map((item) => item.value);
																	}

																	return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
																})(),
																label: `${
																	dataColumns[1] || "Secondary"
																} Metric`,
																color: "#dc004e",
															},
														]}
														width={600}
														height={250}
														skipAnimation={true}
														slotProps={{
															noDataOverlay: { message: "No data available" },
														}}
													/>
												</div>
											) : (
												<Typography
													color="text.secondary"
													sx={{
														display: "flex",
														justifyContent: "center",
														alignItems: "center",
														height: "100%",
													}}>
													No data available
												</Typography>
											)}
										</Box>
									</CardContent>
								</Card>
							</Grid>
							<Grid size={{ xs: 12, md: 4 }}>
								<Card>
									<CardHeader
										title="Portfolio Breakdown"
										subheader="Investment distribution"
									/>
									<CardContent>
										<Box
											sx={{
												height: 300,
												display: "flex",
												justifyContent: "center",
											}}>
											{clientData.length > 0 ? (
												<div style={{ width: "100%", height: "250px" }}>
													<PieChart
														series={[
															{
																data: (() => {
																	// Try to get AI-generated pie chart data first
																	const aiData =
																		getAIChartData("distribution") ||
																		getAIChartData("breakdown") ||
																		getAIChartData("stock");
																	if (
																		aiData &&
																		aiData.data &&
																		Array.isArray(aiData.data)
																	) {
																		return aiData.data.map(
																			(item: any, index: number) => ({
																				id: index,
																				value: item.value || item.desktop || 0,
																				label:
																					item.name ||
																					item.browser ||
																					`Item ${index + 1}`,
																			})
																		);
																	}

																	// Fallback: Create pie chart from categorical data
																	const categoricalFields = dataColumns.filter(
																		(col) => {
																			const values = clientData.map(
																				(record) => record[col]
																			);
																			const uniqueValues = [...new Set(values)];
																			return (
																				uniqueValues.length > 1 &&
																				uniqueValues.length <= 10 &&
																				typeof values[0] === "string"
																			);
																		}
																	);

																	if (categoricalFields.length > 0) {
																		const field = categoricalFields[0]; // Use first categorical field
																		const valueCounts = clientData.reduce(
																			(acc, record) => {
																				const key = record[field] || "Unknown";
																				acc[key] = (acc[key] || 0) + 1;
																				return acc;
																			},
																			{}
																		);

																		return Object.entries(valueCounts)
																			.map(([key, count], index) => ({
																				id: index,
																				value: count as number,
																				label: key,
																			}))
																			.slice(0, 6); // Limit to 6 slices
																	}

																	return [
																		{ id: 0, value: 100, label: "No Data" },
																	];
																})(),
																highlightScope: {
																	fade: "global",
																	highlight: "item",
																},
																faded: {
																	innerRadius: 30,
																	additionalRadius: -30,
																	color: "gray",
																},
															},
														]}
														width={280}
														height={250}
														skipAnimation={true}
														slotProps={{
															noDataOverlay: { message: "No data available" },
														}}
													/>
												</div>
											) : (
												<Typography
													color="text.secondary"
													sx={{ alignSelf: "center" }}>
													No data available
												</Typography>
											)}
										</Box>
									</CardContent>
								</Card>
							</Grid>
						</Grid>

						{/* Second Row - More Unique Charts */}
						<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
							<Grid size={{ xs: 12, md: 6 }}>
								<Card>
									<CardHeader
										title="Market Performance"
										subheader="Quarterly analysis of market trends"
									/>
									<CardContent>
										<Box sx={{ height: 300 }}>
											{clientData.length > 0 ? (
												<div style={{ width: "100%", height: "250px" }}>
													<LineChart
														xAxis={[
															{
																data: ["Q1", "Q2", "Q3", "Q4"],
																scaleType: "point",
															},
														]}
														series={[
															{
																data: (() => {
																	// Try to get AI-generated quarterly data first
																	const aiData =
																		getAIChartData("quarterly") ||
																		getAIChartData("performance") ||
																		getAIChartData("market");
																	if (
																		aiData &&
																		aiData.data &&
																		Array.isArray(aiData.data)
																	) {
																		return aiData.data
																			.slice(0, 4)
																			.map(
																				(item: any) =>
																					item.value || item.desktop || 0
																			);
																	}

																	// Fallback: Create quarterly analysis from numeric data
																	const numericFields = dataColumns.filter(
																		(col) => {
																			const values = clientData
																				.map((record) => record[col])
																				.filter((v) => v != null);
																			return (
																				values.length > 0 &&
																				!isNaN(parseFloat(values[0]))
																			);
																		}
																	);

																	if (numericFields.length > 0) {
																		const field =
																			numericFields[numericFields.length - 1]; // Use last numeric field
																		const values = clientData
																			.map(
																				(record) =>
																					parseFloat(record[field]) || 0
																			)
																			.filter((v) => v > 0);
																		if (values.length >= 4) {
																			const quarterSize = Math.floor(
																				values.length / 4
																			);
																			const quarters = [];
																			for (let i = 0; i < 4; i++) {
																				const start = i * quarterSize;
																				const end =
																					i === 3
																						? values.length
																						: start + quarterSize;
																				const quarterValues = values.slice(
																					start,
																					end
																				);
																				const avg =
																					quarterValues.reduce(
																						(sum, v) => sum + v,
																						0
																					) / quarterValues.length;
																				quarters.push(Math.round(avg));
																			}
																			return quarters;
																		}
																	}

																	return [0, 0, 0, 0];
																})(),
																label: `${
																	dataColumns.find((col) => {
																		const values = clientData.map(
																			(record) => record[col]
																		);
																		return !isNaN(parseFloat(values[0]));
																	}) || "Performance"
																} Trends`,
																color: "#2e7d32",
																curve: "natural",
															},
														]}
														width={400}
														height={250}
														skipAnimation={true}
														slotProps={{
															noDataOverlay: { message: "No data available" },
														}}
													/>
												</div>
											) : (
												<Typography
													color="text.secondary"
													sx={{
														display: "flex",
														justifyContent: "center",
														alignItems: "center",
														height: "100%",
													}}>
													No data available
												</Typography>
											)}
										</Box>
									</CardContent>
								</Card>
							</Grid>
							<Grid size={{ xs: 12, md: 6 }}>
								<Card>
									<CardHeader
										title="Risk Assessment"
										subheader="Multi-factor risk analysis"
									/>
									<CardContent>
										<Box sx={{ height: 300 }}>
											{clientData.length > 0 && dataColumns.length >= 3 ? (
												<div style={{ height: "250px" }}>
													{/* Radar Chart Component */}
													<Box
														sx={{
															display: "flex",
															alignItems: "center",
															justifyContent: "center",
															height: 250,
															bgcolor: "grey.50",
															borderRadius: 1,
															border: "1px dashed",
															borderColor: "grey.300",
														}}>
														<Typography variant="body1" color="text.secondary">
															📊 Radar Chart Visualization
														</Typography>
													</Box>
												</div>
											) : (
												<Box
													sx={{
														display: "flex",
														alignItems: "center",
														justifyContent: "center",
														height: 250,
														bgcolor: "grey.100",
														borderRadius: 1,
													}}>
													<Typography color="text.secondary">
														📊 Not enough data for radar visualization
													</Typography>
												</Box>
											)}
										</Box>
									</CardContent>
								</Card>
							</Grid>
						</Grid>
					</>
				)}

			{/* Remove the Additional Components section from charts template */}
			{!config.showCharts && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					<Grid size={{ xs: 12, lg: 8 }}>
						<BusinessDataTable
							clientData={clientData}
							dataColumns={dataColumns}
						/>
					</Grid>
				</Grid>
			)}

			<Copyright sx={{ my: 4 }} />
		</Box>
	);
}
