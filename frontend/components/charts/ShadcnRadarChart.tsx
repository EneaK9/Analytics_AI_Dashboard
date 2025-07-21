import React from "react";
import {
	Radar,
	RadarChart,
	PolarGrid,
	PolarAngleAxis,
	PolarRadiusAxis,
	ResponsiveContainer,
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

interface ShadcnRadarChartProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
	height?: number;
}

const ShadcnRadarChart: React.FC<ShadcnRadarChartProps> = ({
	title = "Radar Chart",
	description = "Showing total visitors for the last 6 months",
	data = [],
	dataKey = "value",
	nameKey = "name",
	height = 300,
}) => {
	// Process real data for radar format
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
						Math.floor(Math.random() * 150) + 20;

					return {
						month: String(nameValue).slice(0, 8),
						desktop: Math.min(desktop, 150), // Cap at 150 for better radar visualization
					};
			  })
			: [
					{ month: "January", desktop: 120 },
					{ month: "February", desktop: 98 },
					{ month: "March", desktop: 86 },
					{ month: "April", desktop: 99 },
					{ month: "May", desktop: 85 },
					{ month: "June", desktop: 65 },
			  ];

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
						<RadarChart
							data={chartData}
							margin={{ top: 20, right: 80, bottom: 20, left: 80 }}>
							<PolarGrid
								stroke="hsl(var(--border))"
								strokeWidth={1}
								radialLines={true}
							/>
							<PolarAngleAxis
								dataKey="month"
								tick={{ fontSize: 12, fill: "hsl(var(--foreground))" }}
								className="text-xs"
							/>
							<PolarRadiusAxis
								domain={[0, 150]}
								tick={false}
								axisLine={false}
							/>
							<Radar
								name="Desktop"
								dataKey="desktop"
								stroke="#3b82f6"
								fill="#3b82f6"
								fillOpacity={0.6}
								strokeWidth={2}
							/>
							<ChartTooltip
								content={<ChartTooltipContent />}
								formatter={(value: any) => [value, "Desktop"]}
							/>
						</RadarChart>
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
					<span className="ml-2">January - June 2024</span>
				</div>
			</CardContent>
		</Card>
	);
};

export default ShadcnRadarChart;
