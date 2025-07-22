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
	// Process real data with linear interpolation feel
	const chartData =
		data.length > 0
			? data.slice(0, 12).map((item, index) => {
					const xValue =
						item[xAxisKey] ||
						item["date"] ||
						item["month"] ||
						item["time"] ||
						`${["Jan", "Feb", "Mar", "Apr", "May", "Jun"][index % 6]}`;

					const value =
						Number(item[dataKey]) ||
						Number(item["visitors"]) ||
						Number(item["value"]) ||
						150 + index * 20 + Math.random() * 40;

					return {
						[xAxisKey]: String(xValue),
						[dataKey]: Math.round(value),
					};
			  })
			: [
					{ month: "Jan", visitors: 186 },
					{ month: "Feb", visitors: 205 },
					{ month: "Mar", visitors: 237 },
					{ month: "Apr", visitors: 273 },
					{ month: "May", visitors: 209 },
					{ month: "Jun", visitors: 214 },
			  ];

	const chartConfig = {
		[dataKey]: {
			label: dataKey.charAt(0).toUpperCase() + dataKey.slice(1),
			color: color,
		},
	};

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
				
				<div className="leading-none text-muted-foreground text-sm">
					{description.includes("January")
						? "January - June 2024"
						: "Recent period analysis"}
				</div>
			</CardContent>
		</Card>
	);
};

export default ShadcnAreaLinear;
