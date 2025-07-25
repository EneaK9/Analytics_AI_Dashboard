import * as React from "react";
import type {} from "@mui/x-date-pickers/themeAugmentation";
import type {} from "@mui/x-charts/themeAugmentation";
import type {} from "@mui/x-data-grid-pro/themeAugmentation";
import type {} from "@mui/x-tree-view/themeAugmentation";
import { alpha } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import AppNavbar from "./components/AppNavbar";
import Header from "./components/Header";
import MainGrid from "./components/MainGrid";
import SideMenu from "./components/SideMenu";
import AppTheme from "../shared-theme/AppTheme";
import { DateRange } from "./components/CustomDatePicker";
import {
	chartsCustomizations,
	dataGridCustomizations,
	datePickersCustomizations,
	treeViewCustomizations,
} from "./theme/customizations";

const xThemeComponents = {
	...chartsCustomizations,
	...dataGridCustomizations,
	...datePickersCustomizations,
	...treeViewCustomizations,
};

interface DashboardProps {
	disableCustomTheme?: boolean;
	dashboardData?: {
		users: number;
		conversions: number;
		eventCount: number;
		sessions: number;
		pageViews: number;
		isAnalyzing: boolean;
		error: string | null;
	};
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
	onRefreshAIData?: () => void;
	onLogout?: () => void;
}

export default function Dashboard({
	disableCustomTheme,
	dashboardData,
	user,
	onRefreshAIData,
	onLogout,
}: DashboardProps) {
	const [currentDashboardType, setCurrentDashboardType] =
		React.useState<string>("main");
	const [dateRange, setDateRange] = React.useState<DateRange>({
		start: null,
		end: null,
		label: "Last 30 days",
	});

	// Handle dashboard type changes from the dropdown
	const handleDashboardChange = React.useCallback(
		(newDashboardType: string) => {
			console.log(`🔄 Dashboard switched to: ${newDashboardType}`);
			setCurrentDashboardType(newDashboardType);

			// Optionally refresh AI data when switching dashboards
			if (onRefreshAIData && newDashboardType !== "main") {
				console.log("🔄 Refreshing AI data for new dashboard type");
				onRefreshAIData();
			}
		},
		[onRefreshAIData]
	);

	// Handle date range changes from the calendar
	const handleDateRangeChange = React.useCallback(
		(newDateRange: DateRange) => {
			console.log(`📅 Date range changed to: ${newDateRange.label}`);
			setDateRange(newDateRange);

			// Optionally refresh data when date changes
			if (onRefreshAIData) {
				console.log("🔄 Refreshing data for new date range");
				setTimeout(() => onRefreshAIData(), 500); // Small delay to avoid rapid requests
			}
		},
		[onRefreshAIData]
	);

	return (
		<AppTheme
			disableCustomTheme={disableCustomTheme}
			themeComponents={xThemeComponents}>
			<CssBaseline enableColorScheme />
			<Box sx={{ display: "flex" }}>
				<SideMenu user={user} onDashboardChange={handleDashboardChange} />
				<AppNavbar
					dashboardData={dashboardData}
					user={user}
					onRefreshAIData={onRefreshAIData}
					onLogout={onLogout}
				/>
				{/* Main content */}
				<Box
					component="main"
					sx={(theme) => ({
						flexGrow: 1,
						backgroundColor: theme.vars
							? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
							: alpha(theme.palette.background.default, 1),
						overflow: "auto",
					})}>
					<Stack
						spacing={2}
						sx={{
							alignItems: "center",
							mx: 3,
							pb: 5,
							mt: { xs: 8, md: 0 },
						}}>
						<Header onDateRangeChange={handleDateRangeChange} />
						<MainGrid
							dashboardData={dashboardData}
							user={user}
							dashboardType={currentDashboardType}
							dateRange={dateRange}
						/>
					</Stack>
				</Box>
			</Box>
		</AppTheme>
	);
}
