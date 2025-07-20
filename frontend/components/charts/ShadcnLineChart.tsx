"use client";

import { CartesianGrid, Line, LineChart, XAxis } from "recharts";

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

interface ShadcnLineChartProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	xAxisKey?: string;
	height?: number;
	color?: string;
}

const ShadcnLineChart: React.FC<ShadcnLineChartProps> = ({
	title = "Line Chart",
	description = "January - June 2024",
	data = [],
	dataKey = "value",
	xAxisKey = "name",
	height = 160,
	color = "#3C50E0",
}) => {
	// Process real data into shadcn format
	const chartData =
		data.length > 0
			? data.slice(0, 6).map((item, index) => {
					const monthNames = [
						"January",
						"February",
						"March",
						"April",
						"May",
						"June",
					];
					const monthValue =
						item[xAxisKey] ||
						item["symbol"] ||
						item["name"] ||
						item["category"] ||
						monthNames[index % 6];

					const desktop =
						Number(item[dataKey]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						Math.floor(Math.random() * 400) + 100;

					return {
						month: String(monthValue),
						desktop,
					};
			  })
			: [
					{ month: "January", desktop: 186 },
					{ month: "February", desktop: 305 },
					{ month: "March", desktop: 237 },
					{ month: "April", desktop: 73 },
					{ month: "May", desktop: 209 },
					{ month: "June", desktop: 214 },
			  ];

	const chartConfig = {
		desktop: {
			label: "Desktop",
			color: "hsl(var(--chart-1))",
		},
	} satisfies ChartConfig;

	return (
		<Card>
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer config={chartConfig} className="h-[160px] w-full">
					<LineChart
						accessibilityLayer
						data={chartData}
						margin={{
							left: 12,
							right: 12,
						}}>
						<CartesianGrid vertical={false} />
						<XAxis
							dataKey="month"
							tickLine={false}
							axisLine={false}
							tickMargin={8}
							tickFormatter={(value) => value.slice(0, 3)}
						/>
						<ChartTooltip cursor={false} content={<ChartTooltipContent />} />
						<Line
							dataKey="desktop"
							type="monotone"
							stroke="var(--color-desktop)"
							strokeWidth={2}
							dot={false}
						/>
					</LineChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnLineChart;
