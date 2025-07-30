"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface PieChartProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	showLegend?: boolean;
	chartType?: 'pie' | 'donut';
}

export default function PieChart({
	data = [],
	title = "Pie Chart",
	description = "ApexCharts pie chart with real data",
	minimal = false,
	showLegend = true,
	chartType = 'pie',
}: PieChartProps) {
	
	// Process data for pie chart format
	const processPieData = (inputData: any[]) => {
		if (!inputData || inputData.length === 0) {
			return {
				series: [44, 55, 13, 43, 22],
				labels: ['Desktop', 'Mobile', 'Tablet', 'Smart TV', 'Other']
			};
		}

		// If data has name/value structure
		if (inputData.length > 0 && inputData[0].hasOwnProperty('name') && inputData[0].hasOwnProperty('value')) {
			const series = inputData.map(item => Number(item.value) || 0);
			const labels = inputData.map(item => item.name || 'Category');
			
			return { series, labels };
		}

		// If data has multiple properties, use the first numeric one
		if (inputData.length > 0 && typeof inputData[0] === 'object') {
			const keys = Object.keys(inputData[0]);
			const nameKey = keys.find(key => key.toLowerCase().includes('name') || 
											  key.toLowerCase().includes('category') ||
											  key.toLowerCase().includes('label')) || keys[0];
			const valueKeys = keys.filter(key => key !== nameKey && 
				(typeof inputData[0][key] === 'number' || !isNaN(Number(inputData[0][key]))));
			
			if (valueKeys.length > 0) {
				const series = inputData.map(item => Number(item[valueKeys[0]]) || 0);
				const labels = inputData.map(item => item[nameKey] || 'Category');
				
				return { series, labels };
			}
		}

		// If data is just an array of numbers
		if (inputData.length > 0 && typeof inputData[0] === 'number') {
			const series = inputData;
			const labels = series.map((_, index) => `Category ${index + 1}`);
			
			return { series, labels };
		}

		// Fallback data
		return {
			series: [44, 55, 13, 43, 22],
			labels: ['Desktop', 'Mobile', 'Tablet', 'Smart TV', 'Other']
		};
	};

	const { series, labels } = processPieData(data);

	const options: ApexOptions = {
		chart: {
			width: 380,
			type: chartType,
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
		labels: labels,
		colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316', '#84CC16'],
		dataLabels: {
			enabled: true,
			style: {
				fontSize: '12px',
				fontWeight: 'bold',
				colors: ['#fff']
			},
			dropShadow: {
				enabled: false
			}
		},
		plotOptions: {
			pie: {
				donut: chartType === 'donut' ? {
					size: '65%',
					labels: {
						show: true,
						name: {
							show: true,
							fontSize: '16px',
							fontWeight: 600,
							color: '#374151'
						},
						value: {
							show: true,
							fontSize: '14px',
							fontWeight: 'bold',
							color: '#1F2937',
						},
						total: {
							show: true,
							showAlways: false,
							label: 'Total',
							fontSize: '16px',
							fontWeight: 600,
							color: '#374151',
							formatter: function (w: any) {
								return w.globals.seriesTotals.reduce((a: number, b: number) => {
									return a + b
								}, 0)
							}
						}
					}
				} : undefined,
				expandOnClick: true,
				customScale: 1
			}
		},
		legend: {
			show: showLegend,
			position: 'bottom',
			horizontalAlign: 'center',
			fontSize: '12px',
			fontWeight: 500,
			labels: {
				colors: '#374151'
			},
			markers: {
				width: 12,
				height: 12,
				strokeWidth: 0,
				strokeColor: '#fff',
				fillColors: undefined,
				radius: 12,
				customHTML: undefined,
				onClick: undefined,
				offsetX: 0,
				offsetY: 0
			},
			itemMargin: {
				horizontal: 5,
				vertical: 5
			}
		},
		tooltip: {
			enabled: true,
			theme: 'light',
			y: {
				formatter: function (val: number) {
					return val.toString()
				}
			}
		},
		stroke: {
			show: false,
			width: 2,
			colors: ['#fff']
		},
		responsive: [
			{
				breakpoint: 640,
				options: {
					chart: {
						width: 300
					},
					legend: {
						position: 'bottom'
					}
				}
			}
		]
	};

	return (
		<div className="w-full flex justify-center">
			{!minimal && description && (
				<div className="w-full">
					<p className="text-sm text-gray-600 mb-4">{description}</p>
				</div>
			)}
			<Chart
				options={options}
				series={series}
				type={chartType}
				width={380}
			/>
		</div>
	);
} 