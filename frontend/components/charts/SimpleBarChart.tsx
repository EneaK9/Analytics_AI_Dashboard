"use client";

import React from "react";

interface DataPoint {
	name?: string;
	date?: string;
	value: number;
	[key: string]: any;
}

interface SimpleBarChartProps {
	data: DataPoint[];
	color?: string;
	height?: number;
	className?: string;
}

export default function SimpleBarChart({
	data,
	color = "#10b981",
	height = 200,
	className = "",
}: SimpleBarChartProps) {
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
	const values = data.map(d => d.value || d.revenue || d.units || 0);
	const maxValue = Math.max(...values);
	const minValue = Math.min(...values, 0);
	const range = maxValue - minValue || 1;

	// Chart dimensions
	const padding = 20;
	const chartWidth = 300;
	const chartHeight = height - padding * 2;
	const barWidth = Math.max(8, (chartWidth - padding * 2) / data.length - 4);

	return (
		<div className={`relative ${className}`}>
			<svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} className="overflow-visible">
				{/* Grid lines */}
				<defs>
					<pattern id="barGrid" width="20" height="20" patternUnits="userSpaceOnUse">
						<path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
					</pattern>
				</defs>
				<rect width="100%" height="100%" fill="url(#barGrid)" />

				{/* Bars */}
				{data.map((item, index) => {
					const value = values[index];
					const barHeight = Math.abs(value - minValue) / range * chartHeight;
					const x = padding + (index * (chartWidth - padding * 2)) / data.length + ((chartWidth - padding * 2) / data.length - barWidth) / 2;
					const y = value >= 0 
						? padding + chartHeight - barHeight
						: padding + chartHeight - (Math.abs(minValue) / range * chartHeight);

					return (
						<rect
							key={index}
							x={x}
							y={y}
							width={barWidth}
							height={barHeight}
							fill={color}
							className="hover:opacity-80 transition-opacity cursor-pointer"
							rx="2"
						>
							<title>{`${item.name || item.date}: ${value.toLocaleString()}`}</title>
						</rect>
					);
				})}

				{/* Zero line if needed */}
				{minValue < 0 && (
					<line
						x1={padding}
						y1={padding + chartHeight - (Math.abs(minValue) / range * chartHeight)}
						x2={chartWidth - padding}
						y2={padding + chartHeight - (Math.abs(minValue) / range * chartHeight)}
						stroke="#6b7280"
						strokeWidth="1"
						strokeDasharray="2,2"
					/>
				)}
			</svg>

			{/* Y-axis labels */}
			<div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 -ml-2">
				<span>{maxValue.toLocaleString()}</span>
				{minValue < 0 && maxValue > 0 && (
					<span>0</span>
				)}
				<span>{minValue.toLocaleString()}</span>
			</div>

			{/* X-axis labels */}
			<div className="flex justify-between text-xs text-gray-500 mt-2 px-5">
				{data.length <= 3 ? (
					data.map((item, index) => (
						<span key={index} className="truncate">
							{item.name || item.date}
						</span>
					))
				) : (
					<>
						<span>{data[0]?.name || data[0]?.date}</span>
						<span>{data[Math.floor(data.length / 2)]?.name || data[Math.floor(data.length / 2)]?.date}</span>
						<span>{data[data.length - 1]?.name || data[data.length - 1]?.date}</span>
					</>
				)}
			</div>
		</div>
	);
}
