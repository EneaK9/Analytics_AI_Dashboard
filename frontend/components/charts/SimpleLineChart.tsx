"use client";

import React from "react";

interface DataPoint {
	date: string;
	value: number;
	[key: string]: any;
}

interface SimpleLineChartProps {
	data: DataPoint[];
	color?: string;
	height?: number;
	className?: string;
}

export default function SimpleLineChart({
	data,
	color = "#3b82f6",
	height = 200,
	className = "",
}: SimpleLineChartProps) {
	if (!data || data.length === 0) {
		return (
			<div 
				className={`flex items-center justify-center text-gray-400 ${className}`}
				style={{ height }}>
				<p className="text-sm">No data available</p>
			</div>
		);
	}

	// Extract values and find min/max
	const values = data.map(d => d.value || d.inventory || d.units || 0);
	const minValue = Math.min(...values);
	const maxValue = Math.max(...values);
	const range = maxValue - minValue || 1;

	// Chart dimensions
	const padding = 20;
	const chartWidth = 300;
	const chartHeight = height - padding * 2;

	// Create points for the line
	const points = data.map((item, index) => {
		const x = padding + (index / (data.length - 1)) * (chartWidth - padding * 2);
		const y = padding + chartHeight - ((values[index] - minValue) / range) * chartHeight;
		return { x, y, value: values[index] };
	});

	// Create path string for the line
	const pathData = points.reduce((path, point, index) => {
		const command = index === 0 ? 'M' : 'L';
		return `${path} ${command} ${point.x} ${point.y}`;
	}, '');

	// Create area path for fill
	const areaData = `${pathData} L ${points[points.length - 1].x} ${height - padding} L ${padding} ${height - padding} Z`;

	return (
		<div className={`relative ${className}`}>
			<svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} className="overflow-visible">
				{/* Grid lines */}
				<defs>
					<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
						<path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
					</pattern>
				</defs>
				<rect width="100%" height="100%" fill="url(#grid)" />

				{/* Area fill */}
				<path
					d={areaData}
					fill={color}
					fillOpacity="0.1"
				/>

				{/* Line */}
				<path
					d={pathData}
					fill="none"
					stroke={color}
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
				/>

				{/* Data points */}
				{points.map((point, index) => (
					<circle
						key={index}
						cx={point.x}
						cy={point.y}
						r="3"
						fill={color}
						className="hover:r-4 transition-all cursor-pointer"
					>
						<title>{`${data[index].date}: ${point.value.toLocaleString()}`}</title>
					</circle>
				))}
			</svg>

			{/* Y-axis labels */}
			<div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 -ml-2">
				<span>{maxValue.toLocaleString()}</span>
				<span>{Math.round((minValue + maxValue) / 2).toLocaleString()}</span>
				<span>{minValue.toLocaleString()}</span>
			</div>

			{/* X-axis labels */}
			<div className="flex justify-between text-xs text-gray-500 mt-2 px-5">
				<span>{data[0]?.date}</span>
				{data.length > 2 && (
					<span>{data[Math.floor(data.length / 2)]?.date}</span>
				)}
				<span>{data[data.length - 1]?.date}</span>
			</div>
		</div>
	);
}
