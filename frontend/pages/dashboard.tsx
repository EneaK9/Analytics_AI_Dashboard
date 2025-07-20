"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import {
	TrendingUp,
	DollarSign,
	Users,
	LogOut,
	Database,
	BarChart3,
	Activity,
	Target,
	Package,
	ShoppingCart,
} from "lucide-react";
import api from "../lib/axios";

// Import AI-powered analytics components

import SmartMonthlySalesChart from "../components/analytics/SmartMonthlySalesChart";
import {
	StatisticsChart,
	MonthlyTarget,
	RecentOrders,
} from "../components/analytics";
import {
	ShadcnBarChart,
	ShadcnLineChart,
	ShadcnPieChart,
	ShadcnAreaChart,
	ShadcnInteractiveBar,
	ShadcnMultipleArea,
	ShadcnInteractiveDonut,
} from "../components/charts";

import { clientDataService } from "../lib/clientDataService";
import { dashboardService, DashboardConfig } from "../lib/dashboardService";

// Dynamic Chart Renderer Component
const DynamicChartRenderer = ({
	widget,
	clientData,
}: {
	widget: {
		chart_type: string;
		title: string;
		subtitle?: string;
		config?: Record<string, unknown>;
	};
	clientData: Record<string, unknown>[];
}) => {
	const getChartComponent = () => {
		const chartType = widget.chart_type;
		const title = widget.title;
		const config = widget.config || {};

		// 🎯 EXTRACT REAL DATA KEYS FROM AI ORCHESTRATOR
		const dataColumns = (config.data_columns as Record<string, string>) || {};
		const columnMapping =
			(config.column_mapping as Record<string, string>) || {};
		const xAxisKey = dataColumns.xAxisKey || columnMapping.x_axis || "name";
		const dataKey = dataColumns.dataKey || columnMapping.y_axis || "value";

		// 🎨 PROFESSIONAL CHART SELECTION - Using REAL shadcn/ui + Recharts

		switch (chartType) {
			// 🔥 NEW INTERACTIVE SHADCN CHARTS
			case "interactive_bar":
			case "INTERACTIVE_BAR":
				return (
					<ShadcnInteractiveBar
						title={title}
						description="Interactive data comparison"
						data={clientData}
						dataKey1={dataKey}
						dataKey2="quantity"
						xAxisKey={xAxisKey}
					/>
				);

			case "multiple_area":
			case "MULTIPLE_AREA":
				return (
					<ShadcnMultipleArea
						title={title}
						description="Multi-dimensional analysis"
						data={clientData}
						dataKey1={dataKey}
						dataKey2="total_value"
						xAxisKey={xAxisKey}
					/>
				);

			case "interactive_donut":
			case "INTERACTIVE_DONUT":
				return (
					<ShadcnInteractiveDonut
						title={title}
						description="Interactive distribution"
						data={clientData}
						dataKey={dataKey}
						nameKey={xAxisKey}
					/>
				);
			case "line":
			case "LINE":
			case "spline":
				return (
					<ShadcnLineChart
						title={title}
						description="Performance trend analysis"
						data={clientData}
						dataKey={dataKey}
						xAxisKey={xAxisKey}
						height={200}
						color="#3C50E0"
					/>
				);

			case "bar":
			case "BAR":
			case "column":
				return (
					<ShadcnInteractiveBar
						title={title}
						description="Interactive data comparison"
						data={clientData}
						dataKey1={dataKey}
						dataKey2="quantity"
						xAxisKey={xAxisKey}
					/>
				);

			case "horizontal":
				return (
					<ShadcnBarChart
						title={title}
						description="Comparative analysis"
						data={clientData}
						dataKey={dataKey}
						xAxisKey={xAxisKey}
						height={200}
						color="#00C49F"
					/>
				);

			case "pie":
			case "PIE":
			case "doughnut":
			case "DOUGHNUT":
				return (
					<ShadcnPieChart
						title={title}
						description="Distribution breakdown"
						data={clientData}
						dataKey={dataKey}
						nameKey={xAxisKey}
						height={200}
						innerRadius={chartType.includes("doughnut") ? 60 : 0}
					/>
				);

			case "area":
			case "AREA":
				return (
					<ShadcnMultipleArea
						title={title}
						description="Multi-dimensional volume analysis"
						data={clientData}
						dataKey1={dataKey}
						dataKey2="quantity"
						xAxisKey={xAxisKey}
					/>
				);

			case "scatter":
			case "SCATTER":
			case "correlation":
				// Use line chart for scatter/correlation data
				return (
					<ShadcnLineChart
						title={title}
						description="Correlation analysis"
						data={clientData}
						height={350}
						color="#FF8042"
					/>
				);

			case "histogram":
			case "HISTOGRAM":
			case "distribution":
				// Use bar chart for histogram/distribution data
				return (
					<ShadcnBarChart
						title={title}
						description="Distribution analysis"
						data={clientData}
						height={350}
						color="#FFBB28"
					/>
				);

			case "ranking":
			case "RANKING":
			case "leaderboard":
				return (
					<ShadcnBarChart
						title={title}
						description="Performance ranking"
						data={clientData}
						height={350}
						color="#00C49F"
					/>
				);

			case "metric":
			case "METRIC":
			case "kpi":
				return <MonthlyTarget />;

			case "donut":
			case "DONUT":
				return (
					<ShadcnInteractiveDonut
						title={title}
						description="Interactive distribution analysis"
						data={clientData}
						dataKey={dataKey}
						nameKey={xAxisKey}
					/>
				);

			case "table":
			case "TABLE":
			case "list":
				return <RecentOrders />;

			case "gauge":
			case "GAUGE":
			case "progress":
				return (
					<ShadcnPieChart
						title={title}
						description="Performance gauge"
						data={clientData}
						height={300}
						innerRadius={80}
						outerRadius={120}
					/>
				);

			case "funnel":
			case "FUNNEL":
				return (
					<ShadcnBarChart
						title={title}
						description="Conversion funnel"
						data={clientData}
						height={350}
						color="#465FFF"
					/>
				);

			case "heatmap":
			case "HEATMAP":
				return (
					<ShadcnBarChart
						title={title}
						description="Activity heatmap"
						data={clientData}
						height={350}
						color="#FF6B6B"
					/>
				);

			case "radar":
			case "RADAR":
				return (
					<ShadcnAreaChart
						title={title}
						description="Multi-dimensional analysis"
						data={clientData}
						height={350}
						color="#4ECDC4"
					/>
				);

			case "treemap":
			case "TREEMAP":
				return (
					<ShadcnBarChart
						title={title}
						description="Hierarchical data"
						data={clientData}
						height={350}
						color="#95A5A6"
					/>
				);

			default:
				// Smart fallback: use line chart for trends, bar chart for comparisons
				if (
					title.toLowerCase().includes("trend") ||
					title.toLowerCase().includes("time") ||
					title.toLowerCase().includes("progression")
				) {
					return (
						<SmartMonthlySalesChart
							clientData={clientData}
							title={title}
							refreshInterval={300000}
						/>
					);
				} else if (
					title.toLowerCase().includes("distribution") ||
					title.toLowerCase().includes("breakdown")
				) {
					return <StatisticsChart />;
				} else {
					// Generic chart component for unknown types
					return (
						<SmartMonthlySalesChart
							clientData={clientData}
							refreshInterval={300000}
						/>
					);
				}
		}
	};

	return getChartComponent();
};

