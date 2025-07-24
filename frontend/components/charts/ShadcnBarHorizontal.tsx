import React from "react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
	type ChartConfig,
} from "@/components/ui/chart";

interface ShadcnBarHorizontalProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const chartConfig = {
	desktop: {
		label: "Desktop",
		color: "hsl(var(--chart-1))",
	},
} satisfies ChartConfig;

const ShadcnBarHorizontal: React.FC<ShadcnBarHorizontalProps> = ({
	data,
	title = "Bar Chart - Horizontal",
	description = "Horizontal bar chart",
	minimal = false,
}) => {
	// Transform data to match Shadcn format
	const chartData = data.map((item) => ({
		month: item.name || "Item",
		desktop: item.value || item.desktop || 0,
	}));

	return (
		<div className="w-full h-full">
			{!minimal && (
				<div className="mb-4">
					<h3 className="text-lg font-semibold">{title}</h3>
					<p className="text-sm text-muted-foreground">{description}</p>
				</div>
			)}
			<ChartContainer config={chartConfig} className="h-full w-full">
				<BarChart
					accessibilityLayer
					data={chartData}
					layout="vertical"
					margin={{
						left: -20,
					}}>
					<XAxis type="number" dataKey="desktop" hide />
					<YAxis
						dataKey="month"
						type="category"
						tickLine={false}
						tickMargin={10}
						axisLine={false}
						tickFormatter={(value) => value.slice(0, 3)}
					/>
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Bar dataKey="desktop" fill="hsl(var(--chart-1))" radius={5} />
				</BarChart>
			</ChartContainer>
		</div>
	);
};

export default ShadcnBarHorizontal;
