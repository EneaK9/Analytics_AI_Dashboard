"use client";

import React from "react";
import { Pie, PieChart } from "recharts";

import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	ChartConfig,
	ChartContainer,
	ChartLegend,
	ChartLegendContent,
} from "@/components/ui/chart";

interface ShadcnPieLegendProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnPieLegend: React.FC<ShadcnPieLegendProps> = ({
	data,
	title = "Pie Chart - Legend",
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

	if (chartData.length === 0) {
		return (
			<Card className="flex flex-col">
				<CardContent className="flex-1 pb-0">
					<div className="flex items-center justify-center h-[300px] text-muted-foreground">
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
					className="mx-auto aspect-square max-h-[300px]">
					<PieChart>
						<Pie data={chartData} dataKey="value" />
						<ChartLegend
							content={<ChartLegendContent nameKey="name" />}
							className="-translate-y-2 flex-wrap gap-2 *:basis-1/4 *:justify-center"
						/>
					</PieChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnPieLegend;
