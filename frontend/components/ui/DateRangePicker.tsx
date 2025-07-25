"use client";

import React, { useState } from "react";
import { Calendar, ChevronDown, X } from "lucide-react";

export interface DateRange {
	start: Date;
	end: Date;
	label: string;
}

interface DateRangePickerProps {
	value?: DateRange;
	onChange: (range: DateRange) => void;
	presets?: DateRange[];
	placeholder?: string;
	className?: string;
	disabled?: boolean;
	showCustom?: boolean;
}

// Default preset ranges
const defaultPresets: DateRange[] = [
	{
		start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
		end: new Date(),
		label: "Last 7 days",
	},
	{
		start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
		end: new Date(),
		label: "Last 30 days",
	},
	{
		start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
		end: new Date(),
		label: "Last 90 days",
	},
	{
		start: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
		end: new Date(),
		label: "This month",
	},
	{
		start: new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1),
		end: new Date(new Date().getFullYear(), new Date().getMonth(), 0),
		label: "Last month",
	},
	{
		start: new Date(new Date().getFullYear(), 0, 1),
		end: new Date(),
		label: "This year",
	},
];

export default function DateRangePicker({
	value,
	onChange,
	presets = defaultPresets,
	placeholder = "Select date range",
	className = "",
	disabled = false,
	showCustom = true,
}: DateRangePickerProps) {
	const [isOpen, setIsOpen] = useState(false);
	const [customStart, setCustomStart] = useState("");
	const [customEnd, setCustomEnd] = useState("");
	const [showCustomForm, setShowCustomForm] = useState(false);

	const formatDate = (date: Date) => {
		return date.toLocaleDateString("en-US", {
			month: "short",
			day: "numeric",
			year:
				date.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
		});
	};

	const handlePresetSelect = (preset: DateRange) => {
		onChange(preset);
		setIsOpen(false);
		setShowCustomForm(false);
	};

	const handleCustomSubmit = () => {
		if (customStart && customEnd) {
			const start = new Date(customStart);
			const end = new Date(customEnd);

			if (start <= end) {
				onChange({
					start,
					end,
					label: `${formatDate(start)} - ${formatDate(end)}`,
				});
				setIsOpen(false);
				setShowCustomForm(false);
				setCustomStart("");
				setCustomEnd("");
			}
		}
	};

	const handleClear = (e: React.MouseEvent) => {
		e.stopPropagation();
		onChange({
			start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
			end: new Date(),
			label: "Last 30 days",
		});
	};

	const displayValue = value
		? value.label === `${formatDate(value.start)} - ${formatDate(value.end)}`
			? value.label
			: `${formatDate(value.start)} - ${formatDate(value.end)}`
		: placeholder;

	return (
		<div className={`relative ${className}`}>
			{/* Trigger Button */}
			<button
				onClick={() => !disabled && setIsOpen(!isOpen)}
				disabled={disabled}
				className={`
          flex items-center justify-between w-full px-4 py-2 text-left bg-white border border-gray-300 rounded-lg
          hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:bg-gray-100 disabled:cursor-not-allowed
          ${isOpen ? "ring-2 ring-blue-500 border-transparent" : ""}
        `}>
				<div className="flex items-center gap-2">
					<Calendar className="h-4 w-4 text-gray-500" />
					<span className={value ? "text-gray-900" : "text-gray-500"}>
						{displayValue}
					</span>
				</div>
				<div className="flex items-center gap-1">
					{value && (
						<button
							onClick={handleClear}
							className="p-0.5 hover:bg-gray-100 rounded">
							<X className="h-3 w-3 text-gray-400" />
						</button>
					)}
					<ChevronDown
						className={`h-4 w-4 text-gray-500 transition-transform ${
							isOpen ? "rotate-180" : ""
						}`}
					/>
				</div>
			</button>

			{/* Dropdown */}
			{isOpen && (
				<div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
					<div className="p-2">
						{/* Preset Options */}
						<div className="space-y-1">
							{presets.map((preset, index) => (
								<button
									key={index}
									onClick={() => handlePresetSelect(preset)}
									className={`
                    w-full text-left px-3 py-2 rounded hover:bg-gray-100 transition-colors
                    ${
											value &&
											value.start.getTime() === preset.start.getTime() &&
											value.end.getTime() === preset.end.getTime()
												? "bg-blue-50 text-blue-700"
												: "text-gray-700"
										}
                  `}>
									{preset.label}
								</button>
							))}
						</div>

						{/* Custom Date Range */}
						{showCustom && (
							<>
								<div className="border-t border-gray-200 my-2"></div>

								{!showCustomForm ? (
									<button
										onClick={() => setShowCustomForm(true)}
										className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 transition-colors text-gray-700">
										Custom range...
									</button>
								) : (
									<div className="p-3 bg-gray-50 rounded-lg">
										<div className="space-y-3">
											<div>
												<label className="block text-xs font-medium text-gray-700 mb-1">
													Start Date
												</label>
												<input
													type="date"
													value={customStart}
													onChange={(e) => setCustomStart(e.target.value)}
													className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
												/>
											</div>
											<div>
												<label className="block text-xs font-medium text-gray-700 mb-1">
													End Date
												</label>
												<input
													type="date"
													value={customEnd}
													onChange={(e) => setCustomEnd(e.target.value)}
													min={customStart}
													className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
												/>
											</div>
											<div className="flex gap-2">
												<button
													onClick={handleCustomSubmit}
													disabled={!customStart || !customEnd}
													className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed">
													Apply
												</button>
												<button
													onClick={() => {
														setShowCustomForm(false);
														setCustomStart("");
														setCustomEnd("");
													}}
													className="flex-1 px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">
													Cancel
												</button>
											</div>
										</div>
									</div>
								)}
							</>
						)}
					</div>
				</div>
			)}

			{/* Overlay to close dropdown */}
			{isOpen && (
				<div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
			)}
		</div>
	);
}

// Utility functions for common date ranges
export const getDateRange = (
	period: "week" | "month" | "quarter" | "year"
): DateRange => {
	const now = new Date();
	const ranges = {
		week: {
			start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
			end: now,
			label: "Last 7 days",
		},
		month: {
			start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
			end: now,
			label: "Last 30 days",
		},
		quarter: {
			start: new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000),
			end: now,
			label: "Last 90 days",
		},
		year: {
			start: new Date(now.getFullYear(), 0, 1),
			end: now,
			label: "This year",
		},
	};
	return ranges[period];
};

export const createCustomRange = (
	startDate: Date,
	endDate: Date
): DateRange => ({
	start: startDate,
	end: endDate,
	label: `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`,
});
