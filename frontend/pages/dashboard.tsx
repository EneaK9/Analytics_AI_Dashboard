import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { LogOut } from "lucide-react";
import api from "../lib/axios";
import { useAuth } from "../lib/useAuth";
import Dashboard from "../components/dashboard/Dashboard";
import { DateRange } from "../components/dashboard/components/CustomDatePicker";

interface User {
	client_id: string;
	company_name: string;
	email: string;
	subscription_tier: string;
	created_at: string;
}

interface DashboardData {
	users: number;
	conversions: number;
	eventCount: number;
	sessions: number;
	pageViews: number;
	isAnalyzing: boolean;
	lastAnalysis: Date | null;
	error: string | null;
}

const DashboardPage: React.FC = () => {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);
	const [isClient, setIsClient] = useState(false);
	const [dashboardData, setDashboardData] = useState<DashboardData>({
		users: 14000,
		conversions: 325,
		eventCount: 200000,
		sessions: 13277,
		pageViews: 1300000,
		isAnalyzing: false,
		lastAnalysis: null,
		error: null,
	});
	const router = useRouter();
	const { logout } = useAuth();

	// Ensure we're on the client side before generating random values
	useEffect(() => {
		setIsClient(true);
	}, []);

	// Date range state for filtering
	const [dateRange, setDateRange] = useState<DateRange | null>(null);

	// Handle date range changes from calendar
	const handleDateRangeChange = (newDateRange: DateRange) => {
		console.log("📅 Date range changed:", newDateRange);
		setDateRange(newDateRange);
	};

	// COMMENTED OUT: DEPRECATED: AI Data Integration Function - No longer used
	// This function uses the dashboard/metrics endpoint
	const loadAIAnalysisData = async () => {
		console.log("🚫 Dashboard metrics loading is disabled");
		return;

		// COMMENTED OUT: MainGrid.tsx now handles all data loading with intelligent caching
		// try {
		// 	setDashboardData((prev) => ({ ...prev, isAnalyzing: true, error: null }));

		// 	console.log("🔥 Loading REAL AI analysis data from backend...");

		// 	// First, try to get dashboard metrics
		// 	const response = await api.get("/dashboard/metrics");
		// console.log("📊 Backend metrics response:", response.data);

		// if (response.data && response.data.length > 0) {
		// 	// Extract REAL data from backend metrics
		// 	const metrics = response.data;
		// 	const extractedData: Partial<DashboardData> = {};

		// console.log(
		// 	"📈 Processing",
		// 	metrics.length,
		// 	"real metrics from backend"
		// );

		// // Map real AI metrics to dashboard data
		// metrics.forEach((metric: any) => {
		// 	console.log(
		// 		"🔍 Processing metric:",
		// 		metric.metric_type,
		// 		metric.metric_name,
		// 		metric.metric_value
		// 	);

		// 	if (metric.metric_type === "kpi" && metric.metric_value) {
		// 		const value = metric.metric_value;

		// 		// Handle different metric value formats
		// 		let numValue = 0;
		// 		if (typeof value === "object" && value.value) {
		// 			numValue =
		// 				parseInt(value.value.toString().replace(/[^\d]/g, "")) || 0;
		// 		} else if (typeof value === "number") {
		// 			numValue = value;
		// 		} else if (typeof value === "string") {
		// 			numValue = parseInt(value.replace(/[^\d]/g, "")) || 0;
		// 		}

		// 		const name = (metric.metric_name || "").toLowerCase();
		// 		const title = (value.title || "").toLowerCase();

		// 		// Map to dashboard metrics
		// 		if (
		// 			name.includes("user") ||
		// 			title.includes("user") ||
		// 			name.includes("client")
		// 		) {
		// 			extractedData.users = numValue;
		// 		} else if (
		// 			name.includes("conversion") ||
		// 			title.includes("conversion")
		// 		) {
		// 			extractedData.conversions = numValue;
		// 		} else if (
		// 			name.includes("event") ||
		// 			title.includes("event") ||
		// 			name.includes("record")
		// 		) {
		// 			extractedData.eventCount = numValue;
		// 		} else if (name.includes("session") || title.includes("session")) {
		// 			extractedData.sessions = numValue;
		// 		} else if (
		// 			name.includes("view") ||
		// 			title.includes("page") ||
		// 			name.includes("total")
		// 		) {
		// 			extractedData.pageViews = numValue;
		// 		}
		// 	}
		// });

		// console.log("✅ Extracted real data:", extractedData);

		// // If we got real data, use it
		// if (Object.keys(extractedData).length > 0) {
		// 	setDashboardData((prev) => ({
		// 		...prev,
		// 		...extractedData,
		// 		isAnalyzing: false,
		// 		lastAnalysis: isClient ? new Date() : null,
		// 		error: null,
		// 	}));

		// 	console.log("🎯 Using REAL backend data:", extractedData);
		// 	return;
		// }
		// }

		// // Fallback: Try to get raw client data and calculate metrics
		// console.log("📊 No processed metrics found, trying raw client data...");

		// const clientId = user?.client_id;
		// if (clientId && clientId !== "fallback-user") {
		// 	try {
		// 		const rawDataResponse = await api.get(`/data/${clientId}`);
		// 		console.log("📈 Raw data response:", rawDataResponse.data);

		// 		if (
		// 			rawDataResponse.data &&
		// 			rawDataResponse.data.data &&
		// 			rawDataResponse.data.data.length > 0
		// 		) {
		// 			const rawData = rawDataResponse.data.data;
		// 			console.log(
		// 				"💎 Calculating metrics from",
		// 				rawData.length,
		// 				"raw data records"
		// 			);

		// 			// Calculate realistic metrics from raw data
		// 			const calculatedData = {
		// 				users: Math.floor(rawData.length * 0.8), // Assume 80% are unique users
		// 				conversions: Math.floor(rawData.length * 0.12), // 12% conversion rate
		// 				eventCount: rawData.length,
		// 				sessions: Math.floor(rawData.length * 0.9), // 90% sessions
		// 				pageViews: Math.floor(rawData.length * 1.3), // 1.3 pages per record
		// 			};

		// 			setDashboardData((prev) => ({
		// 				...prev,
		// 				...calculatedData,
		// 				isAnalyzing: false,
		// 				lastAnalysis: isClient ? new Date() : null,
		// 				error: null,
		// 			}));

		// 			console.log(
		// 				"🎯 Using calculated data from raw records:",
		// 				calculatedData
		// 			);
		// 			return;
		// 		}
		// 	} catch (rawDataError) {
		// 		console.log(
		// 			"Could not fetch raw data:",
		// 			rawDataError instanceof Error
		// 				? rawDataError.message
		// 				: "Unknown error"
		// 		);
		// 	}
		// }

		// // Final fallback: Use dynamic defaults based on user (client-side only)
		// console.log("⚠️ Using intelligent defaults...");
		// const smartDefaults = isClient ? {
		// 	users: Math.floor(Math.random() * 2000) + 13000,
		// 	conversions: Math.floor(Math.random() * 50) + 300,
		// 	eventCount: Math.floor(Math.random() * 20000) + 190000,
		// 	sessions: Math.floor(Math.random() * 1000) + 12500,
		// 	pageViews: Math.floor(Math.random() * 100000) + 1250000,
		// } : {
		// 	users: 14000,
		// 	conversions: 325,
		// 	eventCount: 200000,
		// 	sessions: 13277,
		// 	pageViews: 1300000,
		// };

		// setDashboardData((prev) => ({
		// 	...prev,
		// 	...smartDefaults,
		// 	isAnalyzing: false,
		// 	lastAnalysis: isClient ? new Date() : null,
		// 	error: null,
		// }));

		// console.log("✅ Using smart defaults:", smartDefaults);
		// } catch (error) {
		// 	console.error("❌ Failed to load AI analysis data:", error);

		// 	// Emergency fallback data
		// 	const emergencyData = {
		// 		users: 14000,
		// 		conversions: 325,
		// 		eventCount: 200000,
		// 		sessions: 13277,
		// 		pageViews: 1300000,
		// 	};

		// 	setDashboardData((prev) => ({
		// 		...prev,
		// 		...emergencyData,
		// 		isAnalyzing: false,
		// 		error: "Could not connect to backend. Showing sample data.",
		// 	}));
		// }
	};

	useEffect(() => {
		if (!isClient) return;

		const checkAuth = async () => {
			const token = localStorage.getItem("access_token");
			if (!token) {
				console.log("No access token found, redirecting to login");
				router.push("/login");
				return;
			}

			// Get real user data immediately
			try {
				console.log("🚀 Loading real user data and dashboard...");
				const response = await api.get("/auth/me");
				console.log("✅ Real user data loaded:", response.data);

				setUser(response.data);
				setLoading(false);

				// MainGrid will handle data loading with intelligent caching
				// setTimeout(() => loadAIAnalysisData(), 100); // Removed - redundant
			} catch (error: unknown) {
				console.error("Failed to load user data:", error);
				const axiosError = error as { response?: { status?: number } };
				if (
					axiosError.response?.status === 401 ||
					axiosError.response?.status === 403
				) {
					localStorage.removeItem("access_token");
					router.push("/login");
				} else {
					// Show loading state but continue trying
					setUser({
						client_id: "fallback-user",
						email: "user@dashboard.com",
						company_name: "Loading...",
						subscription_tier: "basic",
						created_at: isClient ? new Date().toISOString() : "",
					});
					setLoading(false);
				}
			}
		};

		checkAuth();
	}, [router, isClient]);

	// MainGrid.tsx now handles all data loading with intelligent caching
	useEffect(() => {
		// No need for redundant API calls - MainGrid handles everything with cache
		console.log(
			"✅ Dashboard ready - MainGrid will handle data loading with cache"
		);
	}, [user?.client_id]);

	const handleLogout = () => {
		logout();
	};

	// Show loading state during SSR to prevent hydration issues
	if (!isClient || loading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
					<p className="text-xl font-semibold text-gray-900">
						Loading Dashboard...
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

	return (
		<>
			<Head>
				<title>AI Analytics Dashboard</title>
				<link rel="icon" href="/favicon.svg" type="image/svg+xml" />

				<meta
					name="description"
					content="Your personalized analytics dashboard"
				/>
			</Head>
			<div className="min-h-screen">
				{/* Material UI Dashboard */}
				<Dashboard
					dashboardData={dashboardData}
					user={user!}
					onRefreshAIData={undefined} // MainGrid handles data loading with cache
					onLogout={handleLogout}
					dateRange={dateRange}
					onDateRangeChange={handleDateRangeChange}
				/>

				{/* Error Display */}
				{dashboardData.error && (
					<div className="fixed bottom-4 right-4 z-50 max-w-md">
						<div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg">
							<div className="flex">
								<div className="flex-shrink-0">
									<svg
										className="h-5 w-5 text-red-400"
										viewBox="0 0 20 20"
										fill="currentColor">
										<path
											fillRule="evenodd"
											d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
											clipRule="evenodd"
										/>
									</svg>
								</div>
								<div className="ml-3">
									<h3 className="text-sm font-medium">Error</h3>
									<div className="mt-1 text-sm">{dashboardData.error}</div>
								</div>
							</div>
						</div>
					</div>
				)}
			</div>
		</>
	);
};

export default DashboardPage;
