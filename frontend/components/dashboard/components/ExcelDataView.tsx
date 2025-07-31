import React, { useState, useEffect, useMemo } from "react";
import {
	Card,
	CardContent,
	CardHeader,
	Typography,
	Box,
	Chip,
	TextField,
	InputAdornment,
	Select,
	MenuItem,
	FormControl,
	InputLabel,
	Paper,
	Table,
	TableBody,
	TableCell,
	TableContainer,
	TableHead,
	TableRow,
	TablePagination,
	TableSortLabel,
	IconButton,
	Tooltip,
} from "@mui/material";
import {
	Search as SearchIcon,
	Download as DownloadIcon,
	Refresh as RefreshIcon,
} from "@mui/icons-material";
import { clientDataService } from "../../../lib/clientDataService";

interface ExcelDataViewProps {
	user?: {
		client_id: string;
		company_name: string;
		email: string;
	};
}

interface SortConfig {
	key: string;
	direction: "asc" | "desc";
}

export default function ExcelDataView({ user }: ExcelDataViewProps) {
	const [data, setData] = useState<Record<string, unknown>[]>([]);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState("");
	const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
	const [page, setPage] = useState(0);
	const [rowsPerPage, setRowsPerPage] = useState(25);
	const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
	const [availableColumns, setAvailableColumns] = useState<string[]>([]);
	const [totalRecords, setTotalRecords] = useState(0);

	// Load client data
	const loadData = async () => {
		setLoading(true);
		try {
			console.log("📊 Loading Excel view data...");
			const response = await clientDataService.fetchClientData();

			if (response.rawData && response.rawData.length > 0) {
				console.log(
					"✅ Data loaded for Excel view:",
					response.rawData.length,
					"records"
				);
				setData(response.rawData);
				setTotalRecords(response.totalRecords);

				// Get all available columns from the data
				const columns = Object.keys(response.rawData[0] || {});
				setAvailableColumns(columns);
				setSelectedColumns(columns.slice(0, 8)); // Show first 8 columns by default

				console.log("📝 Available columns:", columns);
			} else {
				console.log("⚠️ No data available");
				setData([]);
				setTotalRecords(0);
				setAvailableColumns([]);
			}
		} catch (error) {
			console.error("❌ Error loading data:", error);
			setData([]);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadData();
	}, [user?.client_id]);

	// Filter and sort data
	const processedData = useMemo(() => {
		let result = [...data];

		// Search filter
		if (searchTerm && selectedColumns.length > 0) {
			result = result.filter((row) =>
				selectedColumns.some((col) => {
					const value = row[col];
					return (
						value &&
						value.toString().toLowerCase().includes(searchTerm.toLowerCase())
					);
				})
			);
		}

		// Sort
		if (sortConfig) {
			result.sort((a, b) => {
				const aValue = a[sortConfig.key];
				const bValue = b[sortConfig.key];

				if (aValue === null || aValue === undefined) return 1;
				if (bValue === null || bValue === undefined) return -1;

				if (typeof aValue === "number" && typeof bValue === "number") {
					return sortConfig.direction === "asc"
						? aValue - bValue
						: bValue - aValue;
				}

				const aStr = aValue.toString().toLowerCase();
				const bStr = bValue.toString().toLowerCase();

				if (sortConfig.direction === "asc") {
					return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
				} else {
					return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
				}
			});
		}

		return result;
	}, [data, searchTerm, sortConfig, selectedColumns]);

	// Pagination
	const paginatedData = processedData.slice(
		page * rowsPerPage,
		page * rowsPerPage + rowsPerPage
	);

	const handleSort = (column: string) => {
		setSortConfig({
			key: column,
			direction:
				sortConfig?.key === column && sortConfig.direction === "asc"
					? "desc"
					: "asc",
		});
	};

	const handleColumnToggle = (column: string) => {
		setSelectedColumns((prev) =>
			prev.includes(column)
				? prev.filter((c) => c !== column)
				: [...prev, column]
		);
	};

	const formatCellValue = (value: unknown, column: string): string => {
		if (value === null || value === undefined) return "";

		// Format numbers
		if (typeof value === "number") {
			if (
				column.toLowerCase().includes("price") ||
				column.toLowerCase().includes("revenue") ||
				column.toLowerCase().includes("cost")
			) {
				return `$${value.toLocaleString(undefined, {
					minimumFractionDigits: 2,
				})}`;
			}
			return value.toLocaleString();
		}

		// Format dates
		if (
			column.toLowerCase().includes("date") ||
			column.toLowerCase().includes("time")
		) {
			try {
				return new Date(value as string).toLocaleDateString();
			} catch {
				return value?.toString() || "";
			}
		}

		return value.toString();
	};

	const exportToCSV = () => {
		if (processedData.length === 0) return;

		const headers = selectedColumns.join(",");
		const rows = processedData.map((row) =>
			selectedColumns
				.map((col) => {
					const value = row[col];
					const stringValue = value?.toString() || "";
					// Escape quotes and wrap in quotes if contains comma
					return stringValue.includes(",")
						? `"${stringValue.replace(/"/g, '""')}"`
						: stringValue;
				})
				.join(",")
		);

		const csvContent = [headers, ...rows].join("\n");
		const blob = new Blob([csvContent], { type: "text/csv" });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `${user?.company_name || "data"}-export-${
			new Date().toISOString().split("T")[0]
		}.csv`;
		a.click();
		window.URL.revokeObjectURL(url);
	};

	return (
		<Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
			<CardHeader
				title={
					<Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
						<Typography variant="h5" component="h2">
							📊 Data Tables - Excel View
						</Typography>
						<Chip
							label={`${totalRecords} records`}
							color="primary"
							size="small"
						/>
					</Box>
				}
				subheader={`Real business data for ${
					user?.company_name || "your company"
				}`}
				action={
					<Box sx={{ display: "flex", gap: 1 }}>
						<Tooltip title="Refresh Data">
							<IconButton onClick={loadData} disabled={loading}>
								<RefreshIcon />
							</IconButton>
						</Tooltip>
						<Tooltip title="Export to CSV">
							<IconButton
								onClick={exportToCSV}
								disabled={processedData.length === 0}>
								<DownloadIcon />
							</IconButton>
						</Tooltip>
					</Box>
				}
			/>

			<CardContent
				sx={{ flexGrow: 1, display: "flex", flexDirection: "column", px: 0 }}>
				{/* Toolbar */}
				<Box sx={{ px: 3, pb: 2, borderBottom: 1, borderColor: "divider" }}>
					<Box
						sx={{
							display: "flex",
							gap: 2,
							alignItems: "center",
							flexDirection: { xs: "column", md: "row" },
						}}>
						<Box sx={{ flex: 1, minWidth: { xs: "100%", md: "300px" } }}>
							<TextField
								fullWidth
								size="small"
								placeholder="Search across all data..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								InputProps={{
									startAdornment: (
										<InputAdornment position="start">
											<SearchIcon />
										</InputAdornment>
									),
								}}
							/>
						</Box>
						<Box sx={{ flex: 1, minWidth: { xs: "100%", md: "300px" } }}>
							<FormControl fullWidth size="small">
								<InputLabel>
									Visible Columns ({selectedColumns.length})
								</InputLabel>
								<Select
									multiple
									value={selectedColumns}
									onChange={(e) =>
										setSelectedColumns(e.target.value as string[])
									}
									renderValue={(selected) =>
										`${selected.length} columns selected`
									}>
									{availableColumns.map((column) => (
										<MenuItem key={column} value={column}>
											<Box
												sx={{ display: "flex", alignItems: "center", gap: 1 }}>
												<input
													type="checkbox"
													checked={selectedColumns.includes(column)}
													onChange={() => handleColumnToggle(column)}
												/>
												{column}
											</Box>
										</MenuItem>
									))}
								</Select>
							</FormControl>
						</Box>
					</Box>
				</Box>

				{loading ? (
					<Box sx={{ p: 4, textAlign: "center" }}>
						<Typography>Loading your data...</Typography>
					</Box>
				) : data.length === 0 ? (
					<Box sx={{ p: 4, textAlign: "center" }}>
						<Typography variant="h6" color="text.secondary">
							No data available
						</Typography>
						<Typography color="text.secondary" sx={{ mt: 1 }}>
							Upload CSV data to see it displayed here in Excel format
						</Typography>
					</Box>
				) : (
					<>
						{/* Data Table */}
						<TableContainer component={Paper} sx={{ flexGrow: 1 }}>
							<Table stickyHeader size="small">
								<TableHead>
									<TableRow>
										<TableCell
											sx={{
												bgcolor: "grey.100",
												fontWeight: "bold",
												minWidth: 60,
											}}>
											#
										</TableCell>
										{selectedColumns.map((column) => (
											<TableCell
												key={column}
												sx={{
													bgcolor: "grey.100",
													fontWeight: "bold",
													minWidth: 120,
													cursor: "pointer",
													"&:hover": { bgcolor: "grey.200" },
												}}
												onClick={() => handleSort(column)}>
												<TableSortLabel
													active={sortConfig?.key === column}
													direction={
														sortConfig?.key === column
															? sortConfig.direction
															: "asc"
													}>
													{column
														.replace(/_/g, " ")
														.replace(/\b\w/g, (l) => l.toUpperCase())}
												</TableSortLabel>
											</TableCell>
										))}
									</TableRow>
								</TableHead>
								<TableBody>
									{paginatedData.map((row, index) => (
										<TableRow
											key={index}
											hover
											sx={{
												"&:nth-of-type(odd)": { bgcolor: "action.hover" },
												"&:hover": { bgcolor: "action.selected" },
											}}>
											<TableCell
												sx={{ fontWeight: "bold", color: "primary.main" }}>
												{page * rowsPerPage + index + 1}
											</TableCell>
											{selectedColumns.map((column) => (
												<TableCell key={column} sx={{ fontSize: "0.875rem" }}>
													{formatCellValue(row[column], column)}
												</TableCell>
											))}
										</TableRow>
									))}
								</TableBody>
							</Table>
						</TableContainer>

						{/* Pagination */}
						<TablePagination
							component="div"
							count={processedData.length}
							page={page}
							onPageChange={(_, newPage) => setPage(newPage)}
							rowsPerPage={rowsPerPage}
							onRowsPerPageChange={(e) => {
								setRowsPerPage(parseInt(e.target.value, 10));
								setPage(0);
							}}
							rowsPerPageOptions={[10, 25, 50, 100]}
							showFirstButton
							showLastButton
						/>
					</>
				)}
			</CardContent>
		</Card>
	);
}
