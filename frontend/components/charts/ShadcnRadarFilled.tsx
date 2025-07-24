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

interface ShadcnRadarFilledProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnRadarFilled: React.FC<ShadcnRadarFilledProps> = ({
	data,
	title = "Radar Chart - Grid Filled",
	description = "Filled radar chart with grid",
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
					<PolarGrid gridType="polygon" />
					<PolarAngleAxis dataKey="month" />
					<PolarRadiusAxis angle={0} domain={[0, "dataMax"]} />
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Radar
						name="Desktop"
						dataKey="desktop"
						stroke="var(--color-desktop)"
						fill="var(--color-desktop)"
						fillOpacity={0.6}
					/>
				</RadarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnRadarFilled;
