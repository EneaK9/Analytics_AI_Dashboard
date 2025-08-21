"use client";

import React, { useState } from "react";
import {
	AlertCircle,
	Package,
	TrendingUp,
	TrendingDown,
	Store,
	ShoppingBag,
	ChevronDown,
} from "lucide-react";
import DataTable from "../ui/DataTable";
import { Card, CardContent } from "../ui/card";
import { type SKUData } from "../../lib/inventoryService";
import { useSKUData } from "../../hooks/useSKUData";

interface PlatformSKUListProps {
	clientData?: unknown[];
	refreshInterval?: number;
	className?: string;
}

type Platform = "shopify" | "amazon";

export default function PlatformSKUList({
	className = "",
}: PlatformSKUListProps) {
	// Platform selection state
	const [selectedPlatform, setSelectedPlatform] = useState<Platform>("shopify");

	// Use SKU data hook to get actual SKU inventory data
	const {
		loading,
		error,
		shopifySKUs,
		amazonSKUs,
		shopifyStats,
		amazonStats,
		lastUpdated,
		refresh,
	} = useSKUData({ fastMode: true });

	// Get platform-specific data based on selection
	const currentData = selectedPlatform === "shopify" ? shopifySKUs : amazonSKUs;
	const currentStats =
		selectedPlatform === "shopify" ? shopifyStats : amazonStats;

	// 🔥 FIXED: Calculate real stats from data if API stats are missing
	const safeStats =
		currentStats ||
		(currentData
			? {
					total_skus: currentData.length,
					total_inventory_value: currentData.reduce(
						(sum, sku) => sum + (sku.total_value || 0),
						0
					),
					low_stock_count: currentData.filter(
						(sku) =>
							sku.current_availability > 0 && sku.current_availability <= 10
					).length,
					out_of_stock_count: currentData.filter(
						(sku) => sku.current_availability <= 0
					).length,
					overstock_count: currentData.filter(
						(sku) => sku.current_availability > 100
					).length,
			  }
			: {
					total_skus: 0,
					total_inventory_value: 0,
					low_stock_count: 0,
					out_of_stock_count: 0,
					overstock_count: 0,
			  });

	const currentLoading = loading;
	const currentError = error;
	const currentLastUpdated = lastUpdated;

	// Refresh handler for manual refresh
	const handleRefresh = () => refresh(undefined, true);

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
					<span className="text-blue-600 font-semibold">
						{value.toLocaleString()}
					</span>
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
					<span className="text-red-600 font-semibold">
						{value.toLocaleString()}
					</span>
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
								isOutOfStock
									? "text-red-700"
									: isLowStock
									? "text-yellow-600"
									: "text-green-600"
							}`}>
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
					$
					{value.toLocaleString(undefined, {
						minimumFractionDigits: 2,
						maximumFractionDigits: 2,
					})}
				</div>
			),
		},
	];

	// Platform Dropdown Component
	const [dropdownOpen, setDropdownOpen] = useState(false);

	// Close dropdown when clicking outside
	React.useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			const target = event.target as Element;
			if (dropdownOpen && !target.closest('.platform-dropdown')) {
				setDropdownOpen(false);
			}
		};

		document.addEventListener('mousedown', handleClickOutside);
		return () => {
			document.removeEventListener('mousedown', handleClickOutside);
		};
	}, [dropdownOpen]);

	// Compact Platform Dropdown for table header
	const PlatformDropdownControl = () => (
		<div className="relative platform-dropdown">
			<button
				onClick={() => setDropdownOpen(!dropdownOpen)}
				className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
			>
				{selectedPlatform === "shopify" ? (
					<>
						<Store className="h-4 w-4 text-green-600" />
						<span>Shopify</span>
					</>
				) : (
					<>
						<ShoppingBag className="h-4 w-4 text-orange-600" />
						<span>Amazon</span>
					</>
				)}
				<ChevronDown className="h-4 w-4 text-gray-400" />
			</button>
			
			{dropdownOpen && (
				<div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
					<div className="py-1">
						<button
							onClick={() => {
								setSelectedPlatform("shopify");
								setDropdownOpen(false);
							}}
							className={`flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-gray-50 ${
								selectedPlatform === "shopify" ? "bg-green-50 text-green-700" : "text-gray-700"
							}`}
						>
							<Store className="h-4 w-4" />
							Shopify
						</button>
						<button
							onClick={() => {
								setSelectedPlatform("amazon");
								setDropdownOpen(false);
							}}
							className={`flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-gray-50 ${
								selectedPlatform === "amazon" ? "bg-orange-50 text-orange-700" : "text-gray-700"
							}`}
						>
							<ShoppingBag className="h-4 w-4" />
							Amazon
						</button>
					</div>
				</div>
			)}
		</div>
	);

	return (
		<div className={`space-y-6 ${className}`}>
			{/* Summary Cards
			{safeStats && (
				<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">
										Total SKUs
									</p>
									<p className="text-2xl font-bold text-gray-900">
										{safeStats.total_skus}
									</p>
								</div>
								<Package className="h-8 w-8 text-blue-600" />
							</div>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">
										Total Inventory Value
									</p>
									<p className="text-2xl font-bold text-green-600">
										$
										{(safeStats.total_inventory_value || 0).toLocaleString(
											undefined,
											{ minimumFractionDigits: 0, maximumFractionDigits: 0 }
										)}
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
									<p className="text-sm font-medium text-gray-600">
										Low Stock Alerts
									</p>
									<p className="text-2xl font-bold text-yellow-600">
										{safeStats.low_stock_count}
									</p>
								</div>
								<AlertCircle className="h-8 w-8 text-yellow-600" />
							</div>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm font-medium text-gray-600">
										Out of Stock
									</p>
									<p className="text-2xl font-bold text-red-600">
										{safeStats.out_of_stock_count}
									</p>
								</div>
								<AlertCircle className="h-8 w-8 text-red-600" />
							</div>
						</CardContent>
					</Card>
				</div>
			)} */}

			{/* SKU Data Table */}
			<DataTable
				title={`SKU Inventory List - ${
					selectedPlatform === "shopify" ? "Shopify" : "Amazon"
				}`}
				subtitle={`Comprehensive inventory management with real-time availability tracking • ${
					currentData?.length || 0
				} SKUs`}
				data={currentData || []}
				columns={columns}
				loading={currentLoading}
				search={true}
				export={true}
				pagination={true}
				pageSize={25}
				emptyMessage={`No inventory data available for ${
					selectedPlatform === "shopify" ? "Shopify" : "Amazon"
				}. Please upload CSV data or check data connections.`}
				className="bg-white shadow-sm"
				additionalControls={<PlatformDropdownControl />}
			/>

			{/* Footer with last updated info */}
	
		</div>
	);
}
