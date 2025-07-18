import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to avoid SSR issues with ApexCharts
const ReactApexChart = dynamic(() => import("react-apexcharts"), {
	ssr: false,
});

interface RevenueData {
	month: string;
	revenue: number;
}

interface RevenueChartProps {
	data: RevenueData[];
	title?: string;
	subtitle?: string;
}

const RevenueChart: React.FC<RevenueChartProps> = ({
	data,
	title = "Revenue Over Time",
	subtitle = "Monthly revenue performance",
}) => {
	const chartOptions: ApexOptions = {
		chart: {
			type: "area",
			height: 350,
			toolbar: { show: false },
			fontFamily: "Satoshi, sans-serif",
		},
		colors: ["#3C50E0"],
		dataLabels: { enabled: false },
		stroke: {
			curve: "smooth",
			width: 2,
		},
		fill: {
			type: "gradient",
			gradient: {
				shadeIntensity: 1,
				opacityFrom: 0.1,
				opacityTo: 0.7,
				stops: [0, 90, 100],
			},
		},
		grid: {
			borderColor: "#e0e6ed",
			strokeDashArray: 5,
		},
		xaxis: {
			categories: data.map((item) => item.month),
			axisBorder: { show: false },
			axisTicks: { show: false },
			labels: {
				style: {
					colors: "#64748B",
					fontSize: "12px",
				},
			},
		},
		yaxis: {
			labels: {
				style: {
					colors: "#64748B",
					fontSize: "12px",
				},
				formatter: (value: number) => `$${value.toLocaleString()}`,
			},
		},
		tooltip: {
			theme: "light",
			y: {
				formatter: (value: number) => `$${value.toLocaleString()}`,
			},
		},
	};

	const series = [
		{
			name: "Revenue",
			data: data.map((item) => item.revenue),
		},
	];

	return (
		<div className="col-span-12 rounded-lg border border-stroke bg-white p-7.5 shadow-default dark:border-strokedark dark:bg-boxdark xl:col-span-8">
			<div className="mb-6 flex items-center justify-between">
				<div>
					<h4 className="text-xl font-bold text-black dark:text-white">
						{title}
					</h4>
					<p className="text-body">{subtitle}</p>
				</div>
			</div>
			<div id="revenue-chart">
				<ReactApexChart
					options={chartOptions}
					series={series}
					type="area"
					height={350}
				/>
			</div>
		</div>
	);
};

export default RevenueChart;
