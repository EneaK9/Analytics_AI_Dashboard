import React from "react";
import { ArrowDownIcon, ArrowUpIcon } from "lucide-react";

interface StatCardProps {
	name: string;
	stat: string;
	previousStat: string;
	change: string;
	changeType: "increase" | "decrease";
}

// Official Tailwind UI Stats Component - "With trending"
export const StatCard: React.FC<StatCardProps> = ({
	name,
	stat,
	previousStat,
	change,
	changeType,
}) => {
	return (
		<div className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:px-6 sm:py-6">
			<dt>
				<div className="absolute rounded-md bg-indigo-500 p-3">
					<div className="h-6 w-6 text-white" aria-hidden="true" />
				</div>
				<p className="ml-16 truncate text-sm font-medium text-gray-500">
					{name}
				</p>
			</dt>
			<dd className="ml-16 flex items-baseline">
				<p className="text-2xl font-semibold text-gray-900">{stat}</p>
				<p
					className={`ml-2 flex items-baseline text-sm font-semibold ${
						changeType === "increase" ? "text-green-600" : "text-red-600"
					}`}>
					{changeType === "increase" ? (
						<ArrowUpIcon
							className="h-5 w-5 flex-shrink-0 self-center text-green-500"
							aria-hidden="true"
						/>
					) : (
						<ArrowDownIcon
							className="h-5 w-5 flex-shrink-0 self-center text-red-500"
							aria-hidden="true"
						/>
					)}
					<span className="sr-only">
						{" "}
						{changeType === "increase" ? "Increased" : "Decreased"} by{" "}
					</span>
					{change}
				</p>
				<div className="absolute inset-x-0 bottom-0 bg-gray-50 px-4 py-4 sm:px-6">
					<div className="text-sm">
						<a
							href="#"
							className="font-medium text-indigo-600 hover:text-indigo-500">
							View all<span className="sr-only"> {name} stats</span>
						</a>
					</div>
				</div>
			</dd>
		</div>
	);
};

// Official Tailwind UI Stats Component - "Simple in cards"
export const SimpleStatCard: React.FC<StatCardProps> = ({
	name,
	stat,
	change,
	changeType,
}) => {
	return (
		<div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
			<dt className="truncate text-sm font-medium text-gray-500">{name}</dt>
			<dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
				{stat}
			</dd>
			<dd className="mt-1 flex items-baseline">
				<div
					className={`flex items-baseline text-sm font-semibold ${
						changeType === "increase" ? "text-green-600" : "text-red-600"
					}`}>
					{changeType === "increase" ? (
						<ArrowUpIcon
							className="h-5 w-5 flex-shrink-0 self-center text-green-500"
							aria-hidden="true"
						/>
					) : (
						<ArrowDownIcon
							className="h-5 w-5 flex-shrink-0 self-center text-red-500"
							aria-hidden="true"
						/>
					)}
					<span className="sr-only">
						{" "}
						{changeType === "increase" ? "Increased" : "Decreased"} by{" "}
					</span>
					{change}
				</div>
				<div className="ml-2 text-sm text-gray-500">from last month</div>
			</dd>
		</div>
	);
};

// Official Tailwind UI Stats Component - "Simple"
export const SimpleStats: React.FC<{ stats: StatCardProps[] }> = ({
	stats,
}) => {
	return (
		<div>
			<h3 className="text-base font-semibold leading-6 text-gray-900">
				Last 30 days
			</h3>
			<dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
				{stats.map((item) => (
					<div
						key={item.name}
						className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6">
						<dt className="truncate text-sm font-medium text-gray-500">
							{item.name}
						</dt>
						<dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
							{item.stat}
						</dd>
					</div>
				))}
			</dl>
		</div>
	);
};

// Chart Container using Tailwind UI patterns
interface ChartCardProps {
	title: string;
	subtitle?: string;
	children: React.ReactNode;
	className?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
	title,
	subtitle,
	children,
	className = "",
}) => {
	return (
		<div className={`overflow-hidden rounded-lg bg-white shadow ${className}`}>
			<div className="px-4 py-5 sm:p-6">
				<div className="sm:flex sm:items-center">
					<div className="sm:flex-auto">
						<h3 className="text-base font-semibold leading-6 text-gray-900">
							{title}
						</h3>
						{subtitle && (
							<p className="mt-2 text-sm text-gray-700">{subtitle}</p>
						)}
					</div>
				</div>
				<div className="mt-6">{children}</div>
			</div>
		</div>
	);
};

export default {
	StatCard,
	SimpleStatCard,
	SimpleStats,
	ChartCard,
};
