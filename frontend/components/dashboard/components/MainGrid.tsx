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
	muiDashboardService,
	MUIDashboardData,
	BackendMetric,
} from "../../../lib/muiDashboardService";

// Import various chart components
import * as Charts from "../../charts";
import { PieChart } from "@mui/x-charts/PieChart";
import { BarChart } from "@mui/x-charts/BarChart";
import { LineChart } from "@mui/x-charts/LineChart";
import { ResponsiveRadar } from "@nivo/radar";

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
	trend: "up" | "down" | "neutral";
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
	// If this is the main dashboard, use the original layout
	if (dashboardType === "main") {
		return <OriginalMainGrid dashboardData={dashboardData} user={user} />;
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
}: {
	dashboardData?: MainGridProps["dashboardData"];
	user?: { client_id: string; company_name: string; email: string };
}) {
	const [muiData, setMuiData] = React.useState<MUIDashboardData>({
		kpis: [],
		pieCharts: [],
		barCharts: [],
		lineCharts: [],
		radarCharts: [],
		radialCharts: [],
		areaCharts: [],
		totalMetrics: 0,
		lastUpdated: "",
	});
	const [clientData, setClientData] = React.useState<any[]>([]);
	const [dataColumns, setDataColumns] = React.useState<any[]>([]);
	const [loading, setLoading] = React.useState(true);

	// State for chart dropdown selections
	const [chartDropdownSelections, setChartDropdownSelections] = React.useState<{
		[chartId: string]: string;
	}>({});

	// Helper function to filter chart data based on dropdown selection
	const getFilteredChartData = (chart: any) => {
		if (!chart.hasDropdown || !chart.dropdownOptions) {
			return chart.data;
		}

		const selectedValue = chartDropdownSelections[chart.id];
		if (!selectedValue || selectedValue === "all") {
			return chart.data;
		}

		// Filter data based on selected dropdown value
		return chart.data.filter(
			(item: any) =>
				(item.id || item.name || "")
					.toLowerCase()
					.includes(selectedValue.toLowerCase()) ||
				item.name === selectedValue ||
				item.id === selectedValue
		);
	};

	// Handle dropdown change
	const handleDropdownChange = (chartId: string, value: string) => {
		setChartDropdownSelections((prev) => ({
			...prev,
			[chartId]: value,
		}));
	};

	const summaryStats = {
		totalMetrics: muiData.totalMetrics,
		totalCharts:
			muiData.pieCharts.length +
			muiData.barCharts.length +
			muiData.lineCharts.length,
		totalKPIs: muiData.kpis.length,
		lastUpdated: muiData.lastUpdated,
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

	// Fetch REAL BACKEND DATA for main dashboard
	React.useEffect(() => {
		const fetchRealData = async () => {
			try {
				console.log("🔥 Loading MUI dashboard with backend data");

				// Use MUI dashboard service to get formatted data
				const processedData = await muiDashboardService.processMUIMetrics();
				setMuiData(processedData);

				// Get summary statistics
				const rawMetrics = await muiDashboardService.fetchMetrics();
				const stats = muiDashboardService.generateSummaryStats(rawMetrics);
				// setSummaryStats(stats); // This line was removed as per the new_code

				// Load client data using the SAME method as template dashboard
				await loadClientData();

				console.log("✅ MUI Dashboard data loaded:", {
					kpis: processedData.kpis.length,
					pieCharts: processedData.pieCharts.length,
					barCharts: processedData.barCharts.length,
					lineCharts: processedData.lineCharts.length,
					totalMetrics: processedData.totalMetrics,
				});
			} catch (error) {
				console.error("❌ Error loading MUI dashboard data:", error);
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

	return (
		<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
			{/* REAL Backend KPI Cards */}
			<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
				{/* Display real KPIs from backend */}
				{muiData.kpis.length > 0
					? muiData.kpis.map((card, index) => (
							<Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
								<StatCard
									title={card.title}
									value={card.value}
									interval={card.interval}
									trend={card.trend}
									trendValue={card.trendValue}
									data={card.data}
								/>
							</Grid>
					  ))
					: [
							{
								title: "Total Metrics",
								value: summaryStats.totalMetrics.toString(),
								interval: "Current dataset",
								trend: "neutral" as const,
								trendValue: "Real data",
								data: Array.from(
									{ length: 30 },
									() => summaryStats.totalMetrics
								),
							},
							{
								title: "Chart Data",
								value: summaryStats.totalCharts.toString(),
								interval: "Active charts",
								trend: "neutral" as const,
								trendValue: "Available",
								data: Array.from(
									{ length: 30 },
									() => summaryStats.totalCharts
								),
							},
							{
								title: "KPI Metrics",
								value: summaryStats.totalKPIs.toString(),
								interval: "Current period",
								trend: "neutral" as const,
								trendValue: "Calculated",
								data: Array.from({ length: 30 }, () => summaryStats.totalKPIs),
							},
							{
								title: "Last Updated",
								value: summaryStats.lastUpdated,
								interval: "Recent activity",
								trend: "neutral" as const,
								trendValue: "Current",
								data: Array.from({ length: 30 }, () => 1),
							},
					  ].map((card, index) => (
							<Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
								<StatCard
									title={card.title}
									value={card.value}
									interval={card.interval}
									trend={card.trend}
									trendValue={card.trendValue}
									data={card.data}
								/>
							</Grid>
					  ))}
			</Grid>
			{/* Business Data Table */}
			<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
				<Grid size={{ xs: 12 }}>
					<BusinessDataTable
						clientData={clientData}
						dataColumns={dataColumns}
						title="Business Data Overview"
						subtitle="Key business metrics and performance data from your uploaded data"
					/>
				</Grid>
			</Grid>

			{/* REAL BUSINESS DATA Charts - Only show if data exists */}
			{(muiData.lineCharts.length > 0 || muiData.pieCharts.length > 0) && (
				<>
					{/* Debug: Log available chart metrics */}
					{console.log("🔍 MainGrid - Available chart metrics:", {
						lineCharts: muiData.lineCharts.map((chart) => ({
							title: chart.title,
							dataLength: chart.data.length,
						})),
						pieCharts: muiData.pieCharts.map((chart) => ({
							title: chart.title,
							dataLength: chart.data.length,
						})),
					})}

					<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
						{muiData.lineCharts.length > 0 && (
							<Grid
								size={{ xs: 12, md: muiData.pieCharts.length > 0 ? 6 : 12 }}>
								<RevenueTrendsChart
									dashboardData={{
										totalRevenue: (summaryStats.totalMetrics || 100) * 500,
										totalOrders: summaryStats.totalMetrics || 325,
										averageOrderValue: Math.floor(
											((summaryStats.totalMetrics || 100) * 500) /
												(summaryStats.totalMetrics || 325)
										),
									}}
									revenueData={muiData.lineCharts[0].data}
								/>
							</Grid>
						)}
						{muiData.pieCharts.length > 0 && (
							<Grid
								size={{ xs: 12, md: muiData.lineCharts.length > 0 ? 6 : 12 }}>
								<SalesCategoryChart
									dashboardData={{
										totalSales: (summaryStats.totalMetrics || 100) * 400,
										topCategory: "Electronics",
										categoriesCount: muiData.pieCharts.length || 5,
									}}
									categoryData={(() => {
										// Find the best pie chart metric for sales data
										// Look for charts with meaningful sales values (not all identical small values)
										console.log(
											`🔍 Selecting best pie chart from ${muiData.pieCharts.length} available options`
										);

										let bestChart = null;
										let bestScore = 0;

										for (const chart of muiData.pieCharts) {
											const values = chart.data.map((item) => item.value || 0);
											const uniqueValues = [...new Set(values)];
											const hasVariedValues =
												uniqueValues.length > 1 || uniqueValues[0] > 10;
											const totalValue = values.reduce((a, b) => a + b, 0);
											const avgValue = totalValue / values.length;

											// Calculate a score for this chart
											let score = 0;

											// Prefer charts with varied values
											if (uniqueValues.length > 1) score += 100;

											// Prefer charts with realistic monetary ranges (10-50000)
											if (avgValue >= 100 && avgValue <= 50000) score += 200;
											else if (avgValue >= 10 && avgValue <= 100000)
												score += 100;
											else if (avgValue >= 1 && avgValue <= 10) score += 50; // Small values (counts)

											// Bonus for sales-related titles
											const title = chart.title?.toLowerCase() || "";
											if (
												title.includes("platform") ||
												title.includes("vendor") ||
												title.includes("sales")
											)
												score += 50;

											console.log(`🔍 Evaluating pie chart "${chart.title}":`, {
												values: values.slice(0, 3),
												uniqueValues: uniqueValues.length,
												avgValue: avgValue.toFixed(2),
												hasVariedValues,
												totalValue,
												score,
											});

											if (hasVariedValues && score > bestScore) {
												bestChart = chart;
												bestScore = score;
											}
										}

										if (bestChart) {
											console.log(
												`✅ Selected pie chart "${bestChart.title}" for Sales by Category (score: ${bestScore})`
											);
											return bestChart.data;
										}

										// Fallback to first chart if none meet criteria
										console.warn(
											"⚠️ No suitable pie chart found, using first available"
										);
										return muiData.pieCharts[0]?.data || [];
									})()}
								/>
							</Grid>
						)}
					</Grid>
				</>
			)}

			{/* Real Backend Charts - Pie Charts */}
			{muiData.pieCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.pieCharts.map((pieChart, index) => {
						// Check if this is a status chart
						const isStatusChart =
							pieChart.title?.toLowerCase().includes("status") ||
							pieChart.title?.toLowerCase().includes("activity") ||
							pieChart.title?.toLowerCase().includes("comparison") ||
							pieChart.data.some((item) =>
								["active", "inactive", "archived", "draft", "pending"].some(
									(status) =>
										(item.id || item.name || "").toLowerCase().includes(status)
								)
							);

						// Get filtered data based on dropdown selection
						const filteredData = getFilteredChartData(pieChart);
						const selectedValue = chartDropdownSelections[pieChart.id] || "all";

						return (
							<Grid key={index} size={{ xs: 12, md: 4 }}>
								<Card>
									<CardHeader
										title={pieChart.title}
										subheader={
											isStatusChart
												? `${pieChart.subtitle} • Status Distribution`
												: pieChart.subtitle
										}
										action={
											pieChart.hasDropdown &&
											pieChart.dropdownOptions && (
												<FormControl size="small" sx={{ minWidth: 120 }}>
													<InputLabel id={`chart-dropdown-${pieChart.id}`}>
														Filter
													</InputLabel>
													<Select
														labelId={`chart-dropdown-${pieChart.id}`}
														value={selectedValue}
														label="Filter"
														onChange={(e) =>
															handleDropdownChange(pieChart.id, e.target.value)
														}>
														{pieChart.dropdownOptions.map((option: any) => (
															<MenuItem key={option.value} value={option.value}>
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
														data: filteredData.map((item) => ({
															...item,
															// For status charts, format as counts instead of currency
															label: isStatusChart
																? `${item.id || item.name} (${
																		item.value
																  } items)`
																: item.label,
														})),
														...(isStatusChart
															? {}
															: { valueFormatter: (value) => `$${value}` }),
													},
												]}
												width={300}
												height={300}
												margin={{ top: 40, bottom: 40, left: 40, right: 40 }}
											/>
										</Box>
									</CardContent>
								</Card>
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* Real Backend Charts - Bar Charts */}
			{muiData.barCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.barCharts.map((barChart, index) => {
						// Get filtered data based on dropdown selection
						const filteredData = getFilteredChartData(barChart);
						const selectedValue = chartDropdownSelections[barChart.id] || "all";

						return (
							<Grid key={index} size={{ xs: 12, md: 6 }}>
								<Card>
									<CardHeader
										title={barChart.title}
										subheader={barChart.subtitle}
										action={
											barChart.hasDropdown &&
											barChart.dropdownOptions && (
												<FormControl size="small" sx={{ minWidth: 120 }}>
													<InputLabel id={`bar-chart-dropdown-${barChart.id}`}>
														Filter
													</InputLabel>
													<Select
														labelId={`bar-chart-dropdown-${barChart.id}`}
														value={selectedValue}
														label="Filter"
														onChange={(e) =>
															handleDropdownChange(barChart.id, e.target.value)
														}>
														{barChart.dropdownOptions.map((option: any) => (
															<MenuItem key={option.value} value={option.value}>
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
												dataset={filteredData}
												xAxis={[
													{
														scaleType: "band",
														dataKey: "name",
														tickPlacement: "middle",
														tickLabelPlacement: "middle",
													},
												]}
												series={[
													{
														dataKey: "value",
														label: "Value",
														valueFormatter: (value) => `$${value}`,
													},
												]}
												width={500}
												height={300}
												margin={{ top: 20, bottom: 60, left: 70, right: 20 }}
											/>
										</Box>
									</CardContent>
								</Card>
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* Real Backend Charts - Line Charts */}
			{muiData.lineCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.lineCharts.map((lineChart, index) => {
						// Get filtered data based on dropdown selection
						const filteredData = getFilteredChartData(lineChart);
						const selectedValue =
							chartDropdownSelections[lineChart.id] || "all";

						return (
							<Grid key={index} size={{ xs: 12, md: 6 }}>
								<Card>
									<CardHeader
										title={lineChart.title}
										subheader={lineChart.subtitle}
										action={
											lineChart.hasDropdown &&
											lineChart.dropdownOptions && (
												<FormControl size="small" sx={{ minWidth: 120 }}>
													<InputLabel
														id={`line-chart-dropdown-${lineChart.id}`}>
														Filter
													</InputLabel>
													<Select
														labelId={`line-chart-dropdown-${lineChart.id}`}
														value={selectedValue}
														label="Filter"
														onChange={(e) =>
															handleDropdownChange(lineChart.id, e.target.value)
														}>
														{lineChart.dropdownOptions.map((option: any) => (
															<MenuItem key={option.value} value={option.value}>
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
												dataset={filteredData}
												xAxis={[
													{
														scaleType: "point",
														dataKey: "month",
													},
												]}
												series={[
													{
														dataKey: "value",
														label: "Revenue",
														curve: "linear",
														valueFormatter: (value) => `$${value}`,
													},
												]}
												width={500}
												height={300}
												margin={{ top: 20, bottom: 60, left: 70, right: 20 }}
											/>
										</Box>
									</CardContent>
								</Card>
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* Real Backend Charts - Area Charts */}
			{muiData.areaCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.areaCharts.map((areaChart, index) => (
						<Grid key={index} size={{ xs: 12, md: 6 }}>
							<Card>
								<CardHeader
									title={areaChart.title}
									subheader={areaChart.subtitle}
								/>
								<CardContent>
									<Box sx={{ height: 300 }}>
										<LineChart
											dataset={areaChart.data}
											xAxis={[{ dataKey: "name", scaleType: "band" }]}
											series={[
												{
													dataKey: "value",
													label: "Value",
													area: true,
													stack: areaChart.originalChartType.includes("Stacked")
														? "total"
														: undefined,
													color: "#1976d2",
												},
												{
													dataKey: "desktop",
													label: "Desktop",
													area: true,
													stack: areaChart.originalChartType.includes("Stacked")
														? "total"
														: undefined,
													color: "#42a5f5",
												},
												{
													dataKey: "mobile",
													label: "Mobile",
													area: true,
													stack: areaChart.originalChartType.includes("Stacked")
														? "total"
														: undefined,
													color: "#90caf9",
												},
											]}
											width={500}
											height={300}
											margin={{ top: 40, bottom: 40, left: 40, right: 40 }}
										/>
									</Box>
								</CardContent>
							</Card>
						</Grid>
					))}
				</Grid>
			)}

			{/* Real Backend Charts - Radar Charts */}
			{muiData.radarCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.radarCharts.map((radarChart, index) => {
						// Get filtered data based on dropdown selection
						const filteredData = getFilteredChartData(radarChart);
						const selectedValue =
							chartDropdownSelections[radarChart.id] || "all";

						return (
							<Grid key={index} size={{ xs: 12, md: 6 }}>
								<Card>
									<CardHeader
										title={radarChart.title}
										subheader={radarChart.subtitle}
										action={
											radarChart.hasDropdown &&
											radarChart.dropdownOptions && (
												<FormControl size="small" sx={{ minWidth: 120 }}>
													<InputLabel
														id={`radar-chart-dropdown-${radarChart.id}`}>
														Filter
													</InputLabel>
													<Select
														labelId={`radar-chart-dropdown-${radarChart.id}`}
														value={selectedValue}
														label="Filter"
														onChange={(e) =>
															handleDropdownChange(
																radarChart.id,
																e.target.value
															)
														}>
														{radarChart.dropdownOptions.map((option: any) => (
															<MenuItem key={option.value} value={option.value}>
																{option.label}
															</MenuItem>
														))}
													</Select>
												</FormControl>
											)
										}
									/>
									<CardContent>
										<Box sx={{ height: 400 }}>
											<ResponsiveRadar
												data={filteredData.map((item) => ({
													name: item.name,
													value: item.value,
													...item,
												}))}
												keys={["value"]}
												indexBy="name"
												maxValue="auto"
												margin={{ top: 70, right: 80, bottom: 40, left: 80 }}
												curve="linearClosed"
												borderWidth={2}
												borderColor={{ from: "color" }}
												gridLevels={5}
												gridShape="circular"
												gridLabelOffset={36}
												enableDots={true}
												dotSize={10}
												dotColor={{ theme: "background" }}
												dotBorderWidth={2}
												dotBorderColor={{ from: "color" }}
												enableDotLabel={true}
												dotLabel="value"
												dotLabelYOffset={-12}
												colors={{ scheme: "nivo" }}
												fillOpacity={0.25}
												blendMode="multiply"
												animate={true}
												motionConfig="wobbly"
												isInteractive={true}
											/>
										</Box>
									</CardContent>
								</Card>
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* Real Backend Charts - Radial Charts */}
			{muiData.radialCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.radialCharts.map((radialChart, index) => (
						<Grid key={index} size={{ xs: 12, md: 4 }}>
							<Card>
								<CardHeader
									title={radialChart.title}
									subheader={radialChart.subtitle}
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
													data: radialChart.data,
													innerRadius: 40,
													outerRadius: 80,
												},
											]}
											width={300}
											height={300}
											margin={{ top: 40, bottom: 40, left: 40, right: 40 }}
										/>
									</Box>
								</CardContent>
							</Card>
						</Grid>
					))}
				</Grid>
			)}

			{/* Fallback - Default country chart if no backend charts available */}
			{muiData.pieCharts.length === 0 && muiData.barCharts.length === 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					<Grid size={{ xs: 12, md: 4 }}>
						<ChartUserByCountry />
					</Grid>
					<Grid size={{ xs: 12, md: 8 }}>
						<Card>
							<CardHeader title="Dashboard Summary" />
							<CardContent>
								<Typography variant="body1" color="text.secondary">
									Total Metrics: {summaryStats.totalMetrics}
									<br />
									Charts: {summaryStats.totalCharts}
									<br />
									KPIs: {summaryStats.totalKPIs}
									<br />
									Last Updated: {summaryStats.lastUpdated}
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
				const metricsResponse = await api.get("/dashboard/metrics");
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

	// Get template configuration - COMPLETELY DIFFERENT TEMPLATES
	const getTemplateConfig = () => {
		const filteredData = getFilteredData(clientData);
		const totalRecords = filteredData.length;

		// Create COMPLETELY DIFFERENT templates
		switch (dashboardType) {
			case "sales":
			case "1":
				// DATA ANALYTICS TEMPLATE - Table-focused, raw data analysis
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
				// VISUAL ANALYTICS TEMPLATE - Chart-focused, visual insights
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

	const config = getTemplateConfig();

	return (
		<Box sx={{ width: "100%", maxWidth: { sm: "100%", md: "1700px" } }}>
			{/* Dashboard Header */}
			<Typography component="h1" variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
				{config.title}
			</Typography>
			<Typography variant="body1" sx={{ mb: 3, color: "text.secondary" }}>
				{config.subtitle}
			</Typography>

			{/* KPI Cards */}
			<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
				{config.cards.map((card, index) => (
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

			{/* Template 1: Data Table */}
			{config.showDataTable && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					<Grid size={{ xs: 12 }}>
						<Card>
							<CardHeader
								title="Your Data"
								subheader={`${clientData.length} records from your database`}
							/>
							<CardContent>
								{clientData.length > 0 ? (
									<Box sx={{ overflow: "auto", maxHeight: 400 }}>
										<table
											style={{ width: "100%", borderCollapse: "collapse" }}>
											<thead>
												<tr style={{ backgroundColor: "#f5f5f5" }}>
													{dataColumns.slice(0, 6).map((column) => (
														<th
															key={column}
															style={{
																padding: "12px",
																textAlign: "left",
																borderBottom: "1px solid #ddd",
															}}>
															{column}
														</th>
													))}
												</tr>
											</thead>
											<tbody>
												{clientData.slice(0, 10).map((row, index) => (
													<tr key={index}>
														{dataColumns.slice(0, 6).map((column) => (
															<td
																key={column}
																style={{
																	padding: "12px",
																	borderBottom: "1px solid #eee",
																}}>
																{String(row[column] || "-")}
															</td>
														))}
													</tr>
												))}
											</tbody>
										</table>
									</Box>
								) : (
									<Typography>No data available</Typography>
								)}
							</CardContent>
						</Card>
					</Grid>
				</Grid>
			)}

			{/* Template 2: Charts */}
			{config.showCharts && (
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
											<LineChart
												xAxis={[
													{
														data: [
															"Jan",
															"Feb",
															"Mar",
															"Apr",
															"May",
															"Jun",
															"Jul",
															"Aug",
															"Sep",
															"Oct",
														],
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
														label: `${dataColumns[1] || "Secondary"} Metric`,
														color: "#dc004e",
													},
												]}
												width={600}
												height={250}
											/>
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

															return [{ id: 0, value: 100, label: "No Data" }];
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
											/>
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
																		(record) => parseFloat(record[field]) || 0
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
											/>
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
												<ResponsiveRadar
													data={(() => {
														// Try to get AI-generated radar data first
														const aiData =
															getAIChartData("risk") ||
															getAIChartData("radar") ||
															getAIChartData("analysis");
														if (
															aiData &&
															aiData.data &&
															Array.isArray(aiData.data)
														) {
															return aiData.data.map((item: any) => ({
																metric: item.name || item.browser || "Metric",
																value: item.value || item.desktop || 50,
															}));
														}

														// Fallback: Create radar chart from numeric fields
														const numericFields = dataColumns
															.filter((col) => {
																const values = clientData
																	.map((record) => record[col])
																	.filter((v) => v != null);
																return (
																	values.length > 0 &&
																	!isNaN(parseFloat(values[0]))
																);
															})
															.slice(0, 5); // Limit to 5 metrics

														if (numericFields.length >= 3) {
															return numericFields.map((field) => {
																const values = clientData
																	.map(
																		(record) => parseFloat(record[field]) || 0
																	)
																	.filter((v) => v > 0);
																if (values.length > 0) {
																	const avg =
																		values.reduce((sum, v) => sum + v, 0) /
																		values.length;
																	const normalized = Math.min(
																		Math.round(
																			avg / (Math.max(...values) / 100)
																		),
																		100
																	);
																	return {
																		metric: field
																			.replace(/_/g, " ")
																			.replace(/([A-Z])/g, " $1")
																			.trim(),
																		value: Math.max(normalized, 10), // Ensure minimum visibility
																	};
																}
																return { metric: field, value: 50 };
															});
														}

														// Default fallback
														return [
															{ metric: "Data Quality", value: 80 },
															{ metric: "Completeness", value: 75 },
															{ metric: "Accuracy", value: 85 },
															{ metric: "Consistency", value: 90 },
															{ metric: "Timeliness", value: 70 },
														];
													})()}
													keys={["value"]}
													indexBy="metric"
													maxValue={100}
													margin={{ top: 40, right: 80, bottom: 40, left: 80 }}
													curve="linearClosed"
													borderWidth={2}
													borderColor={{ from: "color" }}
													gridLevels={5}
													gridShape="circular"
													gridLabelOffset={36}
													fillOpacity={0.3}
													blendMode="multiply"
													animate={true}
													motionConfig="wobbly"
													isInteractive={true}
													colors={{ scheme: "category10" }}
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
												Insufficient data for analysis
											</Typography>
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
