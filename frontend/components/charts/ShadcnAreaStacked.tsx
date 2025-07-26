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
	dataKey1 = "series1",
	dataKey2 = "series2",
	xAxisKey = "month",
	height = 300,
}) => {
	// Process real data for stacked areas - NO MORE MOBILE/DESKTOP HARDCODING
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		return data.slice(0, 12).map((item, index) => {
			// Extract meaningful X-axis value (date, period, category, etc.)
			const xValue =
				item[xAxisKey] ||
				item["date"] ||
				item["month"] ||
				item["period"] ||
				item["time"] ||
				item["category"] ||
				`Period ${index + 1}`;

			// Extract first data series (replace "mobile" with real business metric)
			const series1Value =
				Number(item[dataKey1]) ||
				Number(item["quantity"]) ||
				Number(item["orders"]) ||
				Number(item["customers"]) ||
				Number(item["transactions"]) ||
				Number(item["value1"]) ||
				0; // No more Math.random() fallback

			// Extract second data series (replace "desktop" with real business metric)
			const series2Value =
				Number(item[dataKey2]) ||
				Number(item["revenue"]) ||
				Number(item["sales"]) ||
				Number(item["amount"]) ||
				Number(item["total"]) ||
				Number(item["value2"]) ||
				0; // No more Math.random() fallback

			return {
				[xAxisKey]: String(xValue).substring(0, 15), // Limit length for readability
				[dataKey1]: Math.round(series1Value),
				[dataKey2]: Math.round(series2Value),
			};
		});
	}, [data, dataKey1, dataKey2, xAxisKey]);

	// Dynamic chart config based on actual data keys
	const chartConfig = React.useMemo(
		() => ({
			[dataKey1]: {
				label:
					dataKey1.charAt(0).toUpperCase() +
					dataKey1.slice(1).replace(/([A-Z])/g, " $1"),
				color: "#2563eb",
			},
			[dataKey2]: {
				label:
					dataKey2.charAt(0).toUpperCase() +
					dataKey2.slice(1).replace(/([A-Z])/g, " $1"),
				color: "#60a5fa",
			},
		}),
		[dataKey1, dataKey2]
	);

	// Don't render if no data
	if (chartData.length === 0) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>{title}</CardTitle>
					<CardDescription>{description}</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="flex items-center justify-center h-[300px] text-muted-foreground">
						No data available for stacked area chart
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer config={chartConfig}>
					<AreaChart
						accessibilityLayer
						data={chartData}
						margin={{
							left: 12,
							right: 12,
						}}>
						<CartesianGrid vertical={false} />
						<XAxis
							dataKey={xAxisKey}
							tickLine={false}
							axisLine={false}
							tickMargin={8}
							tickFormatter={(value) => value.slice(0, 8)}
						/>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent indicator="dot" />}
						/>
						<Area
							dataKey={dataKey2}
							type="natural"
							fill={`var(--color-${dataKey2})`}
							fillOpacity={0.4}
							stroke={`var(--color-${dataKey2})`}
							stackId="a"
						/>
						<Area
							dataKey={dataKey1}
							type="natural"
							fill={`var(--color-${dataKey1})`}
							fillOpacity={0.4}
							stroke={`var(--color-${dataKey1})`}
							stackId="a"
						/>
					</AreaChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnAreaStacked;
