"use client";

import React, { useMemo } from "react";
import {
	AlertTriangle,
	Store,
	ShoppingBag,
	TrendingUp,
	Eye,
	ExternalLink,
	RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import useMultiPlatformData from "../../hooks/useMultiPlatformData";

interface LowStockAlertsProps {
	className?: string;
}

interface AlertItem {
	id: string;
	sku: string;
	message: string;
	severity: "low" | "medium" | "high" | "critical";
	currentLevel?: number;
	quickLink?: string;
}

export default function LowStockAlerts({
	className = "",
}: LowStockAlertsProps) {
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
	const processLowStockAlerts = (data: any): AlertItem[] => {
		const alerts =
			data?.low_stock_alerts || data?.detailed_alerts?.low_stock_alerts || [];

		return alerts.map((alert: any, index: number) => ({
			id: `low-stock-${index}`,
			sku: alert.sku_code || alert.sku || `Unknown-${index}`,
			message:
				alert.message ||
				`Low stock: ${alert.current_level || 0} units remaining`,
			severity: alert.severity || "high",
			currentLevel: alert.current_level,
			quickLink: `/inventory/sku/${alert.sku_code || alert.sku}`,
		}));
	};

	// Get alerts for each platform
	const shopifyLowStockAlerts = useMemo(() => {
		return shopifyAlerts ? processLowStockAlerts(shopifyAlerts) : [];
	}, [shopifyAlerts]);

	const amazonLowStockAlerts = useMemo(() => {
		return amazonAlerts ? processLowStockAlerts(amazonAlerts) : [];
	}, [amazonAlerts]);

	const allLowStockAlerts = useMemo(() => {
		return [...shopifyLowStockAlerts, ...amazonLowStockAlerts];
	}, [shopifyLowStockAlerts, amazonLowStockAlerts]);

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
					styles[severity as keyof typeof styles] || styles.high
				}`}>
				{severity.toUpperCase()}
			</span>
		);
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
							<AlertTriangle className="h-8 w-8 mx-auto mb-2" />
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
							<p className="text-sm">No low stock alerts</p>
							<p className="text-xs text-gray-400">
								All inventory levels are healthy
							</p>
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
										</div>
										<p className="text-xs text-gray-600 mb-2">
											{alert.message}
										</p>
										{alert.currentLevel !== undefined && (
											<p className="text-xs text-red-600 font-medium">
												{alert.currentLevel} units remaining
											</p>
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
					Low Stock Alerts
				</h2>
				<p className="text-sm text-gray-600">
					Critical inventory levels requiring immediate attention
				</p>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Shopify Low Stock Alerts */}
				<AlertCard
					title="Shopify Low Stock"
					alerts={shopifyLowStockAlerts}
					loading={shopifyLoading}
					error={shopifyError}
					icon={<Store className="h-5 w-5" />}
					iconColor="#059669"
					bgColor="bg-red-50"
					borderColor="border-red-200"
					textColor="text-red-700"
				/>

				{/* Amazon Low Stock Alerts */}
				<AlertCard
					title="Amazon Low Stock"
					alerts={amazonLowStockAlerts}
					loading={amazonLoading}
					error={amazonError}
					icon={<ShoppingBag className="h-5 w-5" />}
					iconColor="#f59e0b"
					bgColor="bg-red-50"
					borderColor="border-red-200"
					textColor="text-red-700"
				/>

				{/* All Platforms Low Stock Alerts */}
				<AlertCard
					title="All Platforms"
					alerts={allLowStockAlerts}
					loading={shopifyLoading || amazonLoading}
					error={shopifyError || amazonError}
					icon={<AlertTriangle className="h-5 w-5" />}
					iconColor="#dc2626"
					bgColor="bg-red-50"
					borderColor="border-red-200"
					textColor="text-red-700"
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
