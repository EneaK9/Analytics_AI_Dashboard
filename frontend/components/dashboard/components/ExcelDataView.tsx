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
	Tabs,
	Tab,
	Grid,
	Alert,
} from "@mui/material";
import {
	Search as SearchIcon,
	Download as DownloadIcon,
	Refresh as RefreshIcon,
	Upload as UploadIcon,
	Business as BusinessIcon,
	People as PeopleIcon,
	TrendingUp as TrendingUpIcon,
	Inventory as InventoryIcon,
	Payment as PaymentIcon,
	// Assessment as AssessmentIcon,
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

interface BusinessInfo {
	industry: string;
	employees: number;
	data_period: string;
	upload_date: string;
	company_name: string;
	headquarters: string;
}

interface CustomerData {
	name: string;
	email: string;
	status: string;
	location: string;
	age_group: string;
	customer_id: string;
	total_spent: number;
	total_orders: number;
	customer_segment: string;
	registration_date: string;
	preferred_category: string;
	average_order_value: number;
}

interface MonthlySummary {
	month: string;
	top_category: string;
	top_platform: string;
	total_orders: number;
	new_customers: number;
	total_revenue: number;
	average_order_value: number;
	returning_customers: number;
}

interface ProductInventory {
	name: string;
	brand: string;
	status: string;
	category: string;
	supplier: string;
	cost_price: number;
	product_id: string;
	units_sold: number;
	reorder_level: number;
	selling_price: number;
	last_restocked: string;
	stock_quantity: number;
	revenue_generated: number;
}

interface SalesTransaction {
	date: string;
	brand: string;
	region: string;
	status: string;
	category: string;
	discount: number;
	platform: string;
	quantity: number;
	sales_rep: string;
	unit_price: number;
	customer_id: string;
	final_amount: number;
	product_name: string;
	total_amount: number;
	payment_method: string;
	transaction_id: string;
}

interface PerformanceMetrics {
	return_rate: number;
	conversion_rate: number;
	total_orders_ytd: number;
	total_revenue_ytd: number;
	average_shipping_time: number;
	customer_lifetime_value: number;
	customer_acquisition_cost: number;
	customer_satisfaction_score: number;
}

interface StructuredBusinessData {
	business_info: BusinessInfo;
	customer_data: CustomerData[];
	monthly_summary: MonthlySummary[];
	product_inventory: ProductInventory[];
	sales_transactions: SalesTransaction[];
	performance_metrics: PerformanceMetrics;
}

export default function ExcelDataView({ user }: ExcelDataViewProps) {
	const [structuredData, setStructuredData] = useState<StructuredBusinessData | null>(null);
	const [loading, setLoading] = useState(true);
	const [uploading, setUploading] = useState(false);
	const [currentTab, setCurrentTab] = useState(0);
	const [searchTerm, setSearchTerm] = useState("");
	
	// Legacy states for fallback mode
	const [legacyData, setLegacyData] = useState<Record<string, unknown>[]>([]);
	const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
	const [page, setPage] = useState(0);
	const [rowsPerPage, setRowsPerPage] = useState(25);
	const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
	const [availableColumns, setAvailableColumns] = useState<string[]>([]);
	const [isStructuredData, setIsStructuredData] = useState(false);

	// Load client data
	const loadData = async () => {
		setLoading(true);
		try {
			console.log("📊 Loading Excel view data...");
			const response = await clientDataService.fetchClientData();

			if (response.rawData && response.rawData.length > 0) {
				console.log("✅ Data loaded for Excel view:", response.rawData.length, "records");
				console.log("🔍 Complete response:", response);

				const firstRecord = response.rawData[0];
				console.log("🔍 First record structure:", firstRecord);

				// Check if this is structured business data (has the expected sections)
				const expectedSections = ['business_info', 'customer_data', 'monthly_summary', 'product_inventory', 'sales_transactions', 'performance_metrics'];
				const hasAllSections = expectedSections.every(section => section in firstRecord);

				if (hasAllSections) {
					console.log("✅ Detected structured business data format");
					setIsStructuredData(true);
					setStructuredData(firstRecord as StructuredBusinessData);
					console.log("📊 Structured data:", firstRecord);
				} else {
					console.log("⚠️ Using legacy flat data format");
					setIsStructuredData(false);
					
					// Fall back to legacy flattening for unstructured data
					const flattenedData = response.rawData.map((record: any) => {
						const flattened: Record<string, unknown> = {};
						
						Object.entries(record).forEach(([key, value]) => {
							if (value === null || value === undefined) {
								flattened[key] = '';
							} else if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
								flattened[key] = value;
							} else {
								try {
									if (Array.isArray(value)) {
										flattened[key] = value.join(', ');
									} else {
										const str = JSON.stringify(value);
										flattened[key] = str.length < 100 ? str.replace(/[{}"]/g, '').replace(/,/g, ', ') : '[Complex Data]';
									}
								} catch (e) {
									flattened[key] = '[Data Object]';
								}
							}
						});
						
						return flattened;
					});

					setLegacyData(flattenedData);
					const columns = Object.keys(flattenedData[0] || {});
					setAvailableColumns(columns);
					setSelectedColumns(columns.slice(0, 8));
				}
			} else {
				console.log("⚠️ No data available");
				setStructuredData(null);
				setLegacyData([]);
				setIsStructuredData(false);
			}
		} catch (error) {
			console.error("❌ Error loading data:", error);
			setStructuredData(null);
			setLegacyData([]);
			setIsStructuredData(false);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadData();
	}, [user?.client_id]);

	// TabPanel component for structured data view
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
				id={`business-tabpanel-${index}`}
				aria-labelledby={`business-tab-${index}`}
				{...other}
			>
				{value === index && <Box sx={{ p: 3 }}>{children}</Box>}
			</div>
		);
	}

	// Helper function to render business info cards
	const renderBusinessInfo = (businessInfo: BusinessInfo) => (
		<Grid container spacing={3}>
			<Grid item xs={12}>
				<Typography variant="h5" gutterBottom>
					{businessInfo.company_name}
				</Typography>
			</Grid>
			<Grid item xs={12} md={6}>
				<Card>
					<CardContent>
						<Typography variant="h6" color="primary" gutterBottom>
							Company Overview
						</Typography>
						<Typography><strong>Industry:</strong> {businessInfo.industry}</Typography>
						<Typography><strong>Employees:</strong> {businessInfo.employees}</Typography>
						<Typography><strong>Headquarters:</strong> {businessInfo.headquarters}</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} md={6}>
				<Card>
					<CardContent>
						<Typography variant="h6" color="primary" gutterBottom>
							Data Information
						</Typography>
						<Typography><strong>Data Period:</strong> {businessInfo.data_period}</Typography>
						<Typography><strong>Upload Date:</strong> {businessInfo.upload_date}</Typography>
					</CardContent>
				</Card>
			</Grid>
		</Grid>
	);

	// Helper function to render performance metrics
	/* const renderPerformanceMetrics = (metrics: PerformanceMetrics) => (
		<Grid container spacing={3}>
			<Grid item xs={12} sm={6} md={3}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Total Revenue YTD</Typography>
						<Typography variant="h4" color="primary">
							${metrics.total_revenue_ytd.toLocaleString()}
						</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} sm={6} md={3}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Total Orders YTD</Typography>
						<Typography variant="h4" color="primary">
							{metrics.total_orders_ytd}
						</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} sm={6} md={3}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Conversion Rate</Typography>
						<Typography variant="h4" color="primary">
							{metrics.conversion_rate}%
						</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} sm={6} md={3}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Customer Satisfaction</Typography>
						<Typography variant="h4" color="primary">
							{metrics.customer_satisfaction_score}/5
						</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} sm={6} md={4}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Customer Lifetime Value</Typography>
						<Typography variant="h5" color="primary">
							${metrics.customer_lifetime_value.toLocaleString()}
						</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} sm={6} md={4}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Return Rate</Typography>
						<Typography variant="h5" color="primary">
							{metrics.return_rate}%
						</Typography>
					</CardContent>
				</Card>
			</Grid>
			<Grid item xs={12} sm={6} md={4}>
				<Card>
					<CardContent>
						<Typography color="textSecondary" gutterBottom>Avg Shipping Time</Typography>
						<Typography variant="h5" color="primary">
							{metrics.average_shipping_time} days
						</Typography>
					</CardContent>
				</Card>
			</Grid>
		</Grid>
	); */

	// Helper function to render generic data table
	const renderDataTable = <T extends Record<string, any>>(
		data: T[],
		title: string,
		getColumns: (item: T) => Array<{ key: keyof T; label: string; format?: (value: any) => string }>
	) => {
		if (!data || data.length === 0) {
			return (
				<Alert severity="info">
					No {title.toLowerCase()} data available
				</Alert>
			);
		}

		const columns = getColumns(data[0]);
		
		return (
			<Card>
				<CardHeader title={title} />
				<CardContent sx={{ px: 0 }}>
					<TableContainer>
						<Table>
							<TableHead>
								<TableRow>
									<TableCell sx={{ bgcolor: 'grey.100', fontWeight: 'bold' }}>
										#
									</TableCell>
									{columns.map((col) => (
										<TableCell 
											key={String(col.key)} 
											sx={{ bgcolor: 'grey.100', fontWeight: 'bold' }}
										>
											{col.label}
										</TableCell>
									))}
								</TableRow>
							</TableHead>
							<TableBody>
								{data.map((row, index) => (
									<TableRow key={index}>
										<TableCell sx={{ fontWeight: 'bold', color: 'primary.main' }}>
											{index + 1}
										</TableCell>
										{columns.map((col) => (
											<TableCell key={String(col.key)}>
												{col.format 
													? col.format(row[col.key])
													: String(row[col.key] ?? '')
												}
											</TableCell>
										))}
									</TableRow>
								))}
							</TableBody>
						</Table>
					</TableContainer>
				</CardContent>
			</Card>
		);
	};

	// Column definitions for each data type
	const customerColumns = (item: CustomerData) => [
		{ key: 'customer_id' as keyof CustomerData, label: 'Customer ID' },
		{ key: 'name' as keyof CustomerData, label: 'Name' },
		{ key: 'email' as keyof CustomerData, label: 'Email' },
		{ key: 'location' as keyof CustomerData, label: 'Location' },
		{ key: 'customer_segment' as keyof CustomerData, label: 'Segment' },
		{ key: 'total_spent' as keyof CustomerData, label: 'Total Spent', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'total_orders' as keyof CustomerData, label: 'Orders' },
		{ key: 'status' as keyof CustomerData, label: 'Status' },
	];

	const monthlyColumns = (item: MonthlySummary) => [
		{ key: 'month' as keyof MonthlySummary, label: 'Month' },
		{ key: 'total_revenue' as keyof MonthlySummary, label: 'Revenue', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'total_orders' as keyof MonthlySummary, label: 'Orders' },
		{ key: 'new_customers' as keyof MonthlySummary, label: 'New Customers' },
		{ key: 'returning_customers' as keyof MonthlySummary, label: 'Returning' },
		{ key: 'average_order_value' as keyof MonthlySummary, label: 'AOV', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'top_category' as keyof MonthlySummary, label: 'Top Category' },
		{ key: 'top_platform' as keyof MonthlySummary, label: 'Top Platform' },
	];

	const productColumns = (item: ProductInventory) => [
		{ key: 'product_id' as keyof ProductInventory, label: 'Product ID' },
		{ key: 'name' as keyof ProductInventory, label: 'Product Name' },
		{ key: 'brand' as keyof ProductInventory, label: 'Brand' },
		{ key: 'category' as keyof ProductInventory, label: 'Category' },
		{ key: 'stock_quantity' as keyof ProductInventory, label: 'Stock' },
		{ key: 'selling_price' as keyof ProductInventory, label: 'Price', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'units_sold' as keyof ProductInventory, label: 'Sold' },
		{ key: 'revenue_generated' as keyof ProductInventory, label: 'Revenue', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'status' as keyof ProductInventory, label: 'Status' },
	];

	const transactionColumns = (item: SalesTransaction) => [
		{ key: 'transaction_id' as keyof SalesTransaction, label: 'Transaction ID' },
		{ key: 'date' as keyof SalesTransaction, label: 'Date' },
		{ key: 'customer_id' as keyof SalesTransaction, label: 'Customer' },
		{ key: 'product_name' as keyof SalesTransaction, label: 'Product' },
		{ key: 'quantity' as keyof SalesTransaction, label: 'Qty' },
		{ key: 'unit_price' as keyof SalesTransaction, label: 'Unit Price', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'final_amount' as keyof SalesTransaction, label: 'Final Amount', format: (val: number) => `$${val.toLocaleString()}` },
		{ key: 'platform' as keyof SalesTransaction, label: 'Platform' },
		{ key: 'status' as keyof SalesTransaction, label: 'Status' },
	];

	// Handle file upload
	const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
		const file = event.target.files?.[0];
		if (!file || !user?.client_id) return;

		setUploading(true);
		try {
			console.log("📤 Uploading file:", file.name);

			const formData = new FormData();
			formData.append('file', file);
			formData.append('data_format', 'csv');
			formData.append('description', `Business data uploaded from ${user.company_name}`);

			const token = localStorage.getItem('access_token');
			const response = await fetch('/api/data/upload-enhanced', {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${token}`,
				},
				body: formData,
			});

			if (response.ok) {
				console.log("✅ File uploaded successfully");
				// Reload data to show the new records
				await loadData();
				alert(`✅ Successfully uploaded ${file.name}! Your business data is now visible in the table.`);
			} else {
				const errorData = await response.json();
				console.error("❌ Upload failed:", errorData);
				alert(`❌ Upload failed: ${errorData.detail || 'Please try again'}`);
			}
		} catch (error) {
			console.error("❌ Upload error:", error);
			alert("❌ Upload failed. Please check your connection and try again.");
		} finally {
			setUploading(false);
			// Clear the input
			event.target.value = '';
		}
	};

	const handleColumnToggle = (column: string) => {
		setSelectedColumns((prev) =>
			prev.includes(column)
				? prev.filter((c) => c !== column)
				: [...prev, column]
		);
	};

	const formatCellValue = (value: unknown, column: string): string => {
		if (value === null || value === undefined || value === '') return "";

		// Since we're doing aggressive flattening upfront, we should rarely see objects here
		// But just in case, handle any remaining objects
		if (typeof value === "object" && value !== null) {
			if (Array.isArray(value)) {
				return value.join(", ");
			}
			
			// This shouldn't happen much with our new flattening, but just in case
			try {
				return JSON.stringify(value);
			} catch {
				return "[Data Object]";
			}
		}

		// Convert to string first
		const stringValue = String(value);

		// Format numbers (but only if they're actually numeric)
		if (typeof value === "number" || (!isNaN(Number(stringValue)) && stringValue.trim() !== '')) {
			const numValue = typeof value === "number" ? value : Number(stringValue);
			
			if (
				column.toLowerCase().includes("price") ||
				column.toLowerCase().includes("revenue") ||
				column.toLowerCase().includes("cost") ||
				column.toLowerCase().includes("amount") ||
				column.toLowerCase().includes("total") ||
				column.toLowerCase().includes("sales")
			) {
				return `$${numValue.toLocaleString(undefined, {
					minimumFractionDigits: 2,
				})}`;
			}
			
			// Don't format small integers (like IDs) or percentages
			if (numValue % 1 === 0 && numValue < 10000) {
				return stringValue;
			}
			
			return numValue.toLocaleString();
		}

		// Format dates
		if (
			(column.toLowerCase().includes("date") ||
			column.toLowerCase().includes("time")) &&
			stringValue.length > 8
		) {
			try {
				// Check if it's already a formatted date
				if (stringValue.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
					return stringValue;
				}
				const date = new Date(stringValue);
				if (!isNaN(date.getTime())) {
					return date.toLocaleDateString();
				}
			} catch {
				// Fall through to return as string
			}
		}

		// Handle booleans
		if (typeof value === "boolean") {
			return value ? "Yes" : "No";
		}

		// Return the string value, trimmed
		return stringValue.trim();
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

	if (loading) {
		return (
			<Card sx={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
				<Typography>
					{uploading ? "Uploading your business data..." : "Loading your data..."}
				</Typography>
			</Card>
		);
	}

	if (!isStructuredData && (!legacyData || legacyData.length === 0)) {
		return (
			<Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
				<CardHeader
					title="Business Data Tables"
					subheader="All your data is gathered here in tabular format"
					action={
						<Tooltip title="Upload CSV File">
							<IconButton 
								component="label" 
								disabled={uploading}
								sx={{ 
									bgcolor: uploading ? 'action.disabled' : 'primary.main',
									color: 'white',

								}}
							>
								<UploadIcon />
								<input
									type="file"
									accept=".csv,.xlsx,.xls"
									onChange={handleFileUpload}
									style={{ display: 'none' }}
								/>
							</IconButton>
						</Tooltip>
					}
				/>
				<CardContent sx={{ flexGrow: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
					<Box sx={{ textAlign: "center" }}>
						<Typography variant="h6" color="text.secondary" gutterBottom>
							No business data available
						</Typography>
						<Typography color="text.secondary" sx={{ mb: 2 }}>
							Click the upload button (📤) above to upload your CSV file with business data
						</Typography>
						<Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
							Supported formats: .csv, .xlsx, .xls
						</Typography>
					</Box>
				</CardContent>
			</Card>
		);
	}

	// Structured Data View
	if (isStructuredData && structuredData) {
		return (
			<Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
				<CardHeader
					title={
						<Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
							<Typography variant="h5" component="h2">
								{structuredData.business_info.company_name} - Business Analytics
							</Typography>
							<Chip
								label={structuredData.business_info.industry}
								color="primary"
								size="small"
							/>
						</Box>
					}
					subheader={`Comprehensive business data analysis • ${structuredData.business_info.data_period}`}
					action={
						<Box sx={{ display: "flex", gap: 1 }}>
							<Tooltip title="Upload New Data">
								<IconButton 
									component="label" 
									disabled={uploading}
									size="small"
								>
									<UploadIcon />
									<input
										type="file"
										accept=".csv,.xlsx,.xls"
										onChange={handleFileUpload}
										style={{ display: 'none' }}
									/>
								</IconButton>
							</Tooltip>
							<Tooltip title="Refresh Data">
								<IconButton onClick={loadData} disabled={loading || uploading} size="small">
									<RefreshIcon />
								</IconButton>
							</Tooltip>
						</Box>
					}
				/>

				<Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
					<Tabs 
						value={currentTab} 
						onChange={(_, newValue) => setCurrentTab(newValue)}
						sx={{
							'& .MuiTab-root': {
								'&:hover': {
									backgroundColor: 'transparent',
								}
							}
						}}
					>
						<Tab icon={<BusinessIcon />} label="Overview" />
						<Tab icon={<PeopleIcon />} label={`Customers (${structuredData.customer_data.length})`} />
						<Tab icon={<TrendingUpIcon />} label={`Monthly (${structuredData.monthly_summary.length})`} />
						<Tab icon={<InventoryIcon />} label={`Products (${structuredData.product_inventory.length})`} />
						<Tab icon={<PaymentIcon />} label={`Transactions (${structuredData.sales_transactions.length})`} />
						{/* <Tab icon={<AssessmentIcon />} label="Performance" /> */}
					</Tabs>
				</Box>

				<Box sx={{ flexGrow: 1, overflow: 'auto' }}>
					<TabPanel value={currentTab} index={0}>
						{renderBusinessInfo(structuredData.business_info)}
					</TabPanel>

					<TabPanel value={currentTab} index={1}>
						{renderDataTable(structuredData.customer_data, 'Customer Data', customerColumns)}
					</TabPanel>

					<TabPanel value={currentTab} index={2}>
						{renderDataTable(structuredData.monthly_summary, 'Monthly Summary', monthlyColumns)}
					</TabPanel>

					<TabPanel value={currentTab} index={3}>
						{renderDataTable(structuredData.product_inventory, 'Product Inventory', productColumns)}
					</TabPanel>

					<TabPanel value={currentTab} index={4}>
						{renderDataTable(structuredData.sales_transactions, 'Sales Transactions', transactionColumns)}
					</TabPanel>

					{/* <TabPanel value={currentTab} index={5}>
						{renderPerformanceMetrics(structuredData.performance_metrics)}
					</TabPanel> */}
				</Box>
			</Card>
		);
	}

	// Legacy Data View (fallback for unstructured data)
	const processedData = useMemo(() => {
		if (!legacyData || legacyData.length === 0) return [];
		
		let result = [...legacyData];
		if (searchTerm && selectedColumns.length > 0) {
			result = result.filter((row) =>
				selectedColumns.some((col) => {
					const value = row[col];
					return value && value.toString().toLowerCase().includes(searchTerm.toLowerCase());
				})
			);
		}
		return result;
	}, [legacyData, searchTerm, selectedColumns]);

	const paginatedData = processedData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

	return (
		<Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
			<CardHeader
				title="Data Tables - Legacy View"
				subheader="All your data is gathered here in tabular format"
				action={
					<Box sx={{ display: "flex", gap: 1 }}>
						<Tooltip title="Upload CSV File">
							<IconButton component="label" disabled={uploading}>
								<UploadIcon />
								<input
									type="file"
									accept=".csv,.xlsx,.xls"
									onChange={handleFileUpload}
									style={{ display: 'none' }}
								/>
							</IconButton>
						</Tooltip>
						<Tooltip title="Refresh Data">
							<IconButton onClick={loadData} disabled={loading}>
								<RefreshIcon />
							</IconButton>
						</Tooltip>
					</Box>
				}
			/>
			<CardContent sx={{ flexGrow: 1, overflow: 'auto' }}>
				<TableContainer>
					<Table>
						<TableHead>
							<TableRow>
								<TableCell>#</TableCell>
								{selectedColumns.map((column) => (
									<TableCell key={column}>{column}</TableCell>
								))}
							</TableRow>
						</TableHead>
						<TableBody>
							{paginatedData.map((row, index) => (
								<TableRow key={index}>
									<TableCell>{page * rowsPerPage + index + 1}</TableCell>
									{selectedColumns.map((column) => (
										<TableCell key={column}>
											{formatCellValue(row[column], column)}
										</TableCell>
									))}
								</TableRow>
							))}
						</TableBody>
					</Table>
				</TableContainer>
			</CardContent>
		</Card>
	);
}

