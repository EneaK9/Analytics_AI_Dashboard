import * as React from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

interface CustomizedDataGridProps {
	clientData?: any[];
	dataColumns?: string[];
}

export default function CustomizedDataGrid({
	clientData = [],
	dataColumns = [],
}: CustomizedDataGridProps) {
	// Create dynamic columns based on real data
	const columns: GridColDef[] = React.useMemo(() => {
		if (dataColumns.length === 0) {
			return [
				{ field: "id", headerName: "ID", width: 90 },
				{ field: "data", headerName: "No Data Available", flex: 1 },
			];
		}

		// Create columns from real data
		const dynamicColumns: GridColDef[] = [
			{ field: "id", headerName: "Row #", width: 90 },
		];

		// Add columns based on actual data structure
		dataColumns.slice(0, 6).forEach((column, index) => {
			dynamicColumns.push({
				field: column,
				headerName: column.charAt(0).toUpperCase() + column.slice(1),
				flex: 1,
				minWidth: 150,
				renderCell: (params) => {
					const value = params.value;
					if (typeof value === "number") {
						return value.toLocaleString();
					}
					return String(value || "");
				},
			});
		});

		return dynamicColumns;
	}, [dataColumns]);

	// Transform client data into DataGrid format
	const rows = React.useMemo(() => {
		if (!clientData || clientData.length === 0) {
			return [{ id: 1, data: "No data available" }];
		}

		return clientData.slice(0, 20).map((item, index) => ({
			id: index + 1,
			...item,
		}));
	}, [clientData]);

	return (
		<DataGrid
			checkboxSelection
			rows={rows}
			columns={columns}
			getRowClassName={(params) =>
				params.indexRelativeToCurrentPage % 2 === 0 ? "even" : "odd"
			}
			initialState={{
				pagination: { paginationModel: { pageSize: 10 } },
			}}
			pageSizeOptions={[5, 10, 20]}
			disableColumnResize
			density="compact"
			slotProps={{
				filterPanel: {
					filterFormProps: {
						logicOperatorInputProps: {
							variant: "outlined",
							size: "small",
						},
						columnInputProps: {
							variant: "outlined",
							size: "small",
							sx: { mt: "auto" },
						},
						operatorInputProps: {
							variant: "outlined",
							size: "small",
							sx: { mt: "auto" },
						},
						valueInputProps: {
							InputComponentProps: {
								variant: "outlined",
								size: "small",
							},
						},
					},
				},
			}}
		/>
	);
}
