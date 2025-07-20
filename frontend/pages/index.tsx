
import {
	AlertCircle,
	Settings,
	Users,
	Database,
	LogIn,
	Shield,
} from "lucide-react";
import { useRouter } from "next/router";

export default function Home() {
	const router = useRouter();

	const handleLoginClick = () => {
		router.push("/login");
	};

	return (
		<div className="min-h-screen bg-gray-2">
			{/* Header */}
			<header className="bg-white border-b border-stroke px-6 py-4">
				<div className="mx-auto max-w-screen-2xl flex items-center justify-between">
					<div>
						<h1 className="text-2xl font-bold text-black dark:text-white">
							Analytics AI Dashboard
						</h1>
						<p className="text-body mt-1">
							Dynamic AI-powered analytics platform for custom data structures
						</p>
					</div>

					<div className="flex items-center space-x-3">
						<button
							onClick={() => router.push("/superadmin/login")}
							className="flex items-center space-x-2 px-4 py-2 bg-danger text-white rounded-lg hover:bg-danger/90 transition-colors">
							<Shield className="h-4 w-4" />
							<span>Admin</span>
						</button>
						<button
							onClick={handleLoginClick}
							className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
							<LogIn className="h-4 w-4" />
							<span>Login</span>
						</button>
					</div>
				</div>
			</header>

			{/* Main Content */}
			<main className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
				{/* Coming Soon Section */}
				<div className="bg-white rounded-lg shadow-sm border border-stroke p-8 text-center">
					<div className="flex justify-center mb-6">
						<div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
							<Database className="w-10 h-10 text-primary" />
						</div>
					</div>

					<h2 className="text-2xl font-bold text-black mb-4">
						System Under Development
					</h2>

					<p className="text-body mb-8 max-w-2xl mx-auto">
						We are building a revolutionary AI-powered analytics platform where
						each client gets a custom dashboard tailored to their unique data
						structure. The system will automatically analyze your data and
						create the perfect visualization interface.
					</p>

					{/* Feature Preview */}
					<div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
						<div className="bg-gray-1 rounded-lg p-6">
							<Users className="w-8 h-8 text-primary mx-auto mb-4" />
							<h3 className="font-semibold text-black mb-2">
								Super Admin Panel
							</h3>
							<p className="text-body text-sm">
								Manage clients and upload their custom data structures
							</p>
						</div>

						<div className="bg-gray-1 rounded-lg p-6">
							<AlertCircle className="w-8 h-8 text-primary mx-auto mb-4" />
							<h3 className="font-semibold text-black mb-2">
								AI Data Analysis
							</h3>
							<p className="text-body text-sm">
								Automatically detect data patterns and create optimal schemas
							</p>
						</div>

						<div className="bg-gray-1 rounded-lg p-6">
							<Settings className="w-8 h-8 text-primary mx-auto mb-4" />
							<h3 className="font-semibold text-black mb-2">
								Dynamic Dashboards
							</h3>
							<p className="text-body text-sm">
								Custom interfaces generated for each client&apos;s unique data
							</p>
						</div>
					</div>

					{/* Status */}
					<div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
						<p className="text-primary font-medium">
							🚧 Phase 1: Setting up Supabase integration and AI analysis engine
						</p>
					</div>
				</div>
			</main>
		</div>
	);
}
