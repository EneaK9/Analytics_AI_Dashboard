"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface HeatmapChartProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	xAxisLabel?: string;
	yAxisLabel?: string;
}

export default function HeatmapChart({
	data = [],
	title = "Heatmap Chart",
	description = "ApexCharts heatmap with real data",
	minimal = false,
	xAxisLabel = "Categories",
	yAxisLabel = "Metrics",
}: HeatmapChartProps) {
	
	// Process data for heatmap format
	const processHeatmapData = (inputData: any[]) => {
		if (!inputData || inputData.length === 0) {
			// Generate sample heatmap data - performance matrix
			const categories = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
			const metrics = ['Sales', 'Visits', 'Conversion', 'Revenue'];
			
			return metrics.map(metric => ({
				name: metric,
				data: categories.map(category => ({
					x: category,
					y: Math.floor(Math.random() * 100) + 10
				}))
			}));
		}

		// If data has heatmap structure (x, y, value)
		if (inputData.length > 0 && inputData[0].hasOwnProperty('x') && 
			inputData[0].hasOwnProperty('y') && inputData[0].hasOwnProperty('value')) {
			
			// Group by y values (series)
			const groupedData = inputData.reduce((acc: any, item) => {
				const seriesName = item.y;
				if (!acc[seriesName]) {
					acc[seriesName] = [];
				}
				acc[seriesName].push({
					x: item.x,
					y: Number(item.value) || 0
				});
				return acc;
			}, {});

			return Object.entries(groupedData).map(([seriesName, seriesData]) => ({
				name: seriesName,
				data: seriesData
			}));
		}

		// If data has matrix structure
		if (inputData.length > 0 && typeof inputData[0] === 'object') {
			const keys = Object.keys(inputData[0]);
			const nameKey = keys.find(key => key.toLowerCase().includes('name') || 
											  key.toLowerCase().includes('category')) || keys[0];
			const numericKeys = keys.filter(key => key !== nameKey && 
				(typeof inputData[0][key] === 'number' || !isNaN(Number(inputData[0][key]))));
			
			if (numericKeys.length > 0) {
				return numericKeys.map(metric => ({
					name: metric.charAt(0).toUpperCase() + metric.slice(1),
					data: inputData.map(item => ({
						x: item[nameKey] || 'Category',
						y: Number(item[metric]) || 0
					}))
				}));
			}
		}

		// If data has simple name/value structure, create time-based heatmap
		if (inputData.length > 0 && inputData[0].hasOwnProperty('name') && 
			inputData[0].hasOwnProperty('value')) {
			
			const hours = ['00:00', '06:00', '12:00', '18:00'];
			const days = inputData.map(item => item.name).slice(0, 7);
			
			return hours.map(hour => ({
				name: hour,
				data: days.map((day, index) => ({
					x: day,
					y: Math.floor(Math.random() * 100) + 10
				}))
			}));
		}

		// Fallback sample data - weekly performance matrix
		const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
		const metrics = ['Performance', 'Quality', 'Efficiency', 'Satisfaction'];
		
		return metrics.map(metric => ({
			name: metric,
			data: days.map(day => ({
				x: day,
				y: Math.floor(Math.random() * 100) + 10
			}))
		}));
	};

	const series = processHeatmapData(data);

    const options: ApexOptions = {
        chart: {
            height: 350,
            width: '100%',
            type: 'heatmap',
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
		plotOptions: {
			heatmap: {
				shadeIntensity: 0.5,
				radius: 8,
				useFillColorAsStroke: true,
				colorScale: {
					ranges: [
						{
							from: 0,
							to: 25,
							name: 'Low',
							color: '#EF4444'
						},
						{
							from: 26,
							to: 50,
							name: 'Medium',
							color: '#F59E0B'
						},
						{
							from: 51,
							to: 75,
							name: 'Good',
							color: '#10B981'
						},
						{
							from: 76,
							to: 100,
							name: 'Excellent',
							color: '#059669'
						}
					]
				}
			}
		},
		dataLabels: {
			enabled: true,
			style: {
				fontSize: '10px',
				fontWeight: 'bold',
				colors: ['#fff']
			}
		},
		xaxis: {
			title: {
				text: xAxisLabel,
				style: {
					fontSize: '12px',
					fontWeight: 600,
					color: '#374151'
				}
			},
			labels: {
				style: {
					fontSize: '11px',
					colors: '#6B7280'
				}
			}
		},
		yaxis: {
			title: {
				text: yAxisLabel,
				style: {
					fontSize: '12px',
					fontWeight: 600,
					color: '#374151'
				}
			},
			labels: {
				style: {
					fontSize: '11px',
					colors: '#6B7280'
				}
			}
		},
		tooltip: {
			theme: 'light',
			custom: function({series, seriesIndex, dataPointIndex, w}) {
				const value = series[seriesIndex][dataPointIndex];
				const xCategory = w.globals.categoryLabels[dataPointIndex];
				const seriesName = w.globals.seriesNames[seriesIndex];
				
				return `
					<div class="px-3 py-2">
						<div class="font-semibold text-sm">${seriesName}</div>
						<div class="text-xs mt-1">
							<div>${xAxisLabel}: <span class="font-medium">${xCategory}</span></div>
							<div>Value: <span class="font-medium">${value}</span></div>
						</div>
					</div>
				`;
			}
		},
		legend: {
			show: false
		},
		grid: {
			show: false,
			padding: {
				left: 20,
				right: 20,
				top: 20,
				bottom: 20
			}
		},
        responsive: [
            {
                breakpoint: 640,
                options: {
                    chart: {
                        height: 300,
                        width: '100%'
                    },
                    dataLabels: {
                        enabled: false
                    }
                }
            }
        ]
	};

	return (
        <div className="w-full">
			{!minimal && description && (
				<div className="mb-4 h-14 flex flex-col justify-start">
					<p 
						className="text-sm text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis max-w-full" 
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
			<Chart
				options={options}
				series={series}
				type="heatmap"
                height={350}
                width="100%"
			/>
		</div>
	);
} 