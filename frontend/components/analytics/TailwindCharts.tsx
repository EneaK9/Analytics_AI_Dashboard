import React from "react";

interface ChartData {
	label: string;
	value: number;
}

// Simple Bar Chart using Tailwind CSS
export const SimpleBarChart: React.FC<{
	data: ChartData[];
	title?: string;
}> = ({ data, title }) => {
	if (!data?.length)
		return (
			<div className="text-gray-500 text-center py-8">No data available</div>
		);

	const maxValue = Math.max(...data.map((d) => d.value));

	return (
		<div className="w-full">
			{title && (
				<h4 className="text-sm font-medium text-gray-900 mb-4">{title}</h4>
			)}
			<div className="space-y-3">
				{data.map((item, index) => (
					<div key={index} className="flex items-center">
						<div className="w-20 text-sm text-gray-600 truncate">
							{item.label}
						</div>
						<div className="flex-1 mx-3">
							<div className="bg-gray-200 rounded-full h-6 relative">
								<div
									className="bg-indigo-600 h-6 rounded-full flex items-center justify-end pr-2"
									style={{ width: `${(item.value / maxValue) * 100}%` }}>
									<span className="text-white text-xs font-medium">
										{item.value}
									</span>
								</div>
							</div>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};

// Simple Line Chart visualization using Tailwind CSS
export const SimpleLineChart: React.FC<{
	data: ChartData[];
	title?: string;
}> = ({ data, title }) => {
	if (!data?.length)
		return (
			<div className="text-gray-500 text-center py-8">No data available</div>
		);

	const maxValue = Math.max(...data.map((d) => d.value));
	const minValue = Math.min(...data.map((d) => d.value));

	return (
		<div className="w-full">
			{title && (
				<h4 className="text-sm font-medium text-gray-900 mb-4">{title}</h4>
			)}
			<div className="h-48 flex items-end space-x-2 border-b border-l border-gray-200 p-4">
				{data.map((item, index) => {
					const height =
						((item.value - minValue) / (maxValue - minValue)) * 100;
					return (
						<div key={index} className="flex flex-col items-center flex-1">
							<div
								className="w-full flex items-end justify-center mb-2"
								style={{ height: "140px" }}>
								<div
									className="w-3 bg-indigo-600 rounded-t"
									style={{ height: `${height}%` }}
									title={`${item.label}: ${item.value}`}
								/>
							</div>
							<div className="text-xs text-gray-600 text-center truncate w-full">
								{item.label}
							</div>
						</div>
					);
				})}
			</div>
		</div>
	);
};

// Simple Pie Chart representation using Tailwind CSS
export const SimplePieChart: React.FC<{
	data: ChartData[];
	title?: string;
}> = ({ data, title }) => {
	if (!data?.length)
		return (
			<div className="text-gray-500 text-center py-8">No data available</div>
		);

	const total = data.reduce((sum, item) => sum + item.value, 0);
	const colors = [
		"bg-indigo-600",
		"bg-purple-600",
		"bg-pink-600",
		"bg-red-600",
		"bg-orange-600",
		"bg-yellow-600",
	];

	return (
		<div className="w-full">
			{title && (
				<h4 className="text-sm font-medium text-gray-900 mb-4">{title}</h4>
			)}
			<div className="flex items-center space-x-6">
				{/* Simple pie representation */}
				<div className="w-32 h-32 rounded-full border-8 border-gray-200 flex items-center justify-center bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600">
					<div className="text-white text-sm font-semibold text-center">
						<div>{total}</div>
						<div className="text-xs opacity-80">Total</div>
					</div>
				</div>

				{/* Legend */}
				<div className="space-y-2">
					{data.map((item, index) => {
						const percentage = ((item.value / total) * 100).toFixed(1);
						return (
							<div key={index} className="flex items-center">
								<div
									className={`w-3 h-3 rounded-full ${
										colors[index % colors.length]
									} mr-2`}
								/>
								<div className="text-sm text-gray-700">
									<span className="font-medium">{item.label}:</span>{" "}
									{item.value} ({percentage}%)
								</div>
							</div>
						);
					})}
				</div>
			</div>
		</div>
	);
};
