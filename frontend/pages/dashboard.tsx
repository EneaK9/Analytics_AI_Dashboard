"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import {
	ChevronDown,
	Database,
	FileText,
	AlertCircle,
	TrendingUp,
	DollarSign,
	Target,
	Users,
	ShoppingCart,
	Package,
	CreditCard,
	Calendar,
	ArrowUpRight,
	ArrowDownRight,
	Activity,
	BarChart3,
	LogOut,
} from "lucide-react";
import api from "../lib/axios";
import { useAuth } from "../lib/useAuth";

// Import AI-powered analytics components

import SmartMonthlySalesChart from "../components/analytics/SmartMonthlySalesChart";
import {
	StatisticsChart,
	MonthlyTarget,
	RecentOrders,
} from "../components/analytics";
import { ChartContainer } from "@/components/ui/chart";

// Import all chart components
import {
	// Area Charts (5)
	ShadcnAreaChart,
	ShadcnAreaInteractive,
	ShadcnAreaLinear,
	ShadcnAreaStep,
	ShadcnAreaStacked,
	// Bar Charts (9)
	ShadcnBarChart,
	ShadcnBarDefault,
	ShadcnBarHorizontal,
	ShadcnBarLabel,
	ShadcnBarLabelCustom,
	ShadcnBarMixed,
	ShadcnBarMultiple,
	ShadcnBarNegative,
	ShadcnBarStacked,
	// Pie Charts (6) - FIXED: Removed non-existent components
	ShadcnPieChart,
	ShadcnPieChartLabel,
	ShadcnPieDonutText,
	ShadcnPieInteractive,
	ShadcnPieLegend,
	ShadcnPieSimple,
	// Radar Charts (5) - FIXED: Removed non-existent ShadcnRadarChart
	ShadcnRadarDefault,
	ShadcnRadarGridFill,
	ShadcnRadarLegend,
	ShadcnRadarLinesOnly,
	ShadcnRadarMultiple,
	// Radial Charts (6)
	ShadcnRadialChart,
	ShadcnRadialLabel,
	ShadcnRadialGrid,
	ShadcnRadialText,
	ShadcnRadialShape,
	ShadcnRadialStacked,
} from "../components/charts";

import { clientDataService } from "../lib/clientDataService";
import { dashboardService, DashboardConfig } from "../lib/dashboardService";

// Simple Error Boundary for Charts
class ChartErrorBoundary extends React.Component<
	{ children: React.ReactNode },
	{ hasError: boolean }
> {
	constructor(props: { children: React.ReactNode }) {
		super(props);
		this.state = { hasError: false };
	}

	static getDerivedStateFromError(error: Error) {
		return { hasError: true };
	}

	componentDidCatch(error: Error, errorInfo: any) {
		console.error("Chart rendering error:", error, errorInfo);
	}

	render() {
		if (this.state.hasError) {
			return null; // Don't render anything if there's an error
		}

		return this.props.children;
	}
}

// Dynamic Chart Renderer Component with BACKEND PROCESSED DATA
interface ChartRendererProps {
	chart: any; // Chart configuration from backend
	chartMetrics: any[]; // Pre-processed chart data from backend metrics
}

