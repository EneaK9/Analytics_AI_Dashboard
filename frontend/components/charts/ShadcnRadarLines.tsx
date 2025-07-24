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

interface ShadcnRadarLinesProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnRadarLines: React.FC<ShadcnRadarLinesProps> = ({
	data,
	title = "Radar Chart - Grid None",
	description = "Radar chart without grid",
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
					<PolarGrid gridType="polygon" stroke="transparent" />
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
						fillOpacity={0.2}
						strokeWidth={2}
						dot={{ r: 6, fill: "var(--color-desktop)", strokeWidth: 2 }}
					/>
				</RadarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnRadarLines;
