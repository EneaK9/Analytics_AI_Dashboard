import React from "react";
import {
	Area,
	AreaChart,
	ResponsiveContainer,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
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

interface ShadcnAreaStackedProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey1?: string;
	dataKey2?: string;
	xAxisKey?: string;
	height?: number;
}

const ShadcnAreaStacked: React.FC<ShadcnAreaStackedProps> = ({
	title = "Area Chart - Stacked",
	description = "Showing total visitors for the last 6 months",
	data = [],
	dataKey1 = "mobile",
	dataKey2 = "desktop",
	xAxisKey = "month",
	height = 300,
}) => {
	// Process real data for stacked areas
	const chartData =
		data.length > 0
			? data.slice(0, 12).map((item, index) => {
					const xValue =
						item[xAxisKey] ||
						item["date"] ||
						item["month"] ||
						item["time"] ||
						`${["Jan", "Feb", "Mar", "Apr", "May", "Jun"][index % 6]}`;

					const value1 =
						Number(item[dataKey1]) ||
						Number(item["mobile"]) ||
						Number(item["value1"]) ||
						80 + Math.random() * 40;

					const value2 =
						Number(item[dataKey2]) ||
						Number(item["desktop"]) ||
						Number(item["value2"]) ||
						100 + Math.random() * 50;

					return {
						[xAxisKey]: String(xValue),
						[dataKey1]: Math.round(value1),
						[dataKey2]: Math.round(value2),
					};
			  })
			: [
					{ month: "Jan", mobile: 80, desktop: 120 },
					{ month: "Feb", mobile: 90, desktop: 140 },
					{ month: "Mar", mobile: 85, desktop: 110 },
					{ month: "Apr", mobile: 95, desktop: 160 },
					{ month: "May", mobile: 100, desktop: 130 },
					{ month: "Jun", mobile: 88, desktop: 150 },
			  ];

	const chartConfig = {
		[dataKey1]: {
			label: dataKey1.charAt(0).toUpperCase() + dataKey1.slice(1),
			color: "#2563eb",
		},
		[dataKey2]: {
			label: dataKey2.charAt(0).toUpperCase() + dataKey2.slice(1),
			color: "#60a5fa",
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
							<linearGradient id="stackedFill1" x1="0" y1="0" x2="0" y2="1">
								<stop offset="5%" stopColor="#2563eb" stopOpacity={0.8} />
								<stop offset="95%" stopColor="#2563eb" stopOpacity={0.3} />
							</linearGradient>
							<linearGradient id="stackedFill2" x1="0" y1="0" x2="0" y2="1">
								<stop offset="5%" stopColor="#60a5fa" stopOpacity={0.8} />
								<stop offset="95%" stopColor="#60a5fa" stopOpacity={0.3} />
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
							dataKey={dataKey1}
							type="natural"
							fill="url(#stackedFill1)"
							stroke="#2563eb"
							strokeWidth={1}
							stackId="1"
						/>
						<Area
							dataKey={dataKey2}
							type="natural"
							fill="url(#stackedFill2)"
							stroke="#60a5fa"
							strokeWidth={1}
							stackId="1"
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

export default ShadcnAreaStacked;
