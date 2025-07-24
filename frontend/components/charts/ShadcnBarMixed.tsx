import React from "react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
	type ChartConfig,
} from "@/components/ui/chart";

interface ShadcnBarMixedProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

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

const ShadcnBarMixed: React.FC<ShadcnBarMixedProps> = ({
	data,
	title = "Bar Chart - Mixed",
	description = "Mixed orientation bar chart",
	minimal = false,
}) => {
	// Transform data to match Shadcn format with fill colors
	const chartData = data.slice(0, 5).map((item, index) => {
		const browsers = ["chrome", "safari", "firefox", "edge", "other"];
		const browser = browsers[index];
		return {
			browser,
			visitors: item.value || item.visitors || 0,
			fill: `hsl(var(--chart-${index + 1}))`,
		};
	});

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
						left: 0,
					}}>
					<YAxis
						dataKey="browser"
						type="category"
						tickLine={false}
						tickMargin={10}
						axisLine={false}
						tickFormatter={(value) =>
							chartConfig[value as keyof typeof chartConfig]?.label
						}
					/>
					<XAxis dataKey="visitors" type="number" hide />
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Bar dataKey="visitors" layout="vertical" radius={5} />
				</BarChart>
			</ChartContainer>
		</div>
	);
};

export default ShadcnBarMixed;
