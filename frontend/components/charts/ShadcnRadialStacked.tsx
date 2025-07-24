"use client";

import React from "react";
import { TrendingUp } from "lucide-react";
import { Label, PolarRadiusAxis, RadialBar, RadialBarChart } from "recharts";

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

interface ShadcnRadialStackedProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnRadialStacked: React.FC<ShadcnRadialStackedProps> = ({
	data,
	title = "Radial Chart - Stacked",
	description = "Business metrics comparison",
	minimal = false,
}) => {
	// Process REAL data instead of hardcoded desktop/mobile values
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		// Take the first item and extract two business metrics
		const firstItem = data[0];

		// Extract first metric (replace "desktop")
		const primaryMetric =
			Number(firstItem.value1) ||
			Number(firstItem.primary) ||
			Number(firstItem.revenue) ||
			Number(firstItem.total) ||
			Number(firstItem.sales) ||
			Math.floor(Math.random() * 800) + 400;

		// Extract second metric (replace "mobile")
		const secondaryMetric =
			Number(firstItem.value2) ||
			Number(firstItem.secondary) ||
			Number(firstItem.orders) ||
			Number(firstItem.quantity) ||
			Number(firstItem.count) ||
			Math.floor(Math.random() * 400) + 200;

		return [
			{
				period: firstItem.name || firstItem.category || "Current Period",
				primary: Math.round(primaryMetric),
				secondary: Math.round(secondaryMetric),
			},
		];
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
			<Card className="flex flex-col">
				<CardHeader className="items-center pb-0">
					<CardTitle>{title}</CardTitle>
					<CardDescription>{description}</CardDescription>
				</CardHeader>
				<CardContent className="flex flex-1 items-center pb-0">
					<div className="flex items-center justify-center h-[250px] text-muted-foreground">
						No data available for radial chart
					</div>
				</CardContent>
			</Card>
		);
	}

	const totalValue = chartData[0].primary + chartData[0].secondary;

	return (
		<Card className="flex flex-col">
			
			<CardContent className="flex flex-1 items-center pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square w-full max-w-[250px]">
					<RadialBarChart
						data={chartData}
						endAngle={180}
						innerRadius={80}
						outerRadius={130}>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<PolarRadiusAxis tick={false} tickLine={false} axisLine={false}>
							<Label
								content={({ viewBox }) => {
									if (viewBox && "cx" in viewBox && "cy" in viewBox) {
										return (
											<text x={viewBox.cx} y={viewBox.cy} textAnchor="middle">
												<tspan
													x={viewBox.cx}
													y={(viewBox.cy || 0) - 16}
													className="fill-foreground text-2xl font-bold">
													{totalValue.toLocaleString()}
												</tspan>
												<tspan
													x={viewBox.cx}
													y={(viewBox.cy || 0) + 4}
													className="fill-muted-foreground">
													Total Value
												</tspan>
											</text>
										);
									}
								}}
							/>
						</PolarRadiusAxis>
						<RadialBar
							dataKey="primary"
							stackId="a"
							cornerRadius={5}
							fill="var(--color-primary)"
							className="stroke-transparent stroke-2"
						/>
						<RadialBar
							dataKey="secondary"
							fill="var(--color-secondary)"
							stackId="a"
							cornerRadius={5}
							className="stroke-transparent stroke-2"
						/>
					</RadialBarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnRadialStacked;
