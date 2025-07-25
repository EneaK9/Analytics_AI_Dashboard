"use client";

import React from "react";
import {
	TrendingUp,
	TrendingDown,
	ArrowUpRight,
	ArrowDownRight,
	DollarSign,
	Users,
	Package,
	ShoppingCart,
	Target,
	Activity,
	BarChart3,
	AlertCircle,
} from "lucide-react";
import { Card, CardContent } from "./card";

interface TrendData {
	value: string;
	isPositive: boolean;
	label?: string;
}

interface KPICardProps {
	title: string;
	value: string | number;
	subtitle?: string;
	trend?: TrendData;
	icon?: string;
	iconColor?: string;
	iconBgColor?: string;
	loading?: boolean;
	error?: string;
	className?: string;
	size?: "small" | "medium" | "large";
	colorScheme?: "default" | "success" | "warning" | "danger" | "info";
}

export default function KPICard({
	title,
	value,
	subtitle,
	trend,
	icon = "BarChart3",
	iconColor = "#2563eb",
	iconBgColor = "#eff6ff",
	loading = false,
	error,
	className = "",
	size = "medium",
	colorScheme = "default",
}: KPICardProps) {
	// Icon mapping
	const getIcon = (iconName: string) => {
		const iconProps = {
			className: `${
				size === "small" ? "h-5 w-5" : size === "large" ? "h-8 w-8" : "h-6 w-6"
			}`,
			style: { color: iconColor },
		};

		const iconMap: { [key: string]: React.ReactNode } = {
			DollarSign: <DollarSign {...iconProps} />,
			Users: <Users {...iconProps} />,
			Package: <Package {...iconProps} />,
			ShoppingCart: <ShoppingCart {...iconProps} />,
			Target: <Target {...iconProps} />,
			Activity: <Activity {...iconProps} />,
			BarChart3: <BarChart3 {...iconProps} />,
			TrendingUp: <TrendingUp {...iconProps} />,
			TrendingDown: <TrendingDown {...iconProps} />,
			AlertCircle: <AlertCircle {...iconProps} />,
		};

		return iconMap[iconName] || <BarChart3 {...iconProps} />;
	};

	// Color scheme styles
	const getColorScheme = () => {
		switch (colorScheme) {
			case "success":
				return {
					iconBg: "bg-green-100",
					iconColor: "text-green-600",
					border: "border-green-200",
					accent: "bg-green-50",
				};
			case "warning":
				return {
					iconBg: "bg-yellow-100",
					iconColor: "text-yellow-600",
					border: "border-yellow-200",
					accent: "bg-yellow-50",
				};
			case "danger":
				return {
					iconBg: "bg-red-100",
					iconColor: "text-red-600",
					border: "border-red-200",
					accent: "bg-red-50",
				};
			case "info":
				return {
					iconBg: "bg-blue-100",
					iconColor: "text-blue-600",
					border: "border-blue-200",
					accent: "bg-blue-50",
				};
			default:
				return {
					iconBg: "bg-gray-100",
					iconColor: "text-gray-600",
					border: "border-gray-200",
					accent: "bg-gray-50",
				};
		}
	};

	const colors = getColorScheme();

	// Size configurations
	const sizeConfig = {
		small: {
			cardPadding: "p-4",
			iconSize: "h-10 w-10",
			titleSize: "text-sm",
			valueSize: "text-lg",
			subtitleSize: "text-xs",
			trendSize: "text-xs",
		},
		medium: {
			cardPadding: "p-6",
			iconSize: "h-12 w-12",
			titleSize: "text-base",
			valueSize: "text-2xl",
			subtitleSize: "text-sm",
			trendSize: "text-sm",
		},
		large: {
			cardPadding: "p-8",
			iconSize: "h-16 w-16",
			titleSize: "text-lg",
			valueSize: "text-4xl",
			subtitleSize: "text-base",
			trendSize: "text-base",
		},
	};

	const config = sizeConfig[size];

	// Format value display
	const formatValue = (val: string | number) => {
		if (typeof val === "number") {
			if (val >= 1000000) {
				return (val / 1000000).toFixed(1) + "M";
			} else if (val >= 1000) {
				return (val / 1000).toFixed(1) + "K";
			}
			return val.toLocaleString();
		}
		return val;
	};

	if (loading) {
		return (
			<Card
				className={`group hover:shadow-lg transition-all duration-300 ${className}`}>
				<CardContent className={config.cardPadding}>
					<div className="animate-pulse">
						<div className="flex items-center justify-between mb-4">
							<div
								className={`${config.iconSize} bg-gray-200 rounded-xl`}></div>
							<div className="w-16 h-6 bg-gray-200 rounded"></div>
						</div>
						<div className="space-y-2">
							<div className="h-8 bg-gray-200 rounded"></div>
							<div className="h-4 bg-gray-200 rounded w-3/4"></div>
						</div>
					</div>
				</CardContent>
			</Card>
		);
	}

	if (error) {
		return (
			<Card
				className={`group hover:shadow-lg transition-all duration-300 border-red-200 ${className}`}>
				<CardContent className={config.cardPadding}>
					<div className="flex items-center justify-between mb-4">
						<div
							className={`${config.iconSize} bg-red-100 rounded-xl flex items-center justify-center`}>
							<AlertCircle className="h-6 w-6 text-red-600" />
						</div>
					</div>
					<div>
						<h3 className={`${config.valueSize} font-bold text-red-600 mb-2`}>
							Error
						</h3>
						<p className={`${config.subtitleSize} text-red-500`}>{error}</p>
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card
			className={`group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 ${colors.border} ${className}`}>
			<CardContent className={config.cardPadding}>
				{/* Header with Icon and Trend */}
				<div className="flex items-center justify-between mb-4">
					<div
						className={`${config.iconSize} rounded-xl flex items-center justify-center shadow-sm`}
						style={{ backgroundColor: iconBgColor }}>
						{getIcon(icon)}
					</div>

					{trend && (
						<div
							className={`flex items-center gap-1 px-3 py-1 rounded-lg font-semibold ${
								config.trendSize
							} ${
								trend.isPositive
									? "text-green-700 bg-green-100 border border-green-200"
									: "text-red-700 bg-red-100 border border-red-200"
							}`}>
							{trend.isPositive ? (
								<ArrowUpRight className="h-3 w-3" />
							) : (
								<ArrowDownRight className="h-3 w-3" />
							)}
							{trend.value}
						</div>
					)}
				</div>

				{/* Value and Title */}
				<div className="space-y-2">
					<h3
						className={`${config.valueSize} font-bold text-gray-900 group-hover:text-blue-600 transition-colors`}>
						{formatValue(value)}
					</h3>
					<p className={`${config.titleSize} font-semibold text-gray-600`}>
						{title}
					</p>
					{subtitle && (
						<p className={`${config.subtitleSize} text-gray-500`}>{subtitle}</p>
					)}
				</div>

				{/* Trend Label */}
				{trend?.label && (
					<div className="mt-3 pt-3 border-t border-gray-100">
						<p className={`${config.trendSize} text-gray-500`}>{trend.label}</p>
					</div>
				)}
			</CardContent>
		</Card>
	);
}

// Preset KPI Cards for common use cases
export const RevenueKPI = (
	props: Omit<KPICardProps, "icon" | "iconColor" | "iconBgColor">
) => (
	<KPICard
		{...props}
		icon="DollarSign"
		iconColor="#059669"
		iconBgColor="#ecfdf5"
		colorScheme="success"
	/>
);

export const UsersKPI = (
	props: Omit<KPICardProps, "icon" | "iconColor" | "iconBgColor">
) => (
	<KPICard
		{...props}
		icon="Users"
		iconColor="#3b82f6"
		iconBgColor="#eff6ff"
		colorScheme="info"
	/>
);

export const OrdersKPI = (
	props: Omit<KPICardProps, "icon" | "iconColor" | "iconBgColor">
) => (
	<KPICard
		{...props}
		icon="ShoppingCart"
		iconColor="#f59e0b"
		iconBgColor="#fffbeb"
		colorScheme="warning"
	/>
);

export const InventoryKPI = (
	props: Omit<KPICardProps, "icon" | "iconColor" | "iconBgColor">
) => (
	<KPICard
		{...props}
		icon="Package"
		iconColor="#8b5cf6"
		iconBgColor="#f3e8ff"
	/>
);
