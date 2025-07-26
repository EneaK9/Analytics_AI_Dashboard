import * as React from 'react';
import { useState, useMemo } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';

interface BusinessDataTableProps {
	clientData?: any[];
	dataColumns?: string[];
	title?: string;
	subtitle?: string;
}

interface BusinessDataRow {
	id: string;
	name: string;
	category: string;
	value: number;
	quantity: number;
	status: 'Active' | 'Archived' | 'Unknown';
	trend: number[];
	growth: number;
	revenue: number;
}

export default function BusinessDataTable({
	clientData = [],
	dataColumns = [],
	title = "Business Data Overview",
	subtitle = "Key business metrics and performance data"
}: BusinessDataTableProps) {
	const [page, setPage] = useState(0);
	const [rowsPerPage, setRowsPerPage] = useState(10);
	const [searchTerm, setSearchTerm] = useState("");
	const search = true; // Enable search by default

	// Process real data and determine available columns
	const processedData = useMemo(() => {
		if (clientData.length === 0) {
			console.log("⚠️ No client data available");
			return { data: [], availableColumns: [] };
		}

		console.log("📊 Raw client data received:", clientData.slice(0, 3));
		console.log("🔍 First item keys:", Object.keys(clientData[0] || {}));

		// Analyze what data is actually available
		const sampleItem = clientData[0] || {};
		const availableFields = Object.keys(sampleItem);
		
		// Map API fields to display columns
		const fieldMapping = {
			name: ['title', 'name', 'product', 'handle'],
			category: ['product_type', 'category', 'type', 'vendor'],
			price: ['price', 'amount', 'value', 'cost'],
			quantity: ['inventory_quantity', 'quantity', 'stock', 'count'],
			status: ['status', 'state', 'published'],
			revenue: ['revenue', 'total_revenue', 'sales']
		};

		// Determine which columns to show based on available data
		const availableColumns: string[] = [];
		const hasData: Record<string, boolean> = {};

		Object.entries(fieldMapping).forEach(([column, possibleFields]) => {
			const hasField = possibleFields.some(field => 
				availableFields.includes(field) && 
				clientData.some(item => item[field] != null && item[field] !== '')
			);
			if (hasField) {
				availableColumns.push(column);
				hasData[column] = true;
			}
		});

		console.log("✅ Available columns with data:", availableColumns);

		// Process the data using only available fields
		const processedItems = clientData.map((item, index) => {
			const result: any = {
				id: item.id || `item_${index}`
			};

			// Extract name
			if (hasData.name) {
				result.name = item.title || item.name || item.product || item.handle || `Item ${index + 1}`;
			}

			// Extract category
			if (hasData.category) {
				result.category = item.product_type || item.category || item.type || item.vendor || 'Uncategorized';
			}

			// Extract price (properly formatted)
			if (hasData.price) {
				const priceValue = item.price || item.amount || item.value || item.cost;
				result.price = priceValue ? parseFloat(priceValue.toString()) : 0;
			}

			// Extract quantity
			if (hasData.quantity) {
				const qtyValue = item.inventory_quantity || item.quantity || item.stock || item.count;
				result.quantity = qtyValue ? parseInt(qtyValue.toString()) : 0;
			}

			// Extract status (properly mapped)
			if (hasData.status) {
				const statusValue = item.status || item.state || item.published;
				if (statusValue === 'active' || statusValue === 'published' || statusValue === true) {
					result.status = 'Active';
				} else if (statusValue === 'archived' || statusValue === 'draft' || statusValue === false) {
					result.status = 'Archived';
				} else {
					result.status = statusValue || 'Unknown';
				}
			}

			// Calculate revenue only if both price and quantity are available
			if (hasData.price && hasData.quantity && result.price && result.quantity) {
				result.revenue = result.price * result.quantity;
			} else if (hasData.revenue) {
				result.revenue = item.revenue || item.total_revenue || item.sales || 0;
			}

			return result;
		});

		return { 
			data: processedItems, 
			availableColumns: availableColumns.filter(col => 
				col === 'name' || // Always show name
				hasData[col] // Show only columns with actual data
			)
		};
	}, [clientData]);

	// Destructure the processed data
	const tableData = processedData.data;
	const availableColumns = processedData.availableColumns;

	// Filter data based on search
	const filteredData = useMemo(() => {
		if (!searchTerm) return tableData;
		
		return tableData.filter(row =>
			availableColumns.some(col => {
				const value = row[col];
				return value && value.toString().toLowerCase().includes(searchTerm.toLowerCase());
			})
		);
	}, [tableData, searchTerm, availableColumns]);

	// Paginated data
	const paginatedData = useMemo(() => {
		const startIndex = page * rowsPerPage;
		return filteredData.slice(startIndex, startIndex + rowsPerPage);
	}, [filteredData, page, rowsPerPage]);

	const handleChangePage = (event: unknown, newPage: number) => {
		setPage(newPage);
	};

	const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
		setRowsPerPage(parseInt(event.target.value, 10));
		setPage(0);
	};

	const getStatusColor = (status: BusinessDataRow['status']) => {
		switch (status) {
			case 'Active': return 'success';
			case 'Archived': return 'error';
			case 'Unknown': return 'default';
			default: return 'default';
		}
	};

	const formatCurrency = (value: number) => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0,
		}).format(value);
	};

	return (
		<Card variant="outlined" sx={{ width: '100%' }}>
			<CardHeader
				title={title}
				subheader={subtitle}
				action={
					<TextField
						size="small"
						placeholder="Search products..."
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
				}
			/>
			<CardContent sx={{ pt: 0 }}>
				{/* Search and filters */}
				{search && tableData.length > 0 && (
					<div className="mb-4">
						<div className="relative">
							<SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
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
				<TableContainer>
					<Table size="small">
						<TableHead>
							<TableRow>
								{availableColumns.map((col) => (
									<TableCell key={col}>
										<strong>{col.charAt(0).toUpperCase() + col.slice(1)}</strong>
									</TableCell>
								))}
							</TableRow>
						</TableHead>
						<TableBody>
							{paginatedData.length === 0 ? (
								<TableRow>
									<TableCell
										colSpan={availableColumns.length}
										align="center"
										sx={{ py: 4 }}>
										<Typography color="text.secondary">
											No data available
										</Typography>
									</TableCell>
								</TableRow>
							) : (
								paginatedData.map((row) => (
									<TableRow key={row.id} hover>
										{availableColumns.map((col) => (
											<TableCell key={col}>
												{col === 'name' ? (
													<Typography variant="body2" fontWeight="medium">
														{row.name}
													</Typography>
												) : col === 'category' ? (
													<Typography variant="body2" color="text.secondary">
														{row.category}
													</Typography>
												) : col === 'price' ? (
													<Typography variant="body2">
														{formatCurrency(row.price)}
													</Typography>
												) : col === 'quantity' ? (
													<Typography variant="body2">
														{row.quantity.toLocaleString()}
													</Typography>
												) : col === 'revenue' ? (
													<Typography variant="body2" fontWeight="medium">
														{formatCurrency(row.revenue)}
													</Typography>
												) : col === 'status' ? (
													<Chip
														label={row.status}
														color={getStatusColor(row.status) as any}
														size="small"
													/>
												) : (
													<Typography variant="body2" color="text.secondary">
														{row[col] || 'N/A'}
													</Typography>
												)}
											</TableCell>
										))}
									</TableRow>
								))
							)}
						</TableBody>
					</Table>
				</TableContainer>
				
				<TablePagination
					component="div"
					count={filteredData.length}
					page={page}
					onPageChange={handleChangePage}
					rowsPerPage={rowsPerPage}
					onRowsPerPageChange={handleChangeRowsPerPage}
					rowsPerPageOptions={[5, 10, 25, 50]}
					sx={{ mt: 2 }}
				/>
			</CardContent>
		</Card>
	);
} 