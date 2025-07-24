"use client";

import * as React from "react";
import { Label, Pie, PieChart, Sector } from "recharts";
import { PieSectorDataItem } from "recharts/types/polar/Pie";

import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	ChartConfig,
	ChartContainer,
	ChartStyle,
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

interface ShadcnPieInteractiveProps {
	data: any[];
	dropdown_options?: Array<{ value: string; label: string }>;
	ai_labels?: {
		dataKey?: string;
		nameKey?: string;
		legend?: string[];
	};
	title?: string;
	description?: string;
	minimal?: boolean;
}

const desktopData = [
	{ month: "january", desktop: 186, fill: "var(--color-january)" },
	{ month: "february", desktop: 305, fill: "var(--color-february)" },
	{ month: "march", desktop: 237, fill: "var(--color-march)" },
	{ month: "april", desktop: 173, fill: "var(--color-april)" },
	{ month: "may", desktop: 209, fill: "var(--color-may)" },
];

const chartConfig = {
	visitors: {
		label: "Visitors",
	},
	desktop: {
		label: "Desktop",
	},
	mobile: {
		label: "Mobile",
	},
	january: {
		label: "January",
		color: "var(--chart-1)",
	},
	february: {
		label: "February",
		color: "var(--chart-2)",
	},
	march: {
		label: "March",
		color: "var(--chart-3)",
	},
	april: {
		label: "April",
		color: "var(--chart-4)",
	},
	may: {
		label: "May",
		color: "var(--chart-5)",
	},
} satisfies ChartConfig;

const ShadcnPieInteractive: React.FC<ShadcnPieInteractiveProps> = ({
	data,
	dropdown_options = [],
	ai_labels = {},
	title = "Pie Chart - Interactive",
	description = "January - June 2024",
	minimal = false,
}) => {
	const id = "pie-interactive";

	// Use real data or fallback to desktop data
	const chartData = React.useMemo(() => {
		if (data && data.length > 0) {
			return data.slice(0, 8).map((item, index) => ({
				month: item.name || item.month || item.category || `Item ${index + 1}`,
				desktop: item.value || item.desktop || item.visitors || 0,
				fill: item.fill || `var(--chart-${(index % 5) + 1})`,
			}));
		}
		return desktopData;
	}, [data]);

	// Use backend dropdown options or generate from data
	const availableOptions = React.useMemo(() => {
		if (dropdown_options.length > 0) {
			return dropdown_options;
		}
		// Generate options from chart data
		return chartData.map((item) => ({
			value: item.month,
			label: item.month.charAt(0).toUpperCase() + item.month.slice(1),
		}));
	}, [dropdown_options, chartData]);

	const [activeMonth, setActiveMonth] = React.useState(
		availableOptions[0]?.value || chartData[0]?.month || "january"
	);

	const activeIndex = React.useMemo(
		() => chartData.findIndex((item) => item.month === activeMonth),
		[activeMonth, chartData]
	);

	return (
		<Card data-chart={id} className="flex flex-col">
			<ChartStyle id={id} config={chartConfig} />
			<CardHeader className="flex-row items-start space-y-0 pb-0">
				<Select value={activeMonth} onValueChange={setActiveMonth}>
					<SelectTrigger
						className="ml-auto h-7 w-[130px] rounded-lg pl-2.5"
						aria-label="Select a value">
						<SelectValue
							placeholder={availableOptions[0]?.label || "Select option"}
						/>
					</SelectTrigger>
					<SelectContent align="end" className="rounded-xl">
						{availableOptions.map((option) => (
							<SelectItem
								key={option.value}
								value={option.value}
								className="rounded-lg [&_span]:flex">
								<div className="flex items-center gap-2 text-xs">
									<span
										className="flex h-3 w-3 shrink-0 rounded-xs"
										style={{
											backgroundColor: `var(--chart-${
												(availableOptions.indexOf(option) % 5) + 1
											})`,
										}}
									/>
									{option.label}
								</div>
							</SelectItem>
						))}
					</SelectContent>
				</Select>
			</CardHeader>
			<CardContent className="flex flex-1 justify-center pb-0">
				<ChartContainer
					id={id}
					config={chartConfig}
					className="mx-auto aspect-square w-full max-w-[300px]">
					<PieChart>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Pie
							data={chartData}
							dataKey="desktop"
							nameKey="month"
							innerRadius={60}
							strokeWidth={5}
							activeIndex={activeIndex}
							activeShape={({
								outerRadius = 0,
								...props
							}: PieSectorDataItem) => (
								<g>
									<Sector {...props} outerRadius={outerRadius + 10} />
									<Sector
										{...props}
										outerRadius={outerRadius + 25}
										innerRadius={outerRadius + 12}
									/>
								</g>
							)}>
							<Label
								content={({ viewBox }) => {
									if (viewBox && "cx" in viewBox && "cy" in viewBox) {
										const activeData = chartData[activeIndex] || chartData[0];
										return (
											<text
												x={viewBox.cx}
												y={viewBox.cy}
												textAnchor="middle"
												dominantBaseline="middle">
												<tspan
													x={viewBox.cx}
													y={viewBox.cy}
													className="fill-foreground text-3xl font-bold">
													{activeData?.desktop?.toLocaleString() || "0"}
												</tspan>
												<tspan
													x={viewBox.cx}
													y={(viewBox.cy || 0) + 24}
													className="fill-muted-foreground">
													{activeData?.month || "Data"}
												</tspan>
											</text>
										);
									}
								}}
							/>
						</Pie>
					</PieChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnPieInteractive;
