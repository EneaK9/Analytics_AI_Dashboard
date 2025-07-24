import React from "react";
import {
	Bar,
	BarChart,
	CartesianGrid,
	XAxis,
	ResponsiveContainer,
	LabelList,
} from "recharts";
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

interface ShadcnBarCustomProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnBarCustom: React.FC<ShadcnBarCustomProps> = ({
	data,
	title = "Custom Bar Chart",
	description = "Custom styled bar chart with labels",
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
				<BarChart
					data={data}
					margin={{
						top: 20,
					}}>
					<CartesianGrid vertical={false} />
					<XAxis
						dataKey="name"
						tickLine={false}
						tickMargin={10}
						axisLine={false}
						tickFormatter={(value) => value.slice(0, 3)}
					/>
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Bar dataKey="value" fill="var(--color-data)" radius={8}>
						<LabelList
							position="top"
							offset={12}
							className="fill-foreground"
							fontSize={12}
						/>
					</Bar>
				</BarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnBarCustom;
