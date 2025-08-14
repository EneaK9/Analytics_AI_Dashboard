"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface LineChartOneProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

export default function LineChartOne({
	data = [],
	title = "Line Chart",
	description = "ApexCharts line chart with real data",
	minimal = false,
}: LineChartOneProps) {
	// Process real data for ApexCharts format
	const { categories, seriesData } = React.useMemo(() => {
		if (!data || data.length === 0) {
			// Use original fallback data if no real data
			const fallbackCategories = [
				"Jan",
				"Feb",
				"Mar",
				"Apr",
				"May",
				"Jun",
				"Jul",
				"Aug",
				"Sep",
				"Oct",
				"Nov",
				"Dec",
			];
			const fallbackSalesData = [
				180, 190, 170, 160, 175, 165, 170, 205, 230, 210, 240, 235,
			];
			const fallbackRevenueData = [
				40, 30, 50, 40, 55, 40, 70, 100, 110, 120, 150, 140,
			];
			return {
				categories: fallbackCategories,
				seriesData: [
					{ name: "Sales", data: fallbackSalesData },
					{ name: "Revenue", data: fallbackRevenueData },
				],
			};
		}

		// Transform real data for ApexCharts
		const processedCategories = data
			.slice(0, 12)
			.map(
				(item, index) =>
					item.name ||
					item.category ||
					item.symbol ||
					item.month ||
					`Item ${index + 1}`
			);

		const salesData = data
			.slice(0, 12)
			.map((item) => item.value || item.sales || item.count || item.total || 0);

		const revenueData = data
			.slice(0, 12)
			.map((item) =>
				Math.round(
					(item.value || item.sales || item.count || item.total || 0) * 0.6
				)
			);

		return {
			categories: processedCategories,
			seriesData: [
				{ name: "Primary", data: salesData },
				{ name: "Secondary", data: revenueData },
			],
		};
	}, [data]);

	const options: ApexOptions = {
		legend: {
			show: false, // Hide legend
			position: "top",
			horizontalAlign: "left",
		},
		colors: ["#465FFF", "#9CB9FF"], // Define line colors
		chart: {
			fontFamily: "Inter, sans-serif",
			height: 350,
			type: "line", // Set the chart type to 'line'
			toolbar: {
				show: false, // Hide chart toolbar
			},
		},
		stroke: {
			curve: "straight", // Define the line style (straight, smooth, or step)
			width: [2, 2], // Line width for each dataset
		},
		fill: {
			type: "gradient",
			gradient: {
				opacityFrom: 0.55,
				opacityTo: 0,
			},
		},
		markers: {
			size: 0, // Size of the marker points
			strokeColors: "#fff", // Marker border color
			strokeWidth: 2,
			hover: {
				size: 6, // Marker size on hover
			},
		},
		grid: {
			xaxis: {
				lines: {
					show: false, // Hide grid lines on x-axis
				},
			},
			yaxis: {
				lines: {
					show: true, // Show grid lines on y-axis
				},
			},
		},
		dataLabels: {
			enabled: false, // Disable data labels
		},
		tooltip: {
			enabled: true, // Enable tooltip
			x: {
				format: "dd MMM yyyy", // Format for x-axis tooltip
			},
		},
		xaxis: {
			type: "category", // Category-based x-axis
			categories: categories,
			axisBorder: {
				show: false, // Hide x-axis border
			},
			axisTicks: {
				show: false, // Hide x-axis ticks
			},
			tooltip: {
				enabled: false, // Disable tooltip for x-axis points
			},
		},
		yaxis: {
			labels: {
				style: {
					fontSize: "12px", // Adjust font size for y-axis labels
					colors: ["#6B7280"], // Color of the labels
				},
			},
			title: {
				text: "", // Remove y-axis title
				style: {
					fontSize: "0px",
				},
			},
		},
	};

	return (
		<div className="w-full h-full">
			{!minimal && (
				<div className="mb-4 h-14 flex flex-col justify-start">
					<h3 
						className="text-lg font-semibold overflow-hidden whitespace-nowrap text-ellipsis max-w-full mb-1" 
						title={title}
						style={{ 
							display: '-webkit-box',
							WebkitLineClamp: 1,
							WebkitBoxOrient: 'vertical',
							overflow: 'hidden'
						}}
					>
						{title}
					</h3>
					<p 
						className="text-sm text-muted-foreground overflow-hidden whitespace-nowrap text-ellipsis max-w-full" 
						title={description}
						style={{ 
							display: '-webkit-box',
							WebkitLineClamp: 1,
							WebkitBoxOrient: 'vertical',
							overflow: 'hidden'
						}}
					>
						{description}
					</p>
				</div>
			)}
			<div className="max-w-full overflow-x-auto">
				<div id="chartEight" className="min-w-[1000px]">
					<Chart
						options={options}
						series={seriesData}
						type="area"
						height={350}
					/>
				</div>
			</div>
		</div>
	);
}
