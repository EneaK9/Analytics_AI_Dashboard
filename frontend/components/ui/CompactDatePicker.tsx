"use client";

import React, { useState } from "react";
import { Calendar, ChevronDown, X } from "lucide-react";

export interface DateRange {
	start: Date;
	end: Date;
	label: string;
}

interface CompactDatePickerProps {
	value?: DateRange;
	onChange: (range: DateRange) => void;
	className?: string;
	disabled?: boolean;
}

// Default preset ranges
const defaultPresets: DateRange[] = [
	{
		start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
		end: new Date(),
		label: "7 days",
	},
	{
		start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
		end: new Date(),
		label: "30 days",
	},
	{
		start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
		end: new Date(),
		label: "90 days",
	},
	{
		start: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
		end: new Date(),
		label: "This month",
	},
];

export default function CompactDatePicker({
	value,
	onChange,
	className = "",
	disabled = false,
}: CompactDatePickerProps) {
	const [isOpen, setIsOpen] = useState(false);
	const [showCustomForm, setShowCustomForm] = useState(false);
	const [customStart, setCustomStart] = useState("");
	const [customEnd, setCustomEnd] = useState("");

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
				const formatDate = (date: Date) => {
					return date.toLocaleDateString("en-US", {
						month: "short",
						day: "numeric",
						year:
							date.getFullYear() !== new Date().getFullYear()
								? "numeric"
								: undefined,
					});
				};

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
		onChange(defaultPresets[1]); // Default to 30 days
	};

	const displayValue = value ? value.label : "Select period";

	return (
		<div className={`relative ${className}`}>
			{/* Compact Trigger Button */}
			<button
				onClick={() => !disabled && setIsOpen(!isOpen)}
				disabled={disabled}
				className={`
          flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-md
          hover:border-gray-300 hover:shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400
          disabled:bg-gray-50 disabled:cursor-not-allowed transition-all duration-150
          ${isOpen ? "ring-1 ring-blue-400 border-blue-400 shadow-sm" : ""}
        `}>
				<Calendar className="h-3.5 w-3.5 text-gray-400" />
				<span
					className={`text-xs font-medium truncate ${
						value ? "text-gray-700" : "text-gray-400"
					}`}>
					{displayValue}
				</span>
				<div className="flex items-center gap-1">
					{value && (
						<span
							onClick={handleClear}
							className="p-0.5 hover:bg-gray-100 rounded cursor-pointer inline-flex items-center justify-center">
							<X className="h-3 w-3 text-gray-400" />
						</span>
					)}
					<ChevronDown
						className={`h-3.5 w-3.5 text-gray-400 transition-transform duration-150 ${
							isOpen ? "rotate-180" : ""
						}`}
					/>
				</div>
			</button>

			{/* Compact Dropdown */}
			{isOpen && (
				<>
					<div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 min-w-[200px]">
						<div className="py-1">
							{/* Preset Options */}
							{defaultPresets.map((preset, index) => (
								<button
									key={index}
									onClick={() => handlePresetSelect(preset)}
									className={`
                    w-full text-left px-3 py-2 text-sm hover:bg-gray-50 transition-colors
                    ${
											value &&
											value.start.getTime() === preset.start.getTime() &&
											value.end.getTime() === preset.end.getTime()
												? "bg-blue-50 text-blue-700 font-medium"
												: "text-gray-700"
										}
                  `}>
									{preset.label}
								</button>
							))}

							{/* Separator */}
							<div className="border-t border-gray-200 my-1"></div>

							{/* Custom Range */}
							{!showCustomForm ? (
								<button
									onClick={() => setShowCustomForm(true)}
									className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 transition-colors text-gray-700">
									Custom range...
								</button>
							) : (
								<div className="p-3 bg-gray-50 rounded-b-md">
									<div className="space-y-2">
										<div>
											<label className="block text-xs font-medium text-gray-600 mb-1">
												Start Date
											</label>
											<input
												id="compact-date-start"
												name="customStart"
												type="date"
												value={customStart}
												onChange={(e) => setCustomStart(e.target.value)}
												className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
											/>
										</div>
										<div>
											<label className="block text-xs font-medium text-gray-600 mb-1">
												End Date
											</label>
											<input
												id="compact-date-end"
												name="customEnd"
												type="date"
												value={customEnd}
												onChange={(e) => setCustomEnd(e.target.value)}
												min={customStart}
												className="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-blue-400 focus:border-blue-400"
											/>
										</div>
										<div className="flex gap-2 pt-1">
											<button
												onClick={handleCustomSubmit}
												disabled={!customStart || !customEnd}
												className="flex-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors">
												Apply
											</button>
											<button
												onClick={() => {
													setShowCustomForm(false);
													setCustomStart("");
													setCustomEnd("");
												}}
												className="flex-1 px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded hover:bg-gray-300 transition-colors">
												Cancel
											</button>
										</div>
									</div>
								</div>
							)}
						</div>
					</div>
					{/* Overlay to close dropdown */}
					<div
						className="fixed inset-0 z-40"
						onClick={() => {
							setIsOpen(false);
							setShowCustomForm(false);
							setCustomStart("");
							setCustomEnd("");
						}}
					/>
				</>
			)}
		</div>
	);
}

// Utility functions for common date ranges - MEMOIZED to prevent re-renders
const dateRangeCache = new Map<string, DateRange>();

export const getDateRange = (
	period: "week" | "month" | "quarter" | "year"
): DateRange => {
	// Use cache to prevent creating new Date objects every render
	const cacheKey = `${period}_${new Date().toDateString()}`;
	if (dateRangeCache.has(cacheKey)) {
		return dateRangeCache.get(cacheKey)!;
	}

	const now = new Date();
	const ranges = {
		week: {
			start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
			end: now,
			label: "7 days",
		},
		month: {
			start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
			end: now,
			label: "30 days",
		},
		quarter: {
			start: new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000),
			end: now,
			label: "90 days",
		},
		year: {
			start: new Date(now.getFullYear(), 0, 1),
			end: now,
			label: "This year",
		},
	};

	const result = ranges[period];
	dateRangeCache.set(cacheKey, result);
	return result;
};
