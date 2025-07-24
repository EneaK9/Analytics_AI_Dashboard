"use client";

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

const chartData = [
	{ month: "January", visitors: 186 },
	{ month: "February", visitors: 205 },
	{ month: "March", visitors: -207 },
	{ month: "April", visitors: 173 },
	{ month: "May", visitors: -209 },
	{ month: "June", visitors: 214 },
];

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
	return (
		<Card>
			
			<CardContent>
				<ChartContainer config={chartConfig}>
					<BarChart accessibilityLayer data={chartData}>
						<CartesianGrid vertical={false} />
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel hideIndicator />}
						/>
						<Bar dataKey="visitors">
							<LabelList position="top" dataKey="month" fillOpacity={1} />
							{chartData.map((item) => (
								<Cell
									key={item.month}
									fill={item.visitors > 0 ? "var(--chart-1)" : "var(--chart-2)"}
								/>
							))}
						</Bar>
					</BarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
};

export default ShadcnBarNegative;
