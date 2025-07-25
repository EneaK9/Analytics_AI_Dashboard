import * as React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import { useTheme } from "@mui/material/styles";

interface HighlightedCardProps {
	dashboardData?: {
		users: number;
		conversions: number;
		eventCount: number;
		sessions: number;
		pageViews: number;
	};
}

export default function HighlightedCard({
	dashboardData,
}: HighlightedCardProps) {
	const theme = useTheme();

	// Calculate some basic analytics if data is available
	const totalMetrics = dashboardData
		? dashboardData.users + dashboardData.conversions + dashboardData.eventCount
		: 0;

	const conversionRate = dashboardData
		? ((dashboardData.conversions / dashboardData.users) * 100).toFixed(1)
		: "2.3";

	return (
		<Card sx={{ height: "100%", bgcolor: "primary.50" }}>
			<CardContent>
				<TrendingUpRoundedIcon sx={{ color: "primary.main", mb: 1 }} />
				<Typography
					component="h2"
					variant="subtitle2"
					gutterBottom
					sx={{ fontWeight: "600", color: "primary.main" }}>
					Performance
				</Typography>
				<Typography variant="h4" sx={{ fontWeight: "bold", mb: 1 }}>
					{conversionRate}%
				</Typography>
				<Typography sx={{ color: "text.secondary", fontSize: "0.875rem" }}>
					Conversion rate
				</Typography>
				<Typography sx={{ color: "success.main", fontSize: "0.75rem", mt: 1 }}>
					↗ +12% from last month
				</Typography>
			</CardContent>
		</Card>
	);
}
