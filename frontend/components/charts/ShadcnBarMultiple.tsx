import React from "react";
import {
	Bar,
	BarChart,
	CartesianGrid,
	XAxis,
	ResponsiveContainer,
} from "recharts";
import {
	ChartTooltip,
	ChartTooltipContent,
	ChartLegend,
	ChartLegendContent,
} from "@/components/ui/chart";

interface ShadcnBarMultipleProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnBarMultiple: React.FC<ShadcnBarMultipleProps> = ({
	data,
	title = "Multiple Bar Chart",
	description = "A bar chart with multiple series",
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
					<ChartTooltip content={<ChartTooltipContent />} />
					<ChartLegend content={<ChartLegendContent />} />
					<Bar dataKey="desktop" fill="hsl(var(--chart-1))" radius={4} />
					<Bar dataKey="mobile" fill="hsl(var(--chart-2))" radius={4} />
				</BarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnBarMultiple;
