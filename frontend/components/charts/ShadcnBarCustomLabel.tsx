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

interface ShadcnBarCustomLabelProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
	height?: number;
}

const ShadcnBarCustomLabel: React.FC<ShadcnBarCustomLabelProps> = ({
	title = "Bar Chart - Custom Label",
	description = "June 2024",
	data = [],
	dataKey = "value",
	nameKey = "name",
	height = 300,
}) => {
	// Process real data for custom label format
	const chartData =
		data.length > 0
			? data.slice(0, 6).map((item, index) => {
					const months = [
						"January",
						"February",
						"March",
						"April",
						"May",
						"June",
					];
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
						name: String(nameValue),
						desktop,
					};
			  })
			: [
					{ name: "January", desktop: 186 },
					{ name: "February", desktop: 305 },
					{ name: "March", desktop: 237 },
					{ name: "April", desktop: 73 },
					{ name: "May", desktop: 209 },
					{ name: "June", desktop: 214 },
			  ];

	// Custom Bar component with internal labels
	const CustomBar = (props: any) => {
		const { payload, x, y, width, height } = props;

		return (
			<g>
				{/* Bar background */}
				<rect x={x} y={y} width={width} height={height} fill="#3b82f6" rx={4} />

				{/* Label inside the bar */}
				<text
					x={x + width - 8}
					y={y + height / 2}
					fill="white"
					textAnchor="end"
					dy={0}
					fontSize={12}
					fontWeight={600}>
					{payload.desktop}
				</text>

				{/* Month label */}
				<text
					x={x + 8}
					y={y + height / 2}
					fill="white"
					textAnchor="start"
					dy={0}
					fontSize={11}
					fontWeight={500}>
					{payload.name}
				</text>
			</g>
		);
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
								top: 20,
								right: 20,
								bottom: 20,
								left: 20,
							}}>
							<XAxis type="number" hide />
							<YAxis dataKey="name" type="category" hide />
							<ChartTooltip
								content={<ChartTooltipContent />}
								cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
							/>
							<Bar
								dataKey="desktop"
								fill="#3b82f6"
								shape={<CustomBar />}
								maxBarSize={40}
							/>
						</BarChart>
					</ResponsiveContainer>
				</div>

				{/* Trending indicator */}
				<div className="flex items-center pt-4 text-xs text-muted-foreground">
					<span className="inline-flex items-center gap-1">
						Trending up by 5.2% this month
						<svg
							width="12"
							height="12"
							viewBox="0 0 12 12"
							className="text-green-600">
							<path
								d="M2.5 7.5L5.5 4.5L8.5 7.5"
								fill="none"
								stroke="currentColor"
								strokeWidth="1.5"
								strokeLinecap="round"
								strokeLinejoin="round"
							/>
						</svg>
					</span>
					<span className="ml-2">
						Showing total visitors for the last 6 months
					</span>
				</div>
			</CardContent>
		</Card>
	);
};

export default ShadcnBarCustomLabel;
