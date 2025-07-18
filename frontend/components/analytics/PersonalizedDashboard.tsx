import React, { useState, useEffect } from "react";
import api from "../../lib/axios";
import {
	RefreshCw,
	Settings,
	AlertCircle,
	CheckCircle,
	Loader2,
} from "lucide-react";
import { SimpleStatCard, ChartCard } from "./TailwindStats";
import {
	SimpleBarChart,
	SimpleLineChart,
	SimplePieChart,
} from "./TailwindCharts";

// Types for dashboard configuration
interface DashboardLayout {
	grid_cols: number;
	grid_rows: number;
	gap: number;
	responsive: boolean;
}

interface KPIWidget {
	id: string;
	title: string;
	value: string;
	icon: string;
	icon_color: string;
	icon_bg_color: string;
	trend?: {
		value: string;
		isPositive: boolean;
	};
	position: {
		row: number;
		col: number;
	};
	size: {
		width: number;
		height: number;
	};
}

interface ChartWidget {
	id: string;
	title: string;
	subtitle?: string;
	chart_type: "line" | "bar" | "pie" | "doughnut" | "area" | "scatter";
	data_source: string;
	config: any;
	position: {
		row: number;
		col: number;
	};
	size: {
		width: number;
		height: number;
	};
}

interface DashboardConfig {
	client_id: string;
	title: string;
	subtitle?: string;
	layout: DashboardLayout;
	kpi_widgets: KPIWidget[];
	chart_widgets: ChartWidget[];
	theme: string;
	last_generated: string;
	version: string;
}

interface DashboardMetric {
	metric_id: string;
	client_id: string;
	metric_name: string;
	metric_value: any;
	metric_type: "kpi" | "chart_data" | "trend";
	calculated_at: string;
}

interface DashboardStatus {
	client_id: string;
	has_dashboard: boolean;
	is_generated: boolean;
	last_updated: string | null;
	metrics_count: number;
}

interface PersonalizedDashboardProps {
	onGenerateClick?: () => void;
	showGenerateButton?: boolean;
	className?: string;
}

