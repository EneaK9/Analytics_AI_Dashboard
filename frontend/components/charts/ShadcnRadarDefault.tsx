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

interface ShadcnRadarDefaultProps {
	data: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

const chartData = [
	{ month: "January", desktop: 186 },
	{ month: "February", desktop: 305 },
	{ month: "March", desktop: 237 },
	{ month: "April", desktop: 273 },
	{ month: "May", desktop: 209 },
	{ month: "June", desktop: 214 },
];

const chartConfig = {
	desktop: {
		label: "Desktop",
		color: "var(--chart-1)",
	},
} satisfies ChartConfig;

const ShadcnRadarDefault: React.FC<ShadcnRadarDefaultProps> = ({
	data,
	title = "Radar Chart",
	description = "Showing total visitors for the last 6 months",
	minimal = false,
}) => {
	// Use real data instead of hardcoded chartData
	const processedData = React.useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		return data.slice(0, 6).map((item, index) => {
			const month =
				item.name || item.month || item.category || `Item ${index + 1}`;
			const desktop =
				item.value || item.desktop || item.visitors || item.amount || 0;

			return {
				month: month.toString().slice(0, 10), // Limit length
				desktop: Number(desktop) || 0,
			};
		});
	}, [data]);

	// Don't render if no data
	if (processedData.length === 0) {
		return (
			<Card>
				<CardHeader className="items-center pb-0">
					{!minimal && (
						<>
							<CardTitle>{title}</CardTitle>
							<CardDescription>{description}</CardDescription>
						</>
					)}
				</CardHeader>
				<CardContent className="pb-0">
					<div className="flex items-center justify-center h-[250px] text-muted-foreground">
						No data available for radar chart
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			<CardHeader className="items-center pb-0">
				{!minimal && (
					<>
						<CardTitle>{title}</CardTitle>
						<CardDescription>{description}</CardDescription>
					</>
				)}
			</CardHeader>
			<CardContent className="pb-0">
				<ChartContainer
					config={chartConfig}
					className="mx-auto aspect-square max-h-[250px]">
					<RadarChart data={processedData}>
						<ChartTooltip cursor={false} content={<ChartTooltipContent />} />
						<PolarAngleAxis dataKey="month" />
						<PolarGrid />
						<Radar
							dataKey="desktop"
							fill="var(--color-desktop)"
							fillOpacity={0.6}
						/>
					</RadarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	);
};

export default ShadcnRadarDefault;
