import * as React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import { BarChart } from "@mui/x-charts/BarChart";
import { useTheme } from "@mui/material/styles";
import CardHeader from "@mui/material/CardHeader";
import Box from "@mui/material/Box";

interface SalesCategoryChartProps {
	dashboardData?: {
		totalSales: number;
		topCategory: string;
		categoriesCount: number;
	};
	categoryData?: any[];
	clientData?: any[]; // Add real client data
}

export default function SalesCategoryChart({
	dashboardData,
	categoryData = [],
	clientData = []
}: SalesCategoryChartProps) {
	const theme = useTheme();
	const colorPalette = [
		theme.palette.primary.dark,
		theme.palette.primary.main,
		theme.palette.primary.light,
		theme.palette.secondary.main,
		theme.palette.info.main,
	];

	// Generate category data ONLY from real API response - NO client data processing
	const generateCategoryData = () => {
		// ONLY use provided categoryData from API response
		if (categoryData && categoryData.length > 0) {
			console.log("📊 SalesCategoryChart - Direct API categoryData:", categoryData.slice(0, 3));
			console.log("📊 SalesCategoryChart - Full API data structure:", categoryData);
			
			// Handle MUI-transformed data structure
			const categories = categoryData.map(item => 
				item.id || item.name || item.label || "Unknown"
			);
			
			// Use MUI-transformed values - this is the key fix!
			const sales = categoryData.map(item => {
				// MUI service transforms API data to have "value" field
				const value = parseFloat(item.value || 0);
				console.log(`📊 Category item: ${item.id || item.name} -> MUI value: ${value} (from transformed data)`);
				return value;
			});
			
			// For orders, try to find count-related fields in transformed data
			const orders = categoryData.map(item => 
				parseInt(item.count || item.orders || item.quantity || item.visitors || 1)
			);
			
			// Calculate totals for summary
			const totalSales = sales.reduce((sum, val) => sum + val, 0);
			const totalOrders = orders.reduce((sum, val) => sum + val, 0);
			
			console.log("📊 SalesCategoryChart - Processed MUI data:", { 
				categories: categories.slice(0, 3), 
				sales: sales.slice(0, 3), 
				orders: orders.slice(0, 3),
				totalSales,
				totalOrders,
				itemCount: categories.length,
				sampleTransformedItem: categoryData[0]
			});
			
			// Skip if all values are zero (transformation failed)
			const hasValidData = sales.some(val => val > 0);
			if (!hasValidData) {
				console.warn("⚠️ SalesCategoryChart - No valid sales values found in transformed data. Raw item:", categoryData[0]);
				return { categories: [], sales: [], orders: [] };
			}
			
			return { categories, sales, orders };
		}

		// No API data available - show empty state
		console.log("⚠️ SalesCategoryChart - No API categoryData available - showing empty state");
		return { 
			categories: [], 
			sales: [], 
			orders: [] 
		};
	};

	const { categories, sales, orders } = generateCategoryData();

	// Calculate total and growth from REAL data only
	const totalSales = sales.reduce((a, b) => a + b, 0);
	const totalOrders = orders.reduce((a, b) => a + b, 0);
	
	// Find top performing category
	const maxSalesIndex = sales.indexOf(Math.max(...sales));
	const topCategory = categories[maxSalesIndex] || "No data";
	const topCategorySales = sales[maxSalesIndex] || 0;
	const topCategoryShare = totalSales > 0 ? ((topCategorySales / totalSales) * 100).toFixed(1) : "0.0";

	// Show "No data" state when no real data is available
	if (categories.length === 0 || sales.length === 0) {
		// Hide chart completely when no data
		return null;
	}

	// Format total sales display
	const formatSalesAmount = (amount: number): string => {
		if (amount >= 1000000) {
			return `$${(amount / 1000000).toFixed(1)}M`;
		} else if (amount >= 1000) {
			return `$${(amount / 1000).toFixed(1)}k`;
		} else {
			return `$${amount.toFixed(0)}`;
		}
	};

	return (
		<Card variant="outlined" sx={{ width: "100%" }}>
			<CardContent>
				<Typography component="h2" variant="subtitle2" gutterBottom>
					Sales by Category
				</Typography>
				<Stack sx={{ justifyContent: "space-between" }}>
					<Stack
						direction="row"
						sx={{
							alignContent: { xs: "center", sm: "flex-start" },
							alignItems: "center",
							gap: 1,
						}}>
						<Typography variant="h4" component="p">
							{formatSalesAmount(totalSales)}
						</Typography>
						<Chip
							size="small"
							color="primary"
							label={`${categories.length} categories`}
						/>
					</Stack>
					<Typography variant="caption" sx={{ color: "text.secondary" }}>
						{topCategory} leads with {topCategoryShare}% of total sales
					</Typography>
				</Stack>
				<BarChart
					colors={colorPalette}
					xAxis={[
						{
							scaleType: "band",
							data: categories,
							tickLabelStyle: {
								angle: -45,
								textAnchor: 'end',
								fontSize: '12px'
							}
						},
					]}
					yAxis={[
						{
							valueFormatter: (value) => `$${(value / 1000).toFixed(0)}k`
						}
					]}
					series={[
						{
							id: "sales",
							label: "Sales ($)",
							data: sales,
							valueFormatter: (value) => `$${value?.toLocaleString() || 0}`
						},
					]}
					height={280}
					margin={{ left: 70, right: 20, top: 20, bottom: 80 }}
					grid={{ horizontal: true }}
					slotProps={{
						legend: {
							hidden: true,
						},
					}}
				/>
			</CardContent>
		</Card>
	);
} 