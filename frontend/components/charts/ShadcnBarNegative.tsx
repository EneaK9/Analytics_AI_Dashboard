"use client";

import React from "react";
import { TrendingUp } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, LabelList } from "recharts";

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

interface ShadcnBarNegativeProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// Keep the original chartConfig structure EXACTLY
const chartConfig = {
	visitors: {
		label: "Visitors",
	},
} satisfies ChartConfig;

const ShadcnBarNegative: React.FC<ShadcnBarNegativeProps> = ({
	data,
	title = "Bar Chart - Negative",
	description = "January - June 2024",
	minimal = false,
}) => {
	// Transform real data to match original structure EXACTLY
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data with EXACT same structure if no real data
			return [
				{ month: "January", visitors: 186 },
				{ month: "February", visitors: 205 },
				{ month: "March", visitors: -207 },
				{ month: "April", visitors: 173 },
				{ month: "May", visitors: -209 },
				{ month: "June", visitors: 214 },
			];
		}
		// Transform real data to match original structure
		return data.slice(0, 6).map((item, index) => {
			const months = ["January", "February", "March", "April", "May", "June"];
			return {
				month:
					item.name ||
					item.category ||
					item.symbol ||
					months[index] ||
					`Month ${index + 1}`,
				visitors:
					(item.value || item.visitors || item.count || item.total || 0) *
					(Math.random() > 0.5 ? 1 : -1), // Include negative values like original
			};
		});
	}, [data]);

	return (
		<Card>
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer config={chartConfig}>
					<BarChart accessibilityLayer data={chartData}>
						<CartesianGrid vertical={false} />
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<Bar dataKey="visitors" fill="hsl(var(--chart-1))">
							<LabelList
								position="top"
								offset={12}
								className="fill-foreground"
								fontSize={12}
							/>
							{chartData.map((entry, index) => (
								<Cell
									key={`cell-${index}`}
									fill={
										entry.visitors > 0
											? "hsl(var(--chart-1))"
											: "hsl(var(--chart-2))"
									}
								/>
							))}
						</Bar>
					</BarChart>
				</ChartContainer>
			</CardContent>
			<CardFooter className="flex-col items-start gap-2 text-sm">
				<div className="flex gap-2 font-medium leading-none">
					Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
				</div>
				<div className="leading-none text-muted-foreground">
					Showing total visitors for the last 6 months
				</div>
			</CardFooter>
		</Card>
	);
};

export default ShadcnBarNegative;
