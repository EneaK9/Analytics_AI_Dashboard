"use client";

import React from "react";
import {
	AlertCircle,
	AlertTriangle,
	TrendingUp,
	TrendingDown,
	Package,
	ExternalLink,
	RefreshCw,
	Bell,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import useInventoryData from "../../hooks/useInventoryData";

interface AlertsSummaryProps {
	clientData?: any[];
	refreshInterval?: number;
	platform?: "shopify" | "amazon";
}

export default function AlertsSummary({
	clientData,
	refreshInterval = 300000,
	platform = "shopify",
}: AlertsSummaryProps) {
	// Use shared inventory data hook - no more duplicate API calls!
	const { loading, error, alertsSummary, lastUpdated, refresh } =
		useInventoryData({
			refreshInterval,
			fastMode: true,
			platform,
		});

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
					styles[severity as keyof typeof styles] || styles.low
				}`}>
				{severity.toUpperCase()}
			</span>
		);
	};

	// Calculate total alerts from summary (handle both old and new structure)
	const totalAlerts =
		(alertsSummary as any)?.summary?.total_alerts ||
		(alertsSummary as any)?.summary_counts?.total_alerts ||
		0;
	const criticalAlerts =
		(alertsSummary as any)?.summary?.critical_alerts ||
		(alertsSummary as any)?.summary_counts?.critical_alerts ||
		0;

	// Helper function to get alerts with fallback
	const getAlerts = (type: string) => {
		return (
			(alertsSummary as any)?.[type] ||
			(alertsSummary as any)?.detailed_alerts?.[type] ||
			[]
		);
	};

	// Only show loading if we have NO data at all - show data immediately if available
	if (loading && !alertsSummary) {
		return (
			<Card>
				<CardHeader>
					<div className="h-6 bg-gray-200 rounded w-48 animate-pulse"></div>
				</CardHeader>
				<CardContent>
					<div className="space-y-4">
						{[...Array(4)].map((_, i) => (
							<div
								key={i}
								className="h-16 bg-gray-200 rounded animate-pulse"></div>
						))}
					</div>
				</CardContent>
			</Card>
		);
	}

	const lowStockAlerts = getAlerts("low_stock_alerts");
	const overstockAlerts = getAlerts("overstock_alerts");
	const salesSpikeAlerts = getAlerts("sales_spike_alerts");
	const salesSlowdownAlerts = getAlerts("sales_slowdown_alerts");

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center justify-between">
					<div className="flex items-center gap-2">
						<Bell className="h-5 w-5 text-red-600" />
						Alerts Summary ({platform === "shopify" ? "Shopify" : "Amazon"})
					</div>
					<div className="flex items-center gap-2 text-sm">
						<span className="text-gray-600">Total: {totalAlerts}</span>
						{criticalAlerts > 0 && (
							<span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs font-medium">
								{criticalAlerts} Critical
							</span>
						)}
					</div>
				</CardTitle>
			</CardHeader>
			<CardContent>
				{error ? (
					<div className="text-center py-8">
						<AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
						<p className="text-gray-600">{error}</p>
					</div>
				) : totalAlerts === 0 ? (
					<div className="text-center py-8">
						<Bell className="h-12 w-12 text-green-400 mx-auto mb-4" />
						<h3 className="text-lg font-medium text-gray-900 mb-2">
							All Clear!
						</h3>
						<p className="text-gray-600">
							No active alerts for{" "}
							{platform === "shopify" ? "Shopify" : "Amazon"} at this time.
						</p>
					</div>
				) : (
					<div className="space-y-4">
						{/* Low Stock Alerts */}
						{lowStockAlerts.length > 0 && (
							<div className="p-4 rounded-lg border border-yellow-200 bg-yellow-50">
								<div className="flex items-start justify-between">
									<div className="flex items-start gap-3">
										<div className="text-yellow-700">
											<AlertTriangle className="h-5 w-5" />
										</div>
										<div className="flex-1">
											<div className="flex items-center gap-2 mb-1">
												<h4 className="font-semibold text-yellow-700">
													Low Stock & Out of Stock Alerts
												</h4>
												{getSeverityBadge("high")}
											</div>
											<p className="text-sm text-gray-600 mb-2">
												{lowStockAlerts.length} SKUs need immediate attention
											</p>
											<div className="text-xs text-gray-500">
												<span className="font-medium">Affected SKUs: </span>
												{lowStockAlerts
													.slice(0, 3)
													.map(
														(alert: any) =>
															alert.sku_code || alert.sku || "Unknown"
													)
													.join(", ")}
												{lowStockAlerts.length > 3 && (
													<span className="ml-1">
														and {lowStockAlerts.length - 3} more...
													</span>
												)}
											</div>
										</div>
									</div>
									<div className="flex items-center gap-2">
										<span className="text-2xl font-bold text-yellow-700">
											{lowStockAlerts.length}
										</span>
										<button
											className="text-gray-400 hover:text-gray-600 transition-colors"
											title="View detailed alert conditions">
											<ExternalLink className="h-4 w-4" />
										</button>
									</div>
								</div>
							</div>
						)}

						{/* Overstock Alerts */}
						{overstockAlerts.length > 0 && (
							<div className="p-4 rounded-lg border border-blue-200 bg-blue-50">
								<div className="flex items-start justify-between">
									<div className="flex items-start gap-3">
										<div className="text-blue-700">
											<Package className="h-5 w-5" />
										</div>
										<div className="flex-1">
											<div className="flex items-center gap-2 mb-1">
												<h4 className="font-semibold text-blue-700">
													Overstock Alerts
												</h4>
												{getSeverityBadge("medium")}
											</div>
											<p className="text-sm text-gray-600 mb-2">
												{overstockAlerts.length} SKUs have excess inventory
											</p>
											<div className="text-xs text-gray-500">
												<span className="font-medium">Affected SKUs: </span>
												{overstockAlerts
													.slice(0, 3)
													.map(
														(alert: any) =>
															alert.sku_code || alert.sku || "Unknown"
													)
													.join(", ")}
												{overstockAlerts.length > 3 && (
													<span className="ml-1">
														and {overstockAlerts.length - 3} more...
													</span>
												)}
											</div>
										</div>
									</div>
									<div className="flex items-center gap-2">
										<span className="text-2xl font-bold text-blue-700">
											{overstockAlerts.length}
										</span>
										<button
											className="text-gray-400 hover:text-gray-600 transition-colors"
											title="View detailed alert conditions">
											<ExternalLink className="h-4 w-4" />
										</button>
									</div>
								</div>
							</div>
						)}

						{/* Sales Spike Alerts */}
						{salesSpikeAlerts.length > 0 && (
							<div className="p-4 rounded-lg border border-green-200 bg-green-50">
								<div className="flex items-start justify-between">
									<div className="flex items-start gap-3">
										<div className="text-green-700">
											<TrendingUp className="h-5 w-5" />
										</div>
										<div className="flex-1">
											<div className="flex items-center gap-2 mb-1">
												<h4 className="font-semibold text-green-700">
													Sales Spike Alerts
												</h4>
												{getSeverityBadge("medium")}
											</div>
											<p className="text-sm text-gray-600 mb-2">
												{salesSpikeAlerts[0]?.message ||
													"Unusual sales increases detected"}
											</p>
										</div>
									</div>
									<div className="flex items-center gap-2">
										<span className="text-2xl font-bold text-green-700">
											{salesSpikeAlerts.length}
										</span>
										<button
											className="text-gray-400 hover:text-gray-600 transition-colors"
											title="View detailed alert conditions">
											<ExternalLink className="h-4 w-4" />
										</button>
									</div>
								</div>
							</div>
						)}

						{/* Sales Slowdown Alerts */}
						{salesSlowdownAlerts.length > 0 && (
							<div className="p-4 rounded-lg border border-orange-200 bg-orange-50">
								<div className="flex items-start justify-between">
									<div className="flex items-start gap-3">
										<div className="text-orange-700">
											<TrendingDown className="h-5 w-5" />
										</div>
										<div className="flex-1">
											<div className="flex items-center gap-2 mb-1">
												<h4 className="font-semibold text-orange-700">
													Sales Slowdown Alerts
												</h4>
												{getSeverityBadge("medium")}
											</div>
											<p className="text-sm text-gray-600 mb-2">
												{salesSlowdownAlerts[0]?.message ||
													"Sales declines detected"}
											</p>
										</div>
									</div>
									<div className="flex items-center gap-2">
										<span className="text-2xl font-bold text-orange-700">
											{salesSlowdownAlerts.length}
										</span>
										<button
											className="text-gray-400 hover:text-gray-600 transition-colors"
											title="View detailed alert conditions">
											<ExternalLink className="h-4 w-4" />
										</button>
									</div>
								</div>
							</div>
						)}
					</div>
				)}

				{/* Footer */}
				{lastUpdated && (
					<div className="mt-6 pt-4 border-t border-gray-200 text-center">
						<p className="text-xs text-gray-500">
							<RefreshCw className="inline h-3 w-3 mr-1" />
							Last updated: {lastUpdated.toLocaleTimeString()} • Real-time alert
							monitoring active for{" "}
							{platform === "shopify" ? "Shopify" : "Amazon"}
						</p>
					</div>
				)}
			</CardContent>
		</Card>
	);
}
