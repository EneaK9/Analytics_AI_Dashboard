"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react";
import { Label, Pie, PieChart } from "recharts";

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

interface ShadcnPieDonutTextProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnPieDonutText: React.FC<ShadcnPieDonutTextProps> = ({
	data,
	title = "Pie Chart - Donut with Text",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Process REAL data only
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		return data
			.slice(0, 5)
			.map((item: any, index: number) => {
				const nameValue =
					item.name || item.category || item.symbol || `Item ${index + 1}`;
				const dataValue =
					Number(item.value) ||
					Number(item.visitors) ||
					Number(item.count) ||
					Number(item.total) ||
					0;

				return {
					name: nameValue,
					value: dataValue,
					fill: item.fill || `var(--chart-${(index % 5) + 1})`,
				};
			})
			.filter((item) => item.value > 0);
	}, [data]);

	// Generate dynamic chart config from real data
	const chartConfig = React.useMemo(() => {
		const config: any = {
			value: {
				label: "Value",
			},
		};

		chartData.forEach((item: any, index: number) => {
			config[item.name] = {
				label: item.name,
				color: `var(--chart-${(index % 5) + 1})`,
			};
		});

		return config;
	}, [chartData]);

	const totalValue = React.useMemo(() => {
		return chartData.reduce((acc, curr) => acc + curr.value, 0);
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
					<PieChart>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Pie
							data={chartData}
							dataKey="value"
							nameKey="name"
							innerRadius={60}
							strokeWidth={5}>
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
													className="fill-foreground text-3xl font-bold">
													{totalValue.toLocaleString()}
												</tspan>
												<tspan
													x={viewBox.cx}
													y={(viewBox.cy || 0) + 24}
													className="fill-muted-foreground">
													Total
												</tspan>
											</text>
										);
									}
								}}
							/>
						</Pie>
					</PieChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnPieDonutText;
