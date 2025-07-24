"use client";

import { TrendingUp } from "lucide-react";
import { Pie, PieChart } from "recharts";

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

interface ShadcnPieSimpleProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const chartData = [
	{ browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
	{ browser: "safari", visitors: 200, fill: "var(--color-safari)" },
	{ browser: "firefox", visitors: 187, fill: "var(--color-firefox)" },
	{ browser: "edge", visitors: 173, fill: "var(--color-edge)" },
	{ browser: "other", visitors: 90, fill: "var(--color-other)" },
];

const chartConfig = {
	visitors: {
		label: "Visitors",
	},
	chrome: {
		label: "Chrome",
		color: "var(--chart-1)",
	},
	safari: {
		label: "Safari",
		color: "var(--chart-2)",
	},
	firefox: {
		label: "Firefox",
		color: "var(--chart-3)",
	},
	edge: {
		label: "Edge",
		color: "var(--chart-4)",
	},
	other: {
		label: "Other",
		color: "var(--chart-5)",
	},
} satisfies ChartConfig;

const ShadcnPieSimple: React.FC<ShadcnPieSimpleProps> = ({
	data,
	title = "Pie Chart",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Use real data instead of hardcoded chartData
	const processedData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		const browsers = ["chrome", "safari", "firefox", "edge", "other"];
		return data.slice(0, 5).map((item, index) => {
			const browser = browsers[index] || `browser${index}`;
			return {
				browser,
				visitors: item.value || item.visitors || item.desktop || 0,
				fill: `var(--chart-${(index % 5) + 1})`,
			};
		});
	}, [data]);

	// Don't render if no data
	if (processedData.length === 0) {
		return (
			<Card className="flex flex-col">
				<CardHeader className="items-center pb-0">
					<CardTitle>{title}</CardTitle>
					<CardDescription>{description}</CardDescription>
				</CardHeader>
				<CardContent className="flex-1 pb-0">
					<div className="flex items-center justify-center h-[250px] text-muted-foreground">
						No data available for pie chart
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card className="flex flex-col">
			<CardHeader className="items-center pb-0">
				{!minimal && (
					<>
						<CardTitle>{title}</CardTitle>
						<CardDescription>{description}</CardDescription>
					</>
				)}
			</CardHeader>
			<CardContent className="flex-1 pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<PieChart>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Pie data={processedData} dataKey="visitors" nameKey="browser" />
					</PieChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnPieSimple;
