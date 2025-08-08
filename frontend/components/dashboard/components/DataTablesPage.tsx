import * as React from "react";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import api from "../../../lib/axios";
interface UseDashboardMetricsReturn {
	data: any;
	loading: boolean;
	error: string | null;
	refetch: () => Promise<void>;
}

interface DateRange {
	start: any;
	end: any;
	label?: string;
}

interface DataTablesPageProps {
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
	dashboardMetrics?: UseDashboardMetricsReturn;
	dateRange?: DateRange;
}

export default function DataTablesPage({ user, dashboardMetrics, dateRange }: DataTablesPageProps) {
	// State for date-filtered data
	const [dateFilteredData, setDateFilteredData] = React.useState<any>(null);
	const [isLoadingDateFilter, setIsLoadingDateFilter] = React.useState(false);
	const [dateFilterError, setDateFilterError] = React.useState<string | null>(null);

	// Extract shared dashboard metrics data
	const metricsData = dashboardMetrics?.data;
	const loading = dashboardMetrics?.loading ?? true;
	const error = dashboardMetrics?.error;

	// Helper function to check if dateRange represents "today" (no filtering needed)
	const isDateRangeToday = React.useCallback((dateRange: any) => {
		if (!dateRange || !dateRange.start) return false;
		
		const today = new Date();
		const selectedDate = dateRange.start?.format ? 
			new Date(dateRange.start.format('YYYY-MM-DD')) : 
			new Date(dateRange.start);
		
		return selectedDate.toDateString() === today.toDateString();
	}, []);

	// Load date-filtered data when dateRange changes
	const loadDateFilteredData = React.useCallback(async () => {
		// Check if no date filter or if the date is today (use shared data)
		if (!user?.client_id || !dateRange || (!dateRange.start && !dateRange.end) || isDateRangeToday(dateRange)) {
			const isToday = isDateRangeToday(dateRange);
			console.log(isToday ? "📅 Today selected - using shared data for tables (no filtering needed)" : "📊 No date filter applied - using shared data for tables");
			setDateFilteredData(null);
			setDateFilterError(null);
			return;
		}

		console.log("📅 Loading date-filtered data for Data Tables:", {
			start: dateRange.start?.format ? dateRange.start.format('YYYY-MM-DD') : dateRange.start,
			end: dateRange.end?.format ? dateRange.end.format('YYYY-MM-DD') : dateRange.end,
			label: dateRange.label
		});

		setIsLoadingDateFilter(true);
		setDateFilterError(null);

		try {
			const params = new URLSearchParams();
			params.append('fast_mode', 'true');
			
			if (dateRange.start) {
				const startDate = dateRange.start?.format ? dateRange.start.format('YYYY-MM-DD') : dateRange.start;
				params.append('start_date', startDate);
			}
			if (dateRange.end) {
				const endDate = dateRange.end?.format ? dateRange.end.format('YYYY-MM-DD') : dateRange.end;
				params.append('end_date', endDate);
			}

			const response = await api.get(`/dashboard/metrics?${params.toString()}`);
			
			if (response.data && response.data.llm_analysis) {
				console.log("✅ Date-filtered data loaded for Data Tables");
				setDateFilteredData(response.data.llm_analysis);
			} else {
				console.error("❌ No LLM analysis in date-filtered response for tables");
				setDateFilterError("No data available for selected date range");
			}
		} catch (error) {
			console.error("❌ Error loading date-filtered data for tables:", error);
			setDateFilterError("Failed to load date-filtered data");
		} finally {
			setIsLoadingDateFilter(false);
		}
	}, [user?.client_id, dateRange, isDateRangeToday]);

	// Trigger date filtering when dateRange changes
	React.useEffect(() => {
		loadDateFilteredData();
	}, [loadDateFilteredData]);

	// Determine which data to use: date-filtered or shared
	const activeData = dateFilteredData || metricsData;
	const isActivelyLoading = loading || isLoadingDateFilter;
	const activeError = error || dateFilterError;

	if (isActivelyLoading) {
		return (
			<Box sx={{ 
				display: 'flex', 
				justifyContent: 'center', 
				alignItems: 'center', 
				minHeight: '400px',
				flexDirection: 'column',
				gap: 2
			}}>
				<CircularProgress size={60} />
				<Typography variant="h6" color="text.secondary">
					{isLoadingDateFilter ? "Loading Date-Filtered Tables..." : "Loading Data Tables..."}
				</Typography>
			</Box>
		);
	}

	if (activeError) {
		return (
			<Box sx={{ p: 3 }}>
				<Alert severity="error" sx={{ mb: 2 }}>
					{activeError}
				</Alert>
			</Box>
		);
	}

	const hasLLMTables = activeData?.tables && activeData.tables.length > 0;

	if (!hasLLMTables) {
		return (
			<Box sx={{ p: 3 }}>
				<Card sx={{
					bgcolor: "grey.50",
					border: "2px dashed #ccc",
					textAlign: "center",
					p: 4
				}}>
					<Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
						📊 No Data Tables Available
					</Typography>
					<Typography color="text.secondary">
						Upload some data to see analysis tables and insights here.
					</Typography>
				</Card>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 3 }}>
			<Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
				📊 Data Tables
			</Typography>
			<Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
				{(dateRange && !isDateRangeToday(dateRange)) ? `AI-generated analysis tables for ${dateRange.label || 'selected date range'}` : 'AI-generated analysis tables from your dashboard metrics'}
			</Typography>

			{/* Date Filter Indicator - Only show for non-today dates */}
			{dateRange && !isDateRangeToday(dateRange) && (
				<Alert severity="info" sx={{ mb: 3 }}>
					📅 Showing data for: <strong>{dateRange.label}</strong>
				</Alert>
			)}

			{/* LLM Analysis Tables */}
			<Grid container spacing={2}>
				{activeData.tables.map((table: any, index: number) => {
					// Skip if no columns or data
					if (
						!table.columns ||
						!Array.isArray(table.columns) ||
						!table.data ||
						!Array.isArray(table.data)
					) {
						return null;
					}

					return (
						<Grid key={index} size={{ xs: 12 }}>
							<Card sx={{ mb: 3 }}>
								<CardHeader
									title={table.display_name}
									subheader={`${table.data.length} rows of data`}
								/>
								<CardContent>
									<Box sx={{ overflow: "auto", maxHeight: 600 }}>
										<table style={{ width: "100%", borderCollapse: "collapse" }}>
											<thead>
												<tr style={{ backgroundColor: "#f5f5f5" }}>
													{table.columns.map((column: string, colIndex: number) => (
														<th
															key={colIndex}
															style={{
																padding: "12px",
																textAlign: "left",
																borderBottom: "1px solid #ddd",
																fontWeight: "bold",
															}}>
															{column}
														</th>
													))}
												</tr>
											</thead>
											<tbody>
												{table.data.map((row: any, rowIndex: number) => (
													<tr key={rowIndex}>
														{Array.isArray(row) ? (
															// Handle array format (row is an array)
															row.map((cell: any, cellIndex: number) => (
																<td
																	key={cellIndex}
																	style={{
																		padding: "12px",
																		borderBottom: "1px solid #eee",
																	}}>
																	{String(cell || "-")}
																</td>
															))
														) : (
															// Handle object format (row is an object)
															table.columns.map((column: string, cellIndex: number) => (
																<td
																	key={cellIndex}
																	style={{
																		padding: "12px",
																		borderBottom: "1px solid #eee",
																	}}>
																	{String(row[column] || "-")}
																</td>
															))
														)}
													</tr>
												))}
											</tbody>
										</table>
									</Box>
								</CardContent>
							</Card>
						</Grid>
					);
				})}
			</Grid>
		</Box>
	);
}
