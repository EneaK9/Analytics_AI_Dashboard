"use client";

import * as React from "react";
import { useState, useMemo } from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Typography from "@mui/material/Typography";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TablePagination from "@mui/material/TablePagination";
import Chip from "@mui/material/Chip";
import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import SearchIcon from "@mui/icons-material/Search";
import Box from "@mui/material/Box";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Alert from "@mui/material/Alert";
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from "lucide-react";

interface InventoryAnalyticsDataTableProps {
	analyticsData?: any;
	title?: string;
	subtitle?: string;
}

interface TabPanelProps {
	children?: React.ReactNode;
	index: number;
	value: number;
}

function TabPanel(props: TabPanelProps) {
	const { children, value, index, ...other } = props;

	return (
		<div
			role="tabpanel"
			hidden={value !== index}
			id={`analytics-tabpanel-${index}`}
			aria-labelledby={`analytics-tab-${index}`}
			{...other}
		>
			{value === index && <Box sx={{ p: 0 }}>{children}</Box>}
		</div>
	);
}

const InventoryAnalyticsDataTable = React.memo(function InventoryAnalyticsDataTable({
	analyticsData,
	title = "Inventory Analytics Dashboard",
	subtitle = "Comprehensive analytics data across all platforms",
}: InventoryAnalyticsDataTableProps) {
	const [page, setPage] = useState(0);
	const [rowsPerPage, setRowsPerPage] = useState(25);
	const [searchTerm, setSearchTerm] = useState("");
	const [selectedTab, setSelectedTab] = useState(0);

	// Format currency
	const formatCurrency = (value: number) => {
		return new Intl.NumberFormat("en-US", {
			style: "currency",
			currency: "USD",
			minimumFractionDigits: 2,
			maximumFractionDigits: 2,
		}).format(value);
	};

	// Format number with commas
	const formatNumber = (value: number) => {
		return new Intl.NumberFormat("en-US").format(value);
	};

	// Format percentage
	const formatPercentage = (value: number) => {
		return `${value.toFixed(1)}%`;
	};

	// Parse the analytics data and create organized table data (optimized with specific dependency)
	const organizedData = useMemo(() => {
		if (!analyticsData?.inventory_analytics?.platforms) {
			return {
				salesKPIs: [],
				inventoryMetrics: [],
				alertsSummary: [],
				trendData: [],
			};
		}

		const platforms = analyticsData.inventory_analytics.platforms;

		// Sales KPIs Data
		const salesKPIs = Object.entries(platforms).map(([platform, data]: [string, any]) => ({
			id: `sales-${platform}`,
			platform: platform.charAt(0).toUpperCase() + platform.slice(1),
			avgDailySales: data.sales_kpis?.avg_daily_sales || 0,
			sales7Days: {
				units: data.sales_kpis?.total_sales_7_days?.units || 0,
				orders: data.sales_kpis?.total_sales_7_days?.orders || 0,
				revenue: data.sales_kpis?.total_sales_7_days?.revenue || 0,
			},
			sales30Days: {
				units: data.sales_kpis?.total_sales_30_days?.units || 0,
				orders: data.sales_kpis?.total_sales_30_days?.orders || 0,
				revenue: data.sales_kpis?.total_sales_30_days?.revenue || 0,
			},
			sales90Days: {
				units: data.sales_kpis?.total_sales_90_days?.units || 0,
				orders: data.sales_kpis?.total_sales_90_days?.orders || 0,
				revenue: data.sales_kpis?.total_sales_90_days?.revenue || 0,
			},
		}));

		// Inventory Metrics Data
		const inventoryMetrics = Object.entries(platforms).map(([platform, data]: [string, any]) => ({
			id: `inventory-${platform}`,
			platform: platform.charAt(0).toUpperCase() + platform.slice(1),
			totalInventoryUnits: data.sales_kpis?.total_inventory_units || 0,
			daysStockRemaining: data.sales_kpis?.days_stock_remaining || 0,
			inventoryTurnoverRate: data.sales_kpis?.inventory_turnover_rate || 0,
			avgDailySales: data.sales_kpis?.avg_daily_sales || 0,
		}));

		// Alerts Summary Data
		const alertsSummary = Object.entries(platforms).map(([platform, data]: [string, any]) => ({
			id: `alerts-${platform}`,
			platform: platform.charAt(0).toUpperCase() + platform.slice(1),
			totalAlerts: data.alerts_summary?.summary_counts?.total_alerts || 0,
			lowStockAlerts: data.alerts_summary?.summary_counts?.low_stock_alerts || 0,
			overstockAlerts: data.alerts_summary?.summary_counts?.overstock_alerts || 0,
			salesSpikeAlerts: data.alerts_summary?.summary_counts?.sales_spike_alerts || 0,
			salesSlowdownAlerts: data.alerts_summary?.summary_counts?.sales_slowdown_alerts || 0,
		}));

		// Trend Analysis Data
		const trendData = Object.entries(platforms).map(([platform, data]: [string, any]) => ({
			id: `trend-${platform}`,
			platform: platform.charAt(0).toUpperCase() + platform.slice(1),
			historicalAvgUnits: data.trend_analysis?.sales_comparison?.historical_avg_units || 0,
			currentPeriodAvgUnits: data.trend_analysis?.sales_comparison?.current_period_avg_units || 0,
			unitsChangePercent: data.trend_analysis?.sales_comparison?.units_change_percent || 0,
			historicalAvgRevenue: data.trend_analysis?.sales_comparison?.historical_avg_revenue || 0,
			currentPeriodAvgRevenue: data.trend_analysis?.sales_comparison?.current_period_avg_revenue || 0,
			revenueChangePercent: data.trend_analysis?.sales_comparison?.revenue_change_percent || 0,
		}));

		return {
			salesKPIs,
			inventoryMetrics,
			alertsSummary,
			trendData,
		};
	}, [analyticsData?.inventory_analytics?.platforms, analyticsData?.timestamp]);

	// Filter data based on search and current tab (memoized for performance)
	const getFilteredData = React.useCallback((data: any[]) => {
		if (!searchTerm) return data;
		return data.filter((row) =>
			row.platform.toLowerCase().includes(searchTerm.toLowerCase())
		);
	}, [searchTerm]);

	const handleChangePage = (event: unknown, newPage: number) => {
		setPage(newPage);
	};

	const handleChangeRowsPerPage = (
		event: React.ChangeEvent<HTMLInputElement>
	) => {
		setRowsPerPage(parseInt(event.target.value, 10));
		setPage(0);
	};

	const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
		setSelectedTab(newValue);
		setPage(0);
	};

	// Get trend indicator
	const getTrendIndicator = (value: number) => {
		if (value > 0) {
			return <TrendingUp className="h-4 w-4 text-green-600" />;
		} else if (value < 0) {
			return <TrendingDown className="h-4 w-4 text-red-600" />;
		}
		return null;
	};



	if (!analyticsData) {
		return (
			<Card variant="outlined" sx={{ width: "100%" }}>
				<CardContent>
					<Alert severity="info">
						No inventory analytics data available. Please check your data source.
					</Alert>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card variant="outlined" sx={{ width: "100%" }}>
			<Box 
				sx={{ 
					p: 2, 
					backgroundColor: "#ffffff",
					borderBottom: "1px solid #e0e0e0",
					display: "flex",
					alignItems: "center",
					justifyContent: "space-between",
					gap: 2,
					flexWrap: "wrap"
				}}
			>
				<Box sx={{ display: "flex", flexDirection: "column", minWidth: "auto" }}>
					<Typography variant="h6" sx={{ fontSize: "1.25rem", fontWeight: 600, mb: 0 }}>
						{title}
					</Typography>
					<Typography variant="body2" color="text.secondary" sx={{ fontSize: "0.875rem" }}>
						{subtitle}
					</Typography>
				</Box>
				<TextField
					size="small"
					placeholder="Search platforms..."
					value={searchTerm}
					onChange={(e) => setSearchTerm(e.target.value)}
					InputProps={{
						startAdornment: (
							<InputAdornment position="start">
								<SearchIcon fontSize="small" />
							</InputAdornment>
						),
					}}
					sx={{ minWidth: 200 }}
				/>
			</Box>
			<CardContent sx={{ pt: 0 }}>
				{/* Tab Navigation */}
				<Box sx={{ borderBottom: 1, borderColor: "divider", mb: 1 }}>
					<Tabs value={selectedTab} onChange={handleTabChange} sx={{
						"& .MuiTab-root": {
							transition: "none",
							"&:hover": {
								backgroundColor: "transparent",
								border: "none",
								outline: "none",
							},
							"&:focus": {
								backgroundColor: "transparent",
								border: "none",
								outline: "none",
							},
							"&:focus-visible": {
								backgroundColor: "transparent",
								border: "none",
								outline: "none",
							},
						},
					}}>
						<Tab label="Sales KPIs" disableRipple />
						<Tab label="Inventory Metrics" disableRipple />
						<Tab label="Alerts Summary" disableRipple />
						<Tab label="Trend Analysis" disableRipple />
					</Tabs>
				</Box>

				{/* Sales KPIs Tab */}
				<TabPanel value={selectedTab} index={0}>
					<TableContainer>
						<Table size="small">
							<TableHead sx={{ backgroundColor: "#ffffff" }}>
								<TableRow>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Platform</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Avg Daily Sales</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>7 Days</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>30 Days</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>90 Days</strong></TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{getFilteredData(organizedData.salesKPIs).map((row) => (
									<TableRow key={row.id}>
										<TableCell>
											<Typography variant="body2" fontWeight="medium">
												{row.platform}
											</Typography>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatNumber(row.avgDailySales)}
											</Typography>
										</TableCell>
										<TableCell>
											<Box>
												<Typography variant="body2" fontWeight="medium">
													{formatCurrency(row.sales7Days.revenue)}
												</Typography>
												<Typography variant="caption" color="text.secondary">
													{formatNumber(row.sales7Days.units)} units, {formatNumber(row.sales7Days.orders)} orders
												</Typography>
											</Box>
										</TableCell>
										<TableCell>
											<Box>
												<Typography variant="body2" fontWeight="medium">
													{formatCurrency(row.sales30Days.revenue)}
												</Typography>
												<Typography variant="caption" color="text.secondary">
													{formatNumber(row.sales30Days.units)} units, {formatNumber(row.sales30Days.orders)} orders
												</Typography>
											</Box>
										</TableCell>
										<TableCell>
											<Box>
												<Typography variant="body2" fontWeight="medium">
													{formatCurrency(row.sales90Days.revenue)}
												</Typography>
												<Typography variant="caption" color="text.secondary">
													{formatNumber(row.sales90Days.units)} units, {formatNumber(row.sales90Days.orders)} orders
												</Typography>
											</Box>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</TableContainer>
				</TabPanel>

				{/* Inventory Metrics Tab */}
				<TabPanel value={selectedTab} index={1}>
					<TableContainer>
						<Table size="small">
							<TableHead sx={{ backgroundColor: "#ffffff" }}>
								<TableRow>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Platform</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Total Inventory Units</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Days Stock Remaining</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Turnover Rate</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Avg Daily Sales</strong></TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{getFilteredData(organizedData.inventoryMetrics).map((row) => (
									<TableRow key={row.id}>
										<TableCell>
											<Typography variant="body2" fontWeight="medium">
												{row.platform}
											</Typography>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatNumber(row.totalInventoryUnits)}
											</Typography>
										</TableCell>
										<TableCell>
											<Box display="flex" alignItems="center" gap={1}>
												<Typography variant="body2">
													{row.daysStockRemaining > 999 ? "999+" : formatNumber(row.daysStockRemaining)} days
												</Typography>
												{row.daysStockRemaining < 7 && (
													<AlertTriangle className="h-4 w-4 text-red-600" />
												)}
												{row.daysStockRemaining >= 7 && row.daysStockRemaining <= 60 && (
													<CheckCircle className="h-4 w-4 text-green-600" />
												)}
											</Box>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{row.inventoryTurnoverRate.toFixed(2)}x
											</Typography>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatNumber(row.avgDailySales)}
											</Typography>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</TableContainer>
				</TabPanel>

				{/* Alerts Summary Tab */}
				<TabPanel value={selectedTab} index={2}>
					<TableContainer>
						<Table size="small">
							<TableHead sx={{ backgroundColor: "#ffffff" }}>
								<TableRow>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Platform</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Total Alerts</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Low Stock</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Overstock</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Sales Spike</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Sales Slowdown</strong></TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{getFilteredData(organizedData.alertsSummary).map((row) => (
									<TableRow key={row.id}>
										<TableCell>
											<Typography variant="body2" fontWeight="medium">
												{row.platform}
											</Typography>
										</TableCell>
																			<TableCell>
										<Typography 
											variant="body2" 
											sx={{ 
												color: row.totalAlerts === 0 ? 'success.main' : 
													   row.totalAlerts < 10 ? 'warning.main' : 'error.main',
												fontWeight: row.totalAlerts > 0 ? 600 : 400
											}}
										>
											{formatNumber(row.totalAlerts)}
										</Typography>
									</TableCell>
																			<TableCell>
										<Typography 
											variant="body2" 
											sx={{ 
												color: row.lowStockAlerts > 0 ? "error.main" : "text.secondary",
												fontWeight: row.lowStockAlerts > 0 ? 600 : 400
											}}
										>
											{formatNumber(row.lowStockAlerts)}
										</Typography>
									</TableCell>
									<TableCell>
										<Typography 
											variant="body2" 
											sx={{ 
												color: row.overstockAlerts > 0 ? "warning.main" : "text.secondary",
												fontWeight: row.overstockAlerts > 0 ? 600 : 400
											}}
										>
											{formatNumber(row.overstockAlerts)}
										</Typography>
									</TableCell>
									<TableCell>
										<Typography 
											variant="body2" 
											sx={{ 
												color: row.salesSpikeAlerts > 0 ? "success.main" : "text.secondary",
												fontWeight: row.salesSpikeAlerts > 0 ? 600 : 400
											}}
										>
											{formatNumber(row.salesSpikeAlerts)}
										</Typography>
									</TableCell>
									<TableCell>
										<Typography 
											variant="body2" 
											sx={{ 
												color: row.salesSlowdownAlerts > 0 ? "error.main" : "text.secondary",
												fontWeight: row.salesSlowdownAlerts > 0 ? 600 : 400
											}}
										>
											{formatNumber(row.salesSlowdownAlerts)}
										</Typography>
									</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</TableContainer>
				</TabPanel>

				{/* Trend Analysis Tab */}
				<TabPanel value={selectedTab} index={3}>
					<TableContainer>
						<Table size="small">
							<TableHead sx={{ backgroundColor: "#ffffff" }}>
								<TableRow>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Platform</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Historical Avg Units</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Current Avg Units</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Units Change</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Historical Avg Revenue</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Current Avg Revenue</strong></TableCell>
									<TableCell sx={{ backgroundColor: "#ffffff" }}><strong>Revenue Change</strong></TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{getFilteredData(organizedData.trendData).map((row) => (
									<TableRow key={row.id}>
										<TableCell>
											<Typography variant="body2" fontWeight="medium">
												{row.platform}
											</Typography>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatNumber(row.historicalAvgUnits)}
											</Typography>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatNumber(row.currentPeriodAvgUnits)}
											</Typography>
										</TableCell>
										<TableCell>
											<Box display="flex" alignItems="center" gap={0.5}>
												<Typography 
													variant="body2" 
													color={row.unitsChangePercent >= 0 ? "success.main" : "error.main"}
												>
													{formatPercentage(row.unitsChangePercent)}
												</Typography>
												{getTrendIndicator(row.unitsChangePercent)}
											</Box>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatCurrency(row.historicalAvgRevenue)}
											</Typography>
										</TableCell>
										<TableCell>
											<Typography variant="body2">
												{formatCurrency(row.currentPeriodAvgRevenue)}
											</Typography>
										</TableCell>
										<TableCell>
											<Box display="flex" alignItems="center" gap={0.5}>
												<Typography 
													variant="body2" 
													color={row.revenueChangePercent >= 0 ? "success.main" : "error.main"}
												>
													{formatPercentage(row.revenueChangePercent)}
												</Typography>
												{getTrendIndicator(row.revenueChangePercent)}
											</Box>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</TableContainer>
				</TabPanel>

				{/* Pagination */}
				<TablePagination
					component="div"
					count={(() => {
						switch (selectedTab) {
							case 0: return getFilteredData(organizedData.salesKPIs).length;
							case 1: return getFilteredData(organizedData.inventoryMetrics).length;
							case 2: return getFilteredData(organizedData.alertsSummary).length;
							case 3: return getFilteredData(organizedData.trendData).length;
							default: return 0;
						}
					})()}
					page={page}
					onPageChange={handleChangePage}
					rowsPerPage={rowsPerPage}
					onRowsPerPageChange={handleChangeRowsPerPage}
					rowsPerPageOptions={[10, 25, 50, 100]}
					sx={{ mt: 1 }}
				/>


			</CardContent>
		</Card>
	);
});

export default InventoryAnalyticsDataTable;
