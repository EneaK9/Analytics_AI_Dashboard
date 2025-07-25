"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react";
import { RadialBar, RadialBarChart } from "recharts";

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

export const description = "A radial chart";

// Keep the original chartConfig structure EXACTLY
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

interface ShadcnRadialChartProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	ai_labels?: any;
}

export function ShadcnRadialChart({
	data = [],
	title,
	description,
	minimal,
	ai_labels,
}: ShadcnRadialChartProps) {
	// Transform real data to match original structure EXACTLY
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data with EXACT same structure
			return [
				{ browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
				{ browser: "safari", visitors: 200, fill: "var(--color-safari)" },
				{ browser: "firefox", visitors: 187, fill: "var(--color-firefox)" },
				{ browser: "edge", visitors: 173, fill: "var(--color-edge)" },
				{ browser: "other", visitors: 90, fill: "var(--color-other)" },
			];
		}

		// Transform real data to match original structure
		return data.slice(0, 5).map((item, index) => {
			const browserName = (
				item.name ||
				item.category ||
				item.symbol ||
				`browser${index + 1}`
			).toLowerCase();
			return {
				browser: browserName,
				visitors: item.value || item.visitors || item.count || item.total || 0,
				fill: `var(--color-chart-${(index % 5) + 1})`,
			};
		});
	}, [data]);

	return (
		<Card className="flex flex-col">
			
			<CardContent className="flex-1 pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<RadialBarChart data={chartData} innerRadius={30} outerRadius={110}>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel nameKey="browser" />}
						/>
						<RadialBar dataKey="visitors" background />
					</RadialBarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
}
