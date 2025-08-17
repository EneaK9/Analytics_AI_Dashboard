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
}

export default function InventorySKUList({
	clientData,
	refreshInterval = 300000,
}: InventorySKUListProps) {
	// Use the comprehensive inventory hook - single API call, optimized
	const {
		loading,
		error,
		skuData,
		summaryStats,
		pagination,
		cached,
		lastUpdated,
		refresh,
		loadPage
	} = useInventoryData({
		refreshInterval,
		fastMode: true
	});

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
				subtitle={`Comprehensive inventory management with real-time availability tracking • ${skuData.length} of ${pagination?.total_count || 0} total SKUs`}
				data={skuData}
				columns={columns}
				loading={loading}
				search={true}
				export={true}
				pagination={false} // Disable client-side pagination since we handle server-side
				pageSize={20}
				emptyMessage="No inventory data available. Please upload CSV data or check data connections."
				className="bg-white shadow-sm"
			/>
			
			{/* Server-side Pagination Controls */}
			{pagination && pagination.total_pages > 1 && (
				<Card className="mt-4">
					<CardContent className="p-4">
						<div className="flex items-center justify-between">
							<div className="text-sm text-gray-600">
								Showing {((pagination.current_page - 1) * pagination.page_size) + 1} to {Math.min(pagination.current_page * pagination.page_size, pagination.total_count)} of {pagination.total_count} SKUs
							</div>
							<div className="flex items-center gap-2">
								<button
									onClick={() => loadPage(pagination.current_page - 1)}
									disabled={!pagination.has_previous || loading}
									className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
								>
									Previous
								</button>
								<span className="px-3 py-1 text-sm">
									Page {pagination.current_page} of {pagination.total_pages}
								</span>
								<button
									onClick={() => loadPage(pagination.current_page + 1)}
									disabled={!pagination.has_next || loading}
									className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
								>
									Next
								</button>
							</div>
						</div>
					</CardContent>
				</Card>
			)}
		</div>
	);
}
