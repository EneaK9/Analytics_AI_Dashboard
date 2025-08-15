"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Search, Download, AlertCircle, Package, TrendingUp, TrendingDown } from "lucide-react";
import DataTable from "../ui/DataTable";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { inventoryService, type SKUData, type SKUSummaryStats } from "../../lib/inventoryService";

interface InventorySKUListProps {
	clientData?: any[];
	refreshInterval?: number;
}

export default function InventorySKUList({
	clientData,
	refreshInterval = 300000,
}: InventorySKUListProps) {
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [skuData, setSKUData] = useState<SKUData[]>([]);
	const [summaryStats, setSummaryStats] = useState<SKUSummaryStats | null>(null);
	const [currentPage, setCurrentPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [totalCount, setTotalCount] = useState(0);
	const [pageSize] = useState(50); // Fixed page size

	// Fetch SKU inventory data from dedicated paginated service
	const fetchSKUData = async (page: number = 1, forceRefresh: boolean = false) => {
		try {
			setLoading(true);
			setError(null);

			console.log(`🔍 Fetching SKU data for page ${page}...`);
			const response = await inventoryService.getPaginatedSKUInventory(page, pageSize, true, forceRefresh);
			
			setSKUData(response.skus);
			setSummaryStats(response.summary_stats || null);
			setCurrentPage(response.pagination.current_page);
			setTotalPages(response.pagination.total_pages);
			setTotalCount(response.pagination.total_count);
			setError(null);
			
			console.log(`✅ Loaded ${response.skus.length} SKUs (page ${page}/${response.pagination.total_pages})`);
			setLoading(false);
		} catch (err: any) {
			console.error("Error fetching SKU data:", err);
			setSKUData([]);
			setSummaryStats(null);
			setError(`Failed to fetch SKU data: ${err.message}`);
			setLoading(false);
		}
	};

	// Handle page changes
	const handlePageChange = (newPage: number) => {
		if (newPage >= 1 && newPage <= totalPages) {
			fetchSKUData(newPage);
		}
	};

	useEffect(() => {
		fetchSKUData(1);

		// Set up refresh interval if specified
		if (refreshInterval > 0) {
			const interval = setInterval(() => fetchSKUData(currentPage), refreshInterval);
			return () => clearInterval(interval);
		}
	}, [refreshInterval]);

	// Refresh current page
	const handleRefresh = () => {
		fetchSKUData(currentPage, true);
	};

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
										${summaryStats.total_inventory_value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
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

			{/* SKU Data Table with Server-Side Pagination */}
			<div className="bg-white shadow-sm rounded-lg">
				<div className="px-6 py-4 border-b border-gray-200">
					<div className="flex items-center justify-between">
						<div>
							<h3 className="text-lg font-medium text-gray-900">SKU Inventory List</h3>
							<p className="text-sm text-gray-600">
								Comprehensive inventory management with real-time availability tracking • 
								{totalCount > 0 ? ` ${totalCount} total SKUs` : ` ${skuData.length} SKUs`}
								{totalPages > 1 && ` • Page ${currentPage} of ${totalPages}`}
							</p>
						</div>
						<button
							onClick={handleRefresh}
							disabled={loading}
							className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
						>
							{loading ? 'Loading...' : 'Refresh'}
						</button>
					</div>
				</div>

				<DataTable
					data={skuData}
					columns={columns}
					loading={loading}
					search={true}
					export={true}
					pagination={false} // Disable client-side pagination
					emptyMessage="No inventory data available. Please upload CSV data or check data connections."
					className="border-0 shadow-none"
				/>

				{/* Server-Side Pagination Controls */}
				{totalPages > 1 && (
					<div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
						<div className="text-sm text-gray-700">
							Showing {Math.min((currentPage - 1) * pageSize + 1, totalCount)} to{' '}
							{Math.min(currentPage * pageSize, totalCount)} of {totalCount} SKUs
						</div>
						<div className="flex space-x-2">
							<button
								onClick={() => handlePageChange(currentPage - 1)}
								disabled={currentPage <= 1 || loading}
								className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Previous
							</button>
							<span className="px-3 py-1 text-sm font-medium text-gray-700">
								Page {currentPage} of {totalPages}
							</span>
							<button
								onClick={() => handlePageChange(currentPage + 1)}
								disabled={currentPage >= totalPages || loading}
								className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Next
							</button>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
