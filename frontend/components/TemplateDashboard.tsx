"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import DataTable from "@/components/ui/DataTable";
import KPICard, {
	RevenueKPI,
	UsersKPI,
	OrdersKPI,
	InventoryKPI,
} from "@/components/ui/KPICard";
import AlertSummary, {
	Alert,
	createLowStockAlert,
	createSalesSpikeAlert,
} from "@/components/ui/AlertSummary";
import DateRangePicker, {
	DateRange,
	getDateRange,
} from "@/components/ui/DateRangePicker";
import * as Charts from "./charts";

// Template types
export enum DashboardTemplateType {
	INVENTORY = "inventory",
	SALES = "sales",
	FINANCIAL = "financial",
	MARKETING = "marketing",
	OPERATIONS = "operations",
	ECOMMERCE = "ecommerce",
	GENERAL = "general",
}

interface TemplateConfig {
	templateType: DashboardTemplateType;
	title: string;
	description: string;
	components: ComponentConfig[];
	colorScheme: {
		primary: string;
		secondary: string;
		success: string;
		warning: string;
		danger: string;
	};
}

interface ComponentConfig {
	id: string;
	type: "kpi_card" | "data_table" | "chart" | "alert_summary" | "date_picker";
	title: string;
	subtitle?: string;
	position: { row: number; col: number };
	size: { width: number; height: number };
	config?: any;
	chartType?: string;
	dataColumns?: string[];
}

interface TemplateDashboardProps {
	templateType: DashboardTemplateType;
	clientData: any[];
	onTemplateChange?: (template: DashboardTemplateType) => void;
	className?: string;
}

