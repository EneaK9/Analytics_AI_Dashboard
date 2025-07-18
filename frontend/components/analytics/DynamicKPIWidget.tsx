import React from "react";
import {
	TrendingUp,
	TrendingDown,
	DollarSign,
	Users,
	ShoppingCart,
	Package,
	BarChart,
	Target,
	PieChart,
	Activity,
	CreditCard,
	Star,
	Calendar,
	Clock,
	AlertTriangle,
	CheckCircle,
	XCircle,
	Eye,
	Heart,
	Zap,
	Award,
	Globe,
	Shield,
	Smartphone,
	Monitor,
	Settings,
	Database,
	FileText,
	Briefcase,
	MessageSquare,
	Mail,
	Phone,
	MapPin,
	Search,
	Filter,
	Download,
	Upload,
	Share,
	Edit,
	Trash2,
	Plus,
	Minus,
} from "lucide-react";

export interface KPITrend {
	value: string;
	isPositive: boolean;
	timeframe?: string;
}

export interface DynamicKPIProps {
	id: string;
	title: string;
	value: string;
	icon: string;
	iconColor?: string;
	iconBgColor?: string;
	trend?: KPITrend;
	loading?: boolean;
	onClick?: () => void;
	className?: string;
	size?: "sm" | "md" | "lg";
	showTrend?: boolean;
	prefix?: string;
	suffix?: string;
	formatter?: (value: string) => string;
}

// Icon mapping for dynamic icon selection
const ICON_MAP: { [key: string]: React.ComponentType<any> } = {
	TrendingUp,
	TrendingDown,
	DollarSign,
	Users,
	ShoppingCart,
	Package,
	BarChart,
	Target,
	PieChart,
	Activity,
	CreditCard,
	Star,
	Calendar,
	Clock,
	AlertTriangle,
	CheckCircle,
	XCircle,
	Eye,
	Heart,
	Zap,
	Award,
	Globe,
	Shield,
	Smartphone,
	Monitor,
	Settings,
	Database,
	FileText,
	Briefcase,
	MessageSquare,
	Mail,
	Phone,
	MapPin,
	Search,
	Filter,
	Download,
	Upload,
	Share,
	Edit,
	Trash2,
	Plus,
	Minus,
};

const DynamicKPIWidget: React.FC<DynamicKPIProps> = ({
	id,
	title,
	value,
	icon,
	iconColor = "text-primary",
	iconBgColor = "bg-primary/10",
	trend,
	loading = false,
	onClick,
	className = "",
	size = "md",
	showTrend = true,
	prefix = "",
	suffix = "",
	formatter,
}) => {
	const IconComponent = ICON_MAP[icon] || BarChart;

	const sizeClasses = {
		sm: {
			container: "p-4",
			icon: "w-8 h-8",
			iconContainer: "w-12 h-12",
			title: "text-sm",
			value: "text-xl",
			trend: "text-xs",
		},
		md: {
			container: "p-6",
			icon: "w-10 h-10",
			iconContainer: "w-16 h-16",
			title: "text-base",
			value: "text-2xl",
			trend: "text-sm",
		},
		lg: {
			container: "p-8",
			icon: "w-12 h-12",
			iconContainer: "w-20 h-20",
			title: "text-lg",
			value: "text-3xl",
			trend: "text-base",
		},
	};

	const currentSize = sizeClasses[size];

	const formatValue = (val: string) => {
		if (formatter) {
			return formatter(val);
		}
		return `${prefix}${val}${suffix}`;
	};

	const getTrendColor = (isPositive: boolean) => {
		return isPositive ? "text-meta-3" : "text-meta-1";
	};

	const getTrendIcon = (isPositive: boolean) => {
		return isPositive ? TrendingUp : TrendingDown;
	};

	return (
		<div
			className={`bg-white dark:bg-boxdark rounded-lg border border-stroke hover:shadow-lg transition-all duration-300 cursor-pointer ${currentSize.container} ${className}`}
			onClick={onClick}
			role={onClick ? "button" : "article"}
			tabIndex={onClick ? 0 : undefined}
			onKeyDown={(e) => {
				if (onClick && (e.key === "Enter" || e.key === " ")) {
					onClick();
				}
			}}>
			<div className="flex items-center justify-between">
				<div className="flex-1">
					<div className="flex items-center gap-4">
						{/* Icon */}
						<div
							className={`flex items-center justify-center rounded-full ${iconBgColor} ${currentSize.iconContainer}`}>
							<IconComponent className={`${currentSize.icon} ${iconColor}`} />
						</div>

						{/* Content */}
						<div className="flex-1">
							<h3
								className={`font-medium text-black dark:text-white ${currentSize.title} mb-1`}>
								{title}
							</h3>

							{loading ? (
								<div className="animate-pulse">
									<div className="bg-gray-200 dark:bg-gray-700 rounded h-6 w-20 mb-2"></div>
									{showTrend && (
										<div className="bg-gray-200 dark:bg-gray-700 rounded h-4 w-16"></div>
									)}
								</div>
							) : (
								<>
									<div
										className={`font-bold text-black dark:text-white ${currentSize.value} mb-1`}>
										{formatValue(value)}
									</div>

									{showTrend && trend && (
										<div
											className={`flex items-center gap-1 ${currentSize.trend}`}>
											{(() => {
												const TrendIcon = getTrendIcon(trend.isPositive);
												return (
													<TrendIcon
														className={`w-4 h-4 ${getTrendColor(
															trend.isPositive
														)}`}
													/>
												);
											})()}
											<span className={getTrendColor(trend.isPositive)}>
												{trend.value}
											</span>
											{trend.timeframe && (
												<span className="text-body dark:text-bodydark">
													{trend.timeframe}
												</span>
											)}
										</div>
									)}
								</>
							)}
						</div>
					</div>
				</div>

				{/* Optional action indicator */}
				{onClick && (
					<div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 opacity-60 hover:opacity-100 transition-opacity">
						<svg
							className="w-3 h-3 text-gray-500 dark:text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24">
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M9 5l7 7-7 7"
							/>
						</svg>
					</div>
				)}
			</div>
		</div>
	);
};

export default DynamicKPIWidget;
