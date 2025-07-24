import React from "react";
import { Pie, PieChart, ResponsiveContainer, Cell } from "recharts";
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

interface ShadcnPieStackedProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

const ShadcnPieStacked: React.FC<ShadcnPieStackedProps> = ({
	data,
	title = "Stacked Pie Chart",
	description = "Multi-layer pie chart",
	minimal = false,
}) => {
	return (
		<div className="w-full h-full">
			{!minimal && (
				<div className="mb-4">
					<h3 className="text-lg font-semibold">{title}</h3>
					<p className="text-sm text-muted-foreground">{description}</p>
				</div>
			)}
			<ResponsiveContainer width="100%" height="100%">
				<PieChart>
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Pie
						data={data}
						cx="50%"
						cy="50%"
						innerRadius={20}
						outerRadius={50}
						paddingAngle={2}
						dataKey="value">
						{data.map((entry, index) => (
							<Cell
								key={`cell-${index}`}
								fill={COLORS[index % COLORS.length]}
							/>
						))}
					</Pie>
					<Pie
						data={data}
						cx="50%"
						cy="50%"
						innerRadius={55}
						outerRadius={80}
						paddingAngle={2}
						dataKey="desktop">
						{data.map((entry, index) => (
							<Cell
								key={`cell-${index}`}
								fill={COLORS[index % COLORS.length]}
								fillOpacity={0.6}
							/>
						))}
					</Pie>
				</PieChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnPieStacked;
