import React from "react";
import { Pie, PieChart } from "recharts";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
	type ChartConfig,
} from "@/components/ui/chart";

interface ShadcnPieChartLabelProps {
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

const ShadcnPieChartLabel: React.FC<ShadcnPieChartLabelProps> = ({
	data,
	title = "Pie Chart - Label",
	description = "A pie chart with labels",
	minimal = false,
}) => {
	// Transform data to match Shadcn format with proper colors
	const browsers = ["chrome", "safari", "firefox", "edge", "other"];
	const chartData = data.slice(0, 5).map((item, index) => {
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
			<ChartContainer
				config={chartConfig}
				className="[&_.recharts-pie-label-text]:fill-foreground mx-auto aspect-square max-h-[250px] h-full w-full">
				<PieChart>
					<ChartTooltip content={<ChartTooltipContent hideLabel />} />
					<Pie data={chartData} dataKey="visitors" label nameKey="browser" />
				</PieChart>
			</ChartContainer>
		</div>
	);
};

export default ShadcnPieChartLabel;
