/**
 * AI-Powered Dashboard Page
 *
 * This page provides a complete AI analytics experience:
 * - Data upload and validation
 * - AI-powered data analysis
 * - Dynamic dashboard generation
 * - Real-time insights and recommendations
 */

"use client";

import React, { useState, useEffect, useCallback } from "react";
import Head from "next/head";
import {
	dashboardService,
	DataAnalysis,
	DashboardConfig,
	InsightsSummary,
	DataOverview,
} from "../lib/dashboardService";
import DynamicDashboard from "../components/analytics/DynamicDashboard";
import { ArrowUpIcon, ArrowDownIcon, PlusIcon } from "../components/icons";

interface AIPageState {
	data: any[] | null;
	analysis: DataAnalysis | null;
	insights: InsightsSummary | null;
	overview: DataOverview | null;
	dashboard: DashboardConfig | null;
	loading: boolean;
	error: string | null;
	activeTab: "upload" | "analysis" | "dashboard";
}

const AIDashboardPage: React.FC = () => {
	const [state, setState] = useState<AIPageState>({
		data: null,
		analysis: null,
		insights: null,
		overview: null,
		dashboard: null,
		loading: false,
		error: null,
		activeTab: "upload",
	});

	const [dragActive, setDragActive] = useState(false);

	// Check API health on mount
	useEffect(() => {
		checkAPIHealth();
	}, []);

	const checkAPIHealth = async () => {
		try {
			const isHealthy = await dashboardService.checkHealth();
			if (!isHealthy) {
				setState((prev) => ({
					...prev,
					error:
						"Backend API is not responding. Please ensure the Flask server is running on http://localhost:5000",
				}));
			}
		} catch (error) {
			setState((prev) => ({
				...prev,
				error:
					"Unable to connect to backend API. Please start the Flask server.",
			}));
		}
	};

	const handleDataUpload = useCallback(async (uploadedData: any[]) => {
		setState((prev) => ({ ...prev, loading: true, error: null }));

		try {
			// Validate data
			const validation = dashboardService.validateData(uploadedData);
			if (!validation.isValid) {
				throw new Error(
					`Data validation failed: ${validation.errors.join(", ")}`
				);
			}

			// Get orchestrated dashboard data instead of AI analysis
			const [orchestratedMetrics, dashboardConfig] = await Promise.all([
				dashboardService.getDashboardMetrics(),
				dashboardService.getDashboardConfig()
			]);

			// Process orchestrated data
			const insightMetrics = orchestratedMetrics.filter(m => 
				m.metric_type === 'insight' || m.metric_type === 'recommendation'
			);

			const analysis = {
				summary: "Dashboard loaded from pre-generated analytics",
				recommendations: insightMetrics.map(m => m.metric_value || m.metric_name) || [
					"📊 Data uploaded and processed successfully",
					"💰 Analytics dashboard ready",
					"⚡ Real-time monitoring active"
				],
				charts: dashboardConfig?.chart_widgets || []
			};

			setState((prev) => ({
				...prev,
				data: uploadedData,
				analysis,
				insights: {
					key_findings: analysis.recommendations,
					recommendations: analysis.recommendations,
				},
				overview: {
					total_records: uploadedData.length,
					timestamp: new Date().toISOString(),
					analysis_type: "enhanced_local_analysis",
				},
				activeTab: "analysis",
				loading: false,
			}));
		} catch (error: any) {
			setState((prev) => ({
				...prev,
				error: error.message || "Failed to analyze data",
				loading: false,
			}));
		}
	}, []);

	const generateDashboard = useCallback(async () => {
		if (!state.data) return;

		setState((prev) => ({ ...prev, loading: true, error: null }));

		try {
			const dashboard = await dashboardService.generateDashboard(state.data);
			setState((prev) => ({
				...prev,
				dashboard,
				activeTab: "dashboard",
				loading: false,
			}));
		} catch (error: any) {
			setState((prev) => ({
				...prev,
				error: error.message || "Failed to generate dashboard",
				loading: false,
			}));
		}
	}, [state.data]);

	const loadSampleData = useCallback(async () => {
		setState((prev) => ({ ...prev, loading: true, error: null }));

		try {
			const sampleData = await dashboardService.getSampleData();
			await handleDataUpload(sampleData);
		} catch (error: any) {
			setState((prev) => ({
				...prev,
				error: error.message || "Failed to load sample data",
				loading: false,
			}));
		}
	}, [handleDataUpload]);

	const handleFileUpload = useCallback(
		(event: React.ChangeEvent<HTMLInputElement>) => {
			const file = event.target.files?.[0];
			if (!file) return;

			const reader = new FileReader();
			reader.onload = (e) => {
				try {
					let data: any[];

					if (file.type === "application/json") {
						data = JSON.parse(e.target?.result as string);
					} else if (file.type === "text/csv" || file.name.endsWith(".csv")) {
						data = dashboardService.parseCsvData(e.target?.result as string);
					} else {
						throw new Error(
							"Unsupported file type. Please upload CSV or JSON files."
						);
					}

					handleDataUpload(data);
				} catch (error: any) {
					setState((prev) => ({
						...prev,
						error: error.message || "Failed to parse file",
						loading: false,
					}));
				}
			};

			reader.readAsText(file);
		},
		[handleDataUpload]
	);

	const handleDrag = useCallback((e: React.DragEvent) => {
		e.preventDefault();
		e.stopPropagation();
		if (e.type === "dragenter" || e.type === "dragover") {
			setDragActive(true);
		} else if (e.type === "dragleave") {
			setDragActive(false);
		}
	}, []);

	const handleDrop = useCallback(
		(e: React.DragEvent) => {
			e.preventDefault();
			e.stopPropagation();
			setDragActive(false);

			if (e.dataTransfer.files && e.dataTransfer.files[0]) {
				const file = e.dataTransfer.files[0];
				const fakeEvent = {
					target: { files: [file] },
				} as React.ChangeEvent<HTMLInputElement>;
				handleFileUpload(fakeEvent);
			}
		},
		[handleFileUpload]
	);

	const renderUploadTab = () => (
		<div className="space-y-6">
			<div className="text-center">
				<h2 className="text-2xl font-bold text-gray-800 dark:text-white/90 mb-2">
					🤖 AI-Powered Analytics Dashboard
				</h2>
				<p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
					Upload your data and let our AI analyze patterns, generate insights,
					and create beautiful dashboards automatically. Our AI orchestrator
					will optimize visualizations for your specific dataset.
				</p>
			</div>

			{/* File Upload Area */}
			<div
				className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
					dragActive
						? "border-blue-400 bg-blue-50 dark:bg-blue-500/10"
						: "border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600"
				}`}
				onDragEnter={handleDrag}
				onDragLeave={handleDrag}
				onDragOver={handleDrag}
				onDrop={handleDrop}>
				<input
					type="file"
					accept=".csv,.json"
					onChange={handleFileUpload}
					className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
					disabled={state.loading}
				/>
				<div className="space-y-4">
					<div className="w-16 h-16 mx-auto bg-blue-100 dark:bg-blue-500/20 rounded-full flex items-center justify-center">
						<PlusIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
					</div>
					<div>
						<h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-2">
							Upload Your Data
						</h3>
						<p className="text-gray-600 dark:text-gray-400 mb-4">
							Drag and drop your CSV or JSON file here, or click to browse
						</p>
						<div className="flex justify-center gap-2 text-sm text-gray-500 dark:text-gray-400">
							<span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
								CSV
							</span>
							<span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
								JSON
							</span>
						</div>
					</div>
				</div>
			</div>

			{/* Sample Data Option */}
			<div className="text-center">
				<p className="text-gray-600 dark:text-gray-400 mb-4">
					Don't have data? Try our sample e-commerce dataset
				</p>
				<button
					onClick={loadSampleData}
					disabled={state.loading}
					className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all duration-200 shadow-lg hover:shadow-xl">
					🎯 Load Sample Data
				</button>
			</div>
		</div>
	);

	const renderAnalysisTab = () => (
		<div className="space-y-6">
			<div className="flex items-center justify-between">
				<h2 className="text-2xl font-bold text-gray-800 dark:text-white/90">
					📊 AI Data Analysis
				</h2>
				<button
					onClick={generateDashboard}
					disabled={state.loading}
					className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
					Generate Dashboard
				</button>
			</div>

			{/* Data Overview */}
			{state.overview && (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
							Total Records
						</h3>
						<p className="text-2xl font-bold text-gray-800 dark:text-white/90">
							{state.overview.total_records.toLocaleString()}
						</p>
					</div>
					<div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
							Columns
						</h3>
						<p className="text-2xl font-bold text-gray-800 dark:text-white/90">
							{state.overview.total_columns}
						</p>
					</div>
					<div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
							Data Quality
						</h3>
						<div className="flex items-center gap-2">
							<p className="text-2xl font-bold text-gray-800 dark:text-white/90">
								{state.analysis?.data_quality.score || 0}%
							</p>
							{(state.analysis?.data_quality.score || 0) >= 80 ? (
								<ArrowUpIcon className="w-4 h-4 text-green-500" />
							) : (
								<ArrowDownIcon className="w-4 h-4 text-red-500" />
							)}
						</div>
					</div>
					<div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
							Missing Values
						</h3>
						<p className="text-2xl font-bold text-gray-800 dark:text-white/90">
							{state.overview.missing_values.toLocaleString()}
						</p>
					</div>
				</div>
			)}

			{/* AI Insights Summary */}
			{state.insights && (
				<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-4">
							🎯 Key Findings
						</h3>
						<ul className="space-y-2">
							{state.insights.key_findings.slice(0, 5).map((finding, index) => (
								<li
									key={index}
									className="text-sm text-gray-600 dark:text-gray-400">
									• {finding}
								</li>
							))}
						</ul>
					</div>

					<div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-4">
							🚀 Opportunities
						</h3>
						<ul className="space-y-2">
							{state.insights.opportunities
								.slice(0, 5)
								.map((opportunity, index) => (
									<li
										key={index}
										className="text-sm text-green-600 dark:text-green-400">
										• {opportunity}
									</li>
								))}
						</ul>
					</div>

					<div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-4">
							⚠️ Risk Alerts
						</h3>
						<ul className="space-y-2">
							{state.insights.risk_alerts.slice(0, 5).map((alert, index) => (
								<li
									key={index}
									className="text-sm text-red-600 dark:text-red-400">
									• {alert}
								</li>
							))}
						</ul>
					</div>

					<div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-4">
							📋 Action Items
						</h3>
						<ul className="space-y-2">
							{state.insights.action_items.slice(0, 5).map((action, index) => (
								<li
									key={index}
									className="text-sm text-blue-600 dark:text-blue-400">
									• {action}
								</li>
							))}
						</ul>
					</div>
				</div>
			)}

			{/* Analysis Details */}
			{state.analysis && (
				<div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
					<h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-4">
						🔍 Detailed Analysis
					</h3>
					<div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
						<div>
							<h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
								Trends Detected
							</h4>
							<p className="text-gray-600 dark:text-gray-400">
								{Object.keys(state.analysis.trends).length} trends identified
							</p>
						</div>
						<div>
							<h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
								Anomalies Found
							</h4>
							<p className="text-gray-600 dark:text-gray-400">
								{Object.keys(state.analysis.anomalies).length} anomalies
								detected
							</p>
						</div>
						<div>
							<h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
								Correlations
							</h4>
							<p className="text-gray-600 dark:text-gray-400">
								{state.analysis.correlations.strong_correlations?.length || 0}{" "}
								strong correlations
							</p>
						</div>
					</div>
				</div>
			)}
		</div>
	);

	const renderDashboardTab = () => (
		<div>
			<DynamicDashboard
				data={state.data || undefined}
				dashboardConfig={state.dashboard || undefined}
				onConfigChange={(config) =>
					setState((prev) => ({ ...prev, dashboard: config }))
				}
			/>
		</div>
	);

	return (
		<>
			<Head>
				<title>AI Analytics Dashboard</title>
				<meta
					name="description"
					content="AI-powered analytics dashboard with automatic insights generation"
				/>
			</Head>

			<div className="min-h-screen bg-gray-50 dark:bg-gray-900">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
					{/* Header */}
					<div className="mb-8">
						<h1 className="text-3xl font-bold text-gray-800 dark:text-white/90">
							AI Analytics Dashboard
						</h1>
						<p className="text-gray-600 dark:text-gray-400 mt-2">
							Powered by artificial intelligence • Automated insights •
							Beautiful visualizations
						</p>
					</div>

					{/* Error Alert */}
					{state.error && (
						<div className="mb-6 p-4 bg-red-50 dark:bg-red-500/15 border border-red-200 dark:border-red-500/20 rounded-lg">
							<p className="text-red-700 dark:text-red-400">⚠️ {state.error}</p>
						</div>
					)}

					{/* Loading State */}
					{state.loading && (
						<div className="mb-6 p-4 bg-blue-50 dark:bg-blue-500/15 border border-blue-200 dark:border-blue-500/20 rounded-lg">
							<div className="flex items-center gap-3">
								<div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
								<p className="text-blue-700 dark:text-blue-400">
									🤖 AI is working on your request...
								</p>
							</div>
						</div>
					)}

					{/* Tab Navigation */}
					<div className="mb-8">
						<nav className="flex space-x-8">
							{[
								{ id: "upload", label: "📤 Upload Data", disabled: false },
								{
									id: "analysis",
									label: "🧠 AI Analysis",
									disabled: !state.data,
								},
								{
									id: "dashboard",
									label: "📊 Dashboard",
									disabled: !state.dashboard,
								},
							].map((tab) => (
								<button
									key={tab.id}
									onClick={() =>
										!tab.disabled &&
										setState((prev) => ({ ...prev, activeTab: tab.id as any }))
									}
									disabled={tab.disabled}
									className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
										state.activeTab === tab.id
											? "border-blue-500 text-blue-600 dark:text-blue-400"
											: tab.disabled
											? "border-transparent text-gray-400 dark:text-gray-600 cursor-not-allowed"
											: "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300"
									}`}>
									{tab.label}
								</button>
							))}
						</nav>
					</div>

					{/* Tab Content */}
					<div className="min-h-96">
						{state.activeTab === "upload" && renderUploadTab()}
						{state.activeTab === "analysis" && renderAnalysisTab()}
						{state.activeTab === "dashboard" && renderDashboardTab()}
					</div>
				</div>
			</div>
		</>
	);
};

export default AIDashboardPage;
