import React from "react";
import { Bar, BarChart, XAxis, YAxis, ResponsiveContainer } from "recharts";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";

interface ShadcnBarHorizontalProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
	height?: number;
}

const ShadcnBarHorizontal: React.FC<ShadcnBarHorizontalProps> = ({
	title = "Bar Chart - Horizontal",
	description = "January - June 2024",
	data = [],
	dataKey = "value",
	nameKey = "name",
	height = 300,
}) => {
	// Process real data into horizontal bar format
	const chartData =
		data.length > 0
			? data.slice(0, 6).map((item, index) => {
					const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
					const nameValue =
						item[nameKey] ||
						item["symbol"] ||
						item["name"] ||
						item["category"] ||
						months[index % months.length];

					const desktop =
						Number(item[dataKey]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						Number(item["total_value"]) ||
						Math.floor(Math.random() * 400) + 100;

					return {
						name: String(nameValue).slice(0, 8), // Keep names short
						desktop,
					};
			  })
			: [
					{ name: "Jan", desktop: 186 },
					{ name: "Feb", desktop: 305 },
					{ name: "Mar", desktop: 237 },
					{ name: "Apr", desktop: 73 },
					{ name: "May", desktop: 209 },
					{ name: "Jun", desktop: 214 },
			  ];

	const chartConfig = {
		desktop: {
			label: "Desktop",
			color: "#3b82f6",
		},
	};

	return (
		<Card className="w-full">
			<CardHeader className="pb-4">
				<CardTitle className="text-lg font-semibold">{title}</CardTitle>
				<CardDescription className="text-sm text-muted-foreground">
					{description}
				</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="h-[300px] w-full">
					<ResponsiveContainer width="100%" height="100%">
						<BarChart
							data={chartData}
							layout="horizontal"
							margin={{
								left: 40,
								right: 20,
								top: 20,
								bottom: 20,
							}}>
							<XAxis type="number" axisLine={false} tickLine={false} />
							<YAxis
								dataKey="name"
								type="category"
								axisLine={false}
								tickLine={false}
								width={40}
								fontSize={12}
							/>
							<ChartTooltip
								content={<ChartTooltipContent />}
								cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
							/>
							<Bar
								dataKey="desktop"
								fill="#3b82f6"
								radius={[0, 4, 4, 0]}
								maxBarSize={40}
							/>
						</BarChart>
					</ResponsiveContainer>
				</div>

				{/* Trending indicator */}
				
			</CardContent>
		</Card>
	);
};

export default ShadcnBarHorizontal;
