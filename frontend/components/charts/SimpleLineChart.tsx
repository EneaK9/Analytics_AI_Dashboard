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

	// Chart dimensions with improved padding for labels
	const leftPadding = 50; // Increased for Y-axis labels
	const rightPadding = 10;
	const topPadding = 20;
	const bottomPadding = 40; // Increased for X-axis labels
	const chartWidth = 300;
	const chartHeight = height - topPadding - bottomPadding;

	// Create points for the line
	const points = data.map((item, index) => {
		const x = leftPadding + (index / (data.length - 1)) * (chartWidth - leftPadding - rightPadding);
		const y = topPadding + ((maxValue - values[index]) / range) * chartHeight;
		return { x, y, value: values[index] };
	});

	// Create path string for the line
	const pathData = points.reduce((path, point, index) => {
		const command = index === 0 ? 'M' : 'L';
		return `${path} ${command} ${point.x} ${point.y}`;
	}, '');

	// Create area path for fill
	const areaData = `${pathData} L ${points[points.length - 1].x} ${topPadding + chartHeight} L ${leftPadding} ${topPadding + chartHeight} Z`;

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
			<div 
				className="absolute left-0 flex flex-col justify-between text-xs text-gray-500 text-right pr-2"
				style={{
					top: `${topPadding}px`,
					height: `${chartHeight}px`,
					width: `${leftPadding - 5}px`
				}}
			>
				<span className="leading-none">{maxValue.toLocaleString()}</span>
				<span className="leading-none">{Math.round((minValue + maxValue) / 2).toLocaleString()}</span>
				<span className="leading-none">{minValue.toLocaleString()}</span>
			</div>

			{/* X-axis labels */}
			<div 
				className="absolute flex justify-between text-xs text-gray-500"
				style={{
					top: `${topPadding + chartHeight + 10}px`,
					left: `${leftPadding}px`,
					right: `${rightPadding}px`,
					width: `${chartWidth - leftPadding - rightPadding}px`
				}}
			>
				<span className="truncate max-w-[60px]" title={data[0]?.date}>
					{data[0]?.date}
				</span>
				{data.length > 2 && (
					<span className="truncate max-w-[60px] text-center" title={data[Math.floor(data.length / 2)]?.date}>
						{data[Math.floor(data.length / 2)]?.date}
					</span>
				)}
				<span className="truncate max-w-[60px] text-right" title={data[data.length - 1]?.date}>
					{data[data.length - 1]?.date}
				</span>
			</div>
		</div>
	);
}
