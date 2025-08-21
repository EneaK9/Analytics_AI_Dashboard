"use client";

import React, { useState, useMemo } from "react";
import {
	ChevronDown,
	ChevronUp,
	Search,
	Download,
	Filter,
	ArrowUpDown,
	MoreHorizontal,
} from "lucide-react";
import { Card as ShadcnCard, CardContent as ShadcnCardContent, CardHeader, CardTitle } from "./card";
import { 
	Pagination, 
	Box, 
	Typography, 
	OutlinedInput, 
	InputAdornment, 
	IconButton, 
	Button,
	LinearProgress,
	Skeleton,
	Card,
	CardContent
} from "@mui/material";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ClearIcon from "@mui/icons-material/Clear";
import DownloadIcon from "@mui/icons-material/Download";

interface DataTableColumn {
	key: string;
	title: string;
	sortable?: boolean;
	type?: "text" | "number" | "currency" | "date" | "percentage";
	width?: string;
	render?: (value: any, row: any) => React.ReactNode;
}

interface DataTableProps {
	data?: any[];
	columns?: DataTableColumn[];
	title?: string;
	subtitle?: string;
	pagination?: boolean;
	pageSize?: number;
	search?: boolean;
	export?: boolean;
	compact?: boolean;
	loading?: boolean;
	emptyMessage?: string;
	className?: string;
	additionalControls?: React.ReactNode;
}

