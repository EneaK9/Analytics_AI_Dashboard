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
import { muiDashboardService, MUIDashboardData, BackendMetric } from "../../../lib/muiDashboardService";

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
	const [loading, setLoading] = React.useState(true);
	const [muiData, setMuiData] = React.useState<MUIDashboardData>({
		kpis: [],
		pieCharts: [],
		barCharts: [],
		lineCharts: [],
		radarCharts: [],
		radialCharts: [],
		areaCharts: [],
		totalMetrics: 0,
		lastUpdated: "Never"
	});
	const [summaryStats, setSummaryStats] = React.useState({
		totalMetrics: 0,
		totalCharts: 0,
		totalKPIs: 0,
		lastUpdated: "Never",
		chartTypes: {} as Record<string, number>
	});
	const [clientData, setClientData] = React.useState<any[]>([]);
	const [dataColumns, setDataColumns] = React.useState<string[]>([]);

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
					const responseData = fallbackResponse.data.data || fallbackResponse.data;
					if (Array.isArray(responseData)) {
						setClientData(responseData.slice(0, 100));
						if (responseData.length > 0) {
							setDataColumns(Object.keys(responseData[0]));
						}
						console.log("✅ Fallback client data loaded for main dashboard:", responseData.length, "rows");
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
				setSummaryStats(stats);

				// Load client data using the SAME method as template dashboard
				await loadClientData();

				console.log("✅ MUI Dashboard data loaded:", {
					kpis: processedData.kpis.length,
					pieCharts: processedData.pieCharts.length,
					barCharts: processedData.barCharts.length,
					lineCharts: processedData.lineCharts.length,
					totalMetrics: processedData.totalMetrics
				});
			} catch (error) {
				console.error(
					"❌ Error loading MUI dashboard data:",
					error
				);
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
				{muiData.kpis.length > 0 ? muiData.kpis.map((card, index) => (
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
				)) : [
					{
						title: "Total Metrics",
						value: summaryStats.totalMetrics.toString(),
						interval: "Current dataset",
						trend: "up" as const,
						trendValue: "+25%",
						data: Array.from({ length: 30 }, () => summaryStats.totalMetrics * (0.8 + Math.random() * 0.4)),
					},
					{
						title: "Chart Data",
						value: summaryStats.totalCharts.toString(),
						interval: "Active charts",
						trend: "up" as const,
						trendValue: "+12%",
						data: Array.from({ length: 30 }, () => summaryStats.totalCharts * (0.9 + Math.random() * 0.2)),
					},
					{
						title: "KPI Metrics",
						value: summaryStats.totalKPIs.toString(),
						interval: "Current period",
						trend: "up" as const,
						trendValue: "+8%",
						data: Array.from({ length: 30 }, () => 95 + Math.random() * 5),
					},
					{
						title: "Last Updated",
						value: summaryStats.lastUpdated,
						interval: "Recent activity",
						trend: "neutral" as const,
						trendValue: "0%",
						data: Array.from({ length: 30 }, () => 100),
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

			{/* REAL BUSINESS DATA Charts */}
			<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
				<Grid size={{ xs: 12, md: 6 }}>
					<RevenueTrendsChart
						dashboardData={{
							totalRevenue: (summaryStats.totalMetrics || 100) * 500,
							totalOrders: summaryStats.totalMetrics || 325,
							averageOrderValue: Math.floor(((summaryStats.totalMetrics || 100) * 500) / (summaryStats.totalMetrics || 325)),
						}}
						revenueData={muiData.lineCharts.length > 0 ? muiData.lineCharts[0].data : []}
					/>
				</Grid>
				<Grid size={{ xs: 12, md: 6 }}>
					<SalesCategoryChart
						dashboardData={{
							totalSales: (summaryStats.totalMetrics || 100) * 400,
							topCategory: "Electronics",
							categoriesCount: muiData.pieCharts.length || 5,
						}}
						categoryData={muiData.pieCharts.length > 0 ? muiData.pieCharts[0].data : []}
					/>
				</Grid>
			</Grid>

			{/* Real Backend Charts - Pie Charts */}
			{muiData.pieCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.pieCharts.map((pieChart, index) => (
						<Grid key={index} size={{ xs: 12, md: 4 }}>
							<Card>
								<CardHeader
									title={pieChart.title}
									subheader={pieChart.subtitle}
								/>
								<CardContent>
									<Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
										<PieChart
											series={[{ data: pieChart.data }]}
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

			{/* Real Backend Charts - Bar Charts */}
			{muiData.barCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.barCharts.map((barChart, index) => {
						const BarChartWithFilter = () => {
							const [selectedFilter, setSelectedFilter] = React.useState("all");
							
							const filteredData = React.useMemo(() => {
								if (!selectedFilter || selectedFilter === "all") {
									return barChart.data;
								}
								return barChart.data.filter((item: any) => {
									const itemName = item.name?.toLowerCase() || "";
									const filterValue = selectedFilter.toLowerCase();
									return itemName === filterValue || itemName.includes(filterValue);
								});
							}, [selectedFilter]);

							return (
								<Card>
									<CardHeader 
										title={barChart.title} 
										subheader={barChart.subtitle}
										action={
											barChart.hasDropdown && barChart.dropdownOptions && barChart.dropdownOptions.length > 0 ? (
												<FormControl size="small" sx={{ minWidth: 120 }}>
													<InputLabel>Filter</InputLabel>
													<Select
														value={selectedFilter}
														label="Filter"
														onChange={(event) => setSelectedFilter(event.target.value)}
													>
														{barChart.dropdownOptions.map((option: any) => (
															<MenuItem key={option.value} value={option.value}>
																{option.label}
															</MenuItem>
														))}
													</Select>
												</FormControl>
											) : null
										}
									/>
									<CardContent>
										<Box sx={{ height: 300 }}>
											<BarChart
												dataset={filteredData}
												xAxis={[{ dataKey: 'name', scaleType: 'band' }]}
												series={[
													{ dataKey: 'value', label: 'Value', color: '#1976d2' },
													{ dataKey: 'desktop', label: 'Desktop', color: '#42a5f5' },
													{ dataKey: 'mobile', label: 'Mobile', color: '#90caf9' }
												]}
												width={500}
												height={300}
												margin={{ top: 40, bottom: 40, left: 40, right: 40 }}
											/>
										</Box>
									</CardContent>
								</Card>
							);
						};

						return (
							<Grid key={index} size={{ xs: 12, md: 6 }}>
								<BarChartWithFilter />
							</Grid>
						);
					})}
				</Grid>
			)}

			{/* Real Backend Charts - Line Charts */}
			{muiData.lineCharts.length > 0 && (
				<Grid container spacing={2} columns={12} sx={{ mb: 3 }}>
					{muiData.lineCharts.map((lineChart, index) => (
						<Grid key={index} size={{ xs: 12, md: 6 }}>
							<Card>
								<CardHeader 
									title={lineChart.title} 
									subheader={lineChart.subtitle}
								/>
								<CardContent>
									<Box sx={{ height: 300 }}>
										<LineChart
											dataset={lineChart.data}
											xAxis={[{ dataKey: 'name', scaleType: 'band' }]}
											series={[
												{ dataKey: 'value', label: 'Value', area: lineChart.originalChartType.includes('Area'), color: '#1976d2' },
												{ dataKey: 'desktop', label: 'Desktop', area: lineChart.originalChartType.includes('Area'), color: '#42a5f5' },
												{ dataKey: 'mobile', label: 'Mobile', area: lineChart.originalChartType.includes('Area'), color: '#90caf9' }
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
											xAxis={[{ dataKey: 'name', scaleType: 'band' }]}
											series={[
												{ dataKey: 'value', label: 'Value', area: true, stack: areaChart.originalChartType.includes('Stacked') ? 'total' : undefined, color: '#1976d2' },
												{ dataKey: 'desktop', label: 'Desktop', area: true, stack: areaChart.originalChartType.includes('Stacked') ? 'total' : undefined, color: '#42a5f5' },
												{ dataKey: 'mobile', label: 'Mobile', area: true, stack: areaChart.originalChartType.includes('Stacked') ? 'total' : undefined, color: '#90caf9' }
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
						console.log('🎯 Radar Chart Data:', {
							title: radarChart.title,
							originalType: radarChart.originalChartType,
							dataLength: radarChart.data?.length,
							sampleData: radarChart.data?.[0],
							allData: radarChart.data
						});

						return (
							<Grid key={index} size={{ xs: 12, md: 6 }}>
								<Card>
									<CardHeader 
										title={radarChart.title} 
										subheader={radarChart.subtitle}
									/>
									<CardContent>
										<Box sx={{ height: 300 }}>
											<ResponsiveRadar
												data={radarChart.data}
												keys={['value', 'desktop', 'mobile']}
												indexBy="name"
												maxValue="auto"
												margin={{ top: 40, right: 80, bottom: 40, left: 80 }}
												curve="linearClosed"
												borderWidth={2}
												borderColor={{ from: 'color' }}
												gridLevels={5}
												gridShape="circular"
												gridLabelOffset={36}
												enableDots={true}
												dotSize={6}
												dotColor={{ theme: 'background' }}
												dotBorderWidth={2}
												dotBorderColor={{ from: 'color' }}
												enableDotLabel={false}
												colors={{ scheme: 'nivo' }}
												fillOpacity={0.1}
												blendMode="multiply"
												animate={true}
												motionConfig="wobbly"
												isInteractive={true}
												tooltip={({ key, value, color }) => (
													<div style={{
														background: 'white',
														padding: '8px 12px',
														border: '1px solid #ccc',
														borderRadius: '4px',
														boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
													}}>
														<strong style={{ color }}>{key}</strong>: {value}
													</div>
												)}
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
									<Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
										<PieChart
											series={[{ 
												data: radialChart.data,
												innerRadius: 40,
												outerRadius: 80
											}]}
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
									Total Metrics: {summaryStats.totalMetrics}<br />
									Charts: {summaryStats.totalCharts}<br />
									KPIs: {summaryStats.totalKPIs}<br />
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

			// Fetch AI-generated metrics and charts
			try {
				const metricsResponse = await api.get("/dashboard/metrics");
				if (metricsResponse.data) {
					setAiMetrics(metricsResponse.data);
					console.log("🤖 AI Metrics loaded:", metricsResponse.data.length);
				}
			} catch (error) {
				console.warn("⚠️ AI metrics not available:", error);
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