// 💎 BACKEND DATA RENDERER - Uses pre-processed financial data from backend
const RealDataOnlyRenderer: React.FC<ChartRendererProps> = ({
	chart,
	chartMetrics,
}) => {
	console.log("💎 BACKEND DATA RENDERER:", chart.chart_type);
	console.log("📊 Chart metrics available:", chartMetrics?.length);

	// 🛡️ VALIDATE CHART CONFIGURATION
	if (!chart || !chart.chart_type) {
		console.error("❌ INVALID CHART CONFIG - HIDING CHART");
		return null; // Don't render invalid charts
	}

	// 🔍 FIND THE RIGHT CHART DATA FROM BACKEND METRICS
	const chartMetric = chartMetrics?.find(
		(metric) =>
			metric.metric_type === "chart_data" &&
			(metric.metric_value?.title === chart.title ||
				metric.metric_value?.chart_type === chart.chart_type)
	);

	const chartData = chartMetric?.metric_value?.data || null;
	const dropdownOptions = chartMetric?.metric_value?.dropdown_options || [];

	if (chartData) {
		console.log(
			"✅ Found BACKEND chart data:",
			chartData.slice(0, 2),
			"with dropdown options:",
			dropdownOptions.length
		);
	} else {
		console.error("❌ No backend chart data found for:", chart.title);
	}

	// 🚫 NO BACKEND DATA = HIDE CHART
	if (!chartData || chartData.length === 0) {
		console.error("❌ NO BACKEND CHART DATA - HIDING CHART");
		return null; // Don't render anything - hide the chart completely
	}

	// ✅ USE BACKEND PROCESSED DATA
	console.log("✅ Using BACKEND processed data:", chartData.slice(0, 2));
	console.log("🔍 BACKEND DATA INSPECTION:");
	console.log("- Chart data points:", chartData.length);
	console.log("- Data structure:", Object.keys(chartData[0] || {}));
	console.log("- Sample values:", chartData.slice(0, 3));

	// 💎 BACKEND DATA IS ALREADY PROCESSED - No need for frontend processing!

	// Enhanced chart props with meaningful business context including dropdown options
	const chartProps = {
		data: chartData,
		dropdown_options: dropdownOptions,
		title: chart.title || "Business Analytics",
		description:
			chart.subtitle || `Live data from ${chartData.length} data points`,
		minimal: true,
	};

	console.log(
		"🎯 RENDERING DIVERSE DATA:",
		chartProps.data?.length,
		"items for",
		chart.chart_type
	);
	console.log("📊 CHART SAMPLE DATA:", {
		chartType: chart.chart_type,
		dataLength: chartProps.data?.length,
		sampleData: chartProps.data?.slice(0, 3),
		dataStructure: chartProps.data?.[0] ? Object.keys(chartProps.data[0]) : [],
	});

	// Get the chart component
	const ChartComponent = (() => {
		switch (chart.chart_type) {
			case "ShadcnAreaChart":
				return ShadcnAreaChart;
			case "ShadcnAreaInteractive":
				return ShadcnAreaInteractive;
			case "ShadcnAreaLinear":
				return ShadcnAreaLinear;
			case "ShadcnAreaStep":
				return ShadcnAreaStep;
			case "ShadcnAreaStacked":
				return ShadcnAreaStacked;
			case "ShadcnBarChart":
				return ShadcnBarChart;
			case "ShadcnBarDefault":
				return ShadcnBarDefault;
			case "ShadcnBarHorizontal":
				return ShadcnBarHorizontal;
			case "ShadcnBarLabel":
				return ShadcnBarLabel;
			case "ShadcnBarLabelCustom":
				return ShadcnBarLabelCustom;
			case "ShadcnBarMixed":
				return ShadcnBarMixed;
			case "ShadcnBarMultiple":
				return ShadcnBarMultiple;
			case "ShadcnBarNegative":
				return ShadcnBarNegative;
			case "ShadcnBarStacked":
				return ShadcnBarStacked;
			case "ShadcnPieChart":
				return ShadcnPieChart;
			case "ShadcnPieChartLabel":
				return ShadcnPieChartLabel;
			case "ShadcnPieDonutText":
				return ShadcnPieDonutText;
			case "ShadcnPieInteractive":
				return ShadcnPieInteractive;
			case "ShadcnPieLegend":
				return ShadcnPieLegend;
			case "ShadcnPieSimple":
				return ShadcnPieSimple;
			case "ShadcnRadarDefault":
				return ShadcnRadarDefault;
			case "ShadcnRadarGridFill":
				return ShadcnRadarGridFill;
			case "ShadcnRadarLegend":
				return ShadcnRadarLegend;
			case "ShadcnRadarLinesOnly":
				return ShadcnRadarLinesOnly;
			case "ShadcnRadarMultiple":
				return ShadcnRadarMultiple;
			case "ShadcnRadialChart":
				return ShadcnRadialChart;
			case "ShadcnRadialLabel":
				return ShadcnRadialLabel;
			case "ShadcnRadialGrid":
				return ShadcnRadialGrid;
			case "ShadcnRadialText":
				return ShadcnRadialText;
			case "ShadcnRadialShape":
				return ShadcnRadialShape;
			case "ShadcnRadialStacked":
				return ShadcnRadialStacked;
			default:
				return null;
		}
	})();

	if (!ChartComponent) {
		return (
			<div className="flex items-center justify-center h-full">
				<div className="text-center">
					<div className="text-red-600 font-medium mb-2">⚠️ Chart Error</div>
					<p className="text-red-500 text-sm">
						Unknown chart type: {chart.chart_type}
					</p>
				</div>
			</div>
		);
	}

	return <ChartComponent {...chartProps} />;
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
	dashboardMetrics: any[];
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
		dashboardMetrics: [],
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

	// AI Orchestration Functions - AGGRESSIVE REAL DATA FETCHING ONLY!
	const performAIAnalysis = async () => {
		const maxRetries = 10;
		let retryCount = 0;

		const attemptDataFetch = async (): Promise<void> => {
			try {
				setAiState((prev) => ({ ...prev, isAnalyzing: true, error: null }));

				console.log(
					`🔥 AGGRESSIVE DATA FETCH ATTEMPT ${retryCount + 1}/${maxRetries}`
				);

				// Get REAL client data with aggressive fetching
				const clientData = await clientDataService.fetchClientData();
				console.log("📊 Client data result:", {
					totalRecords: clientData.totalRecords,
					rawDataLength: clientData.rawData?.length,
					sampleData: clientData.rawData?.slice(0, 1),
				});

				// 🚫 NO REAL DATA = RETRY IMMEDIATELY
				if (!clientData.rawData || clientData.rawData.length === 0) {
					console.error(
						`❌ NO REAL DATA FOUND - RETRY ${retryCount + 1}/${maxRetries}`
					);
					retryCount++;

					if (retryCount < maxRetries) {
						console.log(
							`🔄 RETRYING in 2 seconds... (${retryCount}/${maxRetries})`
						);
						setTimeout(() => attemptDataFetch(), 2000);
						return;
					} else {
						throw new Error("Failed to get real data after maximum retries");
					}
				}

				// ✅ REAL DATA FOUND - Continue with dashboard
				console.log("✅ REAL DATA CONFIRMED - Proceeding with dashboard");

				// Get dashboard configuration only if we have real data
				const [dashboardConfig, orchestratedMetrics] = await Promise.all([
					dashboardService.getDashboardConfig(),
					dashboardService.getDashboardMetrics(),
				]);

				console.log("🎯 Dashboard config with REAL DATA:", {
					hasKPIs: dashboardConfig?.kpi_widgets?.length || 0,
					hasCharts: dashboardConfig?.chart_widgets?.length || 0,
					realDataRecords: clientData.rawData.length,
				});

				// 🔥 FORCE REAL DATA INTO ALL CHARTS
				if (dashboardConfig?.chart_widgets) {
					dashboardConfig.chart_widgets.forEach((widget, index) => {
						console.log(
							`🔧 Injecting REAL DATA into chart ${index + 1}:`,
							widget.title
						);
						if (!widget.config) {
							widget.config = {
								component: widget.chart_type || "ShadcnAreaChart",
								props: {},
								responsive: true,
								real_data_columns: [],
							};
						}
						(widget.config as any).real_data = clientData.rawData;
					});
				}

				const insights =
					orchestratedMetrics?.length > 0
						? orchestratedMetrics
								.map((m) => m.metric_value || m.metric_name)
								.slice(0, 3)
						: ["📊 Real data dashboard active", "💼 Business analytics ready"];

				// Set ONLY real data state
				setAiState((prev) => ({
					...prev,
					isAnalyzing: false,
					lastAnalysis: new Date(),
					clientData: clientData.rawData,
					dashboardMetrics: orchestratedMetrics || [],
					insights,
					dashboardConfig,
					error: null,
				}));

				console.log(
					"🎯 SUCCESS: Real data dashboard loaded with",
					clientData.rawData.length,
					"records"
				);
			} catch (error: unknown) {
				console.error("❌ Dashboard loading failed:", error);
				retryCount++;

				if (retryCount < maxRetries) {
					console.log(
						`🔄 ERROR RETRY ${retryCount}/${maxRetries} in 3 seconds...`
					);
					setTimeout(() => attemptDataFetch(), 3000);
				} else {
					const errorMessage =
						error instanceof Error ? error.message : "Unknown error";
					setAiState((prev) => ({
						...prev,
						isAnalyzing: false,
						clientData: [],
						dashboardMetrics: [],
						insights: ["Failed to load real data after maximum retries"],
						error: `Real data unavailable: ${errorMessage}`,
						dashboardConfig: null,
					}));
				}
			}
		};

		await attemptDataFetch();
	};

	// NEW: Manual dashboard generation with FAST endpoint
	const generateDashboardManually = async () => {
		try {
			setAiState((prev) => ({ ...prev, isAnalyzing: true, error: null }));

			console.log("🚀 Using FAST dashboard generation...");

			// Check if we have an access token
			const token = localStorage.getItem("access_token");
			if (!token) {
				throw new Error("No access token found. Please log in again.");
			}

			// Use the new fast generation endpoint with better error handling
			const response = await api.post(
				"/dashboard/fast-generate",
				{},
				{
					timeout: 10000, // 10 second timeout
				}
			);

			if (response.data.success) {
				console.log("✅ FAST dashboard generation completed:", response.data);

				// Immediately reload the dashboard config since it's now available
				await performAIAnalysis();
			} else {
				throw new Error(
					response.data.message || "Fast dashboard generation failed"
				);
			}
		} catch (error: unknown) {
			console.error("Fast dashboard generation failed:", error);

			// Better error messaging
			let errorMessage = "Unknown error";

			if (error instanceof Error) {
				errorMessage = error.message;
			} else if (error && typeof error === "object" && "response" in error) {
				const axiosError = error as any;
				errorMessage =
					axiosError.response?.data?.detail ||
					axiosError.response?.data?.message ||
					`Server error: ${axiosError.response?.status}`;
			}

			setAiState((prev) => ({
				...prev,
				isAnalyzing: false,
				error: `Fast generation failed: ${errorMessage}. Try refreshing the page or logging in again.`,
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

	const { logout } = useAuth();

	const handleLogout = () => {
		logout();
	};

	const toggleDropdown = () => {
		setShowDropdown(!showDropdown);
	};

	const getInitials = (name: string) => {
		return name.charAt(0).toUpperCase();
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
					<p className="text-xl font-semibold text-gray-900">
						Loading dashboard...
					</p>
					<p className="text-gray-600 mt-2">
						Preparing your analytics experience
					</p>
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
				<div className="flex items-center justify-center min-h-96">
					<div className="text-center">
						{/* Professional Loading Spinner */}
						<div className="relative mb-8">
							<div className="w-16 h-16 mx-auto relative">
								{/* Outer rotating ring */}
								<div className="absolute inset-0 border-3 border-blue-200 rounded-full"></div>
								<div className="absolute inset-0 border-3 border-transparent border-t-blue-600 rounded-full animate-spin"></div>

								{/* Inner pulsing dot */}
								<div className="absolute inset-4 bg-blue-600 rounded-full animate-pulse"></div>

								{/* Floating dots around the spinner */}
								<div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
									<div
										className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
										style={{ animationDelay: "0s" }}></div>
								</div>
								<div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
									<div
										className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
										style={{ animationDelay: "0.5s" }}></div>
								</div>
								<div className="absolute top-1/2 -left-2 transform -translate-y-1/2">
									<div
										className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
										style={{ animationDelay: "0.25s" }}></div>
								</div>
								<div className="absolute top-1/2 -right-2 transform -translate-y-1/2">
									<div
										className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
										style={{ animationDelay: "0.75s" }}></div>
								</div>
							</div>
						</div>

						{/* Loading text with typing animation */}
						<h3 className="text-2xl font-bold text-gray-900 mb-2">
							Loading Dashboard<span className="animate-pulse">...</span>
						</h3>
						<p className="text-gray-600">
							<span className="inline-block animate-pulse">🚀</span> Preparing
							your analytics experience
						</p>

						{/* Progress bar */}
						<div className="mt-6 w-64 mx-auto">
							<div className="bg-gray-200 rounded-full h-2 overflow-hidden">
								<div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full animate-pulse-fast relative">
									<div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
								</div>
							</div>
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
			<div className="space-y-8">
				{/* Enhanced Professional Header Section */}
				<div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-2xl p-8">
					<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
						<div className="flex-1">
							<div className="flex items-center gap-3 mb-3">
								<div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
								<span className="text-sm font-medium text-green-700 bg-green-100 px-3 py-1 rounded-full">
									Live Data
								</span>
								<span className="text-sm text-slate-600">
									{aiState.clientData?.length || 0} records
								</span>
							</div>
							<h1 className="text-4xl font-bold text-slate-900 mb-2">
								Business Analytics Dashboard
							</h1>
							<p className="text-xl text-slate-600 leading-relaxed">
								Real-time insights from your business data • AI-powered
								analytics • {new Date().toLocaleDateString()}
							</p>
						</div>
						<div className="flex flex-col sm:flex-row gap-3">
							<button
								onClick={performAIAnalysis}
								disabled={aiState.isAnalyzing}
								className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
								{aiState.isAnalyzing ? (
									<>
										<div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
										Refreshing...
									</>
								) : (
									<>
										<ArrowUpRight className="w-4 h-4" />
										Refresh Data
									</>
								)}
							</button>
							<button
								onClick={() => router.push("/charts-showcase")}
								className="px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl transition-colors duration-200 flex items-center gap-2">
								<BarChart3 className="w-4 h-4" />
								All Charts
							</button>
						</div>
					</div>
				</div>

				{/* Professional KPI Metrics Grid */}
				{hasKPIWidgets && (
					<div>
						<div className="mb-8">
							<h2 className="text-3xl font-bold text-slate-900 mb-3">
								Key Performance Indicators
							</h2>
							<p className="text-lg text-slate-600">
								Monitor your business performance at a glance
							</p>
						</div>
						<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
							{config.kpi_widgets.map((kpi, index) => (
								<div
									key={kpi.id}
									className="group bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-xl hover:border-slate-300 transition-all duration-300 transform hover:-translate-y-1">
									<div className="flex items-center justify-between mb-6">
										<div
											className="flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg"
											style={{
												backgroundColor: kpi.icon_bg_color || "#EBF4FF",
											}}>
											{(() => {
												// 🎯 CUSTOM ICONS FOR EACH KPI BASED ON TITLE
												const title = kpi.title.toLowerCase();
												const iconProps = {
													className: "h-7 w-7",
													style: { color: kpi.icon_color || "#2563EB" },
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
													const IconComponent =
														uniqueIcons[index] || DollarSign;
													return <IconComponent {...iconProps} />;
												}
											})()}
										</div>

										{kpi.trend && (
											<span
												className={`flex items-center gap-1.5 text-sm font-bold px-3 py-1.5 rounded-xl ${
													kpi.trend.isPositive
														? "text-green-700 bg-green-100 border border-green-200"
														: "text-red-700 bg-red-100 border border-red-200"
												}`}>
												{kpi.trend.isPositive ? (
													<ArrowUpRight className="h-4 w-4" />
												) : (
													<ArrowDownRight className="h-4 w-4" />
												)}
												{kpi.trend.value}
											</span>
										)}
									</div>

									<div>
										<h3 className="text-4xl font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
											{kpi.value}
										</h3>
										<p className="text-base font-semibold text-slate-600">
											{kpi.title}
										</p>
									</div>
								</div>
							))}
						</div>
					</div>
				)}

				{/* Professional Charts Section with Enhanced Layout */}
				{(() => {
					const validCharts = hasChartWidgets
						? config.chart_widgets.filter((widget, index) => {
								// 🧠 STRICT FILTER: Only show charts with valid title and component
								const hasValidTitle =
									widget.title && widget.title.trim() !== "";
								const hasComponent =
									widget.chart_type || widget.config?.component;
								const hasRealData =
									aiState.dashboardMetrics &&
									aiState.dashboardMetrics.length > 0;

								if (!hasValidTitle || !hasComponent || !hasRealData) {
									console.log("Filtering out chart:", widget.title, {
										hasValidTitle,
										hasComponent,
										hasRealData,
									});
									return false;
								}

								return true;
						  })
						: [];

					// ✅ SHOW ALL VALID CHARTS - No aggressive filtering
					const uniqueCharts = validCharts;

					console.log("Chart filtering results:", {
						totalCharts: config.chart_widgets?.length || 0,
						validCharts: validCharts.length,
						uniqueCharts: uniqueCharts.length,
						finalCharts: uniqueCharts.map((c) => ({
							title: c.title,
							type: c.chart_type,
						})),
						clientDataLength: aiState.clientData?.length || 0,
					});

					// 🎯 FINAL RESULT: Professional Analytics Charts Layout
					return uniqueCharts.length > 0 ? (
						<div>
							<div className="mb-8">
								<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
									<div>
										<h2 className="text-3xl font-bold text-slate-900 mb-3">
											Analytics Dashboard
										</h2>
										<p className="text-lg text-slate-600">
											Comprehensive data visualization and insights •{" "}
											{uniqueCharts.length} interactive charts
										</p>
									</div>
									<div className="flex items-center gap-2 text-sm text-slate-500">
										<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
										<span>
											Live Data • Last updated {new Date().toLocaleTimeString()}
										</span>
									</div>
								</div>
							</div>

							{/* Professional Grid Layout - Masonry Style */}
							<div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
								{uniqueCharts.map((widget, index) => {
									// Determine chart size based on type and position
									const isWideChart =
										widget.chart_type?.includes("Area") ||
										widget.chart_type?.includes("Bar") ||
										index === 0;
									const isTallChart =
										widget.chart_type?.includes("Radar") ||
										widget.chart_type?.includes("Radial");

									return (
										<div
											key={`${widget.id}-${index}`}
											className={`
												${isWideChart ? "xl:col-span-2" : "xl:col-span-1"}
												${isTallChart ? "row-span-2" : ""}
											`.trim()}>
											<div className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl hover:border-slate-300 transition-all duration-300 h-full">
												<div className="p-6 h-full flex flex-col">
													{/* Enhanced Chart Header */}
													<div className="mb-6 pb-4 border-b border-slate-100">
														<div className="flex items-start justify-between">
															<div className="flex-1">
																<h3 className="text-xl font-bold text-slate-900 mb-2">
																	{widget.title}
																</h3>
																{widget.subtitle && (
																	<p className="text-sm text-slate-600">
																		{widget.subtitle}
																	</p>
																)}
															</div>
															<div className="flex items-center gap-2">
																<span className="text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded-full">
																	{widget.chart_type
																		?.replace("Shadcn", "")
																		.replace(/([A-Z])/g, " $1")
																		.trim()}
																</span>
															</div>
														</div>
													</div>

													{/* Chart Content with Better Sizing */}
													<div
														className={`flex-1 min-h-0 ${
															isTallChart ? "min-h-[400px]" : "min-h-[300px]"
														}`}>
														<ChartErrorBoundary>
															<ChartContainer
																config={{
																	data: {
																		label: "Business Data",
																		color: "hsl(var(--chart-1))",
																	},
																}}
																className="h-full w-full bg-transparent border-none shadow-none [&>*]:bg-transparent [&>*]:border-none [&>*]:shadow-none">
																<RealDataOnlyRenderer
																	chart={widget}
																	chartMetrics={aiState.dashboardMetrics || []}
																/>
															</ChartContainer>
														</ChartErrorBoundary>
													</div>

													{/* Enhanced Chart Footer */}
													<div className="mt-6 pt-4 border-t border-slate-100">
														<div className="flex items-center justify-between text-xs text-slate-500">
															<div className="flex items-center gap-2">
																<Activity className="w-3 h-3" />
																<span>
																	{aiState.clientData?.length || 0} data points
																</span>
															</div>
															<div className="flex items-center gap-2">
																<Calendar className="w-3 h-3" />
																<span>Real-time data</span>
															</div>
														</div>
													</div>
												</div>
											</div>
										</div>
									);
								})}
							</div>
						</div>
					) : (
						<div className="text-center p-16 bg-white rounded-2xl border border-slate-200 shadow-sm">
							<div className="max-w-lg mx-auto">
								<div className="text-8xl mb-8">📊</div>
								<h3 className="text-3xl font-bold text-slate-900 mb-4">
									No Charts Available
								</h3>
								<p className="text-lg text-slate-600 mb-8 leading-relaxed">
									{config.chart_widgets?.length > 0
										? `${config.chart_widgets.length} charts found but filtered out. Check console for details.`
										: "No charts configured for this dashboard. Upload data to generate charts."}
								</p>
								<div className="flex flex-col sm:flex-row gap-4 justify-center">
									<button
										onClick={performAIAnalysis}
										className="px-8 py-4 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl">
										🔄 Generate Charts
									</button>
									{config.chart_widgets?.length > 0 && (
										<button
											onClick={() =>
												console.log("All chart widgets:", config.chart_widgets)
											}
											className="px-8 py-4 text-slate-600 hover:text-slate-800 font-medium transition-colors border border-slate-200 rounded-xl hover:bg-slate-50">
											🔧 Debug Charts
										</button>
									)}
								</div>
							</div>
						</div>
					);
				})()}

				{/* AI Business Recommendations - Actionables Section */}
				<div>
					<div className="mb-6">
						<h2 className="text-2xl font-bold text-gray-900 mb-2">
							AI Business Recommendations
						</h2>
						<p className="text-gray-600">
							Smart insights to optimize your business performance
						</p>
					</div>

					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						{/* Cost Optimization Card */}
						<div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl border border-red-200 p-6">
							<div className="flex items-start justify-between mb-4">
								<div className="flex items-center">
									<div className="bg-red-100 rounded-lg p-3 mr-3">
										<DollarSign className="h-6 w-6 text-red-600" />
									</div>
									<div>
										<h3 className="text-lg font-semibold text-gray-900">
											Cost Reduction
										</h3>
										<p className="text-sm text-red-600 font-medium">
											High Priority
										</p>
									</div>
								</div>
							</div>
							<div className="space-y-3">
								<div className="bg-white/70 rounded-lg p-4">
									<h4 className="font-medium text-gray-900 mb-2">
										Inventory Optimization
									</h4>
									<p className="text-sm text-gray-600 mb-2">
										Reduce overstocked items by 25% to save ~$12,500 monthly
									</p>
									<div className="flex items-center text-xs text-green-600">
										<span className="bg-green-100 px-2 py-1 rounded-full">
											Potential Savings: $150K/year
										</span>
									</div>
								</div>
								<div className="bg-white/70 rounded-lg p-4">
									<h4 className="font-medium text-gray-900 mb-2">
										Supplier Negotiation
									</h4>
									<p className="text-sm text-gray-600 mb-2">
										3 suppliers show room for 8-15% cost reduction
									</p>
									<div className="flex items-center text-xs text-green-600">
										<span className="bg-green-100 px-2 py-1 rounded-full">
											Potential Savings: $85K/year
										</span>
									</div>
								</div>
							</div>
						</div>

						{/* Revenue Growth Card */}
						<div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-6">
							<div className="flex items-start justify-between mb-4">
								<div className="flex items-center">
									<div className="bg-green-100 rounded-lg p-3 mr-3">
										<TrendingUp className="h-6 w-6 text-green-600" />
									</div>
									<div>
										<h3 className="text-lg font-semibold text-gray-900">
											Revenue Growth
										</h3>
										<p className="text-sm text-green-600 font-medium">
											Medium Priority
										</p>
									</div>
								</div>
							</div>
							<div className="space-y-3">
								<div className="bg-white/70 rounded-lg p-4">
									<h4 className="font-medium text-gray-900 mb-2">
										Cross-selling Opportunities
									</h4>
									<p className="text-sm text-gray-600 mb-2">
										Bundle products to increase average order value by 18%
									</p>
									<div className="flex items-center text-xs text-blue-600">
										<span className="bg-blue-100 px-2 py-1 rounded-full">
											Revenue Impact: +$240K/year
										</span>
									</div>
								</div>
								<div className="bg-white/70 rounded-lg p-4">
									<h4 className="font-medium text-gray-900 mb-2">
										Peak Season Strategy
									</h4>
									<p className="text-sm text-gray-600 mb-2">
										Optimize marketing spend during Q4 peak period
									</p>
									<div className="flex items-center text-xs text-blue-600">
										<span className="bg-blue-100 px-2 py-1 rounded-full">
											Revenue Impact: +$180K/year
										</span>
									</div>
								</div>
							</div>
						</div>

						{/* Operations Efficiency Card */}
						<div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
							<div className="flex items-start justify-between mb-4">
								<div className="flex items-center">
									<div className="bg-blue-100 rounded-lg p-3 mr-3">
										<Activity className="h-6 w-6 text-blue-600" />
									</div>
									<div>
										<h3 className="text-lg font-semibold text-gray-900">
											Operations
										</h3>
										<p className="text-sm text-blue-600 font-medium">
											Low Priority
										</p>
									</div>
								</div>
							</div>
							<div className="space-y-3">
								<div className="bg-white/70 rounded-lg p-4">
									<h4 className="font-medium text-gray-900 mb-2">
										Automation Potential
									</h4>
									<p className="text-sm text-gray-600 mb-2">
										Automate 3 manual processes to save 15 hours/week
									</p>
									<div className="flex items-center text-xs text-purple-600">
										<span className="bg-purple-100 px-2 py-1 rounded-full">
											Time Savings: 780 hrs/year
										</span>
									</div>
								</div>
								<div className="bg-white/70 rounded-lg p-4">
									<h4 className="font-medium text-gray-900 mb-2">
										Staff Optimization
									</h4>
									<p className="text-sm text-gray-600 mb-2">
										Redistribute workload to improve efficiency by 12%
									</p>
									<div className="flex items-center text-xs text-purple-600">
										<span className="bg-purple-100 px-2 py-1 rounded-full">
											Efficiency Gain: 12%
										</span>
									</div>
								</div>
							</div>
						</div>
					</div>

					{/* Action Buttons */}
					<div className="mt-6 flex flex-col sm:flex-row gap-4 items-center justify-center">
						<button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm hover:shadow-md">
							📋 View Detailed Action Plan
						</button>
						<button className="px-6 py-3 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium">
							📧 Email Report to Team
						</button>
						<button className="px-6 py-3 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium">
							📅 Schedule Review Meeting
						</button>
					</div>
				</div>

				{/* Additional Widgets - Based on business context */}
				{config.kpi_widgets?.some((w) => w.title.includes("Order")) && (
					<div>
						<div className="mb-6">
							<h2 className="text-2xl font-bold text-gray-900 mb-2">
								Recent Activity
							</h2>
							<p className="text-gray-600">
								Latest transactions and business activities
							</p>
						</div>
						<div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
							<RecentOrders />
						</div>
					</div>
				)}
			</div>
		);
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
			{/* Enhanced Professional Header */}
			<header className="bg-white/95 backdrop-blur-sm border-b border-slate-200 px-6 py-6 sticky top-0 z-40 shadow-sm">
				<div className="mx-auto max-w-7xl flex items-center justify-between">
					<div className="flex items-center space-x-4">
						<div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl flex items-center justify-center shadow-lg">
							<BarChart3 className="w-6 h-6 text-white" />
						</div>
						<div>
							<h1 className="text-2xl font-bold text-slate-900">
								{aiState.dashboardConfig?.title || "Analytics AI Dashboard"}
							</h1>
							<p className="text-slate-600 text-sm">
								Welcome back, {user.company_name} • Real-time business insights
							</p>
						</div>
					</div>

					<div className="flex items-center space-x-3">
						{/* Status Indicator */}
						<div className="flex items-center space-x-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
							<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
							<span className="text-sm font-medium text-green-700">
								Live Data
							</span>
						</div>

						{/* User Menu */}
						<div className="relative" ref={dropdownRef}>
							<button
								onClick={toggleDropdown}
								className="flex items-center justify-center w-10 h-10 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
								{getInitials(user.company_name)}
							</button>

							{showDropdown && (
								<div className="absolute right-0 mt-3 w-64 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 overflow-hidden">
									<div className="px-5 py-4 bg-gradient-to-r from-slate-50 to-blue-50 border-b border-slate-200">
										<p className="text-sm font-semibold text-slate-900">
											{user.company_name}
										</p>
										<p className="text-xs text-slate-600 capitalize mt-1">
											Free plan • Analytics Dashboard
										</p>
									</div>
									<div className="py-2">
										<button
											onClick={handleLogout}
											className="flex items-center w-full px-5 py-3 text-sm text-red-600 hover:bg-red-50 transition-all duration-200">
											<LogOut className="h-4 w-4 mr-3" />
											<span>Logout</span>
										</button>
									</div>
								</div>
							)}
						</div>
					</div>
				</div>
			</header>

			{/* Main Content */}
			<main className="mx-auto max-w-7xl p-6 md:p-8 2xl:p-12">
				{/* DYNAMIC DASHBOARD - Renders only what AI orchestrator chose */}
				{renderCustomDashboard()}
			</main>
		</div>
	);
};

export default Dashboard;