export default function TemplateDashboard({
	templateType,
	clientData = [],
	onTemplateChange,
	className = "",
}: TemplateDashboardProps) {
	const [dateRange, setDateRange] = useState<DateRange>(getDateRange("month"));
	const [filteredData, setFilteredData] = useState(clientData);
	const [alerts, setAlerts] = useState<Alert[]>([]);

	// Filter data based on date range
	useEffect(() => {
		if (clientData.length === 0) {
			setFilteredData([]);
			return;
		}

		const filtered = clientData.filter((item) => {
			if (!item.date && !item.created_at && !item.updated_at) return true;

			const itemDate = new Date(
				item.date || item.created_at || item.updated_at
			);
			return itemDate >= dateRange.start && itemDate <= dateRange.end;
		});

		setFilteredData(filtered);
	}, [clientData, dateRange]);

	// Generate alerts based on data and template type
	useEffect(() => {
		const generatedAlerts: Alert[] = [];

		if (
			templateType === DashboardTemplateType.INVENTORY &&
			filteredData.length > 0
		) {
			// Generate inventory-specific alerts
			filteredData.forEach((item) => {
				if (
					item.stock_level &&
					item.reorder_point &&
					item.stock_level < item.reorder_point
				) {
					generatedAlerts.push(
						createLowStockAlert(
							item.product_name || item.title || "Unknown Product",
							item.stock_level,
							item.reorder_point
						)
					);
				}
			});

			// Sales spike alerts
			if (filteredData.some((item) => item.units_sold > 100)) {
				generatedAlerts.push(createSalesSpikeAlert("Top Products", "25%"));
			}
		}

		setAlerts(generatedAlerts.slice(0, 5)); // Limit to 5 alerts
	}, [filteredData, templateType]);

	// Get template configuration
	const getTemplateConfig = (): TemplateConfig => {
		switch (templateType) {
			case DashboardTemplateType.INVENTORY:
				return {
					templateType,
					title: "Inventory Management Dashboard",
					description:
						"Complete inventory tracking, stock levels, and turnover analytics",
					colorScheme: {
						primary: "#2563eb",
						secondary: "#f97316",
						success: "#16a34a",
						warning: "#eab308",
						danger: "#dc2626",
					},
					components: [
						{
							id: "inventory_kpis",
							type: "kpi_card",
							title: "Key Metrics",
							position: { row: 0, col: 0 },
							size: { width: 4, height: 1 },
						},
						{
							id: "inventory_table",
							type: "data_table",
							title: "SKU Inventory Overview",
							subtitle: "Complete inventory status by SKU",
							position: { row: 1, col: 0 },
							size: { width: 4, height: 2 },
						},
						{
							id: "inventory_trends",
							type: "chart",
							title: "Inventory Levels Trend",
							subtitle: "Stock level tracking over time",
							chartType: "ShadcnAreaInteractive",
							position: { row: 3, col: 0 },
							size: { width: 2, height: 2 },
						},
						{
							id: "sales_performance",
							type: "chart",
							title: "Sales Performance",
							subtitle: "Units sold analysis",
							chartType: "ShadcnBarMultiple",
							position: { row: 3, col: 2 },
							size: { width: 2, height: 2 },
						},
						{
							id: "inventory_alerts",
							type: "alert_summary",
							title: "Inventory Alerts",
							position: { row: 5, col: 0 },
							size: { width: 4, height: 1 },
						},
					],
				};

			case DashboardTemplateType.SALES:
				return {
					templateType,
					title: "Sales Performance Dashboard",
					description: "Comprehensive sales analytics and revenue tracking",
					colorScheme: {
						primary: "#16a34a",
						secondary: "#2563eb",
						success: "#16a34a",
						warning: "#eab308",
						danger: "#dc2626",
					},
					components: [
						{
							id: "sales_kpis",
							type: "kpi_card",
							title: "Sales Metrics",
							position: { row: 0, col: 0 },
							size: { width: 4, height: 1 },
						},
						{
							id: "revenue_trends",
							type: "chart",
							title: "Revenue Trends",
							subtitle: "Sales performance over time",
							chartType: "ShadcnAreaStacked",
							position: { row: 1, col: 0 },
							size: { width: 3, height: 2 },
						},
						{
							id: "top_products",
							type: "chart",
							title: "Top Products",
							chartType: "ShadcnBarHorizontal",
							position: { row: 1, col: 3 },
							size: { width: 1, height: 2 },
						},
					],
				};

			case DashboardTemplateType.FINANCIAL:
				return {
					templateType,
					title: "Financial Analytics Dashboard",
					description: "Financial performance and profitability analysis",
					colorScheme: {
						primary: "#059669",
						secondary: "#dc2626",
						success: "#16a34a",
						warning: "#eab308",
						danger: "#dc2626",
					},
					components: [
						{
							id: "financial_kpis",
							type: "kpi_card",
							title: "Financial Metrics",
							position: { row: 0, col: 0 },
							size: { width: 4, height: 1 },
						},
					],
				};

			default:
				return {
					templateType: DashboardTemplateType.GENERAL,
					title: "Analytics Dashboard",
					description: "General purpose data analytics",
					colorScheme: {
						primary: "#64748b",
						secondary: "#475569",
						success: "#10b981",
						warning: "#f59e0b",
						danger: "#ef4444",
					},
					components: [],
				};
		}
	};

	const config = getTemplateConfig();

	// Render KPI cards based on template type
	const renderKPICards = () => {
		const kpiData = generateKPIData(filteredData, templateType);

		if (templateType === DashboardTemplateType.INVENTORY) {
			return (
				<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
					<InventoryKPI
						title="Total SKUs"
						value={kpiData.totalSKUs}
						trend={{ value: "+5.2%", isPositive: true }}
					/>
					<KPICard
						title="Low Stock Items"
						value={kpiData.lowStockItems}
						icon="AlertTriangle"
						iconColor="#f97316"
						iconBgColor="#fff7ed"
						colorScheme="warning"
						trend={{ value: "-12%", isPositive: false }}
					/>
					<RevenueKPI
						title="Total Inventory Value"
						value={`$${kpiData.inventoryValue.toLocaleString()}`}
						trend={{ value: "+8.3%", isPositive: true }}
					/>
					<KPICard
						title="Turnover Rate"
						value={`${kpiData.turnoverRate}%`}
						icon="Activity"
						iconColor="#8b5cf6"
						iconBgColor="#f3e8ff"
						trend={{ value: "+2.1%", isPositive: true }}
					/>
				</div>
			);
		} else if (templateType === DashboardTemplateType.SALES) {
			return (
				<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
					<RevenueKPI
						title="Total Revenue"
						value={`$${kpiData.totalRevenue.toLocaleString()}`}
						trend={{ value: "+12.5%", isPositive: true }}
					/>
					<OrdersKPI
						title="Total Orders"
						value={kpiData.totalOrders}
						trend={{ value: "+8.2%", isPositive: true }}
					/>
					<KPICard
						title="Average Order Value"
						value={`$${kpiData.avgOrderValue}`}
						icon="DollarSign"
						iconColor="#059669"
						iconBgColor="#ecfdf5"
						colorScheme="success"
						trend={{ value: "+3.1%", isPositive: true }}
					/>
					<KPICard
						title="Conversion Rate"
						value={`${kpiData.conversionRate}%`}
						icon="Target"
						iconColor="#3b82f6"
						iconBgColor="#eff6ff"
						colorScheme="info"
						trend={{ value: "+1.8%", isPositive: true }}
					/>
				</div>
			);
		}

		// Default KPIs for other templates
		return (
			<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
				<KPICard
					title="Total Records"
					value={filteredData.length}
					icon="BarChart3"
					iconColor={config.colorScheme.primary}
					iconBgColor={`${config.colorScheme.primary}20`}
				/>
				<KPICard
					title="Active Items"
					value={Math.floor(filteredData.length * 0.8)}
					icon="Activity"
					iconColor={config.colorScheme.success}
					iconBgColor={`${config.colorScheme.success}20`}
				/>
			</div>
		);
	};

	// Render data table for inventory template
	const renderDataTable = () => {
		if (
			templateType !== DashboardTemplateType.INVENTORY ||
			filteredData.length === 0
		) {
			return null;
		}

		const columns = [
			{ key: "sku", title: "SKU Code", sortable: true },
			{ key: "title", title: "Product Name", sortable: true },
			{
				key: "stock_level",
				title: "On Hand",
				sortable: true,
				type: "number" as const,
			},
			{
				key: "reorder_point",
				title: "Reorder Point",
				sortable: true,
				type: "number" as const,
			},
			{
				key: "unit_price",
				title: "Unit Price",
				sortable: true,
				type: "currency" as const,
			},
			{
				key: "availability",
				title: "Status",
				render: (value: any, row: any) => {
					const stock = row.stock_level || 0;
					const reorder = row.reorder_point || 0;
					if (stock <= reorder) {
						return (
							<span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">
								Low Stock
							</span>
						);
					} else if (stock > reorder * 2) {
						return (
							<span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs">
								Overstock
							</span>
						);
					}
					return (
						<span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
							Normal
						</span>
					);
				},
			},
		];

		return (
			<DataTable
				data={filteredData}
				columns={columns}
				title="SKU Inventory Overview"
				subtitle="Complete inventory status by SKU"
				pagination={true}
				search={true}
				export={true}
				className="mt-6"
			/>
		);
	};

	// Render charts based on template
	const renderCharts = () => {
		if (filteredData.length === 0) return null;

		const charts = [];

		if (templateType === DashboardTemplateType.INVENTORY) {
			// Inventory level trends
			const trendData = processChartData(filteredData, "date", "stock_level");
			if (trendData.length > 0) {
				charts.push(
					<div
						key="inventory-trends"
						className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
						<div className="mb-4">
							<h3 className="text-lg font-semibold text-gray-900">
								Inventory Levels Trend
							</h3>
							<p className="text-sm text-gray-600">
								Stock level tracking over time
							</p>
						</div>
						<div className="h-[300px]">
							<Charts.ShadcnAreaInteractive
								data={trendData}
								title="Inventory Trends"
								height={300}
							/>
						</div>
					</div>
				);
			}

			// Sales performance
			const salesData = processChartData(filteredData, "title", "units_sold");
			if (salesData.length > 0) {
				charts.push(
					<div
						key="sales-performance"
						className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
						<div className="mb-4">
							<h3 className="text-lg font-semibold text-gray-900">
								Sales Performance
							</h3>
							<p className="text-sm text-gray-600">Units sold by product</p>
						</div>
						<div className="h-[300px]">
							<Charts.ShadcnBarMultiple
								data={salesData.slice(0, 10)}
								title="Sales Performance"
								height={300}
							/>
						</div>
					</div>
				);
			}
		}

		return charts.length > 0 ? (
			<div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">{charts}</div>
		) : null;
	};

	return (
		<div className={`space-y-8 ${className}`}>
			{/* Template Header */}
			<div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
				<div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
					<div className="flex-1">
						<h1
							className="text-3xl font-bold text-gray-900 mb-2"
							style={{ color: config.colorScheme.primary }}>
							{config.title}
						</h1>
						<p className="text-lg text-gray-700 mb-3">{config.description}</p>
						<div className="flex items-center gap-4 text-sm text-gray-600">
							<span className="inline-flex items-center gap-1">
								🏗️ Template-Based Dashboard
							</span>
							<span className="inline-flex items-center gap-1">
								📊 {filteredData.length} data points
							</span>
						</div>
					</div>
					<div className="flex flex-col gap-3">
						<DateRangePicker
							value={dateRange}
							onChange={setDateRange}
							className="w-64"
						/>
						{onTemplateChange && (
							<select
								value={templateType}
								onChange={(e) =>
									onTemplateChange(e.target.value as DashboardTemplateType)
								}
								className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
								<option value={DashboardTemplateType.INVENTORY}>
									Inventory Dashboard
								</option>
								<option value={DashboardTemplateType.SALES}>
									Sales Dashboard
								</option>
								<option value={DashboardTemplateType.FINANCIAL}>
									Financial Dashboard
								</option>
								<option value={DashboardTemplateType.GENERAL}>
									General Dashboard
								</option>
							</select>
						)}
					</div>
				</div>
			</div>

			{/* KPI Cards */}
			<div>
				<div className="mb-6">
					<h2 className="text-2xl font-semibold text-gray-900 mb-2">
						Key Performance Indicators
					</h2>
					<p className="text-gray-600">
						Monitor your business performance at a glance
					</p>
				</div>
				{renderKPICards()}
			</div>

			{/* Data Table (for inventory) */}
			{renderDataTable()}

			{/* Charts */}
			{renderCharts()}

			{/* Alerts (for inventory) */}
			{templateType === DashboardTemplateType.INVENTORY &&
				alerts.length > 0 && (
					<AlertSummary
						alerts={alerts}
						title="Inventory Alerts"
						subtitle="Important notifications and status updates"
						showCounts={true}
						quickActions={true}
					/>
				)}
		</div>
	);
}

