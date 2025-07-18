import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/router";
import {
	TrendingUp,
	DollarSign,
	PieChart,
	Users,
	LogOut,
	Settings,
	Database,
	ChevronDown,
} from "lucide-react";
import api from "../lib/axios";

// Import analytics components
import {
	StatsCard,
	RevenueChart,
	ExpensesChart,
	BusinessOptimization,
	PersonalizedDashboard,
	RevenueData,
	ExpenseData,
} from "../components/analytics";

interface User {
	client_id: string;
	company_name: string;
	email: string;
	subscription_tier: string;
	created_at: string;
}

// Sample data for demonstration
const sampleRevenueData: RevenueData[] = [
	{ month: "Jan", revenue: 45000 },
	{ month: "Feb", revenue: 52000 },
	{ month: "Mar", revenue: 48000 },
	{ month: "Apr", revenue: 61000 },
	{ month: "May", revenue: 55000 },
	{ month: "Jun", revenue: 67000 },
];

const sampleExpenseData: ExpenseData[] = [
	{ category: "Office Rent", amount: 25000 },
	{ category: "Marketing", amount: 15000 },
	{ category: "Technology", amount: 12000 },
	{ category: "Operations", amount: 18000 },
];

const Dashboard: React.FC = () => {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);
	const [showDropdown, setShowDropdown] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);
	const router = useRouter();

	useEffect(() => {
		const checkAuth = async () => {
			try {
				const token = localStorage.getItem("access_token");
				if (!token) {
					router.push("/login");
					return;
				}

				// Verify token with backend
				const response = await api.get("/auth/me");
				setUser(response.data);
			} catch (error) {
				console.error("Auth check failed:", error);
				localStorage.removeItem("access_token");
				router.push("/login");
			} finally {
				setLoading(false);
			}
		};

		checkAuth();
	}, [router]);

	// Close dropdown when clicking outside
	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (
				dropdownRef.current &&
				!dropdownRef.current.contains(event.target as Node)
			) {
				setShowDropdown(false);
			}
		};

		document.addEventListener("mousedown", handleClickOutside);
		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, []);

	const handleLogout = () => {
		localStorage.removeItem("access_token");
		router.push("/login");
	};

	const toggleDropdown = () => {
		setShowDropdown(!showDropdown);
	};

	const getInitials = (name: string) => {
		return name.charAt(0).toUpperCase();
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-gray-2 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
					<p className="text-body">Loading dashboard...</p>
				</div>
			</div>
		);
	}

	if (!user) {
		return null; // Will redirect to login
	}

	return (
		<div className="min-h-screen bg-gray-2">
			{/* Header */}
			<header className="bg-white border-b border-stroke px-6 py-4">
				<div className="mx-auto max-w-screen-2xl flex items-center justify-between">
					<div>
						<h1 className="text-2xl font-bold text-black dark:text-white">
							Analytics Dashboard
						</h1>
						<p className="text-body mt-1">Welcome back, {user.company_name}</p>
					</div>

					<div className="relative" ref={dropdownRef}>
						<button
							onClick={toggleDropdown}
							className="flex items-center justify-center w-10 h-10 bg-primary text-white rounded-full hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2">
							{getInitials(user.company_name)}
						</button>

						{showDropdown && (
							<div className="absolute right-0 mt-2 w-56 bg-white border border-stroke rounded-lg shadow-default z-50">
								<div className="px-4 py-3 border-b border-stroke">
									<p className="text-sm font-medium text-black">
										{user.company_name}
									</p>
									<p className="text-xs text-body capitalize">
										{user.subscription_tier} Plan
									</p>
								</div>
								<div className="py-1">
									<button
										onClick={handleLogout}
										className="flex items-center w-full px-4 py-2 text-sm text-danger hover:bg-gray-1 transition-colors">
										<LogOut className="h-4 w-4 mr-2" />
										<span>Logout</span>
									</button>
								</div>
							</div>
						)}
					</div>
				</div>
			</header>

			{/* Main Content */}
			<main className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
				{/* Personalized Dashboard */}
				<PersonalizedDashboard
					onGenerateClick={() => {
						console.log("Dashboard generated successfully!");
						// You can add a notification system here
					}}
					showGenerateButton={true}
				/>
			</main>
		</div>
	);
};

export default Dashboard;
