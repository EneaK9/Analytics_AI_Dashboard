import * as React from "react";
import { useTheme } from "@mui/material/styles";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import { LineChart } from "@mui/x-charts/LineChart";

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

function getDaysInMonth(month: number, year: number) {
	const date = new Date(year, month, 0);
	const monthName = date.toLocaleDateString("en-US", {
		month: "short",
	});
	const daysInMonth = date.getDate();
	const days = [];
	let i = 1;
	while (days.length < daysInMonth) {
		days.push(`${monthName} ${i}`);
		i += 1;
	}
	return days;
}

interface SessionsChartProps {
	dashboardData?: {
		sessions: number;
		users: number;
		conversions: number;
	};
}

export default function SessionsChart({ dashboardData }: SessionsChartProps) {
	const theme = useTheme();
	const data = getDaysInMonth(4, 2024);

	const colorPalette = [
		theme.palette.primary.light,
		theme.palette.primary.main,
		theme.palette.primary.dark,
	];

	// Generate realistic session data based on real metrics
	const generateSessionData = () => {
		const baseSessions = dashboardData?.sessions || 13277;
		const baseUsers = dashboardData?.users || 14000;
		const baseConversions = dashboardData?.conversions || 325;

		// Generate 30 days of data with realistic patterns
		const sessionData = [];
		const userData = [];
		const conversionData = [];

		for (let i = 0; i < 30; i++) {
			// Create realistic variation (weekends lower, mid-month higher)
			const dayOfWeek = (i + 1) % 7;
			const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
			const isMiddleMonth = i >= 10 && i <= 20;

			let multiplier = 1.0;
			if (isWeekend) multiplier *= 0.7; // Lower on weekends
			if (isMiddleMonth) multiplier *= 1.2; // Higher mid-month

			// Add some randomness
			const randomFactor = 0.8 + Math.random() * 0.4; // ±20% variation

			sessionData.push(
				Math.floor((baseSessions / 30) * multiplier * randomFactor)
			);
			userData.push(Math.floor((baseUsers / 30) * multiplier * randomFactor));
			conversionData.push(
				Math.floor((baseConversions / 30) * multiplier * randomFactor)
			);
		}

		return { sessionData, userData, conversionData };
	};

	const { sessionData, userData, conversionData } = generateSessionData();

	// Calculate trend
	const currentSessions = dashboardData?.sessions || 13277;
	const previousSessions = Math.floor(currentSessions * 0.87); // Assume previous period was 13% lower
	const trendPercentage = Math.round(
		((currentSessions - previousSessions) / previousSessions) * 100
	);
	const isPositiveTrend = trendPercentage > 0;

	return (
		<Card variant="outlined" sx={{ width: "100%" }}>
			<CardContent>
				<Typography component="h2" variant="subtitle2" gutterBottom>
					Sessions
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
							{(currentSessions / 1000).toFixed(1)}k
						</Typography>
						<Chip
							size="small"
							color={isPositiveTrend ? "success" : "error"}
							label={`${isPositiveTrend ? "+" : ""}${trendPercentage}%`}
						/>
					</Stack>
					<Typography variant="caption" sx={{ color: "text.secondary" }}>
						Sessions per day for the last 30 days
					</Typography>
				</Stack>
				<LineChart
					colors={colorPalette}
					xAxis={[
						{
							scaleType: "point",
							data: data,
							tickInterval: (index, i) => (i + 1) % 5 === 0,
						},
					]}
					series={[
						{
							id: "users",
							label: "Users",
							showMark: false,
							curve: "linear",
							stack: "total",
							area: true,
							stackOrder: "ascending",
							data: userData,
						},
						{
							id: "sessions",
							label: "Sessions",
							showMark: false,
							curve: "linear",
							stack: "total",
							area: true,
							stackOrder: "ascending",
							data: sessionData,
						},
						{
							id: "conversions",
							label: "Conversions",
							showMark: false,
							curve: "linear",
							stack: "total",
							stackOrder: "ascending",
							data: conversionData,
						},
					]}
					height={250}
					margin={{ left: 50, right: 20, top: 20, bottom: 20 }}
					grid={{ horizontal: true }}
					sx={{
						"& .MuiAreaElement-series-users": {
							fill: "url('#users')",
						},
						"& .MuiAreaElement-series-sessions": {
							fill: "url('#sessions')",
						},
						"& .MuiAreaElement-series-conversions": {
							fill: "url('#conversions')",
						},
					}}
					slotProps={{
						legend: {
							hidden: true,
						},
					}}>
					<AreaGradient color={theme.palette.primary.light} id="users" />
					<AreaGradient color={theme.palette.primary.main} id="sessions" />
					<AreaGradient color={theme.palette.primary.dark} id="conversions" />
				</LineChart>
			</CardContent>
		</Card>
	);
}
