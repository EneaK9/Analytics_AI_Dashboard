"use client";
import React from "react";
import { TrendingUp } from "lucide-react";
import {
	Bar,
	BarChart,
	CartesianGrid,
	LabelList,
	XAxis,
	YAxis,
} from "recharts";

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

interface ShadcnBarLabelCustomProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnBarLabelCustom: React.FC<ShadcnBarLabelCustomProps> = ({
	data,
	title = "Bar Chart - Custom Label",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Use real data instead of hardcoded chartData
	const processedData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		return data.slice(0, 6).map((item, index) => {
			const month =
				item.name || item.month || item.category || `Item ${index + 1}`;
			const value =
				item.value || item.desktop || item.amount || item.total || 0;

			return {
				month: month.toString().slice(0, 10), // Limit length
				value: Number(value) || 0,
			};
		});
	}, [data]);

	// Generate dynamic chart config from real data
	const chartConfig = React.useMemo(() => {
		return {
			value: {
				label: "Value",
				color: "var(--chart-2)",
			},
			label: {
				color: "var(--background)",
			},
		};
	}, []);

	// Don't render if no data
	if (processedData.length === 0) {
		return (
			<Card>
				<CardHeader>
					{!minimal && (
						<>
							<CardTitle>{title}</CardTitle>
							<CardDescription>{description}</CardDescription>
						</>
					)}
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
			<CardHeader>
				{!minimal && (
					<>
						<CardTitle>{title}</CardTitle>
						<CardDescription>{description}</CardDescription>
					</>
				)}
			</CardHeader>
			<CardContent>
				<ChartContainer config={chartConfig}>
					<BarChart
						accessibilityLayer
						data={processedData}
						layout="vertical"
						margin={{
							right: 16,
						}}>
						<CartesianGrid horizontal={false} />
						<YAxis
							dataKey="month"
							type="category"
							tickLine={false}
							tickMargin={10}
							axisLine={false}
							tickFormatter={(value) => value.slice(0, 3)}
							hide
						/>
						<XAxis dataKey="value" type="number" hide />
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent indicator="line" />}
						/>
						<Bar
							dataKey="value"
							layout="vertical"
							fill="var(--chart-2)"
							radius={4}>
							<LabelList
								dataKey="month"
								position="insideLeft"
								offset={8}
								className="fill-(--color-label)"
								fontSize={12}
							/>
							<LabelList
								dataKey="value"
								position="right"
								offset={8}
								className="fill-foreground"
								fontSize={12}
							/>
						</Bar>
					</BarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnBarLabelCustom;