// Helper functions
function generateKPIData(data: any[], templateType: DashboardTemplateType) {
	if (data.length === 0) {
		return {
			totalSKUs: 0,
			lowStockItems: 0,
			inventoryValue: 0,
			turnoverRate: 0,
			totalRevenue: 0,
			totalOrders: 0,
			avgOrderValue: 0,
			conversionRate: 0,
		};
	}

	const totalSKUs = data.length;
	const lowStockItems = data.filter(
		(item) =>
			item.stock_level &&
			item.reorder_point &&
			item.stock_level < item.reorder_point
	).length;

	const inventoryValue = data.reduce((sum, item) => {
		const price = parseFloat(item.unit_price || item.price || 0);
		const quantity = parseInt(item.stock_level || item.quantity || 0);
		return sum + price * quantity;
	}, 0);

	const totalRevenue = data.reduce((sum, item) => {
		return sum + parseFloat(item.revenue || item.sales || item.amount || 0);
	}, 0);

	const totalOrders = data.reduce((sum, item) => {
		return sum + parseInt(item.orders || item.order_count || 1);
	}, 0);

	return {
		totalSKUs,
		lowStockItems,
		inventoryValue,
		turnoverRate: 0, // Require real calculation instead of Math.random()
		totalRevenue,
		totalOrders,
		avgOrderValue: totalOrders > 0 ? Math.round(totalRevenue / totalOrders) : 0,
		conversionRate: 0, // Require real calculation instead of Math.random()
	};
}

function processChartData(data: any[], xKey: string, yKey: string) {
	if (!data || data.length === 0) return [];

	return data
		.filter(
			(item) => item[xKey] && item[yKey] !== null && item[yKey] !== undefined
		)
		.map((item) => ({
			[xKey]: item[xKey],
			[yKey]: parseFloat(item[yKey]) || 0,
			...item,
		}))
		.slice(0, 20); // Limit for performance
}
