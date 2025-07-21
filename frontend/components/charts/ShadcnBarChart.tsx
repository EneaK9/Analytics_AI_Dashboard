"use client";

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

interface ShadcnBarChartProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	xAxisKey?: string;
	height?: number;
	color?: string;
	minimal?: boolean;
}

const ShadcnBarChart: React.FC<ShadcnBarChartProps> = ({
	title = "Bar Chart",
	description = "January - June 2024",
	data = [],
	dataKey = "value",
	xAxisKey = "name",
	height = 160,
	color = "#8884d8",
	minimal = false,
}) => {
	// Process real data into shadcn format
	const chartData =
		data && data.length > 0
			? data.slice(0, 12).map((item, index) => {
					const monthValue =
						item[xAxisKey] ||
						item["month"] ||
						item["symbol"] ||
						item["name"] ||
						item["category"] ||
						`Month ${index + 1}`;

					const desktop =
						Number(item[dataKey]) ||
						Number(item["value"]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						0;

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

	const chartContent = (
		<ChartContainer config={chartConfig} className="h-full w-full">
			<BarChart accessibilityLayer data={chartData}>
				<CartesianGrid vertical={false} />
				<XAxis
					dataKey="month"
					tickLine={false}
					tickMargin={10}
					axisLine={false}
					tickFormatter={(value) => value.slice(0, 3)}
				/>
				<ChartTooltip
					cursor={false}
					content={<ChartTooltipContent hideLabel />}
				/>
				<Bar dataKey="desktop" fill="var(--color-desktop)" radius={8} />
			</BarChart>
		</ChartContainer>
	);

	if (minimal) {
		return chartContent;
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>{chartContent}</CardContent>
		</Card>
	);
};

export default ShadcnBarChart;
