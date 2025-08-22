"use client";

import React, { useMemo } from "react";
import { Calendar, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useGlobalDataStore } from "../../store/globalDataStore";

interface DaysOfStockKPIsProps {
	clientData?: any[];
	className?: string;
}

type Platform = "shopify" | "amazon" | "all";

interface StockDaysData {
	value: number;
	subtitle: string;
}

const DaysOfStockKPIs = React.memo(function DaysOfStockKPIs({
	clientData,
	className = "",
}: DaysOfStockKPIsProps) {
	// Use global store directly instead of useInventoryData hook
	const inventoryData = useGlobalDataStore((state) => state.inventoryData);
	const loading = useGlobalDataStore((state) => state.loading.inventoryData);
	const error = useGlobalDataStore((state) => state.errors.inventoryData);
	const fetchInventoryData = useGlobalDataStore((state) => state.fetchInventoryData);
	
	// Trigger data fetch on mount if no data
	React.useEffect(() => {
		if (!inventoryData && !loading) {
			fetchInventoryData();
		}
	}, [inventoryData, loading, fetchInventoryData]);



	// Calculate days of stock data for each platform
	const calculateStockDaysData = (
		data: any,
		platform: Platform
	): StockDaysData => {
		if (!data?.sales_kpis?.days_stock_remaining) {
			return {
				value: 0,
				subtitle: "No stock data available",
			};
		}

		const stockDays = data.sales_kpis.days_stock_remaining || 0;

		// Determine health status based on stock days
		let subtitle = `${
			platform === "all"
				? "Combined"
				: platform.charAt(0).toUpperCase() + platform.slice(1)
		} average stock days`;
		if (stockDays > 90) {
			subtitle += " • Overstock risk";
		} else if (stockDays > 60) {
			subtitle += " • High stock";
		} else if (stockDays > 30) {
			subtitle += " • Optimal";
		} else if (stockDays > 14) {
			subtitle += " • Low stock";
		} else {
			subtitle += " • Critical";
		}

		return {
			value: stockDays,
			subtitle,
		};
	};

	// Memoized stock days data for each platform using global state
	const shopifyStockDays = useMemo(() => {
		const shopifyData = inventoryData?.inventory_analytics?.platforms?.shopify;
		return calculateStockDaysData(shopifyData, "shopify");
	}, [inventoryData]);

	const amazonStockDays = useMemo(() => {
		const amazonData = inventoryData?.inventory_analytics?.platforms?.amazon;
		return calculateStockDaysData(amazonData, "amazon");
	}, [inventoryData]);

	const allStockDays = useMemo(() => {
		if (!inventoryData?.inventory_analytics?.platforms) {
			return {
				value: 0,
				subtitle: "Combined stock data unavailable",
			};
		}

		// Use the combined platform data which already aggregates both platforms
		const combinedData = inventoryData.inventory_analytics.platforms.combined;
		return calculateStockDaysData(combinedData, "all");
	}, [inventoryData]);

	// Format stock days
	const formatStockDays = (value: number) => {
		return `${Math.round(value)} days`;
	};

	// Individual KPI Card Component (memoized for performance)
	const StockDaysKPICard = React.memo(
		({
			title,
			data,
			loading,
			error,
			icon,
			iconColor,
			iconBgColor,
		}: {
			title: string;
			data: StockDaysData;
			loading: boolean;
			error: string | null;
			icon: React.ReactNode;
			iconColor: string;
			iconBgColor: string;
		}) => {
			if (loading) {
				return (
					<Card className="bg-gray-100 border-gray-300 hover:shadow-md transition-all duration-300">
						<CardHeader className="pb-3">
							<CardTitle className="text-sm font-medium text-gray-600">
								{title}
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="animate-pulse">
								<div className="flex items-center mb-3">
									<div className="h-10 w-10 bg-gray-200 rounded-lg"></div>
								</div>
								<div className="space-y-2">
									<div className="h-6 bg-gray-200 rounded"></div>
									<div className="h-3 bg-gray-200 rounded w-2/3"></div>
								</div>
							</div>
						</CardContent>
					</Card>
				);
			}

			if (error) {
				return (
					<Card className="bg-gray-100 border-red-200 hover:shadow-md transition-all duration-300">
						<CardHeader className="pb-3">
							<CardTitle className="text-sm font-medium text-gray-600">
								{title}
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="flex items-center justify-center h-20 text-red-600">
								<p className="text-sm">Error loading data</p>
							</div>
						</CardContent>
					</Card>
				);
			}

			return (
				<Card className="bg-gray-100 border-gray-300 hover:shadow-md hover:bg-gray-200 transition-all duration-300">
					<CardHeader className="pb-3">
						<CardTitle className="text-sm font-medium text-gray-600">
							{title}
						</CardTitle>
					</CardHeader>
					<CardContent>
						{/* Header with Icon */}
						<div className="flex items-center mb-3">
							<div
								className="h-10 w-10 rounded-lg flex items-center justify-center"
								style={{ backgroundColor: iconBgColor }}>
								{icon}
							</div>
						</div>

						{/* Value and Subtitle */}
						<div className="space-y-1">
							<h3 className="text-2xl font-bold text-gray-900">
								{formatStockDays(data.value)}
							</h3>
							<p className="text-xs text-gray-500">{data.subtitle}</p>
						</div>
					</CardContent>
				</Card>
			);
		}
	);

	StockDaysKPICard.displayName = "StockDaysKPICard";

	return (
		<div className={`space-y-4 ${className}`}>
			<div className="flex items-center justify-between">
				<h2 className="text-xl font-semibold text-gray-900">
					Days of Stock Remaining
				</h2>
				<p className="text-sm text-gray-600">
					Estimated time until inventory runs out
				</p>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Shopify Stock Days KPI */}
				<StockDaysKPICard
					title="Shopify Stock"
					data={shopifyStockDays}
					loading={loading}
					error={error}
					icon={<Calendar className="h-4 w-4" style={{ color: "#059669" }} />}
					iconColor="#059669"
					iconBgColor="#ecfdf5"
				/>

				{/* Amazon Stock Days KPI */}
				<StockDaysKPICard
					title="Amazon Stock"
					data={amazonStockDays}
					loading={loading}
					error={error}
					icon={<Calendar className="h-4 w-4" style={{ color: "#f59e0b" }} />}
					iconColor="#f59e0b"
					iconBgColor="#fffbeb"
				/>

				{/* All Platforms Stock Days KPI */}
				<StockDaysKPICard
					title="All Platforms"
					data={allStockDays}
					loading={loading}
					error={error}
					icon={<Clock className="h-4 w-4" style={{ color: "#dc2626" }} />}
					iconColor="#dc2626"
					iconBgColor="#fef2f2"
				/>
			</div>
		</div>
	);
});

export default DaysOfStockKPIs;
