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

export const description = "A radar chart with multiple data";

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

interface ShadcnRadarMultipleProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	ai_labels?: any;
}

export function ShadcnRadarMultiple({
	data = [],
	title,
	description,
	minimal,
	ai_labels,
}: ShadcnRadarMultipleProps) {
	// Transform real data to match original structure EXACTLY
	const chartData = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data with EXACT same structure
			return [
				{ month: "January", desktop: 186, mobile: 80 },
				{ month: "February", desktop: 305, mobile: 200 },
				{ month: "March", desktop: 237, mobile: 120 },
				{ month: "April", desktop: 73, mobile: 190 },
				{ month: "May", desktop: 209, mobile: 130 },
				{ month: "June", desktop: 214, mobile: 140 },
			];
		}

		// Transform real data to match original structure
		return data.slice(0, 6).map((item, index) => ({
			month: item.name || item.category || item.symbol || `Month ${index + 1}`,
			desktop: item.value || item.desktop || item.count || item.total || 0,
			mobile: Math.max(
				1,
				Math.round(
					(item.value || item.desktop || item.count || item.total || 0) * 0.7
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
						<PolarGrid />
						<Radar
							dataKey="desktop"
							fill="var(--color-desktop)"
							fillOpacity={0.6}
						/>
						<Radar dataKey="mobile" fill="var(--color-mobile)" />
					</RadarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
}
