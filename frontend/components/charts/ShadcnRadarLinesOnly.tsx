"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from "recharts";

import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import {
	ChartConfig,
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";

export const description = "A radar chart with lines only";

// Keep the original chartConfig structure EXACTLY
const chartConfig = {
	desktop: {
		label: "Desktop",
		color: "var(--chart-1)",
	},
	mobile: {
		label: "Mobile",
		color: "var(--chart-2)",
	},
} satisfies ChartConfig;

interface ShadcnRadarLinesOnlyProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	ai_labels?: any;
}

export function ShadcnRadarLinesOnly({
	data = [],
	title,
	description,
	minimal,
	ai_labels,
}: ShadcnRadarLinesOnlyProps) {
	// Transform real data to match original structure EXACTLY
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data with EXACT same structure
			return [
				{ month: "January", desktop: 186, mobile: 160 },
				{ month: "February", desktop: 185, mobile: 170 },
				{ month: "March", desktop: 207, mobile: 180 },
				{ month: "April", desktop: 173, mobile: 160 },
				{ month: "May", desktop: 160, mobile: 190 },
				{ month: "June", desktop: 174, mobile: 204 },
			];
		}

		// Transform real data to match original structure
		return data.slice(0, 6).map((item, index) => ({
			month: item.name || item.category || item.symbol || `Month ${index + 1}`,
			desktop: item.value || item.desktop || item.count || item.total || 0,
			mobile: Math.max(
				1,
				Math.round(
					(item.value || item.desktop || item.count || item.total || 0) * 0.85
				)
			),
		}));
	}, [data]);

	return (
		<Card>
			
			<CardContent className="pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<RadarChart data={chartData}>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent indicator="line" />}
						/>
						<PolarAngleAxis dataKey="month" />
						<PolarGrid radialLines={false} />
						<Radar
							dataKey="desktop"
							fill="var(--color-desktop)"
							fillOpacity={0}
							stroke="black"
							strokeWidth={2}
						/>
						<Radar
							dataKey="mobile"
							fill="var(--color-mobile)"
							fillOpacity={0}
							stroke="gray"
							strokeWidth={2}
						/>
					</RadarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
}
