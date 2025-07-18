import React, { useState } from "react";
import { Building2 } from "lucide-react";
import api from "../../lib/axios";

interface OptimizationResult {
	message: string;
	results?: Array<{
		name: string;
		price: number;
		savings: number;
		features: string[];
	}>;
	totalSavings?: number;
	status: string;
}

interface BusinessOptimizationProps {
	currentExpenses: Array<{ category: string; amount: number }>;
	onOptimizationComplete?: (result: OptimizationResult) => void;
}

const BusinessOptimization: React.FC<BusinessOptimizationProps> = ({
	currentExpenses,
	onOptimizationComplete,
}) => {
	const [loading, setLoading] = useState(false);
	const [result, setResult] = useState<OptimizationResult | null>(null);

	const handleFindOffices = async () => {
		try {
			setLoading(true);
			setResult(null);

			const response = await api.post("/find-office", {
				currentExpenses,
				budget: 50000,
				location: "downtown",
			});

			const optimizationResult = response.data;
			setResult(optimizationResult);

			if (onOptimizationComplete) {
				onOptimizationComplete(optimizationResult);
			}
		} catch (error) {
			console.error("Error finding cheaper offices:", error);
			const errorResult = {
				message: "Failed to find cheaper offices. Please try again.",
				status: "error",
			};
			setResult(errorResult);
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="rounded-lg border border-stroke bg-white p-6 shadow-default dark:border-strokedark dark:bg-boxdark">
			<div className="mb-4 border-b border-stroke pb-4 dark:border-strokedark">
				<h3 className="text-title-md font-bold text-black dark:text-white">
					Business Optimization
				</h3>
				<p className="text-sm text-body">
					Find cost-saving opportunities for your business
				</p>
			</div>

			<div className="mb-6">
				<div className="flex items-center gap-3 mb-4">
					<div className="flex h-11.5 w-11.5 items-center justify-center rounded-full bg-primary/10">
						<Building2 className="h-5 w-5 text-primary" />
					</div>
					<div>
						<h4 className="text-lg font-semibold text-black dark:text-white">
							Office Space Optimization
						</h4>
						<p className="text-sm text-body">
							Analyze your current office expenses and find cheaper alternatives
						</p>
					</div>
				</div>

				<button
					onClick={handleFindOffices}
					disabled={loading}
					className={`flex w-full items-center justify-center gap-2 rounded-lg px-6 py-3 text-sm font-medium transition-colors
            ${
							loading
								? "bg-gray-300 text-gray-500 cursor-not-allowed"
								: "bg-primary text-white hover:bg-primary/90"
						}`}>
					{loading ? (
						<>
							<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
							Processing...
						</>
					) : (
						<>
							<Building2 className="h-4 w-4" />
							Find Cheaper Offices
						</>
					)}
				</button>
			</div>

			{result && (
				<div
					className={`rounded-lg p-4 ${
						result.status === "error" || result.message.includes("Failed")
							? "bg-red-50 border-l-4 border-red-400 dark:bg-red-900/20"
							: "bg-green-50 border-l-4 border-green-400 dark:bg-green-900/20"
					}`}>
					<div className="flex items-center">
						<div className="flex-shrink-0">
							<Building2
								className={`h-5 w-5 ${
									result.status === "error" ? "text-red-400" : "text-green-400"
								}`}
							/>
						</div>
						<div className="ml-3">
							<h4
								className={`text-sm font-medium ${
									result.status === "error"
										? "text-red-800 dark:text-red-200"
										: "text-green-800 dark:text-green-200"
								}`}>
								{result.message}
							</h4>
							{result.results && result.results.length > 0 && (
								<div className="mt-3 space-y-2">
									{result.results.map((office, index) => (
										<div
											key={index}
											className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-sm">
											<div className="flex justify-between items-start">
												<div>
													<h5 className="font-medium text-gray-900 dark:text-white">
														{office.name}
													</h5>
													<p className="text-sm text-gray-600 dark:text-gray-400">
														${office.price.toLocaleString()}/month
													</p>
												</div>
												<span className="text-sm font-medium text-green-600 dark:text-green-400">
													Save ${office.savings.toLocaleString()}
												</span>
											</div>
											<div className="mt-2 flex flex-wrap gap-1">
												{office.features.map((feature, featureIndex) => (
													<span
														key={featureIndex}
														className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
														{feature}
													</span>
												))}
											</div>
										</div>
									))}
									{result.totalSavings && (
										<div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
											<p className="text-sm font-medium text-green-800 dark:text-green-200">
												Total Potential Savings: $
												{result.totalSavings.toLocaleString()}/month
											</p>
										</div>
									)}
								</div>
							)}
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default BusinessOptimization;
