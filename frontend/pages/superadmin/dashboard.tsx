import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import {
	Users,
	Plus,
	Edit,
	Trash2,
	Shield,
	LogOut,
	Building,
	Mail,
	Key,
	Calendar,
	Eye,
	EyeOff,
} from "lucide-react";
import api from "../../lib/axios";

interface Client {
	client_id: string;
	company_name: string;
	email: string;
	subscription_tier: string;
	created_at: string;
	updated_at: string;
	has_schema?: boolean;
	schema_info?: {
		table_name: string;
		data_type: string;
		data_stored?: boolean;
		row_count?: number;
	};
	actual_data_count?: number;
	data_stored?: boolean;
}

interface CreateClientForm {
	company_name: string;
	email: string;
	password: string;
	// subscription_tier: string;
	data_type: string;
	data_content: string;
	input_method: "paste" | "upload";
	uploaded_file: File | null;
}

const SuperAdminDashboard: React.FC = () => {
	const [clients, setClients] = useState<Client[]>([]);
	const [loading, setLoading] = useState(true);
	const [showCreateForm, setShowCreateForm] = useState(false);
	const [showPassword, setShowPassword] = useState(false);
	const [formData, setFormData] = useState<CreateClientForm>({
		company_name: "",
		email: "",
		password: "",
		// subscription_tier: "basic",
		data_type: "json",
		data_content: "",
		input_method: "paste",
		uploaded_file: null,
	});
	const [formLoading, setFormLoading] = useState(false);
	const [error, setError] = useState("");
	const router = useRouter();

	// Check authentication and load data
	useEffect(() => {
		const checkAuth = async () => {
			try {
				const token = localStorage.getItem("superadmin_token");
				if (!token) {
					router.push("/superadmin/login");
					return;
				}

				await loadClients();
			} catch (error) {
				console.error("Auth check failed:", error);
				localStorage.removeItem("superadmin_token");
				router.push("/superadmin/login");
			} finally {
				setLoading(false);
			}
		};

		checkAuth();
	}, [router]);

	const loadClients = async () => {
		try {
			console.log("🚀 Loading clients SUPER FAST...");
			const response = await api.get("/superadmin/clients");
			console.log("✅ Clients loaded:", response.data);
			setClients(response.data.clients || []);
		} catch (error) {
			console.error("Failed to load clients:", error);
			// Show error but don't break the UI
			setClients([]);
		}
	};

	const handleLogout = () => {
		localStorage.removeItem("superadmin_token");
		router.push("/superadmin/login");
	};

	const handleFormChange = (
		e: React.ChangeEvent<
			HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
		>
	) => {
		const { name, value } = e.target;
		setFormData((prev) => ({
			...prev,
			[name]: value,
		}));
		if (error) setError("");
	};

	const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0] || null;
		setFormData((prev) => ({
			...prev,
			uploaded_file: file,
		}));
		if (error) setError("");
	};

	const handleInputMethodChange = (method: "paste" | "upload") => {
		setFormData((prev) => ({
			...prev,
			input_method: method,
			data_content: method === "upload" ? "" : prev.data_content,
			uploaded_file: method === "paste" ? null : prev.uploaded_file,
		}));
	};

	const handleCreateClient = async (e: React.FormEvent) => {
		e.preventDefault();
		setFormLoading(true);
		setError("");

		try {
			// Create FormData for file upload support
			const submitData = new FormData();
			submitData.append("company_name", formData.company_name);
			submitData.append("email", formData.email);
			submitData.append("password", formData.password);
			submitData.append("data_type", formData.data_type);
			submitData.append("input_method", formData.input_method);

			if (formData.input_method === "paste") {
				submitData.append("data_content", formData.data_content);
			} else if (formData.uploaded_file) {
				submitData.append("uploaded_file", formData.uploaded_file);
			}

			await api.post("/superadmin/clients", submitData, {
				headers: {
					"Content-Type": "multipart/form-data",
				},
			});

			// Reset form and reload clients
			setFormData({
				company_name: "",
				email: "",
				password: "",
				// subscription_tier: "basic",
				data_type: "json",
				data_content: "",
				input_method: "paste",
				uploaded_file: null,
			});
			setShowCreateForm(false);
			await loadClients();
		} catch (err: any) {
			setError(err.response?.data?.detail || "Failed to create client");
		} finally {
			setFormLoading(false);
		}
	};

	const handleDeleteClient = async (clientId: string) => {
		if (!confirm("Are you sure you want to delete this client?")) return;

		try {
			await api.delete(`/superadmin/clients/${clientId}`);
			await loadClients();
		} catch (error) {
			console.error("Failed to delete client:", error);
		}
	};

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString();
	};

	const getTierColor = (tier: string) => {
		switch (tier) {
			case "basic":
				return "bg-gray-100 text-gray-800";
			case "premium":
				return "bg-blue-100 text-blue-800";
			case "enterprise":
				return "bg-purple-100 text-purple-800";
			default:
				return "bg-gray-100 text-gray-800";
		}
	};

	const getPlaceholderText = (dataType: string) => {
		switch (dataType) {
			case "json":
				return `Enter JSON data like:
{
  "users": [
    {"id": 1, "name": "John", "email": "john@email.com"},
    {"id": 2, "name": "Jane", "email": "jane@email.com"}
  ]
}`;
			case "csv":
				return `Enter CSV data like:
id,name,email,age,department
1,John Doe,john@company.com,28,Engineering
2,Jane Smith,jane@company.com,32,Marketing`;
			case "xml":
				return `Enter XML data like:
<users>
  <user id="1">
    <name>John Doe</name>
    <email>john@email.com</email>
  </user>
</users>`;
			case "api":
				return `Enter API endpoint data like:
{
  "endpoint": "/api/users",
  "data": [{"id": 1, "name": "John"}]
}`;
			default:
				return `Enter your ${dataType.toUpperCase()} data here...`;
		}
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-gray-2 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-danger mx-auto mb-4"></div>
					<p className="text-body">Loading dashboard...</p>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gray-2">
			{/* Header */}
			<header className="bg-white border-b border-stroke px-6 py-4">
				<div className="mx-auto max-w-screen-2xl flex items-center justify-between">
					<div className="flex items-center space-x-4">
						<div className="w-10 h-10 bg-danger/10 rounded-full flex items-center justify-center">
							<Shield className="w-5 h-5 text-danger" />
						</div>
						<div>
							<h1 className="text-2xl font-bold text-black">
								Superadmin Dashboard
							</h1>
							<p className="text-body text-sm">
								Manage clients and platform settings
							</p>
						</div>
					</div>

					<button
						onClick={handleLogout}
						className="flex items-center space-x-2 px-4 py-2 bg-danger text-white rounded-lg hover:bg-danger/90 transition-colors">
						<LogOut className="h-4 w-4" />
						<span>Logout</span>
					</button>
				</div>
			</header>

			{/* Main Content */}
			<main className="mx-auto max-w-screen-2xl p-4 md:p-6 2xl:p-10">
				{/* Stats Cards */}
				<div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
					<div className="bg-white rounded-lg shadow-default border border-stroke p-6">
						<div className="flex items-center justify-between">
							<div>
								<p className="text-sm text-body">Total Clients</p>
								<p className="text-2xl font-bold text-black">
									{clients.length}
								</p>
							</div>
							<div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
								<Users className="w-6 h-6 text-primary" />
							</div>
						</div>
					</div>

					<div className="bg-white rounded-lg shadow-default border border-stroke p-6">
						<div className="flex items-center justify-between">
							<div>
								<p className="text-sm text-body">Active Clients</p>
								<p className="text-2xl font-bold text-black">
									{clients.length}
								</p>
							</div>
							<div className="w-12 h-12 bg-success/10 rounded-full flex items-center justify-center">
								<Building className="w-6 h-6 text-success" />
							</div>
						</div>
					</div>

					{/* Commented out subscription tier stats */}
					{/* <div className="bg-white rounded-lg shadow-default border border-stroke p-6">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-sm text-body">Enterprise Clients</p>
									<p className="text-2xl font-bold text-black">
										{
											clients.filter((c) => c.subscription_tier === "enterprise")
												.length
										}
									</p>
								</div>
								<div className="w-12 h-12 bg-warning/10 rounded-full flex items-center justify-center">
									<Shield className="w-6 h-6 text-warning" />
								</div>
							</div>
						</div> */}
				</div>

				{/* Client Management */}
				<div className="bg-white rounded-lg shadow-default border border-stroke">
					<div className="px-6 py-4 border-b border-stroke flex items-center justify-between">
						<h2 className="text-xl font-bold text-black">Client Management</h2>
						<button
							onClick={() => setShowCreateForm(true)}
							className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
							<Plus className="h-4 w-4" />
							<span>Add Client</span>
						</button>
					</div>

					<div className="p-6">
						{clients.length === 0 ? (
							<div className="text-center py-8">
								<Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
								<p className="text-body">
									No clients found. Create your first client to get started.
								</p>
							</div>
						) : (
							<div className="overflow-x-auto">
								<table className="w-full table-auto">
									<thead>
										<tr className="bg-gray-1">
											<th className="px-4 py-3 text-left text-sm font-medium text-black">
												Company
											</th>
											<th className="px-4 py-3 text-left text-sm font-medium text-black">
												Email
											</th>
											<th className="px-4 py-3 text-left text-sm font-medium text-black">
												Data Status
											</th>
											{/* <th className="px-4 py-3 text-left text-sm font-medium text-black">
												Tier
											</th> */}
											<th className="px-4 py-3 text-left text-sm font-medium text-black">
												Created
											</th>
											<th className="px-4 py-3 text-left text-sm font-medium text-black">
												Actions
											</th>
										</tr>
									</thead>
									<tbody>
										{clients.map((client) => (
											<tr
												key={client.client_id}
												className="border-b border-stroke">
												<td className="px-4 py-3 text-sm text-black">
													{client.company_name}
												</td>
												<td className="px-4 py-3 text-sm text-body">
													{client.email}
												</td>
												<td className="px-4 py-3">
													{client.has_schema &&
													(client.actual_data_count || 0) > 0 ? (
														<div className="flex items-center space-x-2">
															<span className="w-2 h-2 bg-success rounded-full"></span>
															<span className="text-xs text-success font-medium">
																{client.schema_info?.data_type?.toUpperCase()} (
																{client.actual_data_count} rows)
															</span>
														</div>
													) : client.has_schema ? (
														<div className="flex items-center space-x-2">
															<span className="w-2 h-2 bg-warning rounded-full"></span>
															<span className="text-xs text-warning font-medium">
																{client.schema_info?.data_type?.toUpperCase()}{" "}
																Schema Only
															</span>
														</div>
													) : (
														<div className="flex items-center space-x-2">
															<span className="w-2 h-2 bg-gray-400 rounded-full"></span>
															<span className="text-xs text-gray-500">
																No Data
															</span>
														</div>
													)}
												</td>
												{/* <td className="px-4 py-3">
													<span
														className={`px-2 py-1 text-xs rounded-full ${getTierColor(
															client.subscription_tier
														)}`}>
														{client.subscription_tier}
													</span>
												</td> */}
												<td className="px-4 py-3 text-sm text-body">
													{formatDate(client.created_at)}
												</td>
												<td className="px-4 py-3">
													<div className="flex items-center space-x-2">
														<button
															onClick={() =>
																handleDeleteClient(client.client_id)
															}
															className="text-danger hover:text-danger/80 transition-colors">
															<Trash2 className="h-4 w-4" />
														</button>
													</div>
												</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>
						)}
					</div>
				</div>

				{/* Create Client Modal */}
				{showCreateForm && (
					<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
						<div className="bg-white rounded-lg shadow-default border border-stroke max-w-md w-full mx-4">
							<div className="px-6 py-4 border-b border-stroke">
								<h3 className="text-xl font-bold text-black">
									Create New Client
								</h3>
							</div>

							<form onSubmit={handleCreateClient} className="p-6 space-y-4">
								{error && (
									<div className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-lg text-sm">
										{error}
									</div>
								)}

								{/* Company Name */}
								<div>
									<label className="block text-sm font-medium text-black mb-2">
										Company Name
									</label>
									<div className="relative">
										<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
											<Building className="h-5 w-5 text-body" />
										</div>
										<input
											type="text"
											name="company_name"
											required
											value={formData.company_name}
											onChange={handleFormChange}
											className="block w-full pl-10 pr-3 py-2 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
											placeholder="Enter company name"
										/>
									</div>
								</div>

								{/* Email */}
								<div>
									<label className="block text-sm font-medium text-black mb-2">
										Email
									</label>
									<div className="relative">
										<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
											<Mail className="h-5 w-5 text-body" />
										</div>
										<input
											type="email"
											name="email"
											required
											value={formData.email}
											onChange={handleFormChange}
											className="block w-full pl-10 pr-3 py-2 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
											placeholder="Enter email address"
										/>
									</div>
								</div>

								{/* Password */}
								<div>
									<label className="block text-sm font-medium text-black mb-2">
										Password
									</label>
									<div className="relative">
										<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
											<Key className="h-5 w-5 text-body" />
										</div>
										<input
											type={showPassword ? "text" : "password"}
											name="password"
											required
											value={formData.password}
											onChange={handleFormChange}
											className="block w-full pl-10 pr-10 py-2 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
											placeholder="Enter password"
										/>
										<button
											type="button"
											onClick={() => setShowPassword(!showPassword)}
											className="absolute inset-y-0 right-0 pr-3 flex items-center">
											{showPassword ? (
												<EyeOff className="h-5 w-5 text-body" />
											) : (
												<Eye className="h-5 w-5 text-body" />
											)}
										</button>
									</div>
								</div>

								{/* Data Upload Section */}
								<div>
									<label className="block text-sm font-medium text-black mb-2">
										Data Type
									</label>
									<select
										name="data_type"
										value={formData.data_type}
										onChange={handleFormChange}
										className="block w-full px-3 py-2 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-primary focus:border-transparent outline-none">
										<option value="json">JSON</option>
										<option value="csv">CSV</option>
										<option value="xml">XML</option>
										<option value="api">API</option>
									</select>
								</div>

								{/* Input Method Toggle */}
								<div>
									<label className="block text-sm font-medium text-black mb-2">
										Input Method
									</label>
									<div className="flex space-x-4">
										<button
											type="button"
											onClick={() => handleInputMethodChange("paste")}
											className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
												formData.input_method === "paste"
													? "bg-primary text-white border-primary"
													: "bg-white text-body border-stroke hover:bg-gray-1"
											}`}>
											Paste Text
										</button>
										<button
											type="button"
											onClick={() => handleInputMethodChange("upload")}
											className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
												formData.input_method === "upload"
													? "bg-primary text-white border-primary"
													: "bg-white text-body border-stroke hover:bg-gray-1"
											}`}>
											Upload File
										</button>
									</div>
								</div>

								{/* Data Content */}
								{formData.input_method === "paste" ? (
									<div>
										<label className="block text-sm font-medium text-black mb-2">
											Data Content
										</label>
										<textarea
											name="data_content"
											value={formData.data_content}
											onChange={handleFormChange}
											rows={4}
											className="block w-full px-3 py-2 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none"
											placeholder={getPlaceholderText(formData.data_type)}
											required
										/>
									</div>
								) : (
									<div>
										<label className="block text-sm font-medium text-black mb-2">
											Upload File
										</label>
										<input
											type="file"
											onChange={handleFileChange}
											accept={
												formData.data_type === "csv"
													? ".csv,.txt"
													: formData.data_type === "json"
													? ".json,.txt"
													: formData.data_type === "xml"
													? ".xml,.txt"
													: ".txt,.json,.csv,.xml"
											}
											className="block w-full px-3 py-2 border border-stroke rounded-lg bg-gray-1 focus:ring-2 focus:ring-primary focus:border-transparent outline-none file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90"
											required
										/>
										{formData.uploaded_file && (
											<p className="mt-2 text-sm text-body">
												Selected: {formData.uploaded_file.name} (
												{(formData.uploaded_file.size / 1024).toFixed(1)} KB)
											</p>
										)}
									</div>
								)}

								{/* Form Actions */}
								<div className="flex space-x-3 pt-4">
									<button
										type="button"
										onClick={() => setShowCreateForm(false)}
										className="flex-1 px-4 py-2 border border-stroke text-body rounded-lg hover:bg-gray-1 transition-colors">
										Cancel
									</button>
									<button
										type="submit"
										disabled={formLoading}
										className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50">
										{formLoading ? "Creating..." : "Create Client"}
									</button>
								</div>
							</form>
						</div>
					</div>
				)}
			</main>
		</div>
	);
};

export default SuperAdminDashboard;
