import React, { useState } from "react";
import {
	Area,
	AreaChart,
	ResponsiveContainer,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
} from "recharts";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";

interface ShadcnAreaInteractiveProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dropdown_options?: Array<{ value: string; label: string }>;
	ai_labels?: {
		xAxis?: string;
		yAxis?: string;
		legend?: string[];
	};
	dataKey1?: string;
	dataKey2?: string;
	xAxisKey?: string;
	height?: number;
	showSelector?: boolean;
}

const ShadcnAreaInteractive: React.FC<ShadcnAreaInteractiveProps> = ({
	title = "Area Chart - Interactive",
	description = "Showing total visitors for the last 3 months",
	data = [],
	dropdown_options = [],
	ai_labels = {},
	dataKey1 = "mobile",
	dataKey2 = "desktop",
	xAxisKey = "month",
	height = 300,
	showSelector = true,
}) => {
	// REAL DATA ONLY - Use backend dropdown options
	const availableOptions = dropdown_options.length > 0 ? dropdown_options : [];

	const [timeRange, setTimeRange] = useState(
		availableOptions[0]?.value || "all"
	);

	// Process and filter REAL DATA based on dropdown selection
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return []; // NO FALLBACK DATA - Return empty if no real data
		}

		let filteredData = [...data];

		// Apply dropdown filter if available
		if (timeRange && timeRange !== "all" && timeRange !== "overview") {
			// Filter data based on dropdown selection
			if (timeRange === "recent") {
				// Show last 30% of data
				const recentCount = Math.floor(data.length * 0.3);
				filteredData = data.slice(-recentCount);
			} else if (timeRange === "top5") {
				// Show top 5 by value
				filteredData = data
					.sort(
						(a: any, b: any) =>
							(Number(b[dataKey1]) || 0) - (Number(a[dataKey1]) || 0)
					)
					.slice(0, 5);
			} else if (timeRange === "comparison") {
				// Show comparison view
				filteredData = data
					.sort(
						(a: any, b: any) =>
							(Number(b[dataKey1]) || 0) - (Number(a[dataKey1]) || 0)
					)
					.slice(0, 8);
			} else {
				// Filter by specific category/symbol (like AAPL, GOOGL, etc.)
				filteredData = data.filter((item: any) => {
					const itemName = String(
						item[xAxisKey] || item.name || item.category || item.symbol || ""
					).toLowerCase();
					const filterValue = timeRange.toLowerCase();

					// Exact match or contains match
					return itemName === filterValue || itemName.includes(filterValue);
				});

				// If no exact matches, show all data for that time period
				if (filteredData.length === 0) {
					// Check if it's a time period (YYYY-MM format)
					if (/^\d{4}-\d{2}$/.test(timeRange)) {
						filteredData = data.filter((item: any) => {
							const itemDate = item.date || item.created_at || item.time || "";
							return String(itemDate).includes(timeRange);
						});
					}
				}
			}
		}

		// Process filtered data - REAL VALUES ONLY
		return filteredData
			.slice(0, 20)
			.map((item, index) => {
				// Get real X-axis value
				const xValue =
					item[xAxisKey] ||
					item["name"] ||
					item["category"] ||
					item["symbol"] ||
					item["date"] ||
					item["month"] ||
					`Item ${index + 1}`;

				// Get real Y-axis values - NO FALLBACKS to desktop/mobile
				const value1 = Number(item[dataKey1]) || 0;
				const value2 = Number(item[dataKey2]) || 0;

				return {
					[xAxisKey]: String(xValue),
					[dataKey1]: value1,
					[dataKey2]: value2,
				};
			})
			.filter((item) => item[dataKey1] > 0 || item[dataKey2] > 0); // Only show items with real values
	}, [data, timeRange, dataKey1, dataKey2, xAxisKey]);

	// Generate REAL chart config from AI labels and actual data
	const chartConfig = React.useMemo(() => {
		// Use AI-generated labels if available, otherwise use actual column names
		const label1 =
			ai_labels.legend?.[0] ||
			dataKey1
				?.replace(/_/g, " ")
				.replace(/([A-Z])/g, " $1")
				.trim() ||
			"Primary";
		const label2 =
			ai_labels.legend?.[1] ||
			dataKey2
				?.replace(/_/g, " ")
				.replace(/([A-Z])/g, " $1")
				.trim() ||
			"Secondary";

		return {
			[dataKey1]: {
				label: label1,
				color: "#2563eb",
			},
			[dataKey2]: {
				label: label2,
				color: "#60a5fa",
			},
		};
	}, [dataKey1, dataKey2, ai_labels]);

	return (
		<Card className="bg-card">
			<CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
				<div className="grid flex-1 gap-1 text-center sm:text-left">
					<CardTitle className="text-lg font-semibold">{title}</CardTitle>
					<CardDescription className="text-sm text-muted-foreground">
						{description}
					</CardDescription>
				</div>
				{showSelector && availableOptions.length > 1 && (
					<Select value={timeRange} onValueChange={setTimeRange}>
						<SelectTrigger
							className="w-[160px] rounded-lg sm:ml-auto"
							aria-label="Select view option">
							<SelectValue
								placeholder={availableOptions[0]?.label || "Select option"}
							/>
						</SelectTrigger>
						<SelectContent className="rounded-xl">
							{availableOptions.map((option) => (
								<SelectItem
									key={option.value}
									value={option.value}
									className="rounded-lg">
									{option.label}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
				)}
			</CardHeader>
			<CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
				<ChartContainer
					config={chartConfig}
					className="aspect-auto h-[250px] w-full">
					<AreaChart data={chartData}>
						<defs>
							<linearGradient id="fill1" x1="0" y1="0" x2="0" y2="1">
								<stop offset="5%" stopColor="#2563eb" stopOpacity={0.8} />
								<stop offset="95%" stopColor="#2563eb" stopOpacity={0.1} />
							</linearGradient>
							<linearGradient id="fill2" x1="0" y1="0" x2="0" y2="1">
								<stop offset="5%" stopColor="#60a5fa" stopOpacity={0.8} />
								<stop offset="95%" stopColor="#60a5fa" stopOpacity={0.1} />
							</linearGradient>
						</defs>
						<CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
						<XAxis
							dataKey={xAxisKey}
							tickLine={false}
							axisLine={false}
							tickMargin={8}
							minTickGap={32}
							className="text-xs"
						/>
						<YAxis hide />
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent className="w-[150px]" hideLabel />}
						/>
						<Area
							dataKey={dataKey2}
							type="natural"
							fill="url(#fill2)"
							stroke="#60a5fa"
							strokeWidth={2}
							stackId="a"
						/>
						<Area
							dataKey={dataKey1}
							type="natural"
							fill="url(#fill1)"
							stroke="#2563eb"
							strokeWidth={2}
							stackId="a"
						/>
					</AreaChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnAreaInteractive;
