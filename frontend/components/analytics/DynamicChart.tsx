import React from "react";
import {
	LineChart,
	Line,
	BarChart,
	Bar,
	PieChart,
	Pie,
	Cell,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	ResponsiveContainer,
	AreaChart,
	Area,
	ScatterChart,
	Scatter,
} from "recharts";

export interface ChartData {
	[key: string]: any;
}

export interface ChartConfig {
	responsive?: boolean;
	showLegend?: boolean;
	showGrid?: boolean;
	colors?: string[];
	strokeWidth?: number;
	fillOpacity?: number;
}

export interface DynamicChartProps {
	type: "line" | "bar" | "pie" | "doughnut" | "area" | "scatter";
	data: ChartData[];
	config?: ChartConfig;
	width?: number;
	height?: number;
	title?: string;
	subtitle?: string;
	dataKey?: string;
	nameKey?: string;
	valueKey?: string;
}

const DEFAULT_COLORS = [
	"#3C50E0", // Primary blue
	"#10B981", // Success green
	"#F59E0B", // Warning yellow
	"#EF4444", // Error red
	"#8B5CF6", // Purple
	"#06B6D4", // Cyan
	"#F97316", // Orange
	"#84CC16", // Lime
];

const DynamicChart: React.FC<DynamicChartProps> = ({
	type,
	data,
	config = {},
	width,
	height = 300,
	title,
	subtitle,
	dataKey = "value",
	nameKey = "name",
	valueKey = "value",
}) => {
	const {
		responsive = true,
		showLegend = true,
		showGrid = true,
		colors = DEFAULT_COLORS,
		strokeWidth = 2,
		fillOpacity = 0.6,
	} = config;

	const renderChart = () => {
		const commonProps = {
			width: responsive ? undefined : width,
			height: responsive ? undefined : height,
			data,
		};

		switch (type) {
			case "line":
				return (
					<LineChart {...commonProps}>
						{showGrid && (
							<CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
						)}
						<XAxis
							dataKey={nameKey}
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<YAxis
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<Tooltip
							contentStyle={{
								backgroundColor: "#FFFFFF",
								border: "1px solid #E5E7EB",
								borderRadius: "8px",
								boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
							}}
						/>
						{showLegend && <Legend />}
						<Line
							type="monotone"
							dataKey={dataKey}
							stroke={colors[0]}
							strokeWidth={strokeWidth}
							dot={{ fill: colors[0], strokeWidth: 2, r: 4 }}
							activeDot={{ r: 6, fill: colors[0] }}
						/>
					</LineChart>
				);

			case "area":
				return (
					<AreaChart {...commonProps}>
						{showGrid && (
							<CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
						)}
						<XAxis
							dataKey={nameKey}
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<YAxis
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<Tooltip
							contentStyle={{
								backgroundColor: "#FFFFFF",
								border: "1px solid #E5E7EB",
								borderRadius: "8px",
								boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
							}}
						/>
						{showLegend && <Legend />}
						<Area
							type="monotone"
							dataKey={dataKey}
							stroke={colors[0]}
							strokeWidth={strokeWidth}
							fill={colors[0]}
							fillOpacity={fillOpacity}
						/>
					</AreaChart>
				);

			case "bar":
				return (
					<BarChart {...commonProps}>
						{showGrid && (
							<CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
						)}
						<XAxis
							dataKey={nameKey}
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<YAxis
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<Tooltip
							contentStyle={{
								backgroundColor: "#FFFFFF",
								border: "1px solid #E5E7EB",
								borderRadius: "8px",
								boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
							}}
						/>
						{showLegend && <Legend />}
						<Bar dataKey={dataKey} fill={colors[0]} radius={[4, 4, 0, 0]} />
					</BarChart>
				);

			case "pie":
			case "doughnut":
				return (
					<PieChart {...commonProps}>
						<Pie
							dataKey={valueKey}
							nameKey={nameKey}
							cx="50%"
							cy="50%"
							innerRadius={type === "doughnut" ? 60 : 0}
							outerRadius={100}
							paddingAngle={2}
							data={data}
							label={({ name, percent }) =>
								`${name} ${(percent * 100).toFixed(0)}%`
							}
							labelLine={false}>
							{data.map((entry, index) => (
								<Cell
									key={`cell-${index}`}
									fill={colors[index % colors.length]}
								/>
							))}
						</Pie>
						<Tooltip
							contentStyle={{
								backgroundColor: "#FFFFFF",
								border: "1px solid #E5E7EB",
								borderRadius: "8px",
								boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
							}}
						/>
						{showLegend && <Legend />}
					</PieChart>
				);

			case "scatter":
				return (
					<ScatterChart {...commonProps}>
						{showGrid && (
							<CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
						)}
						<XAxis
							dataKey={nameKey}
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<YAxis
							axisLine={false}
							tickLine={false}
							tick={{ fill: "#6B7280", fontSize: 12 }}
						/>
						<Tooltip
							contentStyle={{
								backgroundColor: "#FFFFFF",
								border: "1px solid #E5E7EB",
								borderRadius: "8px",
								boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
							}}
						/>
						{showLegend && <Legend />}
						<Scatter dataKey={dataKey} fill={colors[0]} />
					</ScatterChart>
				);

			default:
				return <div>Unsupported chart type: {type}</div>;
		}
	};

	return (
		<div className="w-full bg-white dark:bg-boxdark rounded-lg border border-stroke p-6">
			{(title || subtitle) && (
				<div className="mb-6">
					{title && (
						<h3 className="text-xl font-semibold text-black dark:text-white mb-1">
							{title}
						</h3>
					)}
					{subtitle && (
						<p className="text-sm text-body dark:text-bodydark">{subtitle}</p>
					)}
				</div>
			)}

			<div className="w-full" style={{ height: height }}>
				{responsive ? (
					<ResponsiveContainer width="100%" height="100%">
						{renderChart()}
					</ResponsiveContainer>
				) : (
					renderChart()
				)}
			</div>
		</div>
	);
};

export default DynamicChart;
