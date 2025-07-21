"use client";

import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

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
import { TrendingUp } from "lucide-react";

interface ShadcnMultipleAreaProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey1?: string;
	dataKey2?: string;
	xAxisKey?: string;
}

const ShadcnMultipleArea: React.FC<ShadcnMultipleAreaProps> = ({
	title = "Area Chart - Stacked",
	description = "Showing total visitors for the last 6 months",
	data = [],
	dataKey1 = "value1",
	dataKey2 = "value2",
	xAxisKey = "name",
}) => {
	// Process real data into shadcn format
	const chartData =
		data && data.length > 0
			? data.slice(0, 12).map((item, index) => {
					// Use actual data fields when available
					const monthValue =
						item[xAxisKey] ||
						item["month"] ||
						item["date"] ||
						item["name"] ||
						item["symbol"] ||
						`Month ${index + 1}`;

					const desktop =
						Number(item[dataKey1]) ||
						Number(item["desktop"]) ||
						Number(item["value"]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						0;

					const mobile =
						Number(item[dataKey2]) ||
						Number(item["mobile"]) ||
						Number(item["value2"]) ||
						Number(item["total_value"]) ||
						Number(item["volume"]) ||
						Math.floor(desktop * 0.7); // Calculate mobile as 70% of desktop if not available

					return {
						month: String(monthValue),
						desktop,
						mobile,
					};
			  })
			: [
					{ month: "January", desktop: 186, mobile: 80 },
					{ month: "February", desktop: 305, mobile: 200 },
					{ month: "March", desktop: 237, mobile: 120 },
					{ month: "April", desktop: 73, mobile: 190 },
					{ month: "May", desktop: 209, mobile: 130 },
					{ month: "June", desktop: 214, mobile: 140 },
			  ];

	const chartConfig = {
		desktop: {
			label: "Desktop",
			color: "hsl(var(--chart-1))",
		},
		mobile: {
			label: "Mobile",
			color: "hsl(var(--chart-2))",
		},
	} satisfies ChartConfig;

	return (
		<Card>
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer
					config={chartConfig}
					className="aspect-auto h-[180px] w-full">
					<AreaChart
						accessibilityLayer
						data={chartData}
						margin={{
							left: 12,
							right: 12,
						}}>
						<CartesianGrid vertical={false} />
						<XAxis
							dataKey="month"
							tickLine={false}
							axisLine={false}
							tickMargin={8}
							tickFormatter={(value) => value.slice(0, 3)}
						/>
						<ChartTooltip cursor={false} content={<ChartTooltipContent />} />
						<defs>
							<linearGradient id="fillDesktop" x1="0" y1="0" x2="0" y2="1">
								<stop
									offset="5%"
									stopColor="var(--color-desktop)"
									stopOpacity={0.8}
								/>
								<stop
									offset="95%"
									stopColor="var(--color-desktop)"
									stopOpacity={0.1}
								/>
							</linearGradient>
							<linearGradient id="fillMobile" x1="0" y1="0" x2="0" y2="1">
								<stop
									offset="5%"
									stopColor="var(--color-mobile)"
									stopOpacity={0.8}
								/>
								<stop
									offset="95%"
									stopColor="var(--color-mobile)"
									stopOpacity={0.1}
								/>
							</linearGradient>
						</defs>
						<Area
							dataKey="mobile"
							type="natural"
							fill="url(#fillMobile)"
							fillOpacity={0.4}
							stroke="var(--color-mobile)"
							stackId="a"
						/>
						<Area
							dataKey="desktop"
							type="natural"
							fill="url(#fillDesktop)"
							fillOpacity={0.4}
							stroke="var(--color-desktop)"
							stackId="a"
						/>
					</AreaChart>
				</ChartContainer>
			</CardContent>
			<CardFooter>
				<div className="flex w-full items-start gap-2 text-sm">
					<div className="grid gap-2">
						<div className="flex items-center gap-2 font-medium leading-none">
							Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
						</div>
						<div className="flex items-center gap-2 leading-none text-muted-foreground">
							January - June 2024
						</div>
					</div>
				</div>
			</CardFooter>
		</Card>
	);
};

export default ShadcnMultipleArea;
