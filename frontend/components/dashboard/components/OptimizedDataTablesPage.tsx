/**
 * Optimized Data Tables Page - Simple Tab Version  
 * Uses single-level tabs for data tables
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
import DownloadIcon from "@mui/icons-material/Download";

import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";

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

	// Export functionality
	const handleExport = () => {
		if (!rawData || rawData.data.length === 0) return;

		const csvContent = [
			["#", ...rawData.columns].join(","),
			...rawData.data.map((row, index) =>
				[
					(filters.page - 1) * 50 + index + 1,
					...rawData.columns.map((column) => {
						const value = row[column];
						const formatted = String(value ?? "");
						return `"${formatted.replace(/"/g, '""')}"`;
					})
				].join(",")
			),
		].join("\n");

		const blob = new Blob([csvContent], { type: "text/csv" });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `${rawData.display_name || "data"}.csv`;
		a.click();
		window.URL.revokeObjectURL(url);
	};


	// All hooks must be called before any early returns to follow Rules of Hooks
	// Sync search input with global state when filters change externally
	React.useEffect(() => {
		setSearchInput(filters.search);
	}, [filters.search]);

	// Create flattened list of all available table combinations
	const allTableCombinations = React.useMemo(() => {
		const combinations: Array<{
			id: string;
			platform?: "shopify" | "amazon";
			dataType?: "products" | "orders" | "order_items" | "inbound_shipments" | "inbound_shipment_items";
			count?: number;
			displayName: string;
			type: 'data';
		}> = [];
		
		
		// Add data table combinations
		if (availableTables?.available_tables) {
			Object.entries(availableTables.available_tables).forEach(([platform, tables]) => {
				(tables as any[]).forEach((table) => {
					const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
					// Format display name for compound data types
					const dataTypeName = table.data_type
						.split('_')
						.map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
						.join(' ');
					
					combinations.push({
						id: `${platform}-${table.data_type}`,
						platform: platform as "shopify" | "amazon",
						dataType: table.data_type as "products" | "orders" | "order_items" | "inbound_shipments" | "inbound_shipment_items",
						count: table.count,
						displayName: `${platformName} ${dataTypeName}`,
						type: 'data'
					});
				});
			});
			
			// Sort data combinations: Amazon first, then Shopify, with logical data type ordering
			const dataCombinations = combinations.filter(c => c.type === 'data');
			dataCombinations.sort((a, b) => {
				if (a.platform !== b.platform) {
					return a.platform === "amazon" ? -1 : 1;
				}
				
				// Define priority order for data types
				const dataTypePriority: Record<string, number> = {
					"products": 1,
					"orders": 2,
					"order_items": 3,
					"inbound_shipments": 4,
					"inbound_shipment_items": 5
				};
				
				const aPriority = dataTypePriority[a.dataType || ""] || 999;
				const bPriority = dataTypePriority[b.dataType || ""] || 999;
				
				return aPriority - bPriority;
			});
			
			// Return sorted data combinations only
			return dataCombinations;
		}
		
		return combinations;
	}, [availableTables]);

	// Debug logging
	React.useEffect(() => {
		console.log("📊 OptimizedDataTablesPage mounted with user:", user);
		console.log("🔑 Client ID:", user?.client_id);
		console.log("🎛️ Current filters:", filters);
		console.log("📋 Available tables:", availableTables);
		console.log("🔗 All table combinations:", allTableCombinations);
	}, [user, filters, availableTables, allTableCombinations]);

	// Synchronize active tab with current filters
	React.useEffect(() => {
		const currentIndex = allTableCombinations.findIndex(
			(combination) =>
				combination.type === 'data' &&
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
			// Start with first data table
			const firstDataTab = allTableCombinations.find(c => c.type === 'data');
			if (firstDataTab && (
				filters.platform !== firstDataTab.platform ||
				filters.dataType !== firstDataTab.dataType
			)) {
				setFilters({
					platform: firstDataTab.platform!,
					dataType: firstDataTab.dataType!,
					page: 1,
				});
			}
		}
	}, [allTableCombinations, setFilters, filters.platform, filters.dataType, activeTabIndex]);

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

	// Fetch data when filters change or on mount (only for data tables)
	React.useEffect(() => {
		const currentTab = allTableCombinations[activeTabIndex];
		if (user?.client_id && currentTab?.type === 'data') {
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
		activeTabIndex,
		allTableCombinations,
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

		if (selectedCombination.type === 'data') {
			// Update filters for data tables
			setFilters({
				platform: selectedCombination.platform!,
				dataType: selectedCombination.dataType!,
				page: 1,
				search: "", // Clear search when switching tabs
			});

			// Clear search input UI as well
			setSearchInput("");
		}

	};

	// Handle page change
	const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
		console.log("📄 Page changed to:", page, "Current filters:", filters);
		setFilters({ page });

		// Scroll to top when changing pages for better UX
		window.scrollTo({ top: 0, behavior: "smooth" });
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
						onClick={() => fetchAvailableTables(user.client_id, true)}>
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
							onClick={() => fetchAvailableTables(user.client_id, true)}>
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
	if (loading && currentCombination?.type === 'data') {
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
	if (error && currentCombination?.type === 'data') {
		return (
			<Box sx={{ p: 3 }}>
				<Alert severity="error" sx={{ mb: 2 }}>
					{error}
				</Alert>

			</Box>
		);
	}

	// No data state
	if (currentCombination?.type === 'data' && (!rawData || rawData.data.length === 0)) {
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

				</Card>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 2 }}>
			<Typography variant="h4" sx={{ mb: 2, fontWeight: "bold" }}>
				Data Tables
			</Typography>
			<Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
				All your data is here organized in tabular format
			</Typography>

			{/* All Tables Tabs */}
			{allTableCombinations.length > 0 && (
				<Box sx={{ mb: 2 }}>
					<Tabs
						value={activeTabIndex}
						onChange={handleTabChange}
						variant="scrollable"
						scrollButtons="auto"
						sx={{
							minHeight: 32,
							"& .MuiTab-root": {
								minHeight: 32,
								fontSize: "0.8rem",
								textTransform: "none",
								fontWeight: 500,
								px: 2,
								py: 1,
								minWidth: "auto",
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
							"& .MuiTabs-flexContainer": {
								gap: 0.5,
							},
						}}>
						{allTableCombinations.map((combination, index) => (
							<Tab
								key={combination.id}
								value={index}
								label={combination.displayName}
								disableRipple
							/>
						))}
					</Tabs>
				</Box>
			)}

			{/* Tab Content */}
					{/* Raw Data Tables Content */}
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
					{currentCombination && rawData && (
						<Box sx={{ mb: 2 }}>
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
										label={`${currentCombination.count?.toLocaleString()} Total Records`}
										color="primary"
										variant="outlined"
										size="small"
										sx={{ height: 20, fontSize: "0.7rem" }}
									/>
									<Chip
										label={`${rawData.pagination.current_page}/${rawData.pagination.total_pages}`}
										variant="outlined"
										size="small"
										sx={{ 
											height: 20, 
											fontSize: "0.7rem",
											backgroundColor: "#ffffff",
											color: "#000000",
											borderColor: "#000000",
										}}
									/>
								</Stack>

							</Stack>
						</Box>
					)}

					{/* Data Table */}
					{rawData && (
						<Card 
							variant="outlined" 
							sx={{ 
								height: "100%",
								boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
								borderRadius: 2,
								border: "1px solid #e0e0e0"
							}}>
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
									<Typography variant="h6" sx={{ fontSize: "1.25rem", fontWeight: 600, color: "#212121", mb: 0 }}>
										{rawData.display_name}
									</Typography>
									<Typography variant="body2" sx={{ fontSize: "0.875rem", color: "#757575" }}>
										{rawData.message}
									</Typography>
								</Box>
								<Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
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
									<Button
										variant="outlined"
										onClick={handleExport}
										startIcon={<DownloadIcon />}
										size="small"
										sx={{ whiteSpace: "nowrap" }}
									>
										Export
									</Button>
								</Box>
							</Box>
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
										height: { xs: "60vh", md: "75vh" },
										overflow: "auto",
										position: "relative",
										opacity: paginationLoading ? 0.7 : 1,
										transition: "opacity 0.2s ease-in-out",
										backgroundColor: "#ffffff",
										borderRadius: "0 0 8px 8px",
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
												<tr style={{ backgroundColor: "#ffffff", borderBottom: "2px solid #e0e0e0" }}>
													<th
														style={{
															position: "sticky",
															top: 0,
															zIndex: 1,
															padding: "16px 12px",
															textAlign: "left",
															fontWeight: "600",
															fontSize: "0.875rem",
															color: "#424242",
															background: "#ffffff",
															borderRight: "1px solid #f0f0f0",
															width: "60px",
														}}>
														#
													</th>
												{rawData.columns.map((column, colIndex) => (
													<th
														key={colIndex}
														style={{
															position: "sticky",
															top: 0,
															zIndex: 1,
															padding: "16px 12px",
															textAlign: "left",
															fontWeight: "600",
															fontSize: "0.875rem",
															color: "#424242",
															background: "#ffffff",
															borderRight: colIndex < rawData.columns.length - 1 ? "1px solid #f0f0f0" : "none",
														}}>
														{column}
													</th>
												))}
											</tr>
										</thead>
										<tbody>
											{rawData.data.map((row, rowIndex) => (
												<tr 
													key={rowIndex}
													style={{
														backgroundColor: rowIndex % 2 === 0 ? "#ffffff" : "#fafafa",
														transition: "background-color 0.2s ease",
													}}
													onMouseEnter={(e) => {
														e.currentTarget.style.backgroundColor = "#f5f5f5";
													}}
													onMouseLeave={(e) => {
														e.currentTarget.style.backgroundColor = rowIndex % 2 === 0 ? "#ffffff" : "#fafafa";
													}}
												>
													<td
														style={{
															padding: "12px",
															borderBottom: "1px solid #f0f0f0",
															borderRight: "1px solid #f0f0f0",
															whiteSpace: "nowrap",
															fontSize: "0.875rem",
															color: "#6b7280",
															fontWeight: "500",
															width: "60px",
														}}
													>
														{(filters.page - 1) * 50 + rowIndex + 1}
													</td>
													{rawData.columns.map((column, cellIndex) => {
														const cellValue = row[column];
														const text = String(cellValue ?? "-");
														const searchTerm = filters.search.trim();

														return (
															<td
																key={cellIndex}
																style={{
																	padding: "12px",
																	borderBottom: "1px solid #f0f0f0",
																	borderRight: cellIndex < rawData.columns.length - 1 ? "1px solid #f0f0f0" : "none",
																	whiteSpace: "nowrap",
																	maxWidth: "200px",
																	overflow: "hidden",
																	textOverflow: "ellipsis",
																	fontSize: "0.875rem",
																	color: "#424242",
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
									<Box sx={{ 
										p: 3, 
										display: "flex", 
										justifyContent: "center",
										borderTop: "1px solid #e0e0e0",
										backgroundColor: "#fafafa"
									}}>
										<Pagination
											count={rawData.pagination.total_pages}
											page={rawData.pagination.current_page}
											onChange={handlePageChange}
											size="medium"
											showFirstButton
											showLastButton
											disabled={paginationLoading}
											sx={{
												"& .MuiPaginationItem-root": {
													transition: "all 0.2s ease-in-out",
													fontWeight: 500,
												},
												"& .MuiPaginationItem-root.Mui-disabled": {
													opacity: 0.6,
												},
												"& .MuiPaginationItem-root.Mui-selected": {
													backgroundColor: "#000000",
													color: "#ffffff",
													"&:hover": {
														backgroundColor: "#333333",
													},
												},
											}}
										/>
									</Box>
								)}
							</CardContent>
						</Card>
					)}

		</Box>
	);
}
