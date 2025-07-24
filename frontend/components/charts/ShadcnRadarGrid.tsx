import React from "react";
import {
	Radar,
	RadarChart,
	PolarGrid,
	PolarAngleAxis,
	PolarRadiusAxis,
	ResponsiveContainer,
} from "recharts";
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

interface ShadcnRadarGridProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnRadarGrid: React.FC<ShadcnRadarGridProps> = ({
	data,
	title = "Radar Chart - Grid Custom",
	description = "Custom grid radar chart",
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
				<RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
					<PolarGrid
						gridType="polygon"
						radialLines={true}
						stroke="var(--color-desktop)"
						strokeOpacity={0.3}
					/>
					<PolarAngleAxis dataKey="month" />
					<PolarRadiusAxis angle={0} domain={[0, "dataMax"]} tick={false} />
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Radar
						name="Desktop"
						dataKey="desktop"
						stroke="var(--color-desktop)"
						fill="var(--color-desktop)"
						fillOpacity={0.4}
						strokeWidth={3}
						dot={{ r: 4, fill: "var(--color-desktop)" }}
					/>
				</RadarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnRadarGrid;
