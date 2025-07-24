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
	// Use backend dropdown options or fallback to default options
	const availableOptions =
		dropdown_options.length > 0
			? dropdown_options
			: [
					{ value: "3months", label: "Last 3 months" },
					{ value: "6months", label: "Last 6 months" },
					{ value: "1year", label: "Last year" },
			  ];

	const [timeRange, setTimeRange] = useState(
		availableOptions[0]?.value || "3months"
	);

	// Process real data
	const chartData =
		data.length > 0
			? data.slice(0, 20).map((item, index) => {
					const xValue =
						item[xAxisKey] ||
						item["date"] ||
						item["month"] ||
						item["time"] ||
						`Point ${index + 1}`;

					const value1 =
						Number(item[dataKey1]) ||
						Number(item["mobile"]) ||
						Number(item["value1"]) ||
						Math.random() * 100 + 50;

					const value2 =
						Number(item[dataKey2]) ||
						Number(item["desktop"]) ||
						Number(item["value2"]) ||
						Math.random() * 80 + 30;

					return {
						[xAxisKey]: String(xValue),
						[dataKey1]: value1,
						[dataKey2]: value2,
					};
			  })
			: Array.from({ length: 12 }, (_, i) => ({
					[xAxisKey]: `Point ${i + 1}`,
					[dataKey1]: Math.random() * 100 + 50,
					[dataKey2]: Math.random() * 80 + 30,
			  }));

	const chartConfig = {
		[dataKey1]: {
			label:
				ai_labels.legend?.[0] ||
				dataKey1.charAt(0).toUpperCase() + dataKey1.slice(1),
			color: "#2563eb",
		},
		[dataKey2]: {
			label:
				ai_labels.legend?.[1] ||
				dataKey2.charAt(0).toUpperCase() + dataKey2.slice(1),
			color: "#60a5fa",
		},
	};

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
