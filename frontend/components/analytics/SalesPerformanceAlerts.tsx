"use client";

import React, { useMemo } from "react";
import {
	TrendingDown,
	Store,
	ShoppingBag,
	TrendingUp,
	Eye,
	ExternalLink,
	RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import useMultiPlatformData from "../../hooks/useMultiPlatformData";

interface SalesPerformanceAlertsProps {
	className?: string;
}

interface AlertItem {
	id: string;
	sku: string;
	message: string;
	severity: "low" | "medium" | "high" | "critical";
	changePercentage?: number;
	alertType: "spike" | "slowdown";
	quickLink?: string;
}

export default function SalesPerformanceAlerts({
	className = "",
}: SalesPerformanceAlertsProps) {
	// ⚡ OPTIMIZED: Single API call for ALL platforms - NO re-rendering!
	const {
		loading: multiLoading,
		error: multiError,
		shopifyData: shopifyPlatformData,
		amazonData: amazonPlatformData,
		lastUpdated,
	} = useMultiPlatformData({
		fastMode: true,
	});

	// Extract alerts from platform data - MEMOIZED
	const shopifyAlerts = useMemo(
		() => shopifyPlatformData?.alerts_summary || null,
		[shopifyPlatformData]
	);
	const amazonAlerts = useMemo(
		() => amazonPlatformData?.alerts_summary || null,
		[amazonPlatformData]
	);

	// Derived loading/error states
	const shopifyLoading = multiLoading;
	const amazonLoading = multiLoading;
	const shopifyError = multiError;
	const amazonError = multiError;
	const shopifyLastUpdated = lastUpdated;
	const amazonLastUpdated = lastUpdated;

	// Process alerts for each platform
	const processSalesAlerts = (data: any): AlertItem[] => {
		const spikeAlerts =
			data?.sales_spike_alerts ||
			data?.detailed_alerts?.sales_spike_alerts ||
			[];
		const slowdownAlerts =
			data?.sales_slowdown_alerts ||
			data?.detailed_alerts?.sales_slowdown_alerts ||
			[];

		const processedSpikes = spikeAlerts.map((alert: any, index: number) => ({
			id: `spike-${
				alert.sku_code || alert.sku || "unknown"
			}-${index}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
			sku: alert.sku_code || alert.sku || `Unknown-${index}`,
			message:
				alert.message ||
				`Sales spike: ${alert.change_percentage || 0}% increase`,
			severity: alert.severity || "medium",
			changePercentage: alert.change_percentage,
			alertType: "spike" as const,
			quickLink: `/inventory/sku/${alert.sku_code || alert.sku}`,
		}));

		const processedSlowdowns = slowdownAlerts.map(
			(alert: any, index: number) => ({
				id: `slowdown-${
					alert.sku_code || alert.sku || "unknown"
				}-${index}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
				sku: alert.sku_code || alert.sku || `Unknown-${index}`,
				message:
					alert.message ||
					`Sales decline: ${Math.abs(alert.change_percentage || 0)}% decrease`,
				severity: alert.severity || "medium",
				changePercentage: alert.change_percentage,
				alertType: "slowdown" as const,
				quickLink: `/inventory/sku/${alert.sku_code || alert.sku}`,
			})
		);

		return [...processedSpikes, ...processedSlowdowns];
	};

	// Get alerts for each platform
	const shopifySalesAlerts = useMemo(() => {
		return shopifyAlerts ? processSalesAlerts(shopifyAlerts) : [];
	}, [shopifyAlerts]);

	const amazonSalesAlerts = useMemo(() => {
		return amazonAlerts ? processSalesAlerts(amazonAlerts) : [];
	}, [amazonAlerts]);

	const allSalesAlerts = useMemo(() => {
		return [...shopifySalesAlerts, ...amazonSalesAlerts];
	}, [shopifySalesAlerts, amazonSalesAlerts]);

	// Get severity badge styling
	const getSeverityBadge = (severity: string) => {
		const styles = {
			low: "bg-gray-100 text-gray-700 border-gray-200",
			medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
			high: "bg-orange-100 text-orange-700 border-orange-200",
			critical: "bg-red-100 text-red-700 border-red-200",
		};

		return (
			<span
				className={`px-2 py-1 text-xs font-medium rounded-full border ${
					styles[severity as keyof typeof styles] || styles.medium
				}`}>
				{severity.toUpperCase()}
			</span>
		);
	};

	// Get alert type badge
	const getAlertTypeBadge = (alertType: "spike" | "slowdown") => {
		if (alertType === "spike") {
			return (
				<span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700 border border-green-200">
					SPIKE
				</span>
			);
		} else {
			return (
				<span className="px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-700 border border-orange-200">
					DECLINE
				</span>
			);
		}
	};

	// Individual Alert Card Component
	const AlertCard = ({
		title,
		alerts,
		loading,
		error,
		icon,
		iconColor,
		bgColor,
		borderColor,
		textColor,
	}: {
		title: string;
		alerts: AlertItem[];
		loading: boolean;
		error: string | null;
		icon: React.ReactNode;
		iconColor: string;
		bgColor: string;
		borderColor: string;
		textColor: string;
	}) => {
		if (loading) {
			return (
				<Card className="group hover:shadow-lg transition-all duration-300">
					<CardHeader className="pb-3">
						<CardTitle className="flex items-center gap-2">
							{icon}
							{title}
						</CardTitle>
					</CardHeader>
					<CardContent>
						<div className="space-y-3">
							{[...Array(3)].map((_, i) => (
								<div
									key={i}
									className="h-16 bg-gray-200 rounded animate-pulse"></div>
							))}
						</div>
					</CardContent>
				</Card>
			);
		}

		if (error) {
			return (
				<Card className={`border ${borderColor}`}>
					<CardHeader className="pb-3">
						<CardTitle className="flex items-center gap-2">
							{icon}
							{title}
						</CardTitle>
					</CardHeader>
					<CardContent>
						<div className="text-center py-6 text-red-600">
							<TrendingDown className="h-8 w-8 mx-auto mb-2" />
							<p className="text-sm">Error loading alerts</p>
						</div>
					</CardContent>
				</Card>
			);
		}

		return (
			<Card
				className={`border ${borderColor} ${bgColor} hover:shadow-lg transition-shadow`}>
				<CardHeader className="pb-3">
					<CardTitle className={`flex items-center gap-2 ${textColor}`}>
						{icon}
						{title}
						<span className="text-sm font-normal text-gray-600">
							({alerts.length} alerts)
						</span>
					</CardTitle>
				</CardHeader>
				<CardContent>
					{alerts.length === 0 ? (
						<div className="text-center py-6 text-gray-500">
							<TrendingUp className="h-8 w-8 mx-auto mb-2 text-green-500" />
							<p className="text-sm">No sales performance alerts</p>
							<p className="text-xs text-gray-400">Sales patterns are stable</p>
						</div>
					) : (
						<div className="space-y-3 max-h-64 overflow-y-auto">
							{alerts.slice(0, 10).map((alert) => (
								<div
									key={alert.id}
									className="flex items-start justify-between p-3 bg-white/80 rounded-lg border border-gray-100">
									<div className="flex-1 min-w-0">
										<div className="flex items-center gap-2 mb-1">
											<h4 className="font-semibold text-gray-900 text-sm truncate">
												{alert.sku}
											</h4>
											{getSeverityBadge(alert.severity)}
											{getAlertTypeBadge(alert.alertType)}
										</div>
										<p className="text-xs text-gray-600 mb-2">
											{alert.message}
										</p>
										{alert.changePercentage !== undefined && (
											<div className="flex items-center gap-1">
												{alert.alertType === "spike" ? (
													<TrendingUp className="h-3 w-3 text-green-600" />
												) : (
													<TrendingDown className="h-3 w-3 text-orange-600" />
												)}
												<p
													className={`text-xs font-medium ${
														alert.alertType === "spike"
															? "text-green-600"
															: "text-orange-600"
													}`}>
													{alert.alertType === "spike" ? "+" : ""}
													{alert.changePercentage}%
												</p>
											</div>
										)}
									</div>
									<div className="flex items-center gap-2 ml-2">
										<button
											onClick={() => window.open(alert.quickLink, "_blank")}
											className="text-gray-400 hover:text-blue-600 transition-colors p-1 rounded hover:bg-white/50"
											title="View SKU details">
											<Eye className="h-3 w-3" />
										</button>
										<button
											onClick={() => window.open(alert.quickLink, "_blank")}
											className="text-gray-400 hover:text-blue-600 transition-colors p-1 rounded hover:bg-white/50"
											title="Open in new tab">
											<ExternalLink className="h-3 w-3" />
										</button>
									</div>
								</div>
							))}
							{alerts.length > 10 && (
								<div className="text-center py-2 text-gray-500 text-sm">
									+{alerts.length - 10} more alerts...
								</div>
							)}
						</div>
					)}
				</CardContent>
			</Card>
		);
	};

	return (
		<div className={`space-y-4 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">
					Sales Performance Alerts
				</h2>
				<p className="text-sm text-gray-600">
					Unusual sales patterns and performance changes
				</p>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Shopify Sales Performance Alerts */}
				<AlertCard
					title="Shopify Sales"
					alerts={shopifySalesAlerts}
					loading={shopifyLoading}
					error={shopifyError}
					icon={<Store className="h-5 w-5" />}
					iconColor="#059669"
					bgColor="bg-orange-50"
					borderColor="border-orange-200"
					textColor="text-orange-700"
				/>

				{/* Amazon Sales Performance Alerts */}
				<AlertCard
					title="Amazon Sales"
					alerts={amazonSalesAlerts}
					loading={amazonLoading}
					error={amazonError}
					icon={<ShoppingBag className="h-5 w-5" />}
					iconColor="#f59e0b"
					bgColor="bg-orange-50"
					borderColor="border-orange-200"
					textColor="text-orange-700"
				/>

				{/* All Platforms Sales Performance Alerts */}
				<AlertCard
					title="All Platforms"
					alerts={allSalesAlerts}
					loading={shopifyLoading || amazonLoading}
					error={shopifyError || amazonError}
					icon={<TrendingDown className="h-5 w-5" />}
					iconColor="#ea580c"
					bgColor="bg-orange-50"
					borderColor="border-orange-200"
					textColor="text-orange-700"
				/>
			</div>

			{/* Footer */}
			<div className="text-center text-sm text-gray-500">
				<RefreshCw className="inline h-4 w-4 mr-1" />
				Last updated:{" "}
				{(shopifyLastUpdated || amazonLastUpdated)?.toLocaleTimeString() ||
					"Unknown"}{" "}
				• Real-time monitoring active
			</div>
		</div>
	);
}
