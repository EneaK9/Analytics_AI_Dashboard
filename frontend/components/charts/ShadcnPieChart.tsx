"use client";

import React from "react";
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

interface ShadcnPieChartProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnPieChart: React.FC<ShadcnPieChartProps> = ({
	data,
	title = "Pie Chart",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Transform real data to match original structure with dynamic config
	const { chartData, chartConfig } = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data with EXACT same structure if no real data
			const fallbackData = [
				{ browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
				{ browser: "safari", visitors: 200, fill: "var(--color-safari)" },
				{ browser: "firefox", visitors: 187, fill: "var(--color-firefox)" },
				{ browser: "edge", visitors: 173, fill: "var(--color-edge)" },
				{ browser: "other", visitors: 90, fill: "var(--color-other)" },
			];
			const fallbackConfig = {
				visitors: { label: "Visitors" },
				chrome: { label: "Chrome", color: "var(--chart-1)" },
				safari: { label: "Safari", color: "var(--chart-2)" },
				firefox: { label: "Firefox", color: "var(--chart-3)" },
				edge: { label: "Edge", color: "var(--chart-4)" },
				other: { label: "Other", color: "var(--chart-5)" },
			} satisfies ChartConfig;
			return { chartData: fallbackData, chartConfig: fallbackConfig };
		}

		// Transform real data to match original structure
		const processedData = data.slice(0, 5).map((item, index) => {
			const browserName = (
				item.name ||
				item.category ||
				item.symbol ||
				`item${index + 1}`
			).toLowerCase();
			return {
				browser: browserName,
				visitors: item.value || item.visitors || item.count || item.total || 0,
				fill: `var(--color-chart-${(index % 5) + 1})`,
			};
		});

		// Generate dynamic config based on real data
		const dynamicConfig: ChartConfig = {
			visitors: { label: "Visitors" },
		};

		processedData.forEach((item, index) => {
			dynamicConfig[item.browser] = {
				label: item.browser.charAt(0).toUpperCase() + item.browser.slice(1),
				color: `var(--chart-${(index % 5) + 1})`,
			};
		});

		return { chartData: processedData, chartConfig: dynamicConfig };
	}, [data]);

	return (
		<Card className="flex flex-col">
			
			<CardContent className="flex-1 pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<PieChart>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Pie data={chartData} dataKey="visitors" nameKey="browser" />
					</PieChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
};

export default ShadcnPieChart;
