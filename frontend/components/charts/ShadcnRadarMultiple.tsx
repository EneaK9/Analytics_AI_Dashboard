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

interface ShadcnRadarMultipleProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const chartData = [
	{ month: "January", desktop: 186, mobile: 80 },
	{ month: "February", desktop: 305, mobile: 200 },
	{ month: "March", desktop: 237, mobile: 120 },
	{ month: "April", desktop: 73, mobile: 190 },
	{ month: "May", desktop: 209, mobile: 130 },
	{ month: "June", desktop: 214, mobile: 140 },
];

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

const ShadcnRadarMultiple: React.FC<ShadcnRadarMultipleProps> = ({
	data,
	title = "Radar Chart - Multiple",
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
};

export default ShadcnRadarMultiple;
