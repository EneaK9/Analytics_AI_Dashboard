import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { ArrowLeft, Settings, RefreshCw } from "lucide-react";
import DashboardTemplateSelector, {
	DashboardTemplateType,
} from "../components/DashboardTemplateSelector";
import TemplateDashboard from "../components/TemplateDashboard";
import { clientDataService } from "../lib/clientDataService";
import { useAuth } from "../lib/useAuth";

interface TemplatePageState {
	step: "select" | "dashboard";
	selectedTemplate: DashboardTemplateType | null;
	clientData: any[];
	userDataColumns: string[];
	loading: boolean;
	error: string | null;
}

export default function TemplateDashboardPage() {
	const router = useRouter();
	const { user } = useAuth();
	const [state, setState] = useState<TemplatePageState>({
		step: "select",
		selectedTemplate: null,
		clientData: [],
		userDataColumns: [],
		loading: true,
		error: null,
	});

	// Load client data on mount
	useEffect(() => {
		const loadClientData = async () => {
			try {
				setState((prev) => ({ ...prev, loading: true, error: null }));

				const data = await clientDataService.fetchClientData();
				const columns =
					data.rawData && data.rawData.length > 0
						? Object.keys(data.rawData[0])
						: [];

				setState((prev) => ({
					...prev,
					clientData: data.rawData || [],
					userDataColumns: columns,
					loading: false,
				}));
			} catch (error) {
				console.error("Failed to load client data:", error);
				setState((prev) => ({
					...prev,
					error: "Failed to load your data. Please try again.",
					loading: false,
				}));
			}
		};

		if (user) {
			loadClientData();
		}
	}, [user]);

	const handleTemplateSelect = (template: DashboardTemplateType) => {
		setState((prev) => ({
			...prev,
			selectedTemplate: template,
		}));
	};

	const handleContinue = () => {
		setState((prev) => ({
			...prev,
			step: "dashboard",
		}));
	};

	const handleBackToSelection = () => {
		setState((prev) => ({
			...prev,
			step: "select",
		}));
	};

	const handleTemplateChange = (newTemplate: DashboardTemplateType) => {
		setState((prev) => ({
			...prev,
			selectedTemplate: newTemplate,
		}));
	};

	// Redirect to login if not authenticated
	if (!user) {
		router.push("/login");
		return null;
	}

	if (state.loading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
					<p className="text-xl font-semibold text-gray-900">
						Loading your data...
					</p>
					<p className="text-gray-600 mt-2">Preparing template options</p>
				</div>
			</div>
		);
	}

	if (state.error) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 flex items-center justify-center">
				<div className="text-center max-w-md mx-auto p-8">
					<div className="text-red-600 text-6xl mb-4">⚠️</div>
					<h2 className="text-2xl font-bold text-gray-900 mb-4">
						Unable to Load Data
					</h2>
					<p className="text-gray-600 mb-6">{state.error}</p>
					<div className="flex gap-4 justify-center">
						<button
							onClick={() => window.location.reload()}
							className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
							<RefreshCw className="w-4 h-4" />
							Try Again
						</button>
						<button
							onClick={() => router.push("/dashboard")}
							className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
							Back to Dashboard
						</button>
					</div>
				</div>
			</div>
		);
	}

	return (
		<>
			<Head>
				<title>Template Dashboard </title>
				<link rel="icon" href="/favicon.svg" type="image/svg+xml" />

				<meta name="description" content="Choose from pre-built dashboard templates" />
			</Head>
			<div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
			{/* Navigation Header */}
			<header className="bg-white/95 backdrop-blur-sm border-b border-slate-200 px-6 py-4 sticky top-0 z-50 shadow-sm">
				<div className="mx-auto max-w-7xl flex items-center justify-between">
					<div className="flex items-center space-x-4">
						{state.step === "dashboard" && (
							<button
								onClick={handleBackToSelection}
								className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
								<ArrowLeft className="w-4 h-4" />
								Back to Templates
							</button>
						)}
						<div>
							<h1 className="text-2xl font-bold text-slate-900">
								{state.step === "select"
									? "Template Selection"
									: "Template Dashboard"}
							</h1>
							<p className="text-slate-600 text-sm">
								{state.step === "select"
									? "Choose the perfect dashboard for your business needs"
									: `${state.selectedTemplate
											?.charAt(0)
											.toUpperCase()}${state.selectedTemplate?.slice(
											1
									  )} Dashboard`}
							</p>
						</div>
					</div>

					<div className="flex items-center space-x-3">
						{/* Data Info */}
						<div className="flex items-center space-x-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
							<div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
							<span className="text-sm font-medium text-blue-700">
								{state.clientData.length} data records
							</span>
						</div>

						{/* Settings Button */}
						<button className="flex items-center justify-center w-10 h-10 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors">
							<Settings className="w-5 h-5" />
						</button>
					</div>
				</div>
			</header>

			{/* Main Content */}
			<main className="mx-auto max-w-7xl p-6 md:p-8">
				{state.step === "select" ? (
					// Template Selection Step
					<DashboardTemplateSelector
						selectedTemplate={state.selectedTemplate || undefined}
						onTemplateSelect={handleTemplateSelect}
						onContinue={handleContinue}
						showContinue={true}
						userDataColumns={state.userDataColumns}
						className="max-w-6xl mx-auto"
					/>
				) : (
					// Dashboard Display Step
					state.selectedTemplate && (
						<TemplateDashboard
							templateType={state.selectedTemplate}
							clientData={state.clientData}
							onTemplateChange={handleTemplateChange}
							className="max-w-7xl mx-auto"
						/>
					)
				)}
			</main>

			{/* Footer */}
			<footer className="bg-white border-t border-gray-200 px-6 py-4 mt-12">
				<div className="mx-auto max-w-7xl flex items-center justify-between text-sm text-gray-600">
					<div className="flex items-center gap-4">
						<span>© 2025 Shfa AI LLC</span>
						<span>•</span>
						<span>Template-Based Analytics System</span>
					</div>
					<div className="flex items-center gap-4">
						<button
							onClick={() => router.push("/dashboard")}
							className="text-blue-600 hover:text-blue-700 transition-colors">
							Back to Main Dashboard
						</button>
						<span>•</span>
						<button
							onClick={() => router.push("/charts-showcase")}
							className="text-blue-600 hover:text-blue-700 transition-colors">
							View All Charts
						</button>
					</div>
				</div>
			</footer>
		</div>
		</>
	);
}
