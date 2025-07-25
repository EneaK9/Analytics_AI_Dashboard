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

interface ShadcnPieSimpleProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnPieSimple: React.FC<ShadcnPieSimpleProps> = ({
	data,
	title = "Pie Chart",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Process REAL data only
	const processedData = React.useMemo(() => {
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

		processedData.forEach((item: any, index: number) => {
			config[item.name] = {
				label: item.name,
				color: `var(--chart-${(index % 5) + 1})`,
			};
		});

		return config;
	}, [processedData]);

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
						<Pie data={processedData} dataKey="value" nameKey="name" />
					</PieChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnPieSimple;
