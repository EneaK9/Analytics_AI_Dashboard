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
import ExcelDataView from "./components/ExcelDataView";
import DataTablesPage from "./components/DataTablesPage";
import AppTheme from "../shared-theme/AppTheme";
import useDashboardMetrics from "../../hooks/useDashboardMetrics";
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
	dateRange?: DateRange | null;
	onDateRangeChange?: (dateRange: DateRange) => void;
}

export default function Dashboard({
	disableCustomTheme,
	dashboardData,
	user,
	onRefreshAIData,
	onLogout,
	dateRange,
	onDateRangeChange,
}: DashboardProps) {
	// State for sidebar section selection
	const [selectedSection, setSelectedSection] = React.useState("home");
	const [currentDashboardType, setCurrentDashboardType] =
		React.useState<string>("main");
	
	// Shared dashboard metrics hook
	const dashboardMetrics = useDashboardMetrics(user?.client_id);


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



    const handleSearch = React.useCallback((query: string) => {
        console.log('🔎 Search submitted:', query);
        // Broadcast search to dashboard components for highlight
        const evt = new CustomEvent('dashboard-search', { detail: { query } });
        window.dispatchEvent(evt);
    }, []);

    return (
		<AppTheme
			disableCustomTheme={disableCustomTheme}
			themeComponents={xThemeComponents}>
			<CssBaseline enableColorScheme />
			<Box sx={{ display: "flex" }}>
				<SideMenu
					user={user}
					onDashboardChange={handleDashboardChange}
					selectedSection={selectedSection}
					onSectionChange={setSelectedSection}
				/>
				<AppNavbar
					dashboardData={dashboardData}
					user={user}
					onRefreshAIData={onRefreshAIData}
					onLogout={onLogout}
					selectedSection={selectedSection}
					onSectionChange={setSelectedSection}
					onDashboardChange={handleDashboardChange}
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
											{selectedSection === "data-tables" ? (
						<>
							<Box sx={{ width: "100%", mb: 2 }}>
								<Header onDateRangeChange={onDateRangeChange} />
							</Box>
							<Box sx={{ width: "100%", height: "calc(100vh - 200px)" }}>
								<DataTablesPage user={user} dashboardMetrics={dashboardMetrics} dateRange={dateRange || undefined} />
							</Box>
						</>
					) : (
							<>
                                <Header onDateRangeChange={onDateRangeChange} onSearch={handleSearch} />
								<MainGrid
									dashboardData={dashboardData}
									user={user}
									dashboardType={currentDashboardType}
									dateRange={dateRange || undefined}
									sharedDashboardMetrics={dashboardMetrics}
								/>
							</>
						)}
					</Stack>
				</Box>
			</Box>
		</AppTheme>
	);
}
