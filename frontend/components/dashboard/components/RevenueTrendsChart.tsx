import * as React from "react";
import { useTheme } from "@mui/material/styles";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import { LineChart } from "@mui/x-charts/LineChart";
import CardHeader from "@mui/material/CardHeader";
import Box from "@mui/material/Box";

function AreaGradient({ color, id }: { color: string; id: string }) {
	return (
		<defs>
			<linearGradient id={id} x1="50%" y1="0%" x2="50%" y2="100%">
				<stop offset="0%" stopColor={color} stopOpacity={0.5} />
				<stop offset="100%" stopColor={color} stopOpacity={0} />
			</linearGradient>
		</defs>
	);
}

interface RevenueTrendsChartProps {
	dashboardData?: {
		totalRevenue: number;
		totalOrders: number;
		averageOrderValue: number;
	};
	revenueData?: any[];
	clientData?: any[]; // Add real client data
}

export default function RevenueTrendsChart({ 
	dashboardData,
	revenueData = [],
	clientData = []
}: RevenueTrendsChartProps) {
	const theme = useTheme();

	const colorPalette = [
		theme.palette.primary.light,
		theme.palette.primary.main,
		theme.palette.primary.dark,
	];

	// Generate revenue data ONLY from real API response - NO client data processing
	const generateRevenueData = () => {
		// ONLY use provided revenueData from API response
		if (revenueData && revenueData.length > 0) {
			console.log("📊 RevenueTrendsChart - Direct API revenueData:", revenueData.slice(0, 3));
			console.log("📊 RevenueTrendsChart - Full API data structure:", revenueData);
			
			// Handle MUI-transformed data structure
			const labels = revenueData.map((item, index) => 
				item.month || item.name || item.id || `Item ${index + 1}`
			);
			
			// Use MUI-transformed values - this is the key fix!
			const revenue = revenueData.map(item => {
				// MUI service transforms API data to have "value" field
				const value = parseFloat(item.value || 0);
				console.log(`📊 Revenue item: ${item.name || item.id} -> MUI value: ${value} (from transformed data)`);
				return value;
			});
			
			// For orders, try to find count-related fields in transformed data
			const orders = revenueData.map(item => 
				parseInt(item.count || item.orders || item.quantity || item.visitors || 1)
			);
			
			// Calculate totals for debugging
			const totalRevenue = revenue.reduce((sum, val) => sum + val, 0);
			const totalOrders = orders.reduce((sum, val) => sum + val, 0);
			
			console.log("📊 RevenueTrendsChart - Processed MUI data:", { 
				labels: labels.slice(0, 3), 
				revenue: revenue.slice(0, 3), 
				orders: orders.slice(0, 3),
				totalRevenue,
				totalOrders,
				itemCount: labels.length,
				sampleTransformedItem: revenueData[0]
			});
			
			// Skip if all values are zero (transformation failed)
			const hasValidData = revenue.some(val => val > 0);
			if (!hasValidData) {
				console.warn("⚠️ RevenueTrendsChart - No valid revenue values found in transformed data. Raw item:", revenueData[0]);
				return { labels: [], revenue: [], orders: [] };
			}
			
			return { labels, revenue, orders };
		}

		// No API data available - show empty state
		console.log("⚠️ RevenueTrendsChart - No API revenueData available - showing empty state");
		return { 
			labels: [], 
			revenue: [], 
			orders: [] 
		};
	};

	const { labels, revenue, orders } = generateRevenueData();

	// Calculate trend from REAL data only - no fake percentages
	const calculateRealTrend = () => {
		if (revenue.length < 2) {
			return { percentage: 0, isPositive: null, display: "No trend data" };
		}

		// Compare first half vs second half of the data for trend
		const midPoint = Math.floor(revenue.length / 2);
		const firstHalf = revenue.slice(0, midPoint);
		const secondHalf = revenue.slice(midPoint);
		
		const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
		const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
		
		if (firstAvg === 0) {
			return { percentage: 0, isPositive: null, display: "No change" };
		}
		
		const percentage = Math.round(((secondAvg - firstAvg) / firstAvg) * 100);
		const isPositive = percentage > 0;
		const display = `${isPositive ? '+' : ''}${percentage}%`;
		
		return { percentage, isPositive, display };
	};

	const trendData = calculateRealTrend();
	const currentRevenue = revenue.reduce((a, b) => a + b, 0);
	const currentOrders = orders.reduce((a, b) => a + b, 0);

	// Format revenue display based on actual size
	const formatRevenue = (value: number) => {
		if (value >= 1000000) {
			return `$${(value / 1000000).toFixed(1)}M`;
		} else if (value >= 1000) {
			return `$${(value / 1000).toFixed(1)}k`;
		} else {
			return `$${value.toFixed(0)}`;
		}
	};

	// Debug logging for transparency
	console.log("📊 RevenueTrendsChart Final Values:", {
		currentRevenue,
		currentOrders,
		formattedRevenue: formatRevenue(currentRevenue),
		trendData,
		dataPoints: revenue.length
	});

	// Show "No data" state when no real data is available
	if (labels.length === 0 || revenue.length === 0) {
		// Hide chart completely when no data
		return null;
	}

	return (
		<Card variant="outlined" sx={{ width: "100%" }}>
			<CardContent>
				<Typography component="h2" variant="subtitle2" gutterBottom>
					Revenue Trends
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
							{formatRevenue(currentRevenue)}
						</Typography>
						<Chip
							size="small"
							color={trendData.isPositive ? "success" : "error"}
							label={trendData.display}
						/>
					</Stack>
					<Typography variant="caption" sx={{ color: "text.secondary" }}>
						Total Revenue: {formatRevenue(currentRevenue)} | Total Orders: {currentOrders} | Items: {labels.length}
					</Typography>
				</Stack>
				<LineChart
					colors={colorPalette}
					xAxis={[
						{
							scaleType: "point",
							data: labels,
							tickInterval: (index, i) => (i + 1) % 5 === 0,
						},
					]}
					yAxis={[
						{
							// Let the chart auto-scale based on actual data values
							min: 0,
						},
					]}
					series={[
						{
							id: "revenue",
							label: "Revenue ($)",
							showMark: true,
							curve: "linear",
							area: true,
							data: revenue,
							valueFormatter: (value) => `$${value}`,
						},
						{
							id: "orders", 
							label: "Orders",
							showMark: true,
							curve: "linear",
							data: orders,
							valueFormatter: (value) => `${value} orders`,
						},
					]}
					height={250}
					margin={{ left: 60, right: 20, top: 20, bottom: 20 }}
					grid={{ horizontal: true }}
					sx={{
						"& .MuiAreaElement-series-revenue": {
							fill: "url('#revenue')",
						},
					}}
					slotProps={{
						legend: {
							hidden: false,
							direction: 'row',
							position: { vertical: 'top', horizontal: 'right' },
						},
					}}>
					<AreaGradient color={theme.palette.primary.main} id="revenue" />
				</LineChart>
			</CardContent>
		</Card>
	);
} 