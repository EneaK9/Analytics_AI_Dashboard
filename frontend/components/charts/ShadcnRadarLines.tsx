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
	// Process REAL data only
	const { chartData, dataKey } = React.useMemo(() => {
		if (!data || data.length === 0) {
			return { chartData: [], dataKey: "value" };
		}

		// Find numeric columns for radar metrics
		const numericKeys = Object.keys(data[0] || {}).filter((key) => {
			const values = data
				.map((item: any) => item[key])
				.filter((v) => v != null);
			return values.length > 0 && values.every((v) => !isNaN(Number(v)));
		});

		// Use first numeric column for single metric radar
		const key1 = numericKeys[0] || "value";

		// Process data for radar chart
		const processedData = data
			.slice(0, 6)
			.map((item: any, index: number) => {
				const nameValue =
					item.name ||
					item.month ||
					item.category ||
					item.symbol ||
					`Point ${index + 1}`;
				const value1 =
					Number(item[key1]) ||
					Number(item.value) ||
					Number(item.count) ||
					Number(item.total) ||
					0;

				return {
					name: String(nameValue).slice(0, 8),
					[key1]: value1,
				};
			})
			.filter((item) => Number(item[key1]) > 0);

		return {
			chartData: processedData,
			dataKey: key1,
		};
	}, [data]);

	if (chartData.length === 0) {
		return (
			<div className="w-full h-full">
				{!minimal && (
					<div className="mb-4">
						<h3 className="text-lg font-semibold">{title}</h3>
						<p className="text-sm text-muted-foreground">{description}</p>
					</div>
				)}
				<div className="flex items-center justify-center h-[250px] text-muted-foreground">
					No data available
				</div>
			</div>
		);
	}

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
					<PolarGrid gridType="polygon" stroke="transparent" />
					<PolarAngleAxis dataKey="name" />
					<PolarRadiusAxis angle={0} domain={[0, "dataMax"]} tick={false} />
					<ChartTooltip
						cursor={false}
						content={<ChartTooltipContent hideLabel />}
					/>
					<Radar
						name="Data"
						dataKey={dataKey}
						stroke="var(--chart-1)"
						fill="var(--chart-1)"
						fillOpacity={0.2}
						strokeWidth={2}
						dot={{ r: 6, fill: "var(--chart-1)", strokeWidth: 2 }}
					/>
				</RadarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShadcnRadarLines;