const PersonalizedDashboard: React.FC<PersonalizedDashboardProps> = ({
	onGenerateClick,
	showGenerateButton = true,
	className = "",
}) => {
	const [dashboardConfig, setDashboardConfig] =
		useState<DashboardConfig | null>(null);
	const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetric[]>(
		[]
	);
	const [dashboardStatus, setDashboardStatus] =
		useState<DashboardStatus | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [generating, setGenerating] = useState(false);
	const [refreshing, setRefreshing] = useState(false);

	useEffect(() => {
		loadDashboard();
	}, []);

	const loadDashboard = async () => {
		try {
			setLoading(true);
			setError(null);

			// Get dashboard status first
			const statusResponse = await api.get("/dashboard/status");
			setDashboardStatus(statusResponse.data);

			if (statusResponse.data.has_dashboard) {
				// Load dashboard configuration and metrics
				const [configResponse, metricsResponse] = await Promise.all([
					api.get("/dashboard/config"),
					api.get("/dashboard/metrics"),
				]);

				setDashboardConfig(configResponse.data);
				setDashboardMetrics(metricsResponse.data);
			}
		} catch (err: any) {
			console.error("Failed to load dashboard:", err);
			setError(err.response?.data?.detail || "Failed to load dashboard");
		} finally {
			setLoading(false);
		}
	};

	const generateDashboard = async (force = false) => {
		try {
			setGenerating(true);
			setError(null);

			const response = await api.post("/dashboard/generate", {
				force_regenerate: force,
				include_sample_data: true,
			});

			if (response.data.success) {
				await loadDashboard();
				if (onGenerateClick) onGenerateClick();
			}
		} catch (err: any) {
			console.error("Failed to generate dashboard:", err);
			setError(err.response?.data?.detail || "Failed to generate dashboard");
		} finally {
			setGenerating(false);
		}
	};

	const refreshMetrics = async () => {
		try {
			setRefreshing(true);
			setError(null);

			await api.post("/dashboard/refresh-metrics", {});
			await loadDashboard();
		} catch (err: any) {
			console.error("Failed to refresh metrics:", err);
			setError(err.response?.data?.detail || "Failed to refresh metrics");
		} finally {
			setRefreshing(false);
		}
	};

	const getMetricData = (dataSource: string) => {
		const metric = dashboardMetrics.find((m) => m.metric_name === dataSource);
		return metric?.metric_value || null;
	};

	const renderKPIWidgets = () => {
		if (!dashboardConfig?.kpi_widgets) return null;

		return dashboardConfig.kpi_widgets.map((widget) => {
			const metricData = getMetricData(widget.id);
			const actualValue = metricData?.value || widget.value;
			const actualTrend = metricData?.trend || widget.trend;

			// Convert to Tailwind UI stat format
			const statData = {
				name: widget.title,
				stat: actualValue,
				previousStat: "Previous period", // You can calculate this from actual data
				change: actualTrend?.value || "12.5%",
				changeType: actualTrend?.isPositive
					? ("increase" as const)
					: ("decrease" as const),
			};

			return <SimpleStatCard key={widget.id} {...statData} />;
		});
	};

	const renderChartWidgets = () => {
		if (!dashboardConfig?.chart_widgets) return null;

		return dashboardConfig.chart_widgets.map((widget) => {
			const metricData = getMetricData(widget.data_source);
			const chartData = metricData?.data || [];

			// Convert chart data to our simple format
			const formattedData = chartData.map((item: any) => ({
				label:
					item.category ||
					item.month ||
					item.name ||
					`Item ${chartData.indexOf(item) + 1}`,
				value: item.value || item.amount || 0,
			}));

			// Render appropriate chart type
			const renderChart = () => {
				switch (widget.chart_type) {
					case "bar":
						return <SimpleBarChart data={formattedData} />;
					case "line":
					case "area":
						return <SimpleLineChart data={formattedData} />;
					case "pie":
					case "doughnut":
						return <SimplePieChart data={formattedData} />;
					default:
						return <SimpleBarChart data={formattedData} />;
				}
			};

			return (
				<ChartCard
					key={widget.id}
					title={widget.title}
					subtitle={widget.subtitle}
					className="col-span-full">
					{chartData.length > 0 ? (
						renderChart()
					) : (
						<div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
							<div className="text-center">
								<div className="text-gray-400 text-lg font-medium">
									No data available
								</div>
								<div className="text-gray-500 text-sm mt-1">
									Refresh metrics to load chart data
								</div>
							</div>
						</div>
					)}
				</ChartCard>
			);
		});
	};

	const renderEmptyState = () => (
		<div className="text-center py-12">
			<div className="mx-auto h-12 w-12 text-gray-400">
				<Settings className="h-12 w-12" />
			</div>
			<h3 className="mt-2 text-sm font-semibold text-gray-900">
				No Dashboard Generated Yet
			</h3>
			<p className="mt-1 text-sm text-gray-500">
				Generate your personalized dashboard to see AI-powered insights and
				visualizations based on your data.
			</p>
			{showGenerateButton && (
				<div className="mt-6">
					<button
						onClick={() => generateDashboard(false)}
						disabled={generating}
						className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50">
						{generating ? (
							<>
								<Loader2 className="-ml-0.5 mr-1.5 h-5 w-5 animate-spin" />
								Generating...
							</>
						) : (
							<>
								<Settings className="-ml-0.5 mr-1.5 h-5 w-5" />
								Generate Dashboard
							</>
						)}
					</button>
				</div>
			)}
		</div>
	);

	const renderError = () => (
		<div className="text-center py-12">
			<AlertCircle className="mx-auto h-12 w-12 text-red-500" />
			<h3 className="mt-2 text-sm font-semibold text-gray-900">
				Error Loading Dashboard
			</h3>
			<p className="mt-1 text-sm text-gray-500">{error}</p>
			<div className="mt-6">
				<button
					onClick={loadDashboard}
					className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
					<RefreshCw className="-ml-0.5 mr-1.5 h-5 w-5" />
					Try Again
				</button>
			</div>
		</div>
	);

	if (loading) {
		return (
			<div className="flex items-center justify-center py-12">
				<Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
				<span className="ml-3 text-sm text-gray-500">Loading dashboard...</span>
			</div>
		);
	}

	if (error) {
		return renderError();
	}

	if (!dashboardStatus?.has_dashboard) {
		return renderEmptyState();
	}

	return (
		<div className={`space-y-6 ${className}`}>
			{/* Dashboard Header */}
			<div className="md:flex md:items-center md:justify-between">
				<div className="min-w-0 flex-1">
					<h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
						{dashboardConfig?.title || "Your Dashboard"}
					</h2>
					{dashboardConfig?.subtitle && (
						<p className="mt-1 text-sm text-gray-500">
							{dashboardConfig.subtitle}
						</p>
					)}
				</div>
				<div className="mt-4 flex md:ml-4 md:mt-0">
					<button
						onClick={refreshMetrics}
						disabled={refreshing}
						className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50">
						<RefreshCw
							className={`-ml-0.5 mr-1.5 h-5 w-5 text-gray-400 ${
								refreshing ? "animate-spin" : ""
							}`}
						/>
						Refresh
					</button>
					{showGenerateButton && (
						<button
							onClick={() => generateDashboard(true)}
							disabled={generating}
							className="ml-3 inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50">
							{generating ? (
								<>
									<Loader2 className="-ml-0.5 mr-1.5 h-5 w-5 animate-spin" />
									Generating...
								</>
							) : (
								<>
									<Settings className="-ml-0.5 mr-1.5 h-5 w-5" />
									Regenerate
								</>
							)}
						</button>
					)}
				</div>
			</div>

			{/* Dashboard Status */}
			{dashboardStatus && (
				<div className="rounded-md bg-green-50 p-4">
					<div className="flex">
						<div className="flex-shrink-0">
							<CheckCircle className="h-5 w-5 text-green-400" />
						</div>
						<div className="ml-3">
							<p className="text-sm font-medium text-green-800">
								Dashboard generated • {dashboardStatus.metrics_count} metrics •
								Last updated:{" "}
								{dashboardStatus.last_updated
									? new Date(dashboardStatus.last_updated).toLocaleDateString()
									: "Never"}
							</p>
						</div>
					</div>
				</div>
			)}

			{/* KPI Stats Grid - Official Tailwind UI Pattern */}
			<div>
				<h3 className="text-base font-semibold leading-6 text-gray-900">
					Key Performance Indicators
				</h3>
				<dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
					{renderKPIWidgets()}
				</dl>
			</div>

			{/* Chart Widgets */}
			<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
				{renderChartWidgets()}
			</div>
		</div>
	);
};

export default PersonalizedDashboard;
