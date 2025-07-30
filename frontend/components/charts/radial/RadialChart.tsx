"use client";

import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to prevent SSR issues
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

interface RadialChartProps {
	data?: any[];
	title?: string;
	description?: string;
	minimal?: boolean;
	showLabels?: boolean;
}

export default function RadialChart({
	data = [],
	title = "Radial Chart",
	description = "ApexCharts radial bar chart with real data",
	minimal = false,
	showLabels = true,
}: RadialChartProps) {
	
	console.log("🎯 RadialChart component initialized with:", {
		dataLength: data.length,
		dataStructure: data.map((item, i) => ({
			index: i,
			hasName: !!item?.name,
			hasCategory: !!item?.category,
			hasValue: !!item?.value,
			actualName: item?.name,
			actualCategory: item?.category,
			actualValue: item?.value,
			allKeys: item ? Object.keys(item) : []
		}))
	});
	
	// Process data for radial chart format
	const processRadialData = (inputData: any[]) => {
		console.log("🔍 RadialChart processing:", inputData);
		
		if (!inputData || inputData.length === 0) {
			console.log("📊 RadialChart: No data provided, using fallback");
			return {
				series: [76, 67, 61, 90],
				labels: ['Performance', 'Quality', 'Efficiency', 'Customer Satisfaction']
			};
		}

		// If data has name/value structure
		if (inputData.length > 0 && inputData[0].hasOwnProperty('name') && inputData[0].hasOwnProperty('value')) {
			// Always calculate proper percentages from the values
			const values = inputData.map(item => Number(item.value) || 0);
			const total = values.reduce((sum, val) => sum + val, 0);
			
			const series = inputData.map(item => {
				const rawValue = Number(item.value) || 0;
				// Always calculate percentage as (value / total) * 100
				const percentage = total > 0 ? Math.round((rawValue / total) * 100) : 0;
				return percentage;
			});
			const labels = inputData.map(item => item.name || 'Category');
			
			console.log("📊 RadialChart result:", { series, labels, total });
			return { series, labels };
		}

		// If data has percentage/score structure
		if (inputData.length > 0 && typeof inputData[0] === 'object') {
			const keys = Object.keys(inputData[0]);
			const nameKey = keys.find(key => key.toLowerCase().includes('name') || 
											  key.toLowerCase().includes('category') ||
											  key.toLowerCase().includes('label')) || keys[0];
			const valueKeys = keys.filter(key => key !== nameKey && 
				(typeof inputData[0][key] === 'number' || !isNaN(Number(inputData[0][key]))));
			
			if (valueKeys.length > 0) {
				// Take first 4-5 items for radial chart
				const limitedData = inputData.slice(0, 5);
				const values = limitedData.map(item => Number(item[valueKeys[0]]) || 0);
				const total = values.reduce((sum, val) => sum + val, 0);
				
				const series = limitedData.map(item => {
					const rawValue = Number(item[valueKeys[0]]) || 0;
					// Always calculate proper percentage
					const percentage = total > 0 ? Math.round((rawValue / total) * 100) : 0;
					return percentage;
				});
				const labels = limitedData.map(item => item[nameKey] || 'Category');
				
				console.log("📊 RadialChart object result:", { series, labels, total });
				return { series, labels };
			}
		}

		// If data is just an array of numbers
		if (inputData.length > 0 && typeof inputData[0] === 'number') {
			const series = inputData.slice(0, 5).map(value => {
				const num = Number(value) || 0;
				return num > 100 ? Math.min(num / 10, 100) : num;
			});
			const labels = series.map((_, index) => `Metric ${index + 1}`);
			
			return { series, labels };
		}

		// Fallback data
		return {
			series: [76, 67, 61, 90],
			labels: ['Performance', 'Quality', 'Efficiency', 'Customer Satisfaction']
		};
	};

	const { series, labels } = processRadialData(data);
	
	// Create a lookup map for reliable tooltip access
	const dataMap = new Map();
	data.forEach(item => {
		const key = item.name || item.category;
		if (key) {
			dataMap.set(key, item);
			dataMap.set(key.toLowerCase(), item); // Also store lowercase version
		}
	});
	
	console.log("🗺️ RadialChart data map:", {
		mapKeys: Array.from(dataMap.keys()),
		chartLabels: labels,
		dataMapSize: dataMap.size
	});

	const options: ApexOptions = {
		chart: {
			height: 350,
			type: 'radialBar',
			toolbar: {
				show: !minimal
			},
			animations: {
				enabled: true,
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
			radialBar: {
				offsetY: 0,
				startAngle: 0,
				endAngle: 270,
				hollow: {
					margin: 5,
					size: '30%',
					background: 'transparent',
					image: undefined,
				},
				dataLabels: {
					name: {
						show: showLabels,
						fontSize: '12px',
						fontWeight: 600,
						color: '#374151'
					},
					value: {
						show: true,
						fontSize: '14px',
						fontWeight: 'bold',
						color: '#1F2937',
						formatter: function (val: number) {
							return parseInt(val.toString(), 10).toString() + '%'
						}
					}
				},
				barLabels: {
					enabled: true,
					useSeriesColors: true,
					offsetX: -8,
					fontSize: '12px',
					formatter: function(seriesName: string, opts: any) {
						return seriesName + ":  " + opts.w.globals.series[opts.seriesIndex] + "%"
					},
				},
			}
		},
		colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
		labels: labels,
		legend: {
			show: true,
			floating: true,
			fontSize: '12px',
			position: 'left',
			offsetX: 50,
			offsetY: 10,
			labels: {
				useSeriesColors: true,
			},
			markers: {
				size: 0
			},
			formatter: function(seriesName: string, opts: any) {
				return seriesName + ":  " + opts.w.globals.series[opts.seriesIndex] + "%"
			},
			itemMargin: {
				vertical: 3
			}
		},
		tooltip: {
			enabled: true,
			theme: 'light',
			custom: function({series, seriesIndex, dataPointIndex, w}) {
				const percentage = series[seriesIndex];
				const label = dataPointIndex !== null ? w.globals.labels[dataPointIndex] : null;
				
				console.log("🔍 Tooltip raw data:", { 
					dataPointIndex,
					seriesIndex,
					label,
					allLabels: w.globals.labels,
					mapKeys: Array.from(dataMap.keys())
				});
				
				// Use the data map for reliable lookup or fallback to series index
				let originalItem = null;
				if (label) {
					originalItem = dataMap.get(label) || dataMap.get(label.toLowerCase());
				}
				
				// If still no match, try using seriesIndex as fallback
				if (!originalItem && seriesIndex < data.length) {
					originalItem = data[seriesIndex];
				}
				
				const rawValue = originalItem?.value;
				// Use the original data name as the primary label
				const displayName = originalItem?.name || 
								   originalItem?.category || 
								   label ||
								   `Item ${(dataPointIndex ?? seriesIndex) + 1}`;
				
				console.log("🔍 Tooltip result:", { 
					originalItem,
					rawValue,
					displayName
				});
				
				return `
					<div class="px-3 py-2 bg-white border border-gray-200 rounded shadow-lg">
						<div class="font-semibold text-sm text-gray-800">${displayName}</div>
						<div class="text-xs mt-1 text-gray-600">
							<div>Percentage: <span class="font-medium text-blue-600">${percentage}%</span></div>
							${rawValue !== undefined ? `<div>Raw Value: <span class="font-medium text-gray-800">${rawValue.toLocaleString()}</span></div>` : ''}
						</div>
					</div>
				`;
			}
		},
		responsive: [
			{
				breakpoint: 640,
				options: {
					chart: {
						height: 300
					},
					legend: {
						show: false
					},
					plotOptions: {
						radialBar: {
							dataLabels: {
								name: {
									show: false
								}
							}
						}
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
				type="radialBar"
				height={350}
			/>
		</div>
	);
} 