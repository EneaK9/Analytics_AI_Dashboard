"use client";

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

interface ShadcnRadarGridFillProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const chartData = [
	{ month: "January", desktop: 186 },
	{ month: "February", desktop: 285 },
	{ month: "March", desktop: 237 },
	{ month: "April", desktop: 203 },
	{ month: "May", desktop: 209 },
	{ month: "June", desktop: 264 },
];

const chartConfig = {
	desktop: {
		label: "Desktop",
		color: "var(--chart-1)",
	},
} satisfies ChartConfig;

const ShadcnRadarGridFill: React.FC<ShadcnRadarGridFillProps> = ({
	data,
	title = "Radar Chart - Grid Filled",
	description = "Showing total visitors for the last 6 months",
	minimal = false,
}) => {
	return (
		<Card>
			
			<CardContent className="pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<RadarChart data={chartData}>
						<ChartTooltip
							cursor={false}
							content={<ChartTooltipContent hideLabel />}
						/>
						<PolarGrid className="fill-(--color-desktop) opacity-20" />
						<PolarAngleAxis dataKey="month" />
						<Radar
							dataKey="desktop"
							fill="var(--color-desktop)"
							fillOpacity={0.5}
						/>
					</RadarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
};

export default ShadcnRadarGridFill;
