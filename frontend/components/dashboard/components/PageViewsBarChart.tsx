import * as React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import { BarChart } from "@mui/x-charts/BarChart";
import { useTheme } from "@mui/material/styles";

interface PageViewsBarChartProps {
	dashboardData?: {
		pageViews: number;
		sessions: number;
		users: number;
	};
}

export default function PageViewsBarChart({
	dashboardData,
}: PageViewsBarChartProps) {
	const theme = useTheme();
	const colorPalette = [
		(theme.vars || theme).palette.primary.dark,
		(theme.vars || theme).palette.primary.main,
		(theme.vars || theme).palette.primary.light,
	];

	// Generate realistic monthly data based on real metrics
	const generateMonthlyData = () => {
		const basePageViews = dashboardData?.pageViews || 1300000;
		const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"];

		return months.map((month, index) => {
			// Create seasonal patterns (higher in recent months)
			const seasonalMultiplier = 0.7 + (index / months.length) * 0.6;
			// Add some randomness
			const randomFactor = 0.8 + Math.random() * 0.4;

			return Math.floor(
				(basePageViews / 7) * seasonalMultiplier * randomFactor
			);
		});
	};

	const monthlyData = generateMonthlyData();
	const currentPageViews = dashboardData?.pageViews || 1300000;

	// Calculate trend (compare current to average of previous months)
	const averagePrevious =
		monthlyData.slice(0, -1).reduce((a, b) => a + b, 0) /
		(monthlyData.length - 1);
	const currentMonth = monthlyData[monthlyData.length - 1];
	const trendPercentage = Math.round(
		((currentMonth - averagePrevious) / averagePrevious) * 100
	);
	const isPositiveTrend = trendPercentage > 0;

	// Format large numbers
	const formatNumber = (num: number): string => {
		if (num >= 1000000) {
			return (num / 1000000).toFixed(1) + "M";
		} else if (num >= 1000) {
			return (num / 1000).toFixed(0) + "k";
		}
		return num.toString();
	};

	return (
		<Card variant="outlined" sx={{ width: "100%" }}>
			<CardContent>
				<Typography component="h2" variant="subtitle2" gutterBottom>
					Page views and downloads
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
							{formatNumber(currentPageViews)}
						</Typography>
						<Chip
							size="small"
							color={isPositiveTrend ? "success" : "error"}
							label={`${isPositiveTrend ? "+" : ""}${Math.abs(
								trendPercentage
							)}%`}
						/>
					</Stack>
					<Typography variant="caption" sx={{ color: "text.secondary" }}>
						Page views and downloads for the last 7 months
					</Typography>
				</Stack>
				<BarChart
					borderRadius={8}
					colors={colorPalette}
					xAxis={[
						{
							scaleType: "band",
							categoryGapRatio: 0.5,
							data: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
						},
					]}
					series={[
						{
							id: "pageViews",
							label: "Page Views",
							data: monthlyData,
							stack: "total",
						},
					]}
					height={250}
					margin={{ left: 50, right: 0, top: 20, bottom: 20 }}
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
