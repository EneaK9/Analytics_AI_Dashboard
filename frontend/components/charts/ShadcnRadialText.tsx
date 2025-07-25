"use client";
import React from "react";
import { TrendingUp } from "lucide-react";
import {
	Label,
	PolarGrid,
	PolarRadiusAxis,
	RadialBar,
	RadialBarChart,
} from "recharts";

import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { ChartConfig, ChartContainer } from "@/components/ui/chart";

interface ShadcnRadialTextProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnRadialText: React.FC<ShadcnRadialTextProps> = ({
	data,
	title = "Radial Chart - Text",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Process REAL data only
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return []; // Return empty array if no real data
		}

		// Use first data item for radial text display
		const firstItem = data[0];
		const nameValue =
			firstItem.name || firstItem.category || firstItem.symbol || "Data";
		const dataValue =
			Number(firstItem.value) ||
			Number(firstItem.visitors) ||
			Number(firstItem.count) ||
			Number(firstItem.total) ||
			0;

		return [
			{
				name: nameValue,
				value: dataValue,
				fill: firstItem.fill || "var(--chart-1)",
			},
		];
	}, [data]);

	// Generate dynamic chart config from real data
	const chartConfig = React.useMemo(() => {
		const config: any = {
			value: {
				label: "Value",
			},
		};

		if (chartData.length > 0) {
			config[chartData[0].name] = {
				label: chartData[0].name,
				color: "var(--chart-1)",
			};
		}

		return config;
	}, [chartData]);

	if (chartData.length === 0) {
		return (
			<Card className="flex flex-col">
				<CardContent className="flex-1 pb-0">
					<div className="flex items-center justify-center h-[250px] text-muted-foreground">
						No data available
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card className="flex flex-col">
			<CardContent className="flex-1 pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<RadialBarChart
						data={chartData}
						startAngle={0}
						endAngle={250}
						innerRadius={80}
						outerRadius={110}>
						<PolarGrid
							gridType="circle"
							radialLines={false}
							stroke="none"
							className="first:fill-muted last:fill-background"
							polarRadius={[86, 74]}
						/>
						<RadialBar dataKey="value" background cornerRadius={10} />
						<PolarRadiusAxis tick={false} tickLine={false} axisLine={false}>
							<Label
								content={({ viewBox }) => {
									if (viewBox && "cx" in viewBox && "cy" in viewBox) {
										return (
											<text
												x={viewBox.cx}
												y={viewBox.cy}
												textAnchor="middle"
												dominantBaseline="middle">
												<tspan
													x={viewBox.cx}
													y={viewBox.cy}
													className="fill-foreground text-4xl font-bold">
													{chartData[0].value.toLocaleString()}
												</tspan>
												<tspan
													x={viewBox.cx}
													y={(viewBox.cy || 0) + 24}
													className="fill-muted-foreground">
													Visitors
												</tspan>
											</text>
										);
									}
								}}
							/>
						</PolarRadiusAxis>
					</RadialBarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnRadialText;
