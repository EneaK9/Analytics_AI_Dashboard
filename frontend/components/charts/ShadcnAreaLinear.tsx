import React from "react";
import {
	Area,
	AreaChart,
	ResponsiveContainer,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
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

interface ShadcnAreaLinearProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	xAxisKey?: string;
	height?: number;
	color?: string;
}

const ShadcnAreaLinear: React.FC<ShadcnAreaLinearProps> = ({
	title = "Area Chart - Linear",
	description = "Showing total visitors for the last 6 months",
	data = [],
	dataKey = "visitors",
	xAxisKey = "month",
	height = 300,
	color = "#3b82f6",
}) => {
	// Process real data with linear interpolation feel - NO RANDOM DATA
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return []; // Return empty array instead of fallback data
		}

		return data.slice(0, 12).map((item, index) => {
			const xValue =
				item[xAxisKey] ||
				item["date"] ||
				item["month"] ||
				item["time"] ||
				item["name"] ||
				item["category"] ||
				`Item ${index + 1}`;

			const value =
				Number(item[dataKey]) ||
				Number(item["visitors"]) ||
				Number(item["value"]) ||
				Number(item["amount"]) ||
				Number(item["total"]) ||
				0; // Remove random fallback

			return {
				[xAxisKey]: String(xValue),
				[dataKey]: Math.round(value),
			};
		});
	}, [data, dataKey, xAxisKey]);

	const chartConfig = {
		[dataKey]: {
			label: dataKey.charAt(0).toUpperCase() + dataKey.slice(1),
			color: color,
		},
	};

	// Don't render if no data
	if (chartData.length === 0) {
		return (
			<Card className="bg-card">
				<CardHeader>
					<CardTitle className="text-lg font-semibold">{title}</CardTitle>
					<CardDescription className="text-sm text-muted-foreground">
						{description}
					</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="flex items-center justify-center h-[300px] text-muted-foreground">
						No data available for area chart
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card className="bg-card">
			<CardHeader>
				<CardTitle className="text-lg font-semibold">{title}</CardTitle>
				<CardDescription className="text-sm text-muted-foreground">
					{description}
				</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer
					config={chartConfig}
					className="aspect-auto h-[250px] w-full">
					<AreaChart data={chartData}>
						<defs>
							<linearGradient id="linearFill" x1="0" y1="0" x2="0" y2="1">
								<stop offset="5%" stopColor={color} stopOpacity={0.8} />
								<stop offset="95%" stopColor={color} stopOpacity={0.1} />
							</linearGradient>
						</defs>
						<CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
						<XAxis
							dataKey={xAxisKey}
							tickLine={false}
							axisLine={false}
							tickMargin={8}
							className="text-xs"
						/>
						<YAxis hide />
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent className="w-[150px]" />}
						/>
						<Area
							dataKey={dataKey}
							type="linear"
							fill="url(#linearFill)"
							stroke={color}
							strokeWidth={2}
						/>
					</AreaChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnAreaLinear;
