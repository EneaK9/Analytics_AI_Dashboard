/**
 * Optimized Data Tables Page
 * Uses global state and raw data service with pagination for efficient data management
 */

import * as React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ClearIcon from "@mui/icons-material/Clear";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import RefreshIcon from "@mui/icons-material/Refresh";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Badge from "@mui/material/Badge";
import Pagination from "@mui/material/Pagination";
import Skeleton from "@mui/material/Skeleton";
import LinearProgress from "@mui/material/LinearProgress";

import {
	useRawDataTables,
	useRawDataFilters,
	useAvailableTables,
} from "../../../store/globalDataStore";

interface OptimizedDataTablesPageProps {
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
}

export default function OptimizedDataTablesPage({
	user,
}: OptimizedDataTablesPageProps) {
	const {
		data: rawData,
		loading,
		paginationLoading,
		error,
		fetch: fetchRawData,
	} = useRawDataTables();
	const { filters, setFilters } = useRawDataFilters();
	const {
		data: availableTables,
		loading: tablesLoading,
		error: tablesError,
		fetch: fetchAvailableTables,
	} = useAvailableTables();

	// Local state for search input (debounced) - MUST be called before any early returns
	const [searchInput, setSearchInput] = React.useState(filters.search);
	const [activeTabIndex, setActiveTabIndex] = React.useState(0);

	// All hooks must be called before any early returns to follow Rules of Hooks
	// Sync search input with global state when filters change externally
	React.useEffect(() => {
		setSearchInput(filters.search);
	}, [filters.search]);

	// Create flattened list of all available table combinations
	const allTableCombinations = React.useMemo(() => {
		if (!availableTables?.available_tables) return [];
		
		const combinations: Array<{
			platform: "shopify" | "amazon";
			dataType: "products" | "orders";
			count: number;
			displayName: string;
		}> = [];
		
		Object.entries(availableTables.available_tables).forEach(([platform, tables]) => {
			(tables as any[]).forEach((table) => {
				const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
				const dataTypeName = table.data_type.charAt(0).toUpperCase() + table.data_type.slice(1);
				
				combinations.push({
					platform: platform as "shopify" | "amazon",
					dataType: table.data_type as "products" | "orders",
					count: table.count,
					displayName: `${platformName} ${dataTypeName}`
				});
			});
		});
		
		// Sort combinations: Amazon first, then Shopify, orders before products
		return combinations.sort((a, b) => {
			if (a.platform !== b.platform) {
				return a.platform === "amazon" ? -1 : 1;
			}
			return a.dataType === "orders" ? -1 : 1;
		});
	}, [availableTables]);

	// Debug logging
	React.useEffect(() => {
		console.log("📊 OptimizedDataTablesPage mounted with user:", user);
		console.log("🔑 Client ID:", user?.client_id);
		console.log("🎛️ Current filters:", filters);
		console.log("📋 Available tables:", availableTables);
		console.log("🔗 All table combinations:", allTableCombinations);
	}, [user, filters, availableTables, allTableCombinations]);

	// Fetch available tables on mount
	React.useEffect(() => {
		if (user?.client_id) {
			console.log("🔄 Fetching available tables for client:", user.client_id);
			fetchAvailableTables(user.client_id);
		}
	}, [user?.client_id, fetchAvailableTables]);

	// Debounced search
	React.useEffect(() => {
		const timer = setTimeout(() => {
			if (searchInput !== filters.search) {
				console.log("🔍 Search input changed to:", searchInput);
				setFilters({ search: searchInput, page: 1 }); // Reset to page 1 when searching
			}
		}, 500);
		return () => clearTimeout(timer);
	}, [searchInput, setFilters, filters.search]);

	// Synchronize active tab with current filters
	React.useEffect(() => {
		const currentIndex = allTableCombinations.findIndex(
			(combination) =>
				combination.platform === filters.platform &&
				combination.dataType === filters.dataType
		);
		if (currentIndex !== -1 && currentIndex !== activeTabIndex) {
			setActiveTabIndex(currentIndex);
		}
	}, [filters.platform, filters.dataType, allTableCombinations, activeTabIndex]);

	// Set initial tab when table combinations are loaded
	React.useEffect(() => {
		if (allTableCombinations.length > 0 && activeTabIndex === 0) {
			const firstCombination = allTableCombinations[0];
			if (
				filters.platform !== firstCombination.platform ||
				filters.dataType !== firstCombination.dataType
			) {
				setFilters({
					platform: firstCombination.platform,
					dataType: firstCombination.dataType,
					page: 1,
				});
			}
		}
	}, [allTableCombinations, setFilters, filters.platform, filters.dataType, activeTabIndex]);

	// Fetch data when filters change or on mount
	React.useEffect(() => {
		if (user?.client_id) {
			console.log("🔄 Filters changed, fetching data:", filters);
			fetchRawData(user.client_id);
		}
	}, [
		filters.platform,
		filters.dataType,
		filters.page,
		filters.search,
		user?.client_id,
		fetchRawData,
	]);

	// Helper function to highlight search matches - must be called before early returns
	const highlightSearchText = React.useCallback(
		(text: string, searchTerm: string) => {
			if (!searchTerm || !text || rawData?.search_fallback) {
				return text;
			}

			const regex = new RegExp(
				`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`,
				"gi"
			);
			const parts = text.split(regex);

			return parts.map((part, index) => {
				if (part.toLowerCase() === searchTerm.toLowerCase()) {
					return (
						<span
							key={index}
							style={{
								backgroundColor: "#fff176", // Yellow highlight
								padding: "1px 2px",
								borderRadius: "2px",
								fontWeight: "600",
							}}>
							{part}
						</span>
					);
				}
				return part;
			});
		},
		[rawData?.search_fallback]
	);

	// Early return if no user - now after all hooks
	if (!user?.client_id) {
		return (
			<Box sx={{ p: 3 }}>
				<Alert severity="warning" sx={{ mb: 2 }}>
					User authentication required. Please log in to view data tables.
				</Alert>
			</Box>
		);
	}

	// Handle tab change
	const handleTabChange = (_: React.SyntheticEvent, newTabIndex: number) => {
		if (newTabIndex < 0 || newTabIndex >= allTableCombinations.length) return;

		const selectedCombination = allTableCombinations[newTabIndex];
		console.log("🔄 Tab changed to:", selectedCombination);

		setActiveTabIndex(newTabIndex);
		setFilters({
			platform: selectedCombination.platform,
			dataType: selectedCombination.dataType,
			page: 1,
			search: "", // Clear search when switching tabs
		});

		// Clear search input UI as well
		setSearchInput("");
	};

	// Handle page change
	const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
		console.log("📄 Page changed to:", page, "Current filters:", filters);
		setFilters({ page });

		// Scroll to top when changing pages for better UX
		window.scrollTo({ top: 0, behavior: "smooth" });
	};

	// Handle refresh
	const handleRefresh = () => {
		if (user?.client_id) {
			fetchRawData(user.client_id, true); // Force refresh
		}
	};

	// Skeleton Table Component for loading states
	const SkeletonTable = () => (
		<Box sx={{ p: 2 }}>
			{Array.from({ length: 10 }).map((_, index) => (
				<Skeleton
					key={index}
					variant="rectangular"
					height={40}
					sx={{ mb: 1 }}
				/>
			))}
		</Box>
	);

	// Loading state for available tables
	if (tablesLoading) {
		return (
			<Box
				sx={{
					display: "flex",
					justifyContent: "center",
					alignItems: "center",
					minHeight: "400px",
					flexDirection: "column",
					gap: 2,
				}}>
				<CircularProgress size={60} />
				<Typography variant="h6" color="text.secondary">
					Loading Available Tables...
				</Typography>
			</Box>
		);
	}

	// Error state for available tables
	if (tablesError) {
		return (
			<Box sx={{ p: 3 }}>
				<Alert severity="error" sx={{ mb: 2 }}>
					Failed to load available tables: {tablesError}
				</Alert>
				<Stack direction="row" spacing={2} justifyContent="center">
					<Button
						variant="contained"
						onClick={() => fetchAvailableTables(user.client_id, true)}
						startIcon={<RefreshIcon />}>
						Retry
					</Button>
				</Stack>
			</Box>
		);
	}

	// No available tables
	if (
		!availableTables ||
		Object.keys(availableTables.available_tables).length === 0
	) {
		return (
			<Box sx={{ p: 3 }}>
				<Card
					sx={{
						bgcolor: "grey.50",
						border: "2px dashed #ccc",
						textAlign: "center",
						p: 4,
					}}>
					<Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
						📊 No Data Tables Available
					</Typography>
					<Typography color="text.secondary" sx={{ mb: 3 }}>
						No organized data tables found for this client. Data may need to be
						organized first.
					</Typography>
					<Stack direction="row" spacing={2} justifyContent="center">
						<Button
							variant="contained"
							onClick={() => fetchAvailableTables(user.client_id, true)}
							startIcon={<RefreshIcon />}>
							Refresh
						</Button>
					</Stack>
				</Card>
			</Box>
		);
	}

	// Get current active combination
	const currentCombination = allTableCombinations[activeTabIndex];

	// Loading state for data
	if (loading) {
		return (
			<Box
				sx={{
					display: "flex",
					justifyContent: "center",
					alignItems: "center",
					minHeight: "400px",
					flexDirection: "column",
					gap: 2,
				}}>
				<CircularProgress size={60} />
				<Typography variant="h6" color="text.secondary">
					Loading Data Tables...
				</Typography>
			</Box>
		);
	}

	// Error state
	if (error) {
		return (
			<Box sx={{ p: 3 }}>
				<Alert severity="error" sx={{ mb: 2 }}>
					{error}
				</Alert>
				<Button
					variant="contained"
					onClick={handleRefresh}
					startIcon={<RefreshIcon />}>
					Try Again
				</Button>
			</Box>
		);
	}

	// No data state
	if (!rawData || rawData.data.length === 0) {
		return (
			<Box sx={{ p: 3 }}>
				<Card
					sx={{
						bgcolor: "grey.50",
						border: "2px dashed #ccc",
						textAlign: "center",
						p: 4,
					}}>
					<Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
						📊 No Data Available
					</Typography>
					<Typography color="text.secondary" sx={{ mb: 3 }}>
						{rawData?.pagination.total_records === 0
							? "No data found for the selected filters."
							: "No data matches the current search criteria."}
					</Typography>
					<Stack direction="row" spacing={2} justifyContent="center">
						<Button
							variant="contained"
							onClick={handleRefresh}
							startIcon={<RefreshIcon />}>
							Refresh Data
						</Button>
					</Stack>
				</Card>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 3 }}>
			<Typography variant="h4" sx={{ mb: 3, fontWeight: "bold" }}>
				Data Tables
			</Typography>
			<Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
				All your data is here organized in tabular format
			</Typography>

			{/* Data Tables Tabs */}
			{allTableCombinations.length > 0 && (
				<Box sx={{ mb: 3 }}>
					<Tabs
						value={activeTabIndex}
						onChange={handleTabChange}
						variant="scrollable"
						scrollButtons="auto"
						sx={{
							minHeight: 40,
							"& .MuiTab-root": {
								minHeight: 40,
								fontSize: "0.9rem",
								textTransform: "none",
								fontWeight: 500,
								px: 3,
							},
						}}>
						{allTableCombinations.map((combination, index) => (
							<Tab
								key={`${combination.platform}-${combination.dataType}`}
								value={index}
								label={combination.displayName}
							/>
						))}
					</Tabs>
				</Box>
			)}

			{/* Search Fallback Alert */}
			{rawData?.search_fallback && rawData?.search && (
				<Alert severity="info" sx={{ mb: 3 }}>
					<Typography variant="body2">
						🔍 No results found for "<strong>{rawData.search}</strong>". Showing
						all data instead.
					</Typography>
				</Alert>
			)}

			{/* Current Table Summary - Only for Selected Tab */}
			{currentCombination && (
				<Box sx={{ mb: 3 }}>
					<Stack
						direction={{ xs: "column", sm: "row" }}
						spacing={2}
						justifyContent="space-between"
						alignItems={{ sm: "center" }}>
						<Stack direction="row" spacing={1} flexWrap="wrap" alignItems="center">
							<Typography variant="body1" color="text.secondary">
								{currentCombination.displayName}:
							</Typography>
							<Chip
								label={`${currentCombination.count.toLocaleString()} Total Records`}
								color="primary"
								variant="outlined"
								size="small"
							/>
							{rawData && (
								<Chip
									label={`${rawData.pagination.current_page}/${rawData.pagination.total_pages}`}
									color="secondary"
									variant="outlined"
									size="small"
								/>
							)}
						</Stack>
						<Button
							variant="outlined"
							onClick={handleRefresh}
							startIcon={<RefreshIcon />}
							size="small">
							Refresh
						</Button>
					</Stack>
				</Box>
			)}

			{/* Data Table */}
			<Card sx={{ height: "100%" }}>
				<CardHeader
					title={rawData.display_name}
					subheader={rawData.message}
					action={
						<Stack direction="row" spacing={2} alignItems="center">
							{/* Search Box */}
							<OutlinedInput
								id="optimized-data-table-search"
								name="searchInput"
								size="small"
								value={searchInput}
								onChange={(e) => setSearchInput(e.target.value)}
								placeholder={
									rawData.search_fallback
										? "Search (showing all data)"
										: "Search all data..."
								}
								endAdornment={
									<InputAdornment position="end">
										{searchInput && (
											<IconButton
												size="small"
												onClick={() => setSearchInput("")}>
												<ClearIcon fontSize="small" />
											</IconButton>
										)}
										<SearchRoundedIcon
											fontSize="small"
											sx={{ color: "text.secondary", ml: 0.5 }}
										/>
									</InputAdornment>
								}
								sx={{
									width: { xs: "100%", md: 320 },
									"& .MuiOutlinedInput-root": {
										borderColor: rawData.search_fallback
											? "info.main"
											: undefined,
									},
								}}
							/>
						</Stack>
					}
				/>
				<CardContent sx={{ p: 0 }}>
					{/* Pagination Loading Indicator */}
					{paginationLoading && (
						<LinearProgress
							sx={{
								position: "absolute",
								top: 0,
								left: 0,
								right: 0,
								zIndex: 2,
							}}
						/>
					)}

					{/* Data Table */}
					<Box
						sx={{
							width: "100%",
							height: { xs: "50vh", md: "60vh" },
							overflow: "auto",
							position: "relative",
							opacity: paginationLoading ? 0.7 : 1,
							transition: "opacity 0.2s ease-in-out",
						}}>
						{paginationLoading ? (
							<SkeletonTable />
						) : (
							<table
								style={{
									width: "100%",
									borderCollapse: "collapse",
									tableLayout: "auto",
								}}>
								<thead>
									<tr style={{ backgroundColor: "#f5f5f5" }}>
										{rawData.columns.map((column, colIndex) => (
											<th
												key={colIndex}
												style={{
													position: "sticky",
													top: 0,
													zIndex: 1,
													padding: "12px",
													textAlign: "left",
													borderBottom: "1px solid #ddd",
													fontWeight: "bold",
													background: "#f5f5f5",
												}}>
												{column}
											</th>
										))}
									</tr>
								</thead>
								<tbody>
									{rawData.data.map((row, rowIndex) => (
										<tr key={rowIndex}>
											{rawData.columns.map((column, cellIndex) => {
												const cellValue = row[column];
												const text = String(cellValue ?? "-");
												const searchTerm = filters.search.trim();

												return (
													<td
														key={cellIndex}
														style={{
															padding: "12px",
															borderBottom: "1px solid #eee",
															whiteSpace: "nowrap",
															maxWidth: "200px",
															overflow: "hidden",
															textOverflow: "ellipsis",
														}}
														title={text} // Show full text on hover
													>
														{searchTerm &&
														text
															.toLowerCase()
															.includes(searchTerm.toLowerCase()) &&
														!rawData.search_fallback
															? highlightSearchText(text, searchTerm)
															: text}
													</td>
												);
											})}
										</tr>
									))}
								</tbody>
							</table>
						)}
					</Box>

					{/* Pagination */}
					{rawData.pagination.total_pages > 1 && (
						<Box sx={{ p: 2, display: "flex", justifyContent: "center" }}>
							<Pagination
								count={rawData.pagination.total_pages}
								page={rawData.pagination.current_page}
								onChange={handlePageChange}
								color="primary"
								size="large"
								showFirstButton
								showLastButton
								disabled={paginationLoading}
								sx={{
									"& .MuiPaginationItem-root": {
										transition: "all 0.2s ease-in-out",
									},
									"& .MuiPaginationItem-root.Mui-disabled": {
										opacity: 0.6,
									},
								}}
							/>
						</Box>
					)}
				</CardContent>
			</Card>
		</Box>
	);
}
