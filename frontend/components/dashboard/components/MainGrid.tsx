import * as React from "react";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Copyright from "../internals/components/Copyright";
import { DateRange } from "./CustomDatePicker";

// Import new restructured components
import TotalSalesKPIs from "../../analytics/TotalSalesKPIs";
import InventoryTurnoverKPIs from "../../analytics/InventoryTurnoverKPIs";
import DaysOfStockKPIs from "../../analytics/DaysOfStockKPIs";
import InventoryLevelsCharts from "../../analytics/InventoryLevelsCharts";
import UnitsSoldCharts from "../../analytics/UnitsSoldCharts";
import HistoricalComparisonCharts from "../../analytics/HistoricalComparisonCharts";
import LowStockAlerts from "../../analytics/LowStockAlerts";
import OverstockAlerts from "../../analytics/OverstockAlerts";
import SalesPerformanceAlerts from "../../analytics/SalesPerformanceAlerts";
import PlatformSKUList from "../../analytics/PlatformSKUList";

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
	// Simplified component - no complex state management needed
	// Each child component handles its own data loading and state

	return (
		<Box
			sx={{
				width: "100%",
				maxWidth: { sm: "100%", md: "1700px" },
				px: 2,
				py: 2,
				overflow: "hidden",
			}}>
			
			{/* Total Sales KPIs */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<TotalSalesKPIs />
				</Grid>
			</Grid>

			{/* Inventory Turnover KPIs */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<InventoryTurnoverKPIs />
				</Grid>
			</Grid>

			{/* Days of Stock KPIs */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<DaysOfStockKPIs />
				</Grid>
			</Grid>

			{/* Inventory Levels Charts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<InventoryLevelsCharts />
				</Grid>
			</Grid>

			{/* Units Sold Charts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<UnitsSoldCharts />
				</Grid>
			</Grid>

			{/* Historical Comparison Charts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<HistoricalComparisonCharts />
				</Grid>
			</Grid>

			{/* Low Stock Alerts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<LowStockAlerts />
				</Grid>
			</Grid>

			{/* Overstock Alerts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<OverstockAlerts />
				</Grid>
			</Grid>

			{/* Sales Performance Alerts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<SalesPerformanceAlerts />
				</Grid>
			</Grid>

			{/* Platform SKU List */}
			<Grid container spacing={3} sx={{ mb: 4 }}>
				<Grid size={{ xs: 12 }}>
					<PlatformSKUList />
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
