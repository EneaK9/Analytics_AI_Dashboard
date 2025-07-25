import * as React from "react";
import dayjs, { Dayjs } from "dayjs";
import { useForkRef } from "@mui/material/utils";
import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import CalendarTodayRoundedIcon from "@mui/icons-material/CalendarTodayRounded";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import {
	DatePicker,
	DatePickerFieldProps,
} from "@mui/x-date-pickers/DatePicker";
import {
	useParsedFormat,
	usePickerContext,
	useSplitFieldProps,
} from "@mui/x-date-pickers";

interface ButtonFieldProps extends DatePickerFieldProps {}

function ButtonField(props: ButtonFieldProps) {
	const { forwardedProps } = useSplitFieldProps(props, "date");
	const pickerContext = usePickerContext();
	const handleRef = useForkRef(pickerContext.triggerRef, pickerContext.rootRef);
	const parsedFormat = useParsedFormat();
	const valueStr =
		pickerContext.value == null
			? parsedFormat
			: pickerContext.value.format(pickerContext.fieldFormat);

	return (
		<Button
			{...forwardedProps}
			variant="outlined"
			ref={handleRef}
			size="small"
			startIcon={<CalendarTodayRoundedIcon fontSize="small" />}
			sx={{ minWidth: "fit-content" }}
			onClick={() => pickerContext.setOpen((prev) => !prev)}>
			{pickerContext.label ?? valueStr}
		</Button>
	);
}

export interface DateRange {
	start: Dayjs | null;
	end: Dayjs | null;
	label: string;
}

interface CustomDatePickerProps {
	onDateRangeChange?: (dateRange: DateRange) => void;
	initialValue?: DateRange;
}

export default function CustomDatePicker({
	onDateRangeChange,
	initialValue,
}: CustomDatePickerProps) {
	// Initialize with current date
	const [dateRange, setDateRange] = React.useState<DateRange>(
		initialValue || {
			start: dayjs(),
			end: dayjs(),
			label: "Today",
		}
	);

	const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
	const [customPickerOpen, setCustomPickerOpen] = React.useState(false);
	const [tempStartDate, setTempStartDate] = React.useState<Dayjs | null>(null);
	const [tempEndDate, setTempEndDate] = React.useState<Dayjs | null>(null);

	const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
		setAnchorEl(event.currentTarget);
	};

	const handleMenuClose = () => {
		setAnchorEl(null);
	};

	const handleDateRangeSelect = (newRange: DateRange) => {
		setDateRange(newRange);
		setAnchorEl(null);

		// Notify parent component
		if (onDateRangeChange) {
			onDateRangeChange(newRange);
		}

		console.log(`📅 Date filter changed to: ${newRange.label}`, {
			start: newRange.start?.format("YYYY-MM-DD"),
			end: newRange.end?.format("YYYY-MM-DD"),
		});
	};

	const handleCustomRangeStart = () => {
		setCustomPickerOpen(true);
		setTempStartDate(dateRange.start);
		setTempEndDate(dateRange.end);
		setAnchorEl(null);
	};

	const handleCustomRangeApply = () => {
		if (tempStartDate && tempEndDate) {
			const customRange: DateRange = {
				start: tempStartDate,
				end: tempEndDate,
				label: `${tempStartDate.format("MMM DD")} - ${tempEndDate.format(
					"MMM DD, YYYY"
				)}`,
			};
			handleDateRangeSelect(customRange);
		}
		setCustomPickerOpen(false);
	};

	// Predefined date ranges
	const dateRangeOptions: DateRange[] = [
		{
			start: dayjs(),
			end: dayjs(),
			label: "Today",
		},
		{
			start: dayjs().subtract(1, "day"),
			end: dayjs().subtract(1, "day"),
			label: "Yesterday",
		},
		{
			start: dayjs().subtract(7, "day"),
			end: dayjs(),
			label: "Last 7 days",
		},
		{
			start: dayjs().subtract(30, "day"),
			end: dayjs(),
			label: "Last 30 days",
		},
		{
			start: dayjs().subtract(90, "day"),
			end: dayjs(),
			label: "Last 90 days",
		},
		{
			start: dayjs().startOf("month"),
			end: dayjs().endOf("month"),
			label: "This month",
		},
		{
			start: dayjs().subtract(1, "month").startOf("month"),
			end: dayjs().subtract(1, "month").endOf("month"),
			label: "Last month",
		},
		{
			start: dayjs().startOf("year"),
			end: dayjs().endOf("year"),
			label: "This year",
		},
	];

	return (
		<LocalizationProvider dateAdapter={AdapterDayjs}>
			<ButtonGroup variant="outlined" size="small">
				<Button
					startIcon={<CalendarTodayRoundedIcon fontSize="small" />}
					onClick={handleMenuOpen}
					sx={{ minWidth: "fit-content" }}>
					{dateRange.label}
				</Button>
			</ButtonGroup>

			{/* Date Range Menu */}
			<Menu
				anchorEl={anchorEl}
				open={Boolean(anchorEl)}
				onClose={handleMenuClose}
				PaperProps={{
					sx: { minWidth: 200 },
				}}>
				{dateRangeOptions.map((option, index) => (
					<MenuItem
						key={index}
						onClick={() => handleDateRangeSelect(option)}
						selected={dateRange.label === option.label}>
						{option.label}
					</MenuItem>
				))}
				<MenuItem onClick={handleCustomRangeStart}>Custom Range...</MenuItem>
			</Menu>

			{/* Custom Date Range Dialog */}
			{customPickerOpen && (
				<div
					style={{
						position: "absolute",
						top: "100%",
						left: 0,
						zIndex: 1300,
						backgroundColor: "white",
						border: "1px solid #ccc",
						borderRadius: "4px",
						padding: "16px",
						boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
					}}>
					<div style={{ marginBottom: "16px" }}>
						<DatePicker
							label="Start Date"
							value={tempStartDate}
							onChange={(newValue) => setTempStartDate(newValue)}
							slotProps={{
								textField: { size: "small", fullWidth: true },
							}}
						/>
					</div>
					<div style={{ marginBottom: "16px" }}>
						<DatePicker
							label="End Date"
							value={tempEndDate}
							onChange={(newValue) => setTempEndDate(newValue)}
							slotProps={{
								textField: { size: "small", fullWidth: true },
							}}
						/>
					</div>
					<div
						style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
						<Button size="small" onClick={() => setCustomPickerOpen(false)}>
							Cancel
						</Button>
						<Button
							size="small"
							variant="contained"
							onClick={handleCustomRangeApply}
							disabled={!tempStartDate || !tempEndDate}>
							Apply
						</Button>
					</div>
				</div>
			)}
		</LocalizationProvider>
	);
}
