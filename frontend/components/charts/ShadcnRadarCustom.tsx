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

interface ShadcnRadarCustomProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const ShadcnRadarCustom: React.FC<ShadcnRadarCustomProps> = ({
	data,
	title = "Radar Chart - Custom Label",
	description = "Custom labeled radar chart",
	minimal = false,
}) => {
	// Transform real data to match original structure EXACTLY
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data with EXACT same structure if no real data
			return [
				{ month: "January", desktop: 186 },
				{ month: "February", desktop: 305 },
				{ month: "March", desktop: 237 },
				{ month: "April", desktop: 73 },
				{ month: "May", desktop: 209 },
				{ month: "June", desktop: 214 },
			];
		}
		// Transform real data to match original structure
		return data.slice(0, 6).map((item, index) => ({
			month: item.name || item.category || item.symbol || `Month ${index + 1}`,
			desktop: item.value || item.desktop || item.count || item.total || 0,
		}));
	}, [data]);

	return (
		<div className="w-full h-full">
			{!minimal && (
				<div className="mb-4">
					<h3 className="text-lg font-semibold">{title}</h3>
					<p className="text-sm text-muted-foreground">{description}</p>
				</div>
			)}
			<ResponsiveContainer width="100%" height="100%">
				<RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
					<PolarGrid stroke="#374151" />
					<PolarAngleAxis
						dataKey="month"
						tick={{ fontSize: 12, fill: "#6B7280" }}
					/>
					<PolarRadiusAxis
						angle={0}
						domain={[0, "dataMax"]}
						tick={{ fontSize: 10, fill: "#9CA3AF" }}
					/>
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Radar
						name="Desktop"
						dataKey="desktop"
						stroke="var(--color-desktop)"
						fill="var(--color-desktop)"
						fillOpacity={0.3}
						strokeWidth={2}
					/>
				</RadarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnRadarCustom;
