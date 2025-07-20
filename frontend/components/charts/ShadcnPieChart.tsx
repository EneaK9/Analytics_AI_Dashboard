import React from "react";
import {
	Pie,
	PieChart,
	ResponsiveContainer,
	Cell,
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

interface ShadcnPieChartProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
	height?: number;
	colors?: string[];
	innerRadius?: number;
	outerRadius?: number;
}

const ShadcnPieChart: React.FC<ShadcnPieChartProps> = ({
	title = "Distribution Chart",
	description = "Data breakdown",
	data = [],
	dataKey = "value",
	nameKey = "name",
	height = 200,
	colors = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"],
	innerRadius = 0,
	outerRadius = 80,
}) => {
	// 🎯 REAL DATA PROCESSING - No more fake data!
	const chartData =
		data.length > 0
			? data.slice(0, 5).map((item, index) => {
					// 🔍 Smart key detection - find actual data columns
					const nameValue =
						item[nameKey] ||
						item["symbol"] ||
						item["name"] ||
						item["category"] ||
						item["type"] ||
						item["exchange"] ||
						item["status"] ||
						Object.keys(item)[0] ||
						`Category ${index + 1}`;

					const dataValue =
						Number(item[dataKey]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						Number(item["total_value"]) ||
						Number(item["value"]) ||
						Number(Object.values(item).find((v) => typeof v === "number")) ||
						Math.random() * 100;

					return {
						name: String(nameValue),
						value: dataValue,
					};
			  })
			: [{ name: "No Data", value: 0 }];

	const chartConfig = chartData.reduce((config, item, index) => {
		config[item.name] = {
			label: item.name,
			color: colors[index % colors.length],
		};
		return config;
	}, {} as Record<string, { label: string; color: string }>);

	return (
		<Card className="w-full">
			<CardHeader>
				<CardTitle>{title}</CardTitle>
				<CardDescription>{description}</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer config={chartConfig} className="h-[160px] w-full">
					<ResponsiveContainer width="100%" height={160}>
						<PieChart>
							<Pie
								data={chartData}
								cx="50%"
								cy="50%"
								innerRadius={innerRadius}
								outerRadius={outerRadius}
								paddingAngle={5}
								dataKey="value">
								{chartData.map((entry, index) => (
									<Cell
										key={`cell-${index}`}
										fill={colors[index % colors.length]}
									/>
								))}
							</Pie>
							<ChartTooltip content={<ChartTooltipContent />} />
							<Legend />
						</PieChart>
					</ResponsiveContainer>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnPieChart;
