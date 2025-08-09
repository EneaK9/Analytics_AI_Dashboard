"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface ScatterChartProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	xAxisLabel?: string;
	yAxisLabel?: string;
}

export default function ScatterChart({
	data = [],
	title = "Scatter Chart",
	description = "ApexCharts scatter plot with real data",
	minimal = false,
	xAxisLabel = "X Axis",
	yAxisLabel = "Y Axis",
}: ScatterChartProps) {
	
	// Process data for scatter chart format
	const processScatterData = (inputData: any[]) => {
		if (!inputData || inputData.length === 0) {
			// Generate sample correlation data
			const sampleData = Array.from({ length: 50 }, (_, i) => [
				Math.random() * 100 + 10,
				Math.random() * 80 + 20 + (Math.random() - 0.5) * 20
			]);
			return [{
				name: 'Performance vs Quality',
				data: sampleData
			}];
		}

		// If data has x/y structure
		if (inputData.length > 0 && inputData[0].hasOwnProperty('x') && inputData[0].hasOwnProperty('y')) {
			return [{
				name: 'Data Points',
				data: inputData.map(item => [Number(item.x) || 0, Number(item.y) || 0])
			}];
		}

		// If data has name/value structure, create correlation
		if (inputData.length > 0 && inputData[0].hasOwnProperty('name') && inputData[0].hasOwnProperty('value')) {
			return [{
				name: 'Correlation',
				data: inputData.map((item, index) => [
					index + 1,
					Number(item.value) || 0
				])
			}];
		}

		// If data has multiple numeric properties, create scatter plot
		if (inputData.length > 0 && typeof inputData[0] === 'object') {
			const keys = Object.keys(inputData[0]).filter(key => {
				return typeof inputData[0][key] === 'number' || !isNaN(Number(inputData[0][key]));
			});
			
			if (keys.length >= 2) {
				const series = [];
				
				// Create scatter series for first two numeric columns
				series.push({
					name: `${keys[0]} vs ${keys[1]}`,
					data: inputData.map(item => [
						Number(item[keys[0]]) || 0,
						Number(item[keys[1]]) || 0
					])
				});

				// If there's a third numeric column, add another series
				if (keys.length >= 3) {
					series.push({
						name: `${keys[0]} vs ${keys[2]}`,
						data: inputData.map(item => [
							Number(item[keys[0]]) || 0,
							Number(item[keys[2]]) || 0
						])
					});
				}

				return series;
			}
		}

		// Fallback sample data
		const sampleData = Array.from({ length: 30 }, (_, i) => [
			Math.random() * 100 + 10,
			Math.random() * 80 + 20 + (Math.random() - 0.5) * 20
		]);
		return [{
			name: 'Sample Data',
			data: sampleData
		}];
	};

	const series = processScatterData(data);

    const options: ApexOptions = {
        chart: {
            height: 350,
            width: '100%',
            type: 'scatter',
            zoom: {
                enabled: true,
                type: 'xy'
            },
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
			},
			tickAmount: 10,
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
			},
			tickAmount: 7,
		},
		colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
		markers: {
			size: 6,
			strokeColors: '#fff',
			strokeWidth: 2,
			hover: {
				size: 8
			}
		},
		tooltip: {
			theme: 'light',
			intersect: false,
			shared: false,
			custom: function({series, seriesIndex, dataPointIndex, w}) {
				const point = w.globals.initialSeries[seriesIndex].data[dataPointIndex];
				return `
					<div class="px-3 py-2">
						<div class="font-semibold text-sm">${w.globals.seriesNames[seriesIndex]}</div>
						<div class="text-xs mt-1">
							<div>${xAxisLabel}: <span class="font-medium">${point[0].toFixed(2)}</span></div>
							<div>${yAxisLabel}: <span class="font-medium">${point[1].toFixed(2)}</span></div>
						</div>
					</div>
				`;
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
		grid: {
			show: true,
			borderColor: '#E5E7EB',
			strokeDashArray: 0,
			position: 'back',
			xaxis: {
				lines: {
					show: true
				}
			},
			yaxis: {
				lines: {
					show: true
				}
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
				type="scatter"
                height={350}
                width="100%"
			/>
		</div>
	);
} 