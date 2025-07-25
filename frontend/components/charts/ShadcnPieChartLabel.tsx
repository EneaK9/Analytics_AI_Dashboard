import React from "react";
import { Pie, PieChart } from "recharts";
import {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
	type ChartConfig,
} from "@/components/ui/chart";

interface ShadcnPieChartLabelProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

// NO HARDCODED DATA - All data comes from props

const ShadcnPieChartLabel: React.FC<ShadcnPieChartLabelProps> = ({
	data,
	title = "Pie Chart - Label",
	description = "A pie chart with labels",
	minimal = false,
}) => {
	// Process REAL data only
	const { chartData, chartConfig } = React.useMemo(() => {
		if (!data || data.length === 0) {
			return { chartData: [], chartConfig: {} };
		}

		const processedData = data
			.slice(0, 5)
			.map((item: any, index: number) => {
				const nameValue =
					item.name || item.category || item.symbol || `Item ${index + 1}`;
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

		// Generate dynamic chart config
		const config: any = {
			value: {
				label: "Value",
			},
		};

		processedData.forEach((item: any, index: number) => {
			config[item.name] = {
				label: item.name,
				color: `hsl(var(--chart-${(index % 5) + 1}))`,
			};
		});

		return { chartData: processedData, chartConfig: config };
	}, [data]);

	if (chartData.length === 0) {
		return (
			<div className="w-full h-full">
				{!minimal && (
					<div className="mb-4">
						<h3 className="text-lg font-semibold">{title}</h3>
						<p className="text-sm text-muted-foreground">{description}</p>
					</div>
				)}
				<div className="flex items-center justify-center h-[250px] text-muted-foreground">
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
			<ChartContainer
				config={chartConfig}
				className="[&_.recharts-pie-label-text]:fill-foreground mx-auto aspect-square max-h-[250px] h-full w-full">
				<PieChart>
					<ChartTooltip content={<ChartTooltipContent hideLabel />} />
					<Pie data={chartData} dataKey="value" label nameKey="name" />
				</PieChart>
			</ChartContainer>
		</div>
	);
};

export default ShadcnPieChartLabel;
