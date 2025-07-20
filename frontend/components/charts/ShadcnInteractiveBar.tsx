"use client";

import * as React from "react";
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";

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
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";

interface ShadcnInteractiveBarProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey1?: string;
	dataKey2?: string;
	xAxisKey?: string;
}

const ShadcnInteractiveBar: React.FC<ShadcnInteractiveBarProps> = ({
	title = "Bar Chart - Interactive",
	description = "Showing total visitors for the last 3 months",
	data = [],
	dataKey1 = "value1",
	dataKey2 = "value2",
	xAxisKey = "name",
}) => {
	// Process real data into shadcn format
	const chartData =
		data.length > 0
			? data.slice(0, 12).map((item, index) => {
					const dateValue =
						item[xAxisKey] ||
						item["date"] ||
						item["symbol"] ||
						item["name"] ||
						`2024-04-${String(index + 1).padStart(2, "0")}`;

					const desktop =
						Number(item[dataKey1]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						Math.floor(Math.random() * 400) + 100;

					const mobile =
						Number(item[dataKey2]) ||
						Number(item["total_value"]) ||
						Number(item["volume"]) ||
						Math.floor(Math.random() * 300) + 80;

					return {
						date: String(dateValue),
						desktop,
						mobile,
					};
			  })
			: [
					{ date: "2024-04-01", desktop: 222, mobile: 150 },
					{ date: "2024-04-02", desktop: 97, mobile: 180 },
					{ date: "2024-04-03", desktop: 167, mobile: 120 },
					{ date: "2024-04-04", desktop: 242, mobile: 260 },
					{ date: "2024-04-05", desktop: 373, mobile: 290 },
					{ date: "2024-04-06", desktop: 301, mobile: 340 },
			  ];

	const chartConfig = {
		views: {
			label: "Page Views",
		},
		desktop: {
			label: "Desktop",
			color: "hsl(var(--chart-1))",
		},
		mobile: {
			label: "Mobile",
			color: "hsl(var(--chart-2))",
		},
	} satisfies ChartConfig;

	const [activeChart, setActiveChart] =
		React.useState<keyof typeof chartConfig>("desktop");

	const total = React.useMemo(
		() => ({
			desktop: chartData.reduce((acc, curr) => acc + curr.desktop, 0),
			mobile: chartData.reduce((acc, curr) => acc + curr.mobile, 0),
		}),
		[chartData]
	);

	return (
		<Card>
			<CardHeader className="flex flex-col items-stretch space-y-0 border-b p-0 sm:flex-row">
				<div className="flex flex-1 flex-col justify-center gap-1 px-6 py-5 sm:py-6">
					<CardTitle>{title}</CardTitle>
					<CardDescription>{description}</CardDescription>
				</div>
				<div className="flex">
					{["desktop", "mobile"].map((key) => {
						const chart = key as keyof typeof chartConfig;
						return (
							<button
								key={chart}
								data-active={activeChart === chart}
								className="relative z-30 flex flex-1 flex-col justify-center gap-1 border-t px-6 py-4 text-left even:border-l data-[active=true]:bg-muted/50 sm:border-l sm:border-t-0 sm:px-8 sm:py-6"
								onClick={() => setActiveChart(chart)}>
								<span className="text-xs text-muted-foreground">
									{chartConfig[chart].label}
								</span>
								<span className="text-lg font-bold leading-none sm:text-3xl">
									{total[key as keyof typeof total].toLocaleString()}
								</span>
							</button>
						);
					})}
				</div>
			</CardHeader>
			<CardContent className="px-2 sm:p-6">
				<ChartContainer
					config={chartConfig}
					className="aspect-auto h-[180px] w-full">
					<BarChart
						accessibilityLayer
						data={chartData}
						margin={{
							left: 12,
							right: 12,
						}}>
						<CartesianGrid vertical={false} />
						<XAxis
							dataKey="date"
							tickLine={false}
							axisLine={false}
							tickMargin={8}
							minTickGap={32}
							tickFormatter={(value) => {
								const date = new Date(value);
								return date.toLocaleDateString("en-US", {
									month: "short",
									day: "numeric",
								});
							}}
						/>
						<ChartTooltip
							content={
								<ChartTooltipContent
									className="w-[150px]"
									nameKey="views"
									labelFormatter={(value) => {
										return new Date(value).toLocaleDateString("en-US", {
											month: "short",
											day: "numeric",
											year: "numeric",
										});
									}}
								/>
							}
						/>
						<Bar dataKey={activeChart} fill={`var(--color-${activeChart})`} />
					</BarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnInteractiveBar;
