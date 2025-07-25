"use client";

import React from "react";
import {
	AlertTriangle,
	AlertCircle,
	TrendingUp,
	TrendingDown,
	Package,
	ShoppingCart,
	Clock,
	CheckCircle,
	XCircle,
	Info,
	ExternalLink,
	Bell,
	Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./card";

export interface Alert {
	id: string;
	type:
		| "low_stock"
		| "overstock"
		| "sales_spike"
		| "sales_slowdown"
		| "critical"
		| "warning"
		| "info"
		| "success";
	title: string;
	message: string;
	count?: number;
	timestamp?: Date;
	severity?: "low" | "medium" | "high" | "critical";
	actionUrl?: string;
	actionLabel?: string;
}

interface AlertSummaryProps {
	alerts?: Alert[];
	title?: string;
	subtitle?: string;
	showCounts?: boolean;
	showTimestamps?: boolean;
	quickActions?: boolean;
	maxDisplay?: number;
	className?: string;
	onAlertClick?: (alert: Alert) => void;
	onViewAll?: () => void;
}

export default function AlertSummary({
	alerts = [],
	title = "System Alerts",
	subtitle = "Important notifications and status updates",
	showCounts = true,
	showTimestamps = true,
	quickActions = true,
	maxDisplay = 5,
	className = "",
	onAlertClick,
	onViewAll,
}: AlertSummaryProps) {
	// Group alerts by type for summary stats
	const alertStats = alerts.reduce((acc, alert) => {
		acc[alert.type] = (acc[alert.type] || 0) + (alert.count || 1);
		return acc;
	}, {} as Record<string, number>);

	// Get icon and colors for alert types
	const getAlertConfig = (type: Alert["type"]) => {
		const configs = {
			low_stock: {
				icon: <Package className="h-4 w-4" />,
				color: "text-orange-600",
				bgColor: "bg-orange-50",
				borderColor: "border-orange-200",
				label: "Low Stock",
			},
			overstock: {
				icon: <Package className="h-4 w-4" />,
				color: "text-yellow-600",
				bgColor: "bg-yellow-50",
				borderColor: "border-yellow-200",
				label: "Overstock",
			},
			sales_spike: {
				icon: <TrendingUp className="h-4 w-4" />,
				color: "text-green-600",
				bgColor: "bg-green-50",
				borderColor: "border-green-200",
				label: "Sales Spike",
			},
			sales_slowdown: {
				icon: <TrendingDown className="h-4 w-4" />,
				color: "text-red-600",
				bgColor: "bg-red-50",
				borderColor: "border-red-200",
				label: "Sales Slowdown",
			},
			critical: {
				icon: <AlertTriangle className="h-4 w-4" />,
				color: "text-red-600",
				bgColor: "bg-red-50",
				borderColor: "border-red-200",
				label: "Critical",
			},
			warning: {
				icon: <AlertCircle className="h-4 w-4" />,
				color: "text-yellow-600",
				bgColor: "bg-yellow-50",
				borderColor: "border-yellow-200",
				label: "Warning",
			},
			info: {
				icon: <Info className="h-4 w-4" />,
				color: "text-blue-600",
				bgColor: "bg-blue-50",
				borderColor: "border-blue-200",
				label: "Info",
			},
			success: {
				icon: <CheckCircle className="h-4 w-4" />,
				color: "text-green-600",
				bgColor: "bg-green-50",
				borderColor: "border-green-200",
				label: "Success",
			},
		};
		return configs[type] || configs.info;
	};

	// Format timestamp
	const formatTimestamp = (timestamp: Date) => {
		const now = new Date();
		const diffMs = now.getTime() - timestamp.getTime();
		const diffMins = Math.floor(diffMs / 60000);

		if (diffMins < 1) return "Just now";
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
		return timestamp.toLocaleDateString();
	};

	// Get severity badge
	const getSeverityBadge = (severity: Alert["severity"]) => {
		const badges = {
			low: "bg-gray-100 text-gray-600",
			medium: "bg-yellow-100 text-yellow-700",
			high: "bg-orange-100 text-orange-700",
			critical: "bg-red-100 text-red-700",
		};
		return badges[severity || "low"];
	};

	const displayAlerts = alerts.slice(0, maxDisplay);
	const hasMoreAlerts = alerts.length > maxDisplay;

	if (alerts.length === 0) {
		return (
			<Card className={className}>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<CheckCircle className="h-5 w-5 text-green-600" />
						All Clear
					</CardTitle>
				</CardHeader>
				<CardContent>
					<div className="text-center py-8">
						<div className="text-green-600 mb-2">
							<CheckCircle className="h-12 w-12 mx-auto" />
						</div>
						<p className="text-green-700 font-medium mb-1">No Active Alerts</p>
						<p className="text-green-600 text-sm">
							Everything is running smoothly
						</p>
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card className={className}>
			<CardHeader>
				<div className="flex items-center justify-between">
					<div>
						<CardTitle className="flex items-center gap-2">
							<Bell className="h-5 w-5" />
							{title}
						</CardTitle>
						{subtitle && (
							<p className="text-sm text-gray-600 mt-1">{subtitle}</p>
						)}
					</div>
					{hasMoreAlerts && onViewAll && (
						<button
							onClick={onViewAll}
							className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
							View All
							<ExternalLink className="h-3 w-3" />
						</button>
					)}
				</div>
			</CardHeader>

			<CardContent>
				{/* Alert Statistics Summary */}
				{showCounts && Object.keys(alertStats).length > 0 && (
					<div className="grid grid-cols-2 gap-3 mb-6">
						{Object.entries(alertStats).map(([type, count]) => {
							const config = getAlertConfig(type as Alert["type"]);
							return (
								<div
									key={type}
									className={`p-3 rounded-lg border ${config.borderColor} ${config.bgColor}`}>
									<div className="flex items-center justify-between">
										<div className="flex items-center gap-2">
											<div className={config.color}>{config.icon}</div>
											<span className="text-sm font-medium text-gray-900">
												{config.label}
											</span>
										</div>
										<span className={`font-bold ${config.color}`}>{count}</span>
									</div>
								</div>
							);
						})}
					</div>
				)}

				{/* Individual Alerts */}
				<div className="space-y-3">
					{displayAlerts.map((alert) => {
						const config = getAlertConfig(alert.type);
						return (
							<div
								key={alert.id}
								className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor} hover:shadow-sm transition-shadow cursor-pointer`}
								onClick={() => onAlertClick?.(alert)}>
								<div className="flex items-start justify-between">
									<div className="flex items-start gap-3 flex-1">
										<div className={config.color}>{config.icon}</div>
										<div className="flex-1 min-w-0">
											<div className="flex items-center gap-2 mb-1">
												<h4 className="font-medium text-gray-900 truncate">
													{alert.title}
												</h4>
												{alert.severity && (
													<span
														className={`px-2 py-0.5 text-xs font-medium rounded-full ${getSeverityBadge(
															alert.severity
														)}`}>
														{alert.severity.toUpperCase()}
													</span>
												)}
												{alert.count && alert.count > 1 && (
													<span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
														{alert.count}
													</span>
												)}
											</div>
											<p className="text-sm text-gray-600 mb-2">
												{alert.message}
											</p>
											{showTimestamps && alert.timestamp && (
												<div className="flex items-center gap-1 text-xs text-gray-500">
													<Clock className="h-3 w-3" />
													{formatTimestamp(alert.timestamp)}
												</div>
											)}
										</div>
									</div>

									{quickActions && alert.actionUrl && (
										<button
											onClick={(e) => {
												e.stopPropagation();
												window.open(alert.actionUrl, "_blank");
											}}
											className="ml-2 px-3 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors">
											{alert.actionLabel || "View"}
										</button>
									)}
								</div>
							</div>
						);
					})}
				</div>

				{/* View More Button */}
				{hasMoreAlerts && (
					<div className="mt-4 text-center">
						<button
							onClick={onViewAll}
							className="text-sm text-blue-600 hover:text-blue-700 font-medium">
							View {alerts.length - maxDisplay} more alerts
						</button>
					</div>
				)}
			</CardContent>
		</Card>
	);
}

// Utility function to create common alert types
export const createAlert = (
	type: Alert["type"],
	title: string,
	message: string,
	options: Partial<Alert> = {}
): Alert => ({
	id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
	type,
	title,
	message,
	timestamp: new Date(),
	severity: "medium",
	...options,
});

// Preset alert creators
export const createLowStockAlert = (
	productName: string,
	currentStock: number,
	reorderPoint: number
) =>
	createAlert(
		"low_stock",
		`Low Stock: ${productName}`,
		`Current stock (${currentStock}) is below reorder point (${reorderPoint})`,
		{ severity: "high", actionLabel: "Reorder" }
	);

export const createSalesSpikeAlert = (product: string, increase: string) =>
	createAlert(
		"sales_spike",
		`Sales Spike Detected`,
		`${product} sales increased by ${increase} in the last 24 hours`,
		{ severity: "low", actionLabel: "Analyze" }
	);

export const createOverstockAlert = (product: string, excess: number) =>
	createAlert(
		"overstock",
		`Overstock Warning`,
		`${product} has ${excess} units above optimal stock level`,
		{ severity: "medium", actionLabel: "Review" }
	);
