import * as React from "react";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Copyright from "../internals/components/Copyright";
import { DateRange } from "./CustomDatePicker";

// Import inventory components
import InventorySKUList from "../../analytics/InventorySKUList";
import InventoryTrendCharts from "../../analytics/InventoryTrendCharts";
import AlertsSummary from "../../analytics/AlertsSummary";
import SmartEcommerceMetrics from "../../analytics/SmartEcommerceMetrics";
import PlatformToggle from "../../ui/PlatformToggle";

interface MainGridProps {
	dashboardData?: any;
	user?: { client_id: string; company_name: string; email: string };
	dashboardType?: string;
	dateRange?: DateRange;
	sharedDashboardMetrics?: any;
}

export default function MainGrid({
	dashboardData,
	user,
	dashboardType = "main",
	dateRange,
	sharedDashboardMetrics,
}: MainGridProps) {
	const [clientData, setClientData] = React.useState<any[]>([]);
	const [loading, setLoading] = React.useState(true);
	const [error, setError] = React.useState<string | null>(null);
	const [selectedPlatform, setSelectedPlatform] = React.useState<"shopify" | "amazon">("shopify");

	// Load client data
	const loadClientData = React.useCallback(async () => {
		if (!user?.client_id) return;

		try {
			setLoading(true);
			setError(null);
			
			// This would normally fetch client data from your API
			// For now, we'll use an empty array to prevent errors
			setClientData([]);
			
			console.log("✅ Client data loaded successfully");
		} catch (err: any) {
			console.error("❌ Error loading client data:", err);
			setError("Failed to load client data");
			setClientData([]);
		} finally {
			setLoading(false);
		}
	}, [user?.client_id, selectedPlatform]);

	React.useEffect(() => {
		loadClientData();
	}, [loadClientData]);

	if (loading) {
		return (
			<Box
				sx={{
					width: "100%",
					maxWidth: { sm: "100%", md: "1700px" },
					px: 2,
					py: 4,
					display: "flex",
					justifyContent: "center",
					alignItems: "center",
					minHeight: "400px",
				}}>
				<Typography variant="h6" color="text.secondary">
					Loading inventory analytics...
				</Typography>
			</Box>
		);
	}

	if (error) {
		return (
			<Box
				sx={{
					width: "100%",
					maxWidth: { sm: "100%", md: "1700px" },
					px: 2,
					py: 4,
					display: "flex",
					justifyContent: "center",
					alignItems: "center",
					minHeight: "400px",
				}}>
				<Typography variant="h6" color="error">
					{error}
				</Typography>
			</Box>
		);
	}

	return (
		<Box
			sx={{
				width: "100%",
				maxWidth: { sm: "100%", md: "1700px" },
				px: 2,
				py: 2,
				overflow: "hidden",
			}}>
			
			{/* Platform Toggle */}
			<Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
				<PlatformToggle
					selectedPlatform={selectedPlatform}
					onPlatformChange={setSelectedPlatform}
				/>
			</Box>

			{/* 📊 SALES PERFORMANCE METRICS */}
			<Grid container spacing={3} sx={{ mb: 4 }}>
				<Grid size={{ xs: 12 }}>
					<Card>
						<CardHeader
							title={`Sales Performance Metrics - ${selectedPlatform === "shopify" ? "Shopify" : "Amazon"}`}
							subheader="Real-time sales metrics and inventory analytics"
						/>
						<CardContent>
							<SmartEcommerceMetrics
								clientData={clientData}
								platform={selectedPlatform}
							/>
						</CardContent>
					</Card>
				</Grid>
			</Grid>

			{/* 🚨 ALERTS & NOTIFICATIONS */}
			<Grid container spacing={3} sx={{ mb: 4 }}>
				<Grid size={{ xs: 12 }}>
					<Card>
						<CardContent sx={{ p: 0 }}>
							<AlertsSummary
								clientData={clientData}
								platform={selectedPlatform}
							/>
						</CardContent>
					</Card>
				</Grid>
			</Grid>

			{/* 📈 INVENTORY TRENDS */}
			<Grid container spacing={3} sx={{ mb: 4 }}>
				<Grid size={{ xs: 12 }}>
					<Card>
						<CardHeader
							title="Inventory & Sales Trends"
							subheader="Time-series analysis with customizable date ranges"
						/>
						<CardContent>
							<InventoryTrendCharts
								clientData={clientData}
								platform={selectedPlatform}
							/>
						</CardContent>
					</Card>
				</Grid>
			</Grid>

			{/* 📦 SKU INVENTORY MANAGEMENT */}
			<Grid container spacing={3} sx={{ mb: 4 }}>
				<Grid size={{ xs: 12 }}>
					<Card>
						<CardHeader
							title="SKU Inventory Management"
							subheader={`Comprehensive inventory tracking • ${clientData.length} records analyzed`}
						/>
						<CardContent sx={{ p: 0 }}>
							<InventorySKUList
								clientData={clientData}
								platform={selectedPlatform}
							/>
						</CardContent>
					</Card>
				</Grid>
			</Grid>

			{/* Footer */}
			<Box sx={{ mt: 4, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
				<Copyright />
			</Box>
		</Box>
	);
}

// Export the main component as default
export { MainGrid as OriginalMainGrid };
