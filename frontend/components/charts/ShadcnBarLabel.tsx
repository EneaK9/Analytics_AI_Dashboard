import React from "react";
import {
	Bar,
	BarChart,
	XAxis,
	YAxis,
	ResponsiveContainer,
	Cell,
} from "recharts";
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

interface ShadcnBarLabelProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
	height?: number;
}

const ShadcnBarLabel: React.FC<ShadcnBarLabelProps> = ({
	title = "Bar Chart - Label",
	description = "January - June 2024",
	data = [],
	dataKey = "value",
	nameKey = "name",
	height = 300,
}) => {
	// Process real data with labels
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
						Math.floor(Math.random() * 400) + 50;

					return {
						name: String(nameValue).slice(0, 6),
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

	// Custom label component
	const renderLabel = (props: any) => {
		const { x, y, width, value } = props;
		return (
			<text
				x={x + width / 2}
				y={y - 4}
				fill="hsl(var(--foreground))"
				textAnchor="middle"
				dy={0}
				fontSize={12}
				fontWeight={500}>
				{value}
			</text>
		);
	};

	return (
		<Card className="w-full">
			
			<CardContent>
				<div className="h-[300px] w-full">
					<ResponsiveContainer width="100%" height="100%">
						<BarChart
							data={chartData}
							margin={{
								top: 30,
								right: 30,
								left: 20,
								bottom: 20,
							}}>
							<XAxis
								dataKey="name"
								axisLine={false}
								tickLine={false}
								fontSize={12}
							/>
							<YAxis hide />
							<ChartTooltip
								content={<ChartTooltipContent />}
								cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
							/>
							<Bar
								dataKey="desktop"
								fill="#3b82f6"
								radius={[4, 4, 0, 0]}
								label={renderLabel}
							/>
						</BarChart>
					</ResponsiveContainer>
				</div>

				{/* Trending indicator */}
				
			</CardContent>
		</Card>
	);
};

export default ShadcnBarLabel;
