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
	ChartLegend,
	ChartLegendContent,
	ChartTooltip,
	ChartTooltipContent,
} from "@/components/ui/chart";

interface ShadcnRadarLegendProps {
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

const ShadcnRadarLegend: React.FC<ShadcnRadarLegendProps> = ({
	data,
	title = "Radar Chart - Legend",
	description = "Showing total visitors for the last 6 months",
	minimal = false,
}) => {
	return (
		<Card>
			
			<CardContent>
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<RadarChart
						data={chartData}
						margin={{
							top: -40,
							bottom: -10,
						}}>
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
						<ChartLegend className="mt-8" content={<ChartLegendContent />} />
					</RadarChart>
				</ChartContainer>
			</CardContent>
			
		</Card>
	);
};

export default ShadcnRadarLegend;
