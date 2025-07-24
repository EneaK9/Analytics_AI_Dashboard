import React from "react";
import {
	Bar,
	BarChart,
	CartesianGrid,
	XAxis,
	ResponsiveContainer,
} from "recharts";
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

interface ShadcnBarActiveProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnBarActive: React.FC<ShadcnBarActiveProps> = ({
	data,
	title = "Active Bar Chart",
	description = "Interactive bar chart with active states",
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
				<BarChart data={data}>
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
					<Bar
						dataKey="value"
						fill="var(--color-data)"
						radius={8}
						fillOpacity={0.6}
						activeIndex={2}
						activeBar={{
							fill: "var(--color-data)",
							fillOpacity: 0.8,
						}}
					/>
				</BarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnBarActive;