export default function DataTable({
	data = [],
	columns = [],
	title,
	subtitle,
	pagination = true,
	pageSize = 10,
	search = true,
	export: showExport = false,
	compact = false,
	loading = false,
	emptyMessage = "No data available",
	className = "",
	additionalControls,
}: DataTableProps) {
	const [currentPage, setCurrentPage] = useState(1);
	const [searchTerm, setSearchTerm] = useState("");
	const [sortConfig, setSortConfig] = useState<{
		key: string;
		direction: "asc" | "desc";
	} | null>(null);

	// Sort and filter data
	const processedData = useMemo(() => {
		let result = [...data];

		// Search filter
		if (searchTerm) {
			result = result.filter((row) =>
				columns.some((col) => {
					const value = row[col.key];
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
	}, [data, searchTerm, sortConfig, columns]);

	// Pagination
	const totalPages = Math.ceil(processedData.length / pageSize);
	const paginatedData = pagination
		? processedData.slice((currentPage - 1) * pageSize, currentPage * pageSize)
		: processedData;

	const handleSort = (columnKey: string) => {
		setSortConfig((current) => {
			if (current?.key === columnKey) {
				return {
					key: columnKey,
					direction: current.direction === "asc" ? "desc" : "asc",
				};
			}
			return { key: columnKey, direction: "asc" };
		});
	};

	const formatCellValue = (value: any, column: DataTableColumn) => {
		if (value === null || value === undefined) return "-";

		if (column.render) {
			return column.render(value, {});
		}

		switch (column.type) {
			case "currency":
				return new Intl.NumberFormat("en-US", {
					style: "currency",
					currency: "USD",
				}).format(Number(value) || 0);

			case "number":
				return new Intl.NumberFormat("en-US").format(Number(value) || 0);

			case "percentage":
				return `${Number(value || 0).toFixed(1)}%`;

			case "date":
				return new Date(value).toLocaleDateString();

			default:
				return String(value);
		}
	};

	const handleExport = () => {
		if (!showExport || processedData.length === 0) return;

		const csvContent = [
			columns.map((col) => col.title).join(","),
			...processedData.map((row) =>
				columns
					.map((col) => {
						const value = row[col.key];
						const formatted = formatCellValue(value, col);
						return `"${String(formatted).replace(/"/g, '""')}"`;
					})
					.join(",")
			),
		].join("\n");

		const blob = new Blob([csvContent], { type: "text/csv" });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `${title || "data"}.csv`;
		a.click();
		window.URL.revokeObjectURL(url);
	};

	const getSortIcon = (columnKey: string) => {
		if (sortConfig?.key === columnKey) {
			return sortConfig.direction === "asc" ? (
				<ChevronUp className="w-4 h-4" />
			) : (
				<ChevronDown className="w-4 h-4" />
			);
		}
		return <ArrowUpDown className="w-4 h-4 opacity-50" />;
	};

	if (loading) {
		return (
			<Box sx={{ p: 2 }}>
				<Box sx={{ mb: 2 }}>
						{title && (
						<Typography variant="h6" sx={{ fontSize: "1.25rem", fontWeight: 600, color: "#212121", mb: 0 }}>
								{title}
						</Typography>
					)}
					{subtitle && (
						<Typography variant="body2" sx={{ fontSize: "0.875rem", color: "#757575" }}>
							{subtitle}
						</Typography>
					)}
				</Box>
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
			</Box>
		);
	}

	return (
		<Box>
			{/* Data Table */}
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
									{title}
						</Typography>
						<Typography variant="body2" sx={{ fontSize: "0.875rem", color: "#757575" }}>
							Retrieved {processedData.length} records {pagination && totalPages > 1 ? `(page ${currentPage} of ${totalPages})` : ''}
						</Typography>
					</Box>
					{(search && data.length > 0) || additionalControls ? (
						<Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
							{search && data.length > 0 && (
								<OutlinedInput
									id="data-table-search"
									name="searchInput"
									size="small"
									value={searchTerm}
									onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
									placeholder="Search all data..."
									endAdornment={
										<InputAdornment position="end">
											{searchTerm && (
												<IconButton
													size="small"
													onClick={() => setSearchTerm("")}>
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
									}}
								/>
							)}
						{showExport && processedData.length > 0 && (
								<Button
									variant="outlined"
								onClick={handleExport}
									startIcon={<DownloadIcon />}
									size="small"
									sx={{ whiteSpace: "nowrap" }}
								>
								Export
								</Button>
							)}
							{additionalControls}
						</Box>
					) : null}
				</Box>
				<Box sx={{ p: 0 }}>
				{/* Loading Indicator */}
				{loading && (
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
						opacity: loading ? 0.7 : 1,
						transition: "opacity 0.2s ease-in-out",
						backgroundColor: "#ffffff",
						borderRadius: "0 0 8px 8px",
					}}>
					{paginatedData.length === 0 ? (
						<Box sx={{ 
							display: "flex", 
							justifyContent: "center", 
							alignItems: "center", 
							height: "200px",
							color: "text.secondary"
						}}>
							<Typography variant="body1">{emptyMessage}</Typography>
						</Box>
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
									{columns.map((column, colIndex) => (
									<th
										key={column.key}
											onClick={() => column.sortable && handleSort(column.key)}
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
												borderRight: colIndex < columns.length - 1 ? "1px solid #f0f0f0" : "none",
												cursor: column.sortable ? "pointer" : "default",
												width: column.width,
											}}>
											<div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
											{column.title}
											{column.sortable && getSortIcon(column.key)}
										</div>
									</th>
								))}
							</tr>
						</thead>
						<tbody>
								{paginatedData.map((row, rowIndex) => (
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
											{(currentPage - 1) * pageSize + rowIndex + 1}
										</td>
										{columns.map((column, cellIndex) => {
											const cellValue = row[column.key];
											return (
											<td
												key={column.key}
													style={{
														padding: "12px",
														borderBottom: "1px solid #f0f0f0",
														borderRight: cellIndex < columns.length - 1 ? "1px solid #f0f0f0" : "none",
														whiteSpace: "nowrap",
														maxWidth: "200px",
														overflow: "hidden",
														textOverflow: "ellipsis",
														fontSize: "0.875rem",
														color: "#424242",
													}}
													title={String(cellValue ?? "")}
												>
													{formatCellValue(cellValue, column)}
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
				{pagination && totalPages > 1 && (
					<Box 
						sx={{ 
							p: 3, 
							display: "flex", 
							justifyContent: "center",
							borderTop: "1px solid #e0e0e0",
							backgroundColor: "#fafafa"
						}}
					>
						<Pagination
							count={totalPages}
							page={currentPage}
							onChange={(_, page) => setCurrentPage(page)}
							size="medium"
							showFirstButton
							showLastButton
							disabled={loading}
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
				</Box>
		</Card>
		</Box>
	);
}