import * as React from "react";
import dayjs, { Dayjs } from "dayjs";
import CalendarTodayRoundedIcon from "@mui/icons-material/CalendarTodayRounded";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { TextField } from "@mui/material";

// Simple date selection interface
export interface DateSelection {
	date: Dayjs | null;
	label: string;
}

// Keep DateRange for backward compatibility
export interface DateRange {
	start: Dayjs | null;
	end: Dayjs | null;
	label: string;
}

interface CustomDatePickerProps {
	onDateRangeChange?: (dateRange: DateRange) => void;
	onDateChange?: (dateSelection: DateSelection) => void;
	initialValue?: DateRange | DateSelection;
}

export default function CustomDatePicker({
	onDateRangeChange,
	onDateChange,
	initialValue,
}: CustomDatePickerProps) {
	// Initialize with today
	const [selectedDate, setSelectedDate] = React.useState<Dayjs | null>(
		initialValue?.date || dayjs()
	);

	const handleDateChange = (newDate: Dayjs | null) => {
		setSelectedDate(newDate);

		if (newDate) {
			const dateSelection: DateSelection = {
				date: newDate,
				label: newDate.format("MMM DD, YYYY"),
			};

			// For backward compatibility with DateRange
			const dateRange: DateRange = {
				start: newDate,
				end: newDate,
				label: dateSelection.label,
			};

			// Call both callback types for compatibility
			if (onDateChange) {
				onDateChange(dateSelection);
			}
			if (onDateRangeChange) {
				onDateRangeChange(dateRange);
			}

			console.log(`📅 Date selected: ${dateSelection.label}`, {
				date: newDate.format("YYYY-MM-DD"),
			});
		}
	};

	return (
		<LocalizationProvider dateAdapter={AdapterDayjs}>
			<DatePicker
				value={selectedDate}
				onChange={handleDateChange}
				maxDate={dayjs()} // Don't allow future dates
				format="MMM DD, YYYY"
				enableAccessibleFieldDOMStructure={false}
				slotProps={{
					textField: {
						size: "small",
						style: {
							height: "20px",
						},
						variant: "outlined",
						InputProps: {
							startAdornment: (
								<CalendarTodayRoundedIcon 
									fontSize="small" 
									sx={{ mr: 1, color: "action.active", height: "20px"}} 
								/>
							),
							readOnly: true, // Prevent manual typing
							sx: {
								cursor: "pointer",
								"& input": {
									cursor: "pointer",
								},
							},
						},
						sx: {
							minWidth: "180px",
							"& .MuiOutlinedInput-root": {
								"& > fieldset": {
									border: "none",
								},
								"&:hover": {
									"& > fieldset": {
										border: "none",
									},
								},
								"&.Mui-focused": {
									"& > fieldset": {
										border: "none",
									},
								},
							},
							"& .MuiIconButton-root": {
								border: "none",
								outline: "none",
								boxShadow: "none",
								"&:hover": {
									border: "none",
									outline: "none",
									boxShadow: "none",
									backgroundColor: "transparent",
								},
								"&:focus": {
									border: "none",
									outline: "none",
									boxShadow: "none",
								},
								"&.Mui-focusVisible": {
									border: "none",
									outline: "none",
									boxShadow: "none",
								},
							},
						},
					},
					popper: {
						sx: {
							"& .MuiPickersCalendarHeader-root": {
								paddingLeft: 2,
								paddingRight: 2,
								justifyContent: "space-between",
								"& .MuiPickersArrowSwitcher-root": {
									gap: 1,
									"& .MuiIconButton-root": {
										margin: "0 4px",
										padding: "8px",
										border: "none",
										outline: "none",
										boxShadow: "none",
									},
								},
							},
						},
					},
				}}
			/>
		</LocalizationProvider>
	);
}
