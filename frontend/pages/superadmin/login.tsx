import React, { useState } from "react";
import { useRouter } from "next/router";
import { Eye, EyeOff, Lock, User, Shield } from "lucide-react";
import api from "../../lib/axios";

interface LoginForm {
	username: string;
	password: string;
}

const SuperAdminLogin: React.FC = () => {
	const [formData, setFormData] = useState<LoginForm>({
		username: "",
		password: "",
	});
	const [showPassword, setShowPassword] = useState(false);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const router = useRouter();

	const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const { name, value } = e.target;
		setFormData((prev) => ({
			...prev,
			[name]: value,
		}));
		// Clear error when user starts typing
		if (error) setError("");
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setLoading(true);
		setError("");

		try {
			const response = await api.post("/superadmin/login", formData);

			if (response.data.access_token) {
				// Store token in localStorage
				localStorage.setItem("superadmin_token", response.data.access_token);

				// Redirect to dashboard
				router.push("/superadmin/dashboard");
			}
		} catch (err: any) {
			setError(err.response?.data?.detail || "Login failed. Please try again.");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="min-h-screen bg-gray-2 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
			<div className="max-w-md w-full space-y-8">
				{/* Header */}
				<div className="text-center">
					<div className="flex justify-center mb-6">
						<div className="w-16 h-16 bg-danger/10 rounded-full flex items-center justify-center">
							<Shield className="w-8 h-8 text-danger" />
						</div>
					</div>
					<h2 className="text-3xl font-bold text-black">Superadmin Access</h2>
					<p className="mt-2 text-sm text-body">
						Sign in to manage the analytics platform
					</p>
				</div>

				{/* Login Form */}
				<div className="bg-white rounded-lg shadow-default border border-stroke p-8">
					<form onSubmit={handleSubmit} className="space-y-6">
						{error && (
							<div className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-lg text-sm">
								{error}
							</div>
						)}

						{/* Username Field */}
						<div>
							<label
								htmlFor="username"
								className="block text-sm font-medium text-black mb-2">
								Username
							</label>
							<div className="relative">
								<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
									<User className="h-5 w-5 text-body" />
								</div>
								<input
									id="username"
									name="username"
									type="text"
									autoComplete="username"
									required
									value={formData.username}
									onChange={handleChange}
									className="block w-full pl-10 pr-3 py-3 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-danger focus:border-transparent outline-none transition-colors"
									placeholder="Enter your username"
								/>
							</div>
						</div>

						{/* Password Field */}
						<div>
							<label
								htmlFor="password"
								className="block text-sm font-medium text-black mb-2">
								Password
							</label>
							<div className="relative">
								<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
									<Lock className="h-5 w-5 text-body" />
								</div>
								<input
									id="password"
									name="password"
									type={showPassword ? "text" : "password"}
									autoComplete="current-password"
									required
									value={formData.password}
									onChange={handleChange}
									className="block w-full pl-10 pr-10 py-3 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-danger focus:border-transparent outline-none transition-colors"
									placeholder="Enter your password"
								/>
								<button
									type="button"
									onClick={() => setShowPassword(!showPassword)}
									className="absolute inset-y-0 right-0 pr-3 flex items-center">
									{showPassword ? (
										<EyeOff className="h-5 w-5 text-body hover:text-danger transition-colors" />
									) : (
										<Eye className="h-5 w-5 text-body hover:text-danger transition-colors" />
									)}
								</button>
							</div>
						</div>

						{/* Submit Button */}
						<button
							type="submit"
							disabled={loading}
							className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white transition-colors ${
								loading
									? "bg-gray-400 cursor-not-allowed"
									: "bg-danger hover:bg-danger/90 focus:ring-2 focus:ring-danger focus:ring-offset-2"
							}`}>
							{loading ? (
								<div className="flex items-center">
									<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
									Signing in...
								</div>
							) : (
								"Access Dashboard"
							)}
						</button>
					</form>
				</div>

				{/* Footer */}
				<div className="text-center">
					<p className="text-xs text-body">
						© 2024 Analytics AI Dashboard. Superadmin Access Only.
					</p>
				</div>
			</div>
		</div>
	);
};

export default SuperAdminLogin;
