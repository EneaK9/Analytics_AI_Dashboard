import React from "react";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
	title: string;
	value: string;
	icon: LucideIcon;
	trend?: {
		value: string;
		isPositive: boolean;
	};
	iconBgColor?: string;
	iconColor?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
	title,
	value,
	icon: Icon,
	trend,
	iconBgColor = "bg-primary/10",
	iconColor = "text-primary",
}) => {
	return (
		<div className="rounded-lg border border-stroke bg-white p-6 shadow-default dark:border-strokedark dark:bg-boxdark">
			<div className="flex items-center justify-between">
				<div>
					<p className="text-sm font-medium text-body">{title}</p>
					<h4 className="text-title-md font-bold text-black dark:text-white">
						{value}
					</h4>
					{trend && (
						<p
							className={`text-sm font-medium ${
								trend.isPositive ? "text-meta-3" : "text-meta-1"
							}`}>
							{trend.isPositive ? "+" : ""}
							{trend.value}
						</p>
					)}
				</div>
				<div
					className={`flex h-11.5 w-11.5 items-center justify-center rounded-full ${iconBgColor}`}>
					<Icon className={`h-5 w-5 ${iconColor}`} />
				</div>
			</div>
		</div>
	);
};

export default StatsCard;
