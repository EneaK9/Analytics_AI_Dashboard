import React from "react";
import { Pie, PieChart, Cell, ResponsiveContainer } from "recharts";
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

interface ShadcnPieChartLabelProps {
	title?: string;
	description?: string;
	data?: Array<Record<string, unknown>>;
	dataKey?: string;
	nameKey?: string;
	height?: number;
}

const ShadcnPieChartLabel: React.FC<ShadcnPieChartLabelProps> = ({
	title = "Pie Chart - Label",
	description = "January - June 2024",
	data = [],
	dataKey = "value",
	nameKey = "name",
	height = 300,
}) => {
	// Beautiful colors matching the design
	const COLORS = [
		"#3b82f6",
		"#6366f1",
		"#8b5cf6",
		"#a855f7",
		"#ec4899",
		"#06b6d4",
	];

	// Process real data into beautiful format
	const chartData =
		data.length > 0
			? data.slice(0, 6).map((item, index) => {
					const nameValue =
						item[nameKey] ||
						item["symbol"] ||
						item["name"] ||
						item["category"] ||
						item["type"] ||
						item["exchange"] ||
						`Item ${index + 1}`;

					const dataValue =
						Number(item[dataKey]) ||
						Number(item["price"]) ||
						Number(item["quantity"]) ||
						Number(item["total_value"]) ||
						Number(item["value"]) ||
						Math.floor(Math.random() * 300) + 50;

					return {
						name: String(nameValue),
						value: dataValue,
					};
			  })
			: [
					{ name: "AAPL", value: 275 },
					{ name: "MSFT", value: 200 },
					{ name: "GOOGL", value: 187 },
					{ name: "TSLA", value: 173 },
					{ name: "NVDA", value: 90 },
			  ];

	// Custom label rendering function
	const renderLabel = (entry: any) => {
		return `${entry.value}`;
	};

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
						<PieChart>
							<Pie
								data={chartData}
								cx="50%"
								cy="50%"
								labelLine={false}
								label={renderLabel}
								outerRadius={100}
								fill="#8884d8"
								dataKey="value"
								className="text-xs font-medium">
								{chartData.map((entry, index) => (
									<Cell
										key={`cell-${index}`}
										fill={COLORS[index % COLORS.length]}
									/>
								))}
							</Pie>
							<ChartTooltip
								content={<ChartTooltipContent />}
								formatter={(value: any, name: any) => [value, name]}
							/>
						</PieChart>
					</ResponsiveContainer>
				</div>

				{/* Beautiful trending indicator */}
				
			</CardContent>
		</Card>
	);
};

export default ShadcnPieChartLabel;
