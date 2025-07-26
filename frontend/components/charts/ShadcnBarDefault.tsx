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
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";

interface ShadcnBarDefaultProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnBarDefault: React.FC<ShadcnBarDefaultProps> = ({
	data,
	title = "Bar Chart",
	description = "Business data overview",
	minimal = false,
}) => {
	// Process REAL data instead of hardcoded monthly desktop values
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		return data.slice(0, 6).map((item, index) => {
			// Extract meaningful category/period name
			const categoryName =
				item.name ||
				item.category ||
				item.period ||
				item.month ||
				item.date ||
				`Item ${index + 1}`;

			// Extract meaningful business value (replace "desktop")
			const businessValue =
				Number(item.value) ||
				Number(item.amount) ||
				Number(item.total) ||
				Number(item.count) ||
				Number(item.quantity) ||
				Number(item.revenue) ||
				0; // No more Math.random() fallback

			return {
				category: String(categoryName).substring(0, 12),
				value: Math.round(businessValue),
			};
		});
	}, [data]);

	// Dynamic chart config
	const chartConfig = React.useMemo(
		() => ({
			value: {
				label: "Business Value",
				color: "var(--chart-1)",
			},
		}),
		[]
	);

	// Don't render if no meaningful data
	if (chartData.length === 0 || chartData.every(item => item.value === 0)) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>{title}</CardTitle>
					<CardDescription>{description}</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="flex items-center justify-center h-[300px] text-muted-foreground">
						No data available for bar chart
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
							dataKey="category"
							tickLine={false}
							tickMargin={10}
							axisLine={false}
							tickFormatter={(value) => value.slice(0, 8)}
						/>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Bar dataKey="value" fill="var(--color-value)" radius={8} />
					</BarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
};

export default ShadcnBarDefault;