interface User {
	client_id: string;
	company_name: string;
	email: string;
	subscription_tier: string;
	created_at: string;
}

interface AIOrchestrationState {
	isAnalyzing: boolean;
	lastAnalysis: Date | null;
	clientData: Record<string, unknown>[];
	insights: string[];
	dashboardConfig: DashboardConfig | null;
	error: string | null;
}

const Dashboard: React.FC = () => {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);
	const [showDropdown, setShowDropdown] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);
	const router = useRouter();

	// AI Orchestration State
	const [aiState, setAiState] = useState<AIOrchestrationState>({
		isAnalyzing: false,
		lastAnalysis: null,
		clientData: [],
		insights: [],
		dashboardConfig: null,
		error: null,
	});

	useEffect(() => {
		const checkAuth = async () => {
			const token = localStorage.getItem("access_token");
			if (!token) {
				console.log("No access token found, redirecting to login");
				router.push("/login");
				return;
			}

			// 🚀 INSTANT AUTH - Show dashboard immediately if token exists
			console.log("Token found - loading dashboard instantly");
			setUser({
				client_id: "instant-user",
				email: "user@dashboard.com",
				company_name: "Loading...",
				subscription_tier: "basic",
				created_at: new Date().toISOString(),
			});
			setLoading(false);

			// 🔥 Background auth verification - no blocking!
			setTimeout(async () => {
				try {
					console.log("Background auth verification...");
					const response = await api.get("/auth/me");
					console.log("Auth verification successful:", response.data);
					setUser(response.data);
				} catch (error: unknown) {
					console.error("Background auth failed:", error);
					// Only redirect if auth completely fails
					const axiosError = error as { response?: { status?: number } };
					if (
						axiosError.response?.status === 401 ||
						axiosError.response?.status === 403
					) {
						localStorage.removeItem("access_token");
						router.push("/login");
					}
				}
			}, 100);
		};

		checkAuth();
	}, [router]);

	// AI Orchestration Functions - Now loads REAL dashboard config!
	const performAIAnalysis = async () => {
		try {
			setAiState((prev) => ({ ...prev, isAnalyzing: true, error: null }));

			// Get REAL client data
			const clientData = await clientDataService.fetchClientData();

			// Get REAL dashboard configuration from AI orchestrator
			const [dashboardConfig, orchestratedMetrics] = await Promise.all([
				dashboardService.getDashboardConfig(),
				dashboardService.getDashboardMetrics(),
			]);

			// Extract insights from orchestrated metrics
			const insightMetrics = orchestratedMetrics.filter(
				(m) => m.metric_type === "insight" || m.metric_type === "recommendation"
			);

			const insights =
				insightMetrics.length > 0
					? insightMetrics.map((m) => m.metric_value || m.metric_name)
					: [
							"📊 Dashboard loaded from AI orchestrator",
							"💰 Custom analytics for your business",
							"⚡ Real-time data monitoring active",
					  ];

			// Set data with REAL dashboard config
			setAiState((prev) => ({
				...prev,
				isAnalyzing: false,
				lastAnalysis: new Date(),
				clientData: clientData.rawData,
				insights,
				dashboardConfig,
				error: null,
			}));

			console.log("✅ Dashboard config loaded:", dashboardConfig);
		} catch (error: unknown) {
			console.error("Dashboard loading failed:", error);
			const errorMessage =
				error instanceof Error ? error.message : "Unknown error";

			setAiState((prev) => ({
				...prev,
				isAnalyzing: false,
				clientData: [],
				insights: ["Failed to load custom dashboard"],
				error: `Dashboard unavailable: ${errorMessage}`,
				dashboardConfig: null,
			}));
		}
	};

	// Manual dashboard generation for when background generation fails
	const generateDashboardNow = async () => {
		try {
			setAiState((prev) => ({ ...prev, isAnalyzing: true, error: null }));

			console.log("🚀 Manually triggering dashboard generation...");
			const response = await api.post("/dashboard/generate-now");

			if (response.data.success) {
				console.log("✅ Dashboard generated successfully!");

				// Reload dashboard config
				await performAIAnalysis();

				setAiState((prev) => ({
					...prev,
					insights: [
						"✅ Dashboard generated successfully!",
						"💰 Custom analytics created for your business",
						"⚡ Real-time monitoring now active",
					],
				}));
			}
		} catch (error: unknown) {
			console.error("Manual dashboard generation failed:", error);
			const errorMessage =
				error instanceof Error ? error.message : "Unknown error";
			setAiState((prev) => ({
				...prev,
				isAnalyzing: false,
				error: `Failed to generate dashboard: ${errorMessage}`,
			}));
		}
	};

	// Auto-refresh AI analysis immediately when user loads
	useEffect(() => {
		if (user) {
			performAIAnalysis();
		}
	}, [user]);

	// Close dropdown when clicking outside
	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (
				dropdownRef.current &&
				!dropdownRef.current.contains(event.target as Node)
			) {
				setShowDropdown(false);
			}
		};

		document.addEventListener("mousedown", handleClickOutside);
		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, []);

	const handleLogout = () => {
		localStorage.removeItem("access_token");
		router.push("/login");
	};

	const toggleDropdown = () => {
		setShowDropdown(!showDropdown);
	};

	const getInitials = (name: string) => {
		return name.charAt(0).toUpperCase();
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-gray-2 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
					<p className="text-body">Loading dashboard...</p>
				</div>
			</div>
		);
	}

	if (!user) {
		return null; // Will redirect to login
	}

	// Render dashboard based on AI orchestrator decisions
	const renderCustomDashboard = () => {
		if (!aiState.dashboardConfig) {
			return (
				<div className="space-y-6">
					<div className="text-center p-12 bg-white rounded-lg border border-stroke">
						<div className="mx-auto mb-4 h-16 w-16 rounded-full bg-gray-100 flex items-center justify-center">
							<Database className="h-8 w-8 text-gray-400" />
						</div>
						<h3 className="text-lg font-semibold text-gray-900 mb-2">
							AI Dashboard Being Generated
						</h3>
						<p className="text-gray-600 mb-4">
							Your custom dashboard is being created by our AI. This usually
							takes a few moments after your account is set up.
						</p>
						<div className="space-y-3">
							<div className="flex gap-3 justify-center">
								<button
									onClick={performAIAnalysis}
									disabled={aiState.isAnalyzing}
									className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors font-medium">
									{aiState.isAnalyzing
										? "🔄 Checking Status..."
										: "🔍 Check Dashboard Status"}
								</button>
								<button
									onClick={generateDashboardNow}
									disabled={aiState.isAnalyzing}
									className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors font-medium">
									{aiState.isAnalyzing ? "🔄 Generating..." : "🚀 Generate Now"}
								</button>
							</div>
							<p className="text-xs text-gray-500 text-center">
								💡 Background generation usually takes 1-2 minutes.
								<br />
								Click &quot;Generate Now&quot; if you want to create your
								dashboard immediately.
							</p>
						</div>
					</div>
				</div>
			);
		}

		const config = aiState.dashboardConfig;
		const hasKPIWidgets = config.kpi_widgets && config.kpi_widgets.length > 0;
		const hasChartWidgets =
			config.chart_widgets && config.chart_widgets.length > 0;

		return (
			<div className="space-y-6">
				{/* KPI Metrics - Render ACTUAL KPIs from AI orchestrator config */}
				{hasKPIWidgets && (
					<div>
						<h3 className="text-lg font-semibold text-black mb-4">
							Key Performance Indicators
						</h3>
						<div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
							{config.kpi_widgets.map((kpi, index) => (
								<div
									key={kpi.id}
									className="rounded-sm border border-gray-200 bg-white py-6 px-7.5 shadow-lg dark:border-gray-700 dark:bg-gray-800">
									<div
										className={`flex h-11.5 w-11.5 items-center justify-center rounded-full`}
										style={{ backgroundColor: kpi.icon_bg_color || "#E8F4FD" }}>
										{(() => {
											// 🎯 CUSTOM ICONS FOR EACH KPI BASED ON TITLE
											const title = kpi.title.toLowerCase();
											const iconProps = {
												className: `h-6 w-6`,
												style: { color: kpi.icon_color || "#3C50E0" },
											};

											if (title.includes("price") || title.includes("cost")) {
												return <DollarSign {...iconProps} />;
											} else if (
												title.includes("quantity") ||
												title.includes("count")
											) {
												return <Package {...iconProps} />;
											} else if (
												title.includes("trade") ||
												title.includes("transaction")
											) {
												return <Activity {...iconProps} />;
											} else if (
												title.includes("value") ||
												title.includes("total")
											) {
												return <BarChart3 {...iconProps} />;
											} else if (
												title.includes("revenue") ||
												title.includes("sales")
											) {
												return <DollarSign {...iconProps} />;
											} else if (
												title.includes("user") ||
												title.includes("customer")
											) {
												return <Users {...iconProps} />;
											} else if (
												title.includes("order") ||
												title.includes("purchase")
											) {
												return <ShoppingCart {...iconProps} />;
											} else if (
												title.includes("target") ||
												title.includes("goal")
											) {
												return <Target {...iconProps} />;
											} else if (
												title.includes("performance") ||
												title.includes("rate")
											) {
												return <TrendingUp {...iconProps} />;
											} else {
												// 🎯 UNIQUE ICON FOR EACH POSITION AS FALLBACK
												const uniqueIcons = [
													DollarSign,
													Package,
													Activity,
													BarChart3,
												];
												const IconComponent = uniqueIcons[index] || DollarSign;
												return <IconComponent {...iconProps} />;
											}
										})()}
									</div>

									<div className="mt-4 flex items-end justify-between">
										<div>
											<h4 className="text-title-md font-bold text-black dark:text-white">
												{kpi.value}
											</h4>
											<span className="text-sm font-medium text-gray-600 dark:text-gray-400">
												{kpi.title}
											</span>
										</div>

										{kpi.trend && (
											<span
												className={`flex items-center gap-1 text-sm font-medium ${
													kpi.trend.isPositive
														? "text-green-600"
														: "text-red-600"
												}`}>
												{kpi.trend.value}
												{kpi.trend.isPositive ? (
													<svg
														className="h-4 w-4"
														fill="currentColor"
														viewBox="0 0 20 20">
														<path
															fillRule="evenodd"
															d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L10 4.414 4.707 9.707a1 1 0 01-1.414 0z"
															clipRule="evenodd"
														/>
													</svg>
												) : (
													<svg
														className="h-4 w-4"
														fill="currentColor"
														viewBox="0 0 20 20">
														<path
															fillRule="evenodd"
															d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L10 15.586l5.293-5.293a1 1 0 011.414 0z"
															clipRule="evenodd"
														/>
													</svg>
												)}
											</span>
										)}
									</div>
								</div>
							))}
						</div>
					</div>
				)}

				{/* Charts - Only show charts with actual data (SMART AI ORCHESTRATOR) */}
				{(() => {
					const validCharts = hasChartWidgets
						? config.chart_widgets.filter((widget) => {
								// 🧠 FRONTEND SMART FILTER: Only show charts that will actually display data
								const hasValidTitle =
									widget.title && widget.title.trim() !== "";
								const hasClientData =
									aiState.clientData && aiState.clientData.length > 0;
								return hasValidTitle && hasClientData;
						  })
						: [];

					// Only render the section if we have valid charts
					return validCharts.length > 0 ? (
						<div>
							<h3 className="text-lg font-semibold text-black mb-4">
								AI-Selected Analytics
							</h3>
							<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
								{validCharts.map((widget) => (
									<div
										key={widget.id}
										className={`
										${widget.size?.width === 4 ? "lg:col-span-2 xl:col-span-3" : ""}
										${widget.size?.width === 2 ? "lg:col-span-1" : ""}
									`}>
										<DynamicChartRenderer
											widget={widget}
											clientData={aiState.clientData}
										/>
									</div>
								))}
							</div>
						</div>
					) : null; // 🧠 Hide entire section if no valid charts
				})()}

				{/* Additional Widgets - Based on business context */}
				{config.kpi_widgets?.some((w) => w.title.includes("Order")) && (
					<div>
						<h3 className="text-lg font-semibold text-black mb-4">
							Recent Activity
						</h3>
						<RecentOrders />
					</div>
				)}
			</div>
		);
	};

	return (
		<div className="min-h-screen bg-gray-2">
			{/* Header */}
			<header className="bg-white border-b border-stroke px-6 py-4">
				<div className="mx-auto max-w-screen-2xl flex items-center justify-between">
					<div>
						<h1 className="text-2xl font-bold text-black dark:text-white">
							{aiState.dashboardConfig?.title || "Analytics Dashboard"}
						</h1>
						<p className="text-body mt-1">Welcome back, {user.company_name}</p>
					</div>

					<div className="relative" ref={dropdownRef}>
						<button
							onClick={toggleDropdown}
							className="flex items-center justify-center w-10 h-10 bg-primary text-white rounded-full hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2">
							{getInitials(user.company_name)}
						</button>

						{showDropdown && (
							<div className="absolute right-0 mt-2 w-56 bg-white border border-stroke rounded-lg shadow-default z-50">
								<div className="px-4 py-3 border-b border-stroke">
									<p className="text-sm font-medium text-black">
										{user.company_name}
									</p>
									<p className="text-xs text-body capitalize">
										{user.subscription_tier} Plan
									</p>
								</div>
								<div className="py-1">
									<button
										onClick={handleLogout}
										className="flex items-center w-full px-4 py-2 text-sm text-danger hover:bg-gray-1 transition-colors">
										<LogOut className="h-4 w-4 mr-2" />
										<span>Logout</span>
									</button>
								</div>
							</div>
						)}
					</div>
				</div>
			</header>

			{/* Main Content */}
			<main className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
				{/* AI Orchestrator Status */}
				<div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-500/10 dark:to-purple-500/10 rounded-lg border border-blue-200 dark:border-blue-500/20">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-3">
							<div
								className={`w-3 h-3 rounded-full ${
									aiState.isAnalyzing
										? "bg-blue-500 animate-pulse"
										: aiState.dashboardConfig
										? "bg-green-500"
										: "bg-yellow-500"
								}`}></div>
							<div>
								<h3 className="text-sm font-semibold text-blue-800 dark:text-blue-400">
									🤖 AI Orchestrator Status
								</h3>
								<p className="text-xs text-blue-600 dark:text-blue-300">
									{aiState.isAnalyzing
										? "Analyzing your data patterns..."
										: aiState.dashboardConfig
										? `Custom dashboard ready • Last generated: ${new Date(
												aiState.dashboardConfig.last_generated
										  ).toLocaleTimeString()}`
										: "Ready to create your custom dashboard"}
								</p>
							</div>
						</div>
						<button
							onClick={performAIAnalysis}
							disabled={aiState.isAnalyzing}
							className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm">
							{aiState.isAnalyzing ? "🔄 Analyzing..." : "🚀 Refresh Dashboard"}
						</button>
					</div>

					{/* AI Insights */}
					{aiState.insights.length > 0 && (
						<div className="mt-3 p-3 bg-white/50 rounded-lg dark:bg-black/20">
							<h4 className="text-xs font-medium text-blue-800 dark:text-blue-400 mb-2">
								Latest AI Insights:
							</h4>
							<ul className="space-y-1">
								{aiState.insights.slice(0, 3).map((insight, index) => (
									<li
										key={index}
										className="text-xs text-blue-700 dark:text-blue-300">
										• {insight}
									</li>
								))}
							</ul>
						</div>
					)}

					{/* Error State */}
					{aiState.error && (
						<div className="mt-3 p-3 bg-red-50 rounded-lg dark:bg-red-500/15">
							<p className="text-xs text-red-600 dark:text-red-400">
								⚠️ {aiState.error}
							</p>
						</div>
					)}
				</div>

				{/* DYNAMIC DASHBOARD - Renders only what AI orchestrator chose */}
				{renderCustomDashboard()}
			</main>
		</div>
	);
};

export default Dashboard;
