import React from "react";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";

// Dynamic import to avoid SSR issues with ApexCharts
const ReactApexChart = dynamic(() => import("react-apexcharts"), {
	ssr: false,
});

interface ExpenseData {
	category: string;
	amount: number;
}

interface ExpensesChartProps {
	data: ExpenseData[];
	title?: string;
	subtitle?: string;
}

const ExpensesChart: React.FC<ExpensesChartProps> = ({
	data,
	title = "Expenses by Category",
	subtitle = "Breakdown of business expenses",
}) => {
	const chartOptions: ApexOptions = {
		chart: {
			type: "bar",
			height: 350,
			toolbar: { show: false },
			fontFamily: "Satoshi, sans-serif",
		},
		colors: [
			"#80CAEE",
			"#0FADCF",
			"#FF6766",
			"#FFBA00",
			"#219653",
			"#D34053",
			"#8A99AF",
			"#F0950C",
		],
		plotOptions: {
			bar: {
				horizontal: false,
				columnWidth: "55%",
				borderRadius: 4,
			},
		},
		dataLabels: { enabled: false },
		stroke: {
			show: true,
			width: 2,
			colors: ["transparent"],
		},
		grid: {
			borderColor: "#e0e6ed",
			strokeDashArray: 5,
		},
		xaxis: {
			categories: data.map((item) => item.category),
			axisBorder: { show: false },
			axisTicks: { show: false },
			labels: {
				style: {
					colors: "#64748B",
					fontSize: "12px",
				},
				rotate: -45,
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
		legend: {
			show: false,
		},
	};

	const series = [
		{
			name: "Expenses",
			data: data.map((item) => item.amount),
		},
	];

	return (
		<div className="col-span-12 rounded-lg border border-stroke bg-white p-7.5 shadow-default dark:border-strokedark dark:bg-boxdark xl:col-span-4">
			<div className="mb-6 flex items-center justify-between">
				<div>
					<h4 className="text-xl font-bold text-black dark:text-white">
						{title}
					</h4>
					<p className="text-body">{subtitle}</p>
				</div>
			</div>
			<div id="expenses-chart">
				<ReactApexChart
					options={chartOptions}
					series={series}
					type="bar"
					height={350}
				/>
			</div>
		</div>
	);
};

export default ExpensesChart;
