import React, { Suspense, lazy } from "react";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Copyright from "../internals/components/Copyright";
import { DateRange } from "./CustomDatePicker";

// Lazy load components for better performance
const TotalSalesKPIs = lazy(() => import("../../analytics/TotalSalesKPIs"));
const InventoryTurnoverKPIs = lazy(
	() => import("../../analytics/InventoryTurnoverKPIs")
);
const DaysOfStockKPIs = lazy(() => import("../../analytics/DaysOfStockKPIs"));
const InventoryLevelsCharts = lazy(
	() => import("../../analytics/InventoryLevelsCharts")
);
const UnitsSoldCharts = lazy(() => import("../../analytics/UnitsSoldCharts"));
const HistoricalComparisonCharts = lazy(
	() => import("../../analytics/HistoricalComparisonCharts")
);
const LowStockAlerts = lazy(() => import("../../analytics/LowStockAlerts"));
const OverstockAlerts = lazy(() => import("../../analytics/OverstockAlerts"));
const SalesPerformanceAlerts = lazy(
	() => import("../../analytics/SalesPerformanceAlerts")
);
const PlatformSKUList = lazy(() => import("../../analytics/PlatformSKUList"));

interface MainGridProps {
	dashboardData?: any;
	user?: { client_id: string; company_name: string; email: string };
	dashboardType?: string;
	dateRange?: DateRange;
	sharedDashboardMetrics?: any;
}

// Loading fallback component
const LoadingFallback = ({ height = "200px" }: { height?: string }) => (
	<Box
		sx={{
			display: "flex",
			justifyContent: "center",
			alignItems: "center",
			height,
			minHeight: "120px",
		}}>
		<CircularProgress size={40} />
	</Box>
);

const MainGrid = React.memo(function MainGrid({
	dashboardData,
	user,
	dashboardType = "main",
	dateRange,
	sharedDashboardMetrics,
}: MainGridProps) {
	// Add delay before rendering analytics components to ensure auth is stable
	const [isReady, setIsReady] = React.useState(false);

	React.useEffect(() => {
		if (user?.client_id) {
			// Reduced delay - only 200ms to ensure auth is stable
			const timer = setTimeout(() => {
				setIsReady(true);
			}, 200); // Much faster - just ensure auth is stable

			return () => clearTimeout(timer);
		}
	}, [user?.client_id]);

	if (!user || !isReady) {
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
				<div className="text-center">
					<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
					<Typography variant="h6" color="text.secondary">
						{user
							? "Loading analytics..."
							: "Please log in to view dashboard analytics..."}
					</Typography>
				</div>
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
			{/* Total Sales KPIs */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="150px" />}>
						<TotalSalesKPIs />
					</Suspense>
				</Grid>
			</Grid>

			{/* Inventory Turnover KPIs */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="150px" />}>
						<InventoryTurnoverKPIs />
					</Suspense>
				</Grid>
			</Grid>

			{/* Days of Stock KPIs */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="150px" />}>
						<DaysOfStockKPIs />
					</Suspense>
				</Grid>
			</Grid>

			{/* Inventory Levels Charts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="300px" />}>
						<InventoryLevelsCharts />
					</Suspense>
				</Grid>
			</Grid>

			{/* Units Sold Charts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="300px" />}>
						<UnitsSoldCharts />
					</Suspense>
				</Grid>
			</Grid>

			{/* Historical Comparison Charts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="300px" />}>
						<HistoricalComparisonCharts />
					</Suspense>
				</Grid>
			</Grid>

			{/* Low Stock Alerts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="200px" />}>
						<LowStockAlerts />
					</Suspense>
				</Grid>
			</Grid>

			{/* Overstock Alerts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="200px" />}>
						<OverstockAlerts />
					</Suspense>
				</Grid>
			</Grid>

			{/* Sales Performance Alerts */}
			<Grid container spacing={3} sx={{ mb: 6 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="200px" />}>
						<SalesPerformanceAlerts />
					</Suspense>
				</Grid>
			</Grid>

			{/* Platform SKU List */}
			<Grid container spacing={3} sx={{ mb: 4 }}>
				<Grid size={{ xs: 12 }}>
					<Suspense fallback={<LoadingFallback height="400px" />}>
						<PlatformSKUList />
					</Suspense>
				</Grid>
			</Grid>

			{/* Footer */}
			<Box
				sx={{ mt: 4, pt: 3, borderTop: "1px solid", borderColor: "divider" }}>
				<Copyright />
			</Box>
		</Box>
	);
});

export default MainGrid;
