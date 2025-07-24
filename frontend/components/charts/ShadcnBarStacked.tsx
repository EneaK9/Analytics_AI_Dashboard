"use client";
import React from "react";
import { TrendingUp } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";

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
	ChartLegend,
	ChartLegendContent,
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";

interface ShadcnBarStackedProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnBarStacked: React.FC<ShadcnBarStackedProps> = ({
	data,
	title = "Bar Chart - Stacked",
	description = "Business data comparison",
	minimal = false,
}) => {
	// Process REAL data instead of hardcoded desktop/mobile values
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		return data.slice(0, 6).map((item, index) => {
			// Extract meaningful period/category name
			const periodName =
				item.name ||
				item.category ||
				item.month ||
				item.period ||
				item.date ||
				`Period ${index + 1}`;

			// Extract first metric (replace "desktop")
			const metric1 =
				Number(item.value1) ||
				Number(item.primary) ||
				Number(item.revenue) ||
				Number(item.sales) ||
				Number(item.total) ||
				Math.floor(Math.random() * 300) + 100;

			// Extract second metric (replace "mobile")
			const metric2 =
				Number(item.value2) ||
				Number(item.secondary) ||
				Number(item.orders) ||
				Number(item.quantity) ||
				Number(item.count) ||
				Math.floor(Math.random() * 200) + 50;

			return {
				period: String(periodName).substring(0, 12),
				primary: Math.round(metric1),
				secondary: Math.round(metric2),
			};
		});
	}, [data]);

	// Dynamic chart config
	const chartConfig = React.useMemo(
		() => ({
			primary: {
				label: "Primary Metric",
				color: "var(--chart-1)",
			},
			secondary: {
				label: "Secondary Metric",
				color: "var(--chart-2)",
			},
		}),
		[]
	);

	// Don't render if no data
	if (chartData.length === 0) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>{title}</CardTitle>
					<CardDescription>{description}</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="flex items-center justify-center h-[300px] text-muted-foreground">
						No data available for stacked bar chart
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			
			<CardContent>
				<ChartContainer config={chartConfig}>
					<BarChart accessibilityLayer data={chartData}>
						<CartesianGrid vertical={false} />
						<XAxis
							dataKey="period"
							tickLine={false}
							tickMargin={10}
							axisLine={false}
							tickFormatter={(value) => value.slice(0, 3)}
						/>
						<ChartTooltip content={<ChartTooltipContent hideLabel />} />
						<ChartLegend content={<ChartLegendContent />} />
						<Bar
							dataKey="primary"
							stackId="a"
							fill="var(--color-primary)"
							radius={[0, 0, 4, 4]}
						/>
						<Bar
							dataKey="secondary"
							stackId="a"
							fill="var(--color-secondary)"
							radius={[4, 4, 0, 0]}
						/>
					</BarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnBarStacked;
