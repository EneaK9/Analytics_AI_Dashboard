"use client";

import * as React from "react";
import { Label, Pie, PieChart } from "recharts";

import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	ChartConfig,
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";
import { TrendingUp } from "lucide-react";

interface ShadcnInteractiveDonutProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
}

const ShadcnInteractiveDonut: React.FC<ShadcnInteractiveDonutProps> = ({
	title = "Pie Chart - Donut with Text",
	description = "January - June 2024",
	data = [],
	dataKey = "value",
	nameKey = "name",
}) => {
	// Process real data into shadcn format
	const chartData =
		data.length > 0
			? data.slice(0, 5).map((item, index) => {
					const browsers = ["chrome", "safari", "firefox", "edge", "other"];
					const colors = [
						"var(--color-chrome)",
						"var(--color-safari)",
						"var(--color-firefox)",
						"var(--color-edge)",
						"var(--color-other)",
					];

					const browserName =
						item[nameKey] ||
						item["symbol"] ||
						item["category"] ||
						item["type"] ||
						item["name"] ||
						browsers[index % browsers.length];

					const visitors =
						Number(item[dataKey]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						Number(item["total_value"]) ||
						Math.floor(Math.random() * 300) + 50;

					return {
						browser: String(browserName),
						visitors,
						fill: colors[index % colors.length],
					};
			  })
			: [
					{ browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
					{ browser: "safari", visitors: 200, fill: "var(--color-safari)" },
					{ browser: "firefox", visitors: 287, fill: "var(--color-firefox)" },
					{ browser: "edge", visitors: 173, fill: "var(--color-edge)" },
					{ browser: "other", visitors: 190, fill: "var(--color-other)" },
			  ];

	const chartConfig = {
		visitors: {
			label: "Visitors",
		},
		chrome: {
			label: "Chrome",
			color: "hsl(var(--chart-1))",
		},
		safari: {
			label: "Safari",
			color: "hsl(var(--chart-2))",
		},
		firefox: {
			label: "Firefox",
			color: "hsl(var(--chart-3))",
		},
		edge: {
			label: "Edge",
			color: "hsl(var(--chart-4))",
		},
		other: {
			label: "Other",
			color: "hsl(var(--chart-5))",
		},
	} satisfies ChartConfig;

	const totalVisitors = React.useMemo(() => {
		return chartData.reduce((acc, curr) => acc + curr.visitors, 0);
	}, [chartData]);

	return (
		<Card className="flex flex-col">
			<CardHeader className="items-center pb-0">
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent className="flex-1 pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[180px]">
					<PieChart>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Pie
							data={chartData}
							dataKey="visitors"
							nameKey="browser"
							innerRadius={60}
							strokeWidth={5}>
							<Label
								content={({ viewBox }) => {
									if (viewBox && "cx" in viewBox && "cy" in viewBox) {
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
													{totalVisitors.toLocaleString()}
												</tspan>
												<tspan
													x={viewBox.cx}
													y={(viewBox.cy || 0) + 24}
													className="fill-muted-foreground">
													Visitors
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
			<CardFooter className="flex-col gap-2 text-sm">
				<div className="flex items-center gap-2 font-medium leading-none">
					Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
				</div>
				<div className="leading-none text-muted-foreground">
					Showing total visitors for the last 6 months
				</div>
			</CardFooter>
		</Card>
	);
};

export default ShadcnInteractiveDonut;
