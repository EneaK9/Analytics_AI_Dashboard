"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface BarChartOneProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

export default function BarChartOne({
	data = [],
	title = "Bar Chart",
	description = "ApexCharts bar chart with real data",
	minimal = false,
}: BarChartOneProps) {
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
			const fallbackData = [
				168, 385, 201, 298, 187, 195, 291, 110, 215, 390, 280, 112,
			];
			return { categories: fallbackCategories, seriesData: fallbackData };
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
		const processedData = data
			.slice(0, 12)
			.map((item) => item.value || item.sales || item.count || item.total || 0);

		return { categories: processedCategories, seriesData: processedData };
	}, [data]);

	const options: ApexOptions = {
		colors: ["#465fff"],
		chart: {
			fontFamily: "Inter, sans-serif",
			type: "bar",
			height: 350,
			toolbar: {
				show: false,
			},
		},
		plotOptions: {
			bar: {
				horizontal: false,
				columnWidth: "39%",
				borderRadius: 5,
				borderRadiusApplication: "end",
			},
		},
		dataLabels: {
			enabled: false,
		},
		stroke: {
			show: true,
			width: 4,
			colors: ["transparent"],
		},
		xaxis: {
			categories: categories,
			axisBorder: {
				show: false,
			},
			axisTicks: {
				show: false,
			},
		},
		legend: {
			show: true,
			position: "top",
			horizontalAlign: "left",
			fontFamily: "Inter",
		},
		yaxis: {
			title: {
				text: undefined,
			},
		},
		grid: {
			yaxis: {
				lines: {
					show: true,
				},
			},
		},
		fill: {
			opacity: 1,
		},
		tooltip: {
			x: {
				show: false,
			},
			y: {
				formatter: (val: number) => `${val}`,
			},
		},
	};

	const series = [
		{
			name: "Sales",
			data: seriesData,
		},
	];

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
				<div id="chartOne" className="min-w-[1000px]">
					<Chart options={options} series={series} type="bar" height={350} />
				</div>
			</div>
		</div>
	);
}
