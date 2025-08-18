"use client";

import React, { useMemo } from "react";
import { Search, Download, AlertCircle, Package, TrendingUp, TrendingDown } from "lucide-react";
import DataTable from "../ui/DataTable";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { type SKUData, type SKUSummaryStats } from "../../lib/inventoryService";
import useInventoryData from "../../hooks/useInventoryData";

interface InventorySKUListProps {
	clientData?: any[];
	refreshInterval?: number;
	platform?: "shopify" | "amazon";
	// Pre-fetched data props to avoid duplicate API calls
	skuData?: SKUData[];
	summaryStats?: SKUSummaryStats;
	loading?: boolean;
	error?: string | null;
}

export default function InventorySKUList({
	clientData,
	refreshInterval = 300000,
	platform = "shopify",
	// Accept pre-fetched data to avoid duplicate API calls
	skuData: preFetchedSkuData,
	summaryStats: preFetchedSummaryStats,
	loading: preFetchedLoading,
	error: preFetchedError
}: InventorySKUListProps) {
	// Only use hook if no pre-fetched data is provided
	const hookData = useInventoryData({
		refreshInterval: preFetchedSkuData ? 0 : refreshInterval, // Disable if data is pre-fetched
		fastMode: true,
		platform
	});

	// Use pre-fetched data if available, otherwise use hook data
	const loading = preFetchedLoading !== undefined ? preFetchedLoading : hookData.loading;
	const error = preFetchedError !== undefined ? preFetchedError : hookData.error;
	const skuData = preFetchedSkuData || hookData.skuData;
	const summaryStats = preFetchedSummaryStats || hookData.summaryStats;
	const pagination = hookData.pagination;
	const cached = hookData.cached;
	const lastUpdated = hookData.lastUpdated;
	const refresh = hookData.refresh;

	// Refresh handler for manual refresh
	const handleRefresh = () => refresh(true);

	// Define table columns for SKU data
	const columns = [
		{
			key: "sku_code",
			title: "SKU Code",
			sortable: true,
			width: "120px",
			render: (value: string) => (
				<div className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
					{value}
				</div>
			),
		},
		{
			key: "item_name",
			title: "Item Name",
			sortable: true,
			width: "200px",
			render: (value: string) => (
				<div className="font-medium text-gray-900 truncate" title={value}>
					{value}
				</div>
			),
		},
		{
			key: "on_hand_inventory",
			title: "On-hand Inventory",
			sortable: true,
			type: "number" as const,
			width: "120px",
			render: (value: number) => (
				<div className="text-center">
					<span className="font-semibold">{value.toLocaleString()}</span>
				</div>
			),
		},
		{
			key: "incoming_inventory",
			title: "Incoming Inventory",
			sortable: true,
			type: "number" as const,
			width: "130px",
			render: (value: number) => (
				<div className="text-center">
					<span className="text-blue-600 font-semibold">{value.toLocaleString()}</span>
					<TrendingUp className="inline ml-1 h-3 w-3 text-blue-600" />
				</div>
			),
		},
		{
			key: "outgoing_inventory",
			title: "Outgoing Inventory",
			sortable: true,
			type: "number" as const,
			width: "130px",
			render: (value: number) => (
				<div className="text-center">
					<span className="text-red-600 font-semibold">{value.toLocaleString()}</span>
					<TrendingDown className="inline ml-1 h-3 w-3 text-red-600" />
				</div>
			),
		},
		{
			key: "current_availability",
			title: "Current Availability",
			sortable: true,
			type: "number" as const,
			width: "140px",
			render: (value: number, row: SKUData) => {
				const isLowStock = value < 10;
				const isOutOfStock = value <= 0;
				
				return (
					<div className="text-center">
						<span 
							className={`font-bold ${
								isOutOfStock ? 'text-red-700' : 
								isLowStock ? 'text-yellow-600' : 
								'text-green-600'
							}`}
						>
							{value.toLocaleString()}
						</span>
						{isLowStock && (
							<AlertCircle className="inline ml-1 h-3 w-3 text-yellow-500" />
						)}
					</div>
				);
			},
		},
		{
			key: "unit_price",
			title: "Unit Price",
			sortable: true,
			type: "currency" as const,
			width: "100px",
		},
		{
			key: "total_value",
			title: "Total Value",
			sortable: true,
			type: "currency" as const,
			width: "120px",
			render: (value: number) => (
				<div className="text-right font-semibold text-gray-900">
					${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
				</div>
			),
		},
	];

	// Data loading and refresh are now handled by the useInventoryData hook

	return (
		<div className="space-y-6">
			{/* Summary Cards */}
			{summaryStats && (
				<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Total SKUs</p>
									<p className="text-2xl font-bold text-gray-900">{summaryStats.total_skus}</p>
								</div>
								<Package className="h-8 w-8 text-blue-600" />
							</div>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Total Inventory Value</p>
									<p className="text-2xl font-bold text-green-600">
										${(summaryStats.total_inventory_value || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
									</p>
								</div>
								<TrendingUp className="h-8 w-8 text-green-600" />
							</div>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Low Stock Alerts</p>
									<p className="text-2xl font-bold text-yellow-600">{summaryStats.low_stock_count}</p>
								</div>
								<AlertCircle className="h-8 w-8 text-yellow-600" />
							</div>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">Out of Stock</p>
									<p className="text-2xl font-bold text-red-600">{summaryStats.out_of_stock_count}</p>
								</div>
								<AlertCircle className="h-8 w-8 text-red-600" />
							</div>
						</CardContent>
					</Card>
				</div>
			)}

			{/* SKU Data Table */}
			<DataTable
				title="SKU Inventory List"
				subtitle={`Comprehensive inventory management with real-time availability tracking • ${skuData.length} SKUs`}
				data={skuData}
				columns={columns}
				loading={loading}
				search={true}
				export={true}
				pagination={true}
				pageSize={20}
				emptyMessage="No inventory data available. Please upload CSV data or check data connections."
				className="bg-white shadow-sm"
			/>
		</div>
	);
}
