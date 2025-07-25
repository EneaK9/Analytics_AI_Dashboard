import React from "react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
	type ChartConfig,
} from "@/components/ui/chart";

interface ShadcnBarMixedProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnBarMixed: React.FC<ShadcnBarMixedProps> = ({
	data,
	title = "Bar Chart - Mixed",
	description = "Mixed orientation bar chart",
	minimal = false,
}) => {
	// Process REAL data only
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return []; // Return empty array if no real data
		}

		return data
			.slice(0, 5)
			.map((item: any, index: number) => {
				const nameValue =
					item.name ||
					item.category ||
					item.symbol ||
					item.browser ||
					`Item ${index + 1}`;
				const dataValue =
					Number(item.value) ||
					Number(item.visitors) ||
					Number(item.count) ||
					Number(item.total) ||
					0;

				return {
					name: nameValue,
					value: dataValue,
					fill: item.fill || `hsl(var(--chart-${(index % 5) + 1}))`,
				};
			})
			.filter((item) => item.value > 0);
	}, [data]);

	// Generate dynamic chart config from real data
	const chartConfig = React.useMemo(() => {
		const config: any = {
			value: {
				label: "Value",
			},
		};

		chartData.forEach((item: any, index: number) => {
			config[item.name] = {
				label: item.name,
				color: `hsl(var(--chart-${(index % 5) + 1}))`,
			};
		});

		return config;
	}, [chartData]);

	if (chartData.length === 0) {
		return (
			<div className="w-full h-full">
				{!minimal && (
					<div className="mb-4">
						<h3 className="text-lg font-semibold">{title}</h3>
						<p className="text-sm text-muted-foreground">{description}</p>
					</div>
				)}
				<div className="flex items-center justify-center h-[300px] text-muted-foreground">
					No data available
				</div>
			</div>
		);
	}

	return (
		<div className="w-full h-full">
			{!minimal && (
				<div className="mb-4">
					<h3 className="text-lg font-semibold">{title}</h3>
					<p className="text-sm text-muted-foreground">{description}</p>
				</div>
			)}
			<ChartContainer config={chartConfig} className="h-full w-full">
				<BarChart
					accessibilityLayer
					data={chartData}
					layout="vertical"
					margin={{
						left: 0,
					}}>
					<YAxis
						dataKey="name"
						type="category"
						tickLine={false}
						tickMargin={10}
						axisLine={false}
						tickFormatter={(value) =>
							chartConfig[value as keyof typeof chartConfig]?.label || value
						}
					/>
					<XAxis dataKey="value" type="number" hide />
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Bar dataKey="value" layout="vertical" radius={5} />
				</BarChart>
			</ChartContainer>
		</div>
	);
};

export default ShadcnBarMixed;
