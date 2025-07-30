"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface RadarChartProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
}

export default function RadarChart({
	data = [],
	title = "Radar Chart",
	description = "ApexCharts radar chart with real data",
	minimal = false,
}: RadarChartProps) {
	
	// Process data for radar chart format
	const processRadarData = (inputData: any[]) => {
		if (!inputData || inputData.length === 0) {
			return {
				series: [{
					name: 'Performance',
					data: [80, 50, 30, 40, 100, 20]
				}],
				categories: ['Quality', 'Efficiency', 'Speed', 'Innovation', 'Customer Satisfaction', 'Cost Effectiveness']
			};
		}

		// If data has name/value structure
		if (inputData.length > 0 && inputData[0].hasOwnProperty('name') && inputData[0].hasOwnProperty('value')) {
			return {
				series: [{
					name: 'Metrics',
					data: inputData.map(item => Number(item.value) || 0)
				}],
				categories: inputData.map(item => item.name || 'Category')
			};
		}

		// If data has multiple metrics (for multi-series radar)
		if (inputData.length > 0 && typeof inputData[0] === 'object') {
			const keys = Object.keys(inputData[0]).filter(key => key !== 'name' && key !== 'category');
			const categories = inputData.map(item => item.name || item.category || 'Category');
			
			const series = keys.map(key => ({
				name: key.charAt(0).toUpperCase() + key.slice(1),
				data: inputData.map(item => Number(item[key]) || 0)
			}));

			return { series, categories };
		}

		// Fallback data
		return {
			series: [{
				name: 'Performance',
				data: [80, 50, 30, 40, 100, 20]
			}],
			categories: ['Quality', 'Efficiency', 'Speed', 'Innovation', 'Customer Satisfaction', 'Cost Effectiveness']
		};
	};

	const { series, categories } = processRadarData(data);

	const options: ApexOptions = {
		chart: {
			height: 350,
			type: 'radar',
			toolbar: {
				show: !minimal
			},
			animations: {
				enabled: true,
				easing: 'easeinout',
				speed: 800,
			}
		},
		title: minimal ? undefined : {
			text: title,
			style: {
				fontSize: '16px',
				fontWeight: 'bold',
				color: '#374151'
			}
		},
		xaxis: {
			categories: categories,
			labels: {
				style: {
					fontSize: '12px',
					fontWeight: 500,
					colors: '#6B7280'
				}
			}
		},
		yaxis: {
			show: true,
			tickAmount: 4,
			labels: {
				style: {
					fontSize: '10px',
					colors: '#9CA3AF'
				}
			}
		},
		plotOptions: {
			radar: {
				size: 140,
				polygons: {
					strokeColors: '#e9e9e9',
					strokeWidth: 1,
					connectorColors: '#e9e9e9',
					fill: {
						colors: ['#f8f9fa', '#e9ecef']
					}
				}
			}
		},
		colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
		markers: {
			size: 4,
			colors: ['#fff'],
			strokeColors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
			strokeWidth: 2,
		},
		tooltip: {
			theme: 'light',
			y: {
				formatter: function (val: number) {
					return val.toFixed(1)
				}
			}
		},
		legend: {
			show: series.length > 1,
			position: 'bottom',
			horizontalAlign: 'center',
			fontSize: '12px',
			fontWeight: 500,
			labels: {
				colors: '#374151'
			}
		},
		stroke: {
			show: true,
			width: 2
		},
		fill: {
			opacity: 0.2
		},
		responsive: [
			{
				breakpoint: 640,
				options: {
					plotOptions: {
						radar: {
							size: 100
						}
					},
					legend: {
						position: 'bottom'
					}
				}
			}
		]
	};

	return (
		<div className="w-full">
			{!minimal && description && (
				<p className="text-sm text-gray-600 mb-4">{description}</p>
			)}
			<Chart
				options={options}
				series={series}
				type="radar"
				height={350}
			/>
		</div>
	);
} 