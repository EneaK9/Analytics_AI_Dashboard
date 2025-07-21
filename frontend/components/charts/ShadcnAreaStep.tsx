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

interface ShadcnAreaStepProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	xAxisKey?: string;
	height?: number;
	color?: string;
}

const ShadcnAreaStep: React.FC<ShadcnAreaStepProps> = ({
	title = "Area Chart - Step",
	description = "Showing total visitors for the last 6 months",
	data = [],
	dataKey = "visitors",
	xAxisKey = "month",
	height = 300,
	color = "#6366f1",
}) => {
	// Process real data with step-like values
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
						Math.floor((150 + index * 30) / 50) * 50; // Creates step-like values

					return {
						[xAxisKey]: String(xValue),
						[dataKey]: Math.round(value),
					};
			  })
			: [
					{ month: "Jan", visitors: 200 },
					{ month: "Feb", visitors: 250 },
					{ month: "Mar", visitors: 250 },
					{ month: "Apr", visitors: 300 },
					{ month: "May", visitors: 200 },
					{ month: "Jun", visitors: 250 },
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
							<linearGradient id="stepFill" x1="0" y1="0" x2="0" y2="1">
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
							type="step"
							fill="url(#stepFill)"
							stroke={color}
							strokeWidth={2}
						/>
					</AreaChart>
				</ChartContainer>
				<div className="flex items-center gap-2 text-sm mt-4">
					<div className="flex items-center gap-2 font-medium leading-none">
						Trending up by 5.2% this month
						<span className="text-lg">📈</span>
					</div>
				</div>
				<div className="leading-none text-muted-foreground text-sm">
					{description.includes("January")
						? "January - June 2024"
						: "Recent period analysis"}
				</div>
			</CardContent>
		</Card>
	);
};

export default ShadcnAreaStep;
