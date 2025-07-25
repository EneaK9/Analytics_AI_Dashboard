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
import { Card, CardContent, CardHeader, CardTitle } from "./card";

interface DataTableColumn {
	key: string;
	title: string;
	sortable?: boolean;
	type?: "text" | "number" | "currency" | "date" | "percentage";
	width?: string;
	render?: (value: any, row: any) => React.ReactNode;
}

interface DataTableProps {
	data: any[];
	columns: DataTableColumn[];
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
		const column = columns.find((col) => col.key === columnKey);
		if (!column?.sortable) return;

		setSortConfig((current) => {
			if (current?.key === columnKey) {
				return current.direction === "asc"
					? { key: columnKey, direction: "desc" }
					: null;
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
			<Card className={className}>
				{(title || subtitle) && (
					<CardHeader className={compact ? "pb-3" : ""}>
						{title && (
							<CardTitle className={compact ? "text-lg" : ""}>
								{title}
							</CardTitle>
						)}
						{subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
					</CardHeader>
				)}
				<CardContent>
					<div className="space-y-4">
						{/* Loading skeleton */}
						{[...Array(5)].map((_, i) => (
							<div key={i} className="flex space-x-4">
								{columns.map((col, j) => (
									<div
										key={j}
										className="bg-gray-200 animate-pulse h-4 rounded flex-1"></div>
								))}
							</div>
						))}
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card className={className}>
			{(title || subtitle) && (
				<CardHeader className={compact ? "pb-3" : ""}>
					<div className="flex items-start justify-between">
						<div>
							{title && (
								<CardTitle className={compact ? "text-lg" : ""}>
									{title}
								</CardTitle>
							)}
							{subtitle && (
								<p className="text-sm text-gray-600 mt-1">{subtitle}</p>
							)}
						</div>
						{showExport && processedData.length > 0 && (
							<button
								onClick={handleExport}
								className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
								<Download className="w-4 h-4" />
								Export
							</button>
						)}
					</div>
				</CardHeader>
			)}

			<CardContent className={compact ? "pt-0" : ""}>
				{/* Search and filters */}
				{search && data.length > 0 && (
					<div className="mb-4">
						<div className="relative">
							<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
							<input
								type="text"
								placeholder="Search..."
								value={searchTerm}
								onChange={(e) => setSearchTerm(e.target.value)}
								className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
					</div>
				)}

				{/* Table */}
				<div className="overflow-x-auto">
					<table className="w-full">
						<thead>
							<tr className="border-b border-gray-200">
								{columns.map((column) => (
									<th
										key={column.key}
										className={`text-left py-3 px-4 font-semibold text-gray-900 ${
											column.sortable ? "cursor-pointer hover:bg-gray-50" : ""
										} ${compact ? "py-2 text-sm" : ""}`}
										style={{ width: column.width }}
										onClick={() => handleSort(column.key)}>
										<div className="flex items-center gap-2">
											{column.title}
											{column.sortable && getSortIcon(column.key)}
										</div>
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{paginatedData.length === 0 ? (
								<tr>
									<td
										colSpan={columns.length}
										className="text-center py-8 text-gray-500">
										{emptyMessage}
									</td>
								</tr>
							) : (
								paginatedData.map((row, index) => (
									<tr
										key={index}
										className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
										{columns.map((column) => (
											<td
												key={column.key}
												className={`py-3 px-4 ${
													compact ? "py-2 text-sm" : ""
												}`}>
												<div className="truncate">
													{formatCellValue(row[column.key], column)}
												</div>
											</td>
										))}
									</tr>
								))
							)}
						</tbody>
					</table>
				</div>

				{/* Pagination */}
				{pagination && totalPages > 1 && (
					<div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
						<div className="text-sm text-gray-600">
							Showing {(currentPage - 1) * pageSize + 1} to{" "}
							{Math.min(currentPage * pageSize, processedData.length)} of{" "}
							{processedData.length} results
						</div>
						<div className="flex items-center gap-2">
							<button
								onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
								disabled={currentPage === 1}
								className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
								Previous
							</button>

							{/* Page numbers */}
							{[...Array(totalPages)].map((_, i) => {
								const page = i + 1;
								if (
									page === 1 ||
									page === totalPages ||
									(page >= currentPage - 1 && page <= currentPage + 1)
								) {
									return (
										<button
											key={page}
											onClick={() => setCurrentPage(page)}
											className={`px-3 py-1 border rounded ${
												currentPage === page
													? "bg-blue-500 text-white border-blue-500"
													: "border-gray-300 hover:bg-gray-50"
											}`}>
											{page}
										</button>
									);
								} else if (
									page === currentPage - 2 ||
									page === currentPage + 2
								) {
									return (
										<span key={page} className="px-2">
											...
										</span>
									);
								}
								return null;
							})}

							<button
								onClick={() =>
									setCurrentPage((p) => Math.min(totalPages, p + 1))
								}
								disabled={currentPage === totalPages}
								className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
								Next
							</button>
						</div>
					</div>
				)}
			</CardContent>
		</Card>
	);
}
