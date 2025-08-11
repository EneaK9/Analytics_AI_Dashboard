import * as React from "react";
import dayjs, { Dayjs } from "dayjs";
import CalendarTodayRoundedIcon from "@mui/icons-material/CalendarTodayRounded";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Box, MenuItem, Select, TextField } from "@mui/material";

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
    onPresetChange?: (preset: string) => void;
    initialValue?: DateRange | DateSelection;
}

export default function CustomDatePicker({
	onDateRangeChange,
	onDateChange,
    onPresetChange,
	initialValue,
}: CustomDatePickerProps) {
    // Range state + presets
    const initialIsSelection = (initialValue as DateSelection | undefined) && typeof (initialValue as any).date !== 'undefined';
    const initialSingle = initialIsSelection ? (initialValue as DateSelection).date : null;
    const initialStart = !initialIsSelection && (initialValue as DateRange | undefined) && (initialValue as DateRange).start ? (initialValue as DateRange).start : null;
    const initialEnd = !initialIsSelection && (initialValue as DateRange | undefined) && (initialValue as DateRange).end ? (initialValue as DateRange).end : null;

    const [selectedDate, setSelectedDate] = React.useState<Dayjs | null>(
        initialSingle || dayjs()
    );
    const [range, setRange] = React.useState<[Dayjs | null, Dayjs | null]>([
        initialStart || dayjs(),
        initialEnd || dayjs(),
    ]);
    const [preset, setPreset] = React.useState<string>("today");

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

    const handleRangeChange = (newRange: [Dayjs | null, Dayjs | null]) => {
        setRange(newRange);
        const [start, end] = newRange;
        if (start && end && onDateRangeChange) {
            onDateRangeChange({
                start,
                end,
                label: `${start.format("MMM DD, YYYY")} - ${end.format("MMM DD, YYYY")}`,
            });
        }
    };

    const handlePresetChange = (value: string) => {
        setPreset(value);
        if (onPresetChange) onPresetChange(value);
        // Update local range for UX feedback
        const today = dayjs();
        let start = today;
        let end = today;
        if (value === "yesterday") {
            start = today.subtract(1, "day");
            end = start;
        } else if (value === "last_7_days") {
            start = today.subtract(6, "day");
        } else if (value === "last_30_days") {
            start = today.subtract(29, "day");
        } else if (value === "this_month") {
            start = today.startOf("month");
        } else if (value === "last_month") {
            const lastMonth = today.subtract(1, "month");
            start = lastMonth.startOf("month");
            end = lastMonth.endOf("month");
        } else if (value === "last_year") {
            const lastYear = today.subtract(1, "year");
            start = lastYear.startOf("year");
            end = lastYear.endOf("year");
        }
        setRange([start, end]);
        if (onDateRangeChange) {
            onDateRangeChange({ start, end, label: value });
        }
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Box display="flex" gap={1.5} alignItems="center">
                <Select
                    size="small"
                    value={preset}
                    onChange={(e) => handlePresetChange(e.target.value as string)}
                    sx={{
                        borderRadius: 2,
                        '& .MuiOutlinedInput-notchedOutline': { borderColor: 'divider' },
                    }}
                >
                    <MenuItem value="today">Today</MenuItem>
                    <MenuItem value="yesterday">Yesterday</MenuItem>
                    <MenuItem value="last_7_days">Last week</MenuItem>
                    <MenuItem value="last_year">Last year</MenuItem>
                    <MenuItem value="last_month">Last month</MenuItem>
                    <MenuItem value="custom">Custom range</MenuItem>
                </Select>

                {preset === "custom" ? (
                    <Box display="flex" gap={1}>
                        <DatePicker
                            label="Start"
                            value={range[0]}
                            onChange={(d) => handleRangeChange([d, range[1]])}
                            maxDate={range[1] || dayjs()}
                            format="MMM DD, YYYY"
                            slotProps={{
                                textField: {
                                    size: "small",
                                    variant: "outlined",
                                    sx: {
                                        borderRadius: 2,
                                        '& .MuiIconButton-root': {
                                            border: 'none', outline: 'none', boxShadow: 'none', backgroundColor: 'transparent',
                                            '&:hover': { backgroundColor: 'transparent' }
                                        }
                                    }
                                },
                                popper: {
                                    sx: {
                                        '& .MuiPickersArrowSwitcher-button': {
                                            border: 'none', outline: 'none', boxShadow: 'none', backgroundColor: 'transparent',
                                            '&:hover': { backgroundColor: 'transparent' }
                                        }
                                    }
                                }
                            }}
                        />
                        <DatePicker
                            label="End"
                            value={range[1]}
                            onChange={(d) => handleRangeChange([range[0], d])}
                            minDate={range[0] || undefined}
                            maxDate={dayjs()}
                            format="MMM DD, YYYY"
                            slotProps={{
                                textField: {
                                    size: "small",
                                    variant: "outlined",
                                    sx: {
                                        borderRadius: 2,
                                        '& .MuiIconButton-root': {
                                            border: 'none', outline: 'none', boxShadow: 'none', backgroundColor: 'transparent',
                                            '&:hover': { backgroundColor: 'transparent' }
                                        }
                                    }
                                },
                                popper: {
                                    sx: {
                                        '& .MuiPickersArrowSwitcher-button': {
                                            border: 'none', outline: 'none', boxShadow: 'none', backgroundColor: 'transparent',
                                            '&:hover': { backgroundColor: 'transparent' }
                                        }
                                    }
                                }
                            }}
                        />
                    </Box>
                ) : null}
            </Box>
        </LocalizationProvider>
    );
}
