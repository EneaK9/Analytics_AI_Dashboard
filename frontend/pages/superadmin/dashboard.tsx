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
	Store,
	Cloud,
	ShoppingCart,
	Package,
	Globe,
	CheckCircle,
	AlertTriangle,
	X,
} from "lucide-react";
import api from "../../lib/axios";
import { useAuth } from "../../lib/useAuth";
import SftpProgressModal from "../../components/SftpProgressModal";

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
	input_method: "paste" | "upload" | "api" | "sftp";
	uploaded_file: File | null;

	// API Integration fields
	platform_type: "manual" | "shopify" | "amazon" | "woocommerce";
	connection_name: string;

	// SFTP Integration fields
	sftp_host: string;
	sftp_username: string;
	sftp_password: string;
	sftp_port: number;
	sftp_remote_path: string;
	sftp_file_pattern: string;
	auto_sync_enabled: boolean;

	// Shopify fields
	shop_domain: string;
	shopify_access_token: string;

	// Amazon fields
	amazon_seller_id: string;
	amazon_marketplace_ids: string;
	amazon_access_key_id: string;
	amazon_secret_access_key: string;
	amazon_refresh_token: string;
	amazon_region: string;

	// WooCommerce fields
	woo_site_url: string;
	woo_consumer_key: string;
	woo_consumer_secret: string;
	woo_version: string;

	sync_frequency_hours: number;
}

interface PlatformConfig {
	platform_type: string;
	display_name: string;
	description: string;
	required_fields: Record<string, any>;
	optional_fields: Record<string, any>;
	setup_instructions: string;
	documentation_url: string;
}

const SuperAdminDashboard: React.FC = () => {
	const [clients, setClients] = useState<Client[]>([]);
	const [loading, setLoading] = useState(true);
	const [showCreateForm, setShowCreateForm] = useState(false);
	const [showPassword, setShowPassword] = useState(false);
	const [platformConfigs, setPlatformConfigs] = useState<PlatformConfig[]>([]);
	const [connectionTestResult, setConnectionTestResult] = useState<{
		success: boolean;
		message: string;
		tested: boolean;
	}>({ success: false, message: "", tested: false });
	const [formData, setFormData] = useState<CreateClientForm>({
		company_name: "",
		email: "",
		password: "",
		// subscription_tier: "basic",
		data_type: "json",
		data_content: "",
		input_method: "paste",
		uploaded_file: null,

		// API Integration fields
		platform_type: "manual",
		connection_name: "",

		// Shopify fields
		shop_domain: "",
		shopify_access_token: "",

		// Amazon fields
		amazon_seller_id: "",
		amazon_marketplace_ids: "ATVPDKIKX0DER",
		amazon_access_key_id: "",
		amazon_secret_access_key: "",
		amazon_refresh_token: "",
		amazon_region: "us-east-1",

		// WooCommerce fields
		woo_site_url: "",
		woo_consumer_key: "",
		woo_consumer_secret: "",
		woo_version: "wc/v3",

		// SFTP fields
		sftp_host: "",
		sftp_username: "",
		sftp_password: "",
		sftp_port: 22,
		sftp_remote_path: "/",
		sftp_file_pattern: "*.*",
		auto_sync_enabled: false,

		sync_frequency_hours: 24,
	});
	const [formLoading, setFormLoading] = useState(false);
	const [error, setError] = useState("");
	const router = useRouter();

	// SFTP state
	const [sftpConnectionTest, setSftpConnectionTest] = useState<{
		success: boolean;
		message: string;
		tested: boolean;
		files: any[];
	}>({ success: false, message: "", tested: false, files: [] });
	const [selectedSftpFiles, setSelectedSftpFiles] = useState<string[]>([]);

	// Progress modal state
	const [showProgressModal, setShowProgressModal] = useState(false);
	const [progressClientId, setProgressClientId] = useState<string>("");
	const [progressClientName, setProgressClientName] = useState<string>("");

	// Check authentication and load data
	useEffect(() => {
		const checkAuth = async () => {
			try {
				const token = localStorage.getItem("superadmin_token");
				if (!token) {
					router.push("/superadmin/login");
					return;
				}

				await Promise.all([loadClients(), loadPlatformConfigs()]);
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

	const loadPlatformConfigs = async () => {
		try {
			const response = await api.get("/superadmin/api-platforms");
			setPlatformConfigs(response.data.platforms || []);
		} catch (error) {
			console.error("Failed to load platform configs:", error);
			setPlatformConfigs([]);
		}
	};

	const { logout } = useAuth();

	const handleLogout = () => {
		logout();
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

	const handleInputMethodChange = (
		method: "paste" | "upload" | "api" | "sftp"
	) => {
		setFormData((prev) => ({
			...prev,
			input_method: method,
			data_content:
				method === "upload" || method === "api" ? "" : prev.data_content,
			uploaded_file:
				method === "paste" || method === "api" ? null : prev.uploaded_file,
		}));

		// Reset connection test when changing input method
		if (method !== "api") {
			setConnectionTestResult({ success: false, message: "", tested: false });
		}
		if (method !== "sftp") {
			setSftpConnectionTest({
				success: false,
				message: "",
				tested: false,
				files: [],
			});
			setSelectedSftpFiles([]);
		}
	};

	const testAPIConnection = async () => {
		if (
			formData.input_method !== "api" ||
			formData.platform_type === "manual"
		) {
			return;
		}

		setFormLoading(true);
		setConnectionTestResult({
			success: false,
			message: "Testing connection...",
			tested: false,
		});

		try {
			let credentials: any = {};

			if (formData.platform_type === "shopify") {
				credentials = {
					shop_domain: formData.shop_domain,
					access_token: formData.shopify_access_token,
					scopes: ["read_orders", "read_products", "read_customers"],
				};
			} else if (formData.platform_type === "amazon") {
				credentials = {
					seller_id: formData.amazon_seller_id,
					marketplace_ids: formData.amazon_marketplace_ids
						.split(",")
						.map((id) => id.trim()),
					access_key_id: formData.amazon_access_key_id,
					secret_access_key: formData.amazon_secret_access_key,
					refresh_token: formData.amazon_refresh_token,
					region: formData.amazon_region,
				};
			} else if (formData.platform_type === "woocommerce") {
				credentials = {
					site_url: formData.woo_site_url,
					consumer_key: formData.woo_consumer_key,
					consumer_secret: formData.woo_consumer_secret,
					version: formData.woo_version,
				};
			}

			const testData = new FormData();
			testData.append("platform_type", formData.platform_type);
			testData.append("credentials_json", JSON.stringify(credentials));

			const response = await api.post(
				"/superadmin/test-api-connection",
				testData,
				{
					headers: {
						"Content-Type": "multipart/form-data",
					},
				}
			);

			setConnectionTestResult({
				success: response.data.success,
				message: response.data.message,
				tested: true,
			});
		} catch (error: any) {
			console.error("API connection test failed:", error);

			let errorMessage = "Connection test failed";

			// Handle specific error cases
			if (error.response?.status === 401) {
				errorMessage =
					"Authentication failed - please refresh the page and try again (your session may have expired)";
			} else if (error.response?.data?.detail === "Token expired") {
				errorMessage =
					"Your session has expired. Please refresh the page and log in again.";
			} else if (error.response?.data?.message) {
				errorMessage = error.response.data.message;
			} else if (error.response?.data?.detail) {
				errorMessage = error.response.data.detail;
			}

			setConnectionTestResult({
				success: false,
				message: errorMessage,
				tested: true,
			});
		} finally {
			setFormLoading(false);
		}
	};

	const testSFTPConnection = async () => {
		if (formData.input_method !== "sftp") {
			return;
		}

		setFormLoading(true);
		setSftpConnectionTest({
			success: false,
			message: "Testing SFTP connection...",
			tested: false,
			files: [],
		});

		try {
			const testData = new FormData();
			testData.append("sftp_host", formData.sftp_host);
			testData.append("sftp_username", formData.sftp_username);
			testData.append("sftp_password", formData.sftp_password);
			testData.append("sftp_port", formData.sftp_port.toString());
			testData.append("sftp_remote_path", formData.sftp_remote_path);
			testData.append("sftp_file_pattern", formData.sftp_file_pattern);

			const response = await api.post(
				"/superadmin/test-sftp-connection",
				testData,
				{
					headers: {
						"Content-Type": "multipart/form-data",
					},
				}
			);

			setSftpConnectionTest({
				success: response.data.success,
				message: response.data.message,
				tested: true,
				files: response.data.files || [],
			});

			if (response.data.success) {
				// Auto-select all files by default
				setSelectedSftpFiles(response.data.files.map((f: any) => f.filename));
			}
		} catch (error: any) {
			console.error("SFTP connection test failed:", error);

			let errorMessage = "SFTP connection test failed";

			if (error.response?.status === 401) {
				errorMessage =
					"Authentication failed - please refresh the page and try again";
			} else if (error.response?.data?.message) {
				errorMessage = error.response.data.message;
			} else if (error.response?.data?.detail) {
				errorMessage = error.response.data.detail;
			}

			setSftpConnectionTest({
				success: false,
				message: errorMessage,
				tested: true,
				files: [],
			});
		} finally {
			setFormLoading(false);
		}
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

			// Handle different input methods
			if (formData.input_method === "api") {
				// API Integration
				submitData.append("platform_type", formData.platform_type);
				submitData.append("connection_name", formData.connection_name);
				submitData.append(
					"sync_frequency_hours",
					formData.sync_frequency_hours.toString()
				);

				// Add platform-specific credentials
				if (formData.platform_type === "shopify") {
					submitData.append("shop_domain", formData.shop_domain);
					submitData.append(
						"shopify_access_token",
						formData.shopify_access_token
					);
				} else if (formData.platform_type === "amazon") {
					submitData.append("amazon_seller_id", formData.amazon_seller_id);
					submitData.append(
						"amazon_marketplace_ids",
						formData.amazon_marketplace_ids
					);
					submitData.append(
						"amazon_access_key_id",
						formData.amazon_access_key_id
					);
					submitData.append(
						"amazon_secret_access_key",
						formData.amazon_secret_access_key
					);
					submitData.append(
						"amazon_refresh_token",
						formData.amazon_refresh_token
					);
					submitData.append("amazon_region", formData.amazon_region);
				} else if (formData.platform_type === "woocommerce") {
					submitData.append("woo_site_url", formData.woo_site_url);
					submitData.append("woo_consumer_key", formData.woo_consumer_key);
					submitData.append(
						"woo_consumer_secret",
						formData.woo_consumer_secret
					);
					submitData.append("woo_version", formData.woo_version);
				}

				await api.post("/superadmin/clients/api-integration", submitData, {
					headers: {
						"Content-Type": "multipart/form-data",
					},
				});
			} else if (formData.input_method === "sftp") {
				// SFTP Integration
				submitData.append("sftp_host", formData.sftp_host);
				submitData.append("sftp_username", formData.sftp_username);
				submitData.append("sftp_password", formData.sftp_password);
				submitData.append("sftp_port", formData.sftp_port.toString());
				submitData.append("sftp_remote_path", formData.sftp_remote_path);
				submitData.append("sftp_file_pattern", formData.sftp_file_pattern);
				submitData.append(
					"auto_sync_enabled",
					formData.auto_sync_enabled.toString()
				);
				submitData.append(
					"sync_frequency_hours",
					formData.sync_frequency_hours.toString()
				);

				// Add selected files if any
				if (selectedSftpFiles.length > 0) {
					submitData.append(
						"selected_files",
						JSON.stringify(selectedSftpFiles)
					);
				}

				const response = await api.post(
					"/superadmin/clients/sftp-integration",
					submitData,
					{
						headers: {
							"Content-Type": "multipart/form-data",
						},
					}
				);

				// Show progress modal for SFTP client
				if (response.data && response.data.client_id) {
					setProgressClientId(response.data.client_id);
					setProgressClientName(formData.company_name);
					setShowProgressModal(true);
				}
			} else {
				// Manual data upload (existing logic)
				submitData.append("data_type", formData.data_type);
				submitData.append("input_method", formData.input_method);

				if (formData.input_method === "paste") {
					submitData.append("data_content", formData.data_content);
				} else if (formData.uploaded_file) {
					submitData.append("uploaded_file", formData.uploaded_file);
				}

				const response = await api.post("/superadmin/clients", submitData, {
					headers: {
						"Content-Type": "multipart/form-data",
					},
				});

				// For SFTP clients, show progress modal
				if (
					formData.input_method === "sftp" &&
					response.data &&
					response.data.client_id
				) {
					setProgressClientId(response.data.client_id);
					setProgressClientName(formData.company_name);
					setShowProgressModal(true);
				}
			}

			// Reset form and reload clients
			setFormData({
				company_name: "",
				email: "",
				password: "",
				data_type: "json",
				data_content: "",
				input_method: "paste",
				uploaded_file: null,

				// API Integration fields
				platform_type: "manual",
				connection_name: "",

				// Shopify fields
				shop_domain: "",
				shopify_access_token: "",

				// Amazon fields
				amazon_seller_id: "",
				amazon_marketplace_ids: "ATVPDKIKX0DER",
				amazon_access_key_id: "",
				amazon_secret_access_key: "",
				amazon_refresh_token: "",
				amazon_region: "us-east-1",

				// WooCommerce fields
				woo_site_url: "",
				woo_consumer_key: "",
				woo_consumer_secret: "",
				woo_version: "wc/v3",

				// SFTP fields
				sftp_host: "",
				sftp_username: "",
				sftp_password: "",
				sftp_port: 22,
				sftp_remote_path: "/",
				sftp_file_pattern: "*.*",
				auto_sync_enabled: false,

				sync_frequency_hours: 24,
			});
			setShowCreateForm(false);
			setConnectionTestResult({ success: false, message: "", tested: false });
			setSftpConnectionTest({
				success: false,
				message: "",
				tested: false,
				files: [],
			});
			setSelectedSftpFiles([]);
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
					<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
						<div className="bg-white rounded-lg shadow-default border border-stroke max-w-2xl w-full max-h-[90vh] flex flex-col">
							<div className="px-6 py-4 border-b border-stroke flex items-center justify-between flex-shrink-0">
								<h3 className="text-xl font-bold text-black">
									Create New Client
								</h3>
								<button
									onClick={() => setShowCreateForm(false)}
									className="text-gray-400 hover:text-gray-600">
									<X className="h-6 w-6" />
								</button>
							</div>

							{/* Scrollable Form Content */}
							<div className="flex-1 overflow-y-auto">
								<form
									id="create-client-form"
									onSubmit={handleCreateClient}
									className="p-4 space-y-3">
									{error && (
										<div className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-lg text-sm">
											{error}
										</div>
									)}

									{/* Basic Information */}
									<div className="grid grid-cols-1 gap-3">
										{/* Company Name */}
										<div>
											<label className="block text-xs font-medium text-black mb-1">
												Company Name
											</label>
											<div className="relative">
												<div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
													<Building className="h-4 w-4 text-body" />
												</div>
												<input
													type="text"
													name="company_name"
													required
													value={formData.company_name}
													onChange={handleFormChange}
													className="block w-full pl-8 pr-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
													placeholder="Enter company name"
												/>
											</div>
										</div>

										{/* Email & Password Row */}
										<div className="grid grid-cols-2 gap-3">
											<div>
												<label className="block text-xs font-medium text-black mb-1">
													Email
												</label>
												<div className="relative">
													<div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
														<Mail className="h-4 w-4 text-body" />
													</div>
													<input
														type="email"
														name="email"
														required
														value={formData.email}
														onChange={handleFormChange}
														className="block w-full pl-8 pr-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
														placeholder="Email"
													/>
												</div>
											</div>

											<div>
												<label className="block text-xs font-medium text-black mb-1">
													Password
												</label>
												<div className="relative">
													<div className="absolute inset-y-0 left-0 pl-2 flex items-center pointer-events-none">
														<Key className="h-4 w-4 text-body" />
													</div>
													<input
														type={showPassword ? "text" : "password"}
														name="password"
														required
														value={formData.password}
														onChange={handleFormChange}
														className="block w-full pl-8 pr-8 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
														placeholder="Password"
													/>
													<button
														type="button"
														onClick={() => setShowPassword(!showPassword)}
														className="absolute inset-y-0 right-0 pr-2 flex items-center">
														{showPassword ? (
															<EyeOff className="h-4 w-4 text-body" />
														) : (
															<Eye className="h-4 w-4 text-body" />
														)}
													</button>
												</div>
											</div>
										</div>
									</div>

									{/* Data Type Selection */}
									{formData.input_method !== "api" && (
										<div>
											<label className="block text-xs font-medium text-black mb-1">
												Data Type
											</label>
											<select
												name="data_type"
												value={formData.data_type}
												onChange={handleFormChange}
												className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none">
												<option value="json">JSON</option>
												<option value="csv">CSV</option>
												<option value="xml">XML</option>
											</select>
										</div>
									)}

									{/* Input Method Toggle */}
									<div>
										<label className="block text-sm font-medium text-black mb-2">
											Data Source
										</label>
										<div className="grid grid-cols-4 gap-2">
											<button
												type="button"
												onClick={() => handleInputMethodChange("paste")}
												className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
													formData.input_method === "paste"
														? "bg-primary text-white border-primary"
														: "bg-white text-body border-stroke hover:bg-gray-1"
												}`}>
												<div className="flex flex-col items-center space-y-1">
													<Edit className="h-4 w-4" />
													<span>Paste</span>
												</div>
											</button>
											<button
												type="button"
												onClick={() => handleInputMethodChange("upload")}
												className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
													formData.input_method === "upload"
														? "bg-primary text-white border-primary"
														: "bg-white text-body border-stroke hover:bg-gray-1"
												}`}>
												<div className="flex flex-col items-center space-y-1">
													<Package className="h-4 w-4" />
													<span>Upload</span>
												</div>
											</button>
											<button
												type="button"
												onClick={() => handleInputMethodChange("api")}
												className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
													formData.input_method === "api"
														? "bg-primary text-white border-primary"
														: "bg-white text-body border-stroke hover:bg-gray-1"
												}`}>
												<div className="flex flex-col items-center space-y-1">
													<Cloud className="h-4 w-4" />
													<span>API</span>
												</div>
											</button>
											<button
												type="button"
												onClick={() => handleInputMethodChange("sftp")}
												className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
													formData.input_method === "sftp"
														? "bg-primary text-white border-primary"
														: "bg-white text-body border-stroke hover:bg-gray-1"
												}`}>
												<div className="flex flex-col items-center space-y-1">
													<Package className="h-4 w-4" />
													<span>SFTP</span>
												</div>
											</button>
										</div>
									</div>

									{/* Data Content */}
									{formData.input_method === "paste" ? (
										<div>
											<label className="block text-xs font-medium text-black mb-1">
												Data Content
											</label>
											<textarea
												name="data_content"
												value={formData.data_content}
												onChange={handleFormChange}
												rows={3}
												className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none resize-none"
												placeholder={getPlaceholderText(formData.data_type)}
												required
											/>
										</div>
									) : formData.input_method === "upload" ? (
										<div>
											<label className="block text-xs font-medium text-black mb-1">
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
												className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90"
												required
											/>
											{formData.uploaded_file && (
												<p className="mt-1 text-xs text-body">
													{formData.uploaded_file.name} (
													{(formData.uploaded_file.size / 1024).toFixed(1)} KB)
												</p>
											)}
										</div>
									) : formData.input_method === "api" ? (
										/* API Integration Forms */
										<div className="space-y-4">
											{/* Platform Selection */}
											<div>
												<label className="block text-sm font-medium text-black mb-2">
													Platform
												</label>
												<div className="grid grid-cols-3 gap-2">
													<button
														type="button"
														onClick={() =>
															setFormData({
																...formData,
																platform_type: "shopify",
															})
														}
														className={`p-2 rounded-lg border transition-colors text-xs ${
															formData.platform_type === "shopify"
																? "bg-green-50 border-green-500 text-green-700"
																: "bg-white border-stroke hover:bg-gray-1"
														}`}>
														<Store className="h-5 w-5 mx-auto mb-1" />
														<div className="font-medium">Shopify</div>
													</button>
													<button
														type="button"
														onClick={() =>
															setFormData({
																...formData,
																platform_type: "amazon",
															})
														}
														className={`p-2 rounded-lg border transition-colors text-xs ${
															formData.platform_type === "amazon"
																? "bg-orange-50 border-orange-500 text-orange-700"
																: "bg-white border-stroke hover:bg-gray-1"
														}`}>
														<ShoppingCart className="h-5 w-5 mx-auto mb-1" />
														<div className="font-medium">Amazon</div>
													</button>
													<button
														type="button"
														onClick={() =>
															setFormData({
																...formData,
																platform_type: "woocommerce",
															})
														}
														className={`p-2 rounded-lg border transition-colors text-xs ${
															formData.platform_type === "woocommerce"
																? "bg-purple-50 border-purple-500 text-purple-700"
																: "bg-white border-stroke hover:bg-gray-1"
														}`}>
														<Globe className="h-5 w-5 mx-auto mb-1" />
														<div className="font-medium">WooCommerce</div>
													</button>
												</div>
											</div>

											{/* Connection Name */}
											<div>
												<label className="block text-xs font-medium text-black mb-1">
													Connection Name
												</label>
												<input
													type="text"
													name="connection_name"
													value={formData.connection_name}
													onChange={handleFormChange}
													placeholder="e.g., Main Store, Amazon US"
													className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
													required
												/>
											</div>

											{/* Shopify Configuration */}
											{formData.platform_type === "shopify" && (
												<div className="bg-green-50 p-3 rounded-lg border border-green-200 space-y-3">
													<div className="flex items-center space-x-2">
														<Store className="h-4 w-4 text-green-600" />
														<h4 className="text-sm font-medium text-green-800">
															Shopify Setup
														</h4>
													</div>
													<div className="grid grid-cols-1 gap-3">
														<div>
															<label className="block text-xs font-medium text-green-800 mb-1">
																Shop Domain
															</label>
															<input
																type="text"
																name="shop_domain"
																value={formData.shop_domain}
																onChange={handleFormChange}
																placeholder="mystore.myshopify.com"
																className="block w-full px-2 py-1.5 text-sm border border-green-300 rounded bg-white focus:ring-1 focus:ring-green-500 focus:border-transparent outline-none"
																required
															/>
														</div>
														<div>
															<label className="block text-xs font-medium text-green-800 mb-1">
																Access Token
															</label>
															<input
																type="password"
																name="shopify_access_token"
																value={formData.shopify_access_token}
																onChange={handleFormChange}
																placeholder="shpat_..."
																className="block w-full px-2 py-1.5 text-sm border border-green-300 rounded bg-white focus:ring-1 focus:ring-green-500 focus:border-transparent outline-none"
																required
															/>
														</div>
													</div>
												</div>
											)}

											{/* Amazon Configuration */}
											{formData.platform_type === "amazon" && (
												<div className="bg-orange-50 p-3 rounded-lg border border-orange-200 space-y-3">
													<div className="flex items-center space-x-2">
														<ShoppingCart className="h-4 w-4 text-orange-600" />
														<h4 className="text-sm font-medium text-orange-800">
															Amazon SP-API Setup
														</h4>
													</div>
													<div className="grid grid-cols-2 gap-2">
														<div>
															<label className="block text-xs font-medium text-orange-800 mb-1">
																Seller ID
															</label>
															<input
																type="text"
																name="amazon_seller_id"
																value={formData.amazon_seller_id}
																onChange={handleFormChange}
																placeholder="A1B2C3D4E5F6G7"
																className="block w-full px-2 py-1.5 text-sm border border-orange-300 rounded bg-white focus:ring-1 focus:ring-orange-500 focus:border-transparent outline-none"
																required
															/>
														</div>
														<div>
															<label className="block text-xs font-medium text-orange-800 mb-1">
																Marketplace IDs
															</label>
															<input
																type="text"
																name="amazon_marketplace_ids"
																value={formData.amazon_marketplace_ids}
																onChange={handleFormChange}
																placeholder="ATVPDKIKX0DER"
																className="block w-full px-2 py-1.5 text-sm border border-orange-300 rounded bg-white focus:ring-1 focus:ring-orange-500 focus:border-transparent outline-none"
																required
															/>
														</div>
														<div>
															<label className="block text-xs font-medium text-orange-800 mb-1">
																Access Key ID
															</label>
															<input
																type="text"
																name="amazon_access_key_id"
																value={formData.amazon_access_key_id}
																onChange={handleFormChange}
																placeholder="AKIA..."
																className="block w-full px-2 py-1.5 text-sm border border-orange-300 rounded bg-white focus:ring-1 focus:ring-orange-500 focus:border-transparent outline-none"
																required
															/>
														</div>
														<div>
															<label className="block text-xs font-medium text-orange-800 mb-1">
																Secret Key
															</label>
															<input
																type="password"
																name="amazon_secret_access_key"
																value={formData.amazon_secret_access_key}
																onChange={handleFormChange}
																placeholder="Secret key"
																className="block w-full px-2 py-1.5 text-sm border border-orange-300 rounded bg-white focus:ring-1 focus:ring-orange-500 focus:border-transparent outline-none"
																required
															/>
														</div>
													</div>
													<div>
														<label className="block text-xs font-medium text-orange-800 mb-1">
															Refresh Token
														</label>
														<input
															type="password"
															name="amazon_refresh_token"
															value={formData.amazon_refresh_token}
															onChange={handleFormChange}
															placeholder="Atzr|..."
															className="block w-full px-2 py-1.5 text-sm border border-orange-300 rounded bg-white focus:ring-1 focus:ring-orange-500 focus:border-transparent outline-none"
															required
														/>
													</div>
												</div>
											)}

											{/* WooCommerce Configuration */}
											{formData.platform_type === "woocommerce" && (
												<div className="bg-purple-50 p-3 rounded-lg border border-purple-200 space-y-3">
													<div className="flex items-center space-x-2">
														<Globe className="h-4 w-4 text-purple-600" />
														<h4 className="text-sm font-medium text-purple-800">
															WooCommerce Setup
														</h4>
													</div>
													<div>
														<label className="block text-xs font-medium text-purple-800 mb-1">
															Site URL
														</label>
														<input
															type="url"
															name="woo_site_url"
															value={formData.woo_site_url}
															onChange={handleFormChange}
															placeholder="https://mystore.com"
															className="block w-full px-2 py-1.5 text-sm border border-purple-300 rounded bg-white focus:ring-1 focus:ring-purple-500 focus:border-transparent outline-none"
															required
														/>
													</div>
													<div className="grid grid-cols-2 gap-2">
														<div>
															<label className="block text-xs font-medium text-purple-800 mb-1">
																Consumer Key
															</label>
															<input
																type="text"
																name="woo_consumer_key"
																value={formData.woo_consumer_key}
																onChange={handleFormChange}
																placeholder="ck_..."
																className="block w-full px-2 py-1.5 text-sm border border-purple-300 rounded bg-white focus:ring-1 focus:ring-purple-500 focus:border-transparent outline-none"
																required
															/>
														</div>
														<div>
															<label className="block text-xs font-medium text-purple-800 mb-1">
																Consumer Secret
															</label>
															<input
																type="password"
																name="woo_consumer_secret"
																value={formData.woo_consumer_secret}
																onChange={handleFormChange}
																placeholder="cs_..."
																className="block w-full px-2 py-1.5 text-sm border border-purple-300 rounded bg-white focus:ring-1 focus:ring-purple-500 focus:border-transparent outline-none"
																required
															/>
														</div>
													</div>
												</div>
											)}

											{/* Connection Test */}
											{formData.platform_type !== "manual" && (
												<div>
													<button
														type="button"
														onClick={testAPIConnection}
														disabled={formLoading}
														className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2">
														{formLoading ? (
															<>
																<div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
																<span>Testing...</span>
															</>
														) : (
															<>
																<CheckCircle className="h-3 w-3" />
																<span>Test Connection</span>
															</>
														)}
													</button>

													{/* Connection Test Result */}
													{connectionTestResult.tested && (
														<div
															className={`mt-2 p-2 rounded text-xs border ${
																connectionTestResult.success
																	? "bg-green-50 border-green-200 text-green-700"
																	: "bg-red-50 border-red-200 text-red-700"
															}`}>
															<div className="flex items-center space-x-2">
																{connectionTestResult.success ? (
																	<CheckCircle className="h-3 w-3 text-green-600" />
																) : (
																	<AlertTriangle className="h-3 w-3 text-red-600" />
																)}
																<span className="font-medium">
																	{connectionTestResult.success
																		? "Success!"
																		: "Failed"}
																</span>
															</div>
															<p className="text-xs mt-1">
																{connectionTestResult.message}
															</p>
														</div>
													)}
												</div>
											)}

											{/* Sync Frequency */}
											<div>
												<label className="block text-xs font-medium text-black mb-1">
													Sync Frequency
												</label>
												<select
													name="sync_frequency_hours"
													value={formData.sync_frequency_hours}
													onChange={handleFormChange}
													className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-gray-1 focus:ring-1 focus:ring-primary focus:border-transparent outline-none">
													<option value={1}>Every Hour</option>
													<option value={6}>Every 6 Hours</option>
													<option value={12}>Every 12 Hours</option>
													<option value={24}>Daily</option>
													<option value={168}>Weekly</option>
												</select>
											</div>
										</div>
									) : formData.input_method === "sftp" ? (
										/* SFTP Integration Forms */
										<div className="space-y-4">
											{/* SFTP Connection Details */}
											<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
												<h4 className="text-sm font-medium text-blue-800 mb-3 flex items-center">
													<Package className="h-4 w-4 mr-2" />
													SFTP Server Configuration
												</h4>
												<div className="grid grid-cols-2 gap-3">
													{/* Host */}
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															SFTP Host
														</label>
														<input
															type="text"
															name="sftp_host"
															value={formData.sftp_host}
															onChange={handleFormChange}
															placeholder="sftp.yardiaspxtl1.com"
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
															required
														/>
													</div>

													{/* Port */}
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															Port
														</label>
														<input
															type="number"
															name="sftp_port"
															value={formData.sftp_port}
															onChange={handleFormChange}
															placeholder="22"
															min="1"
															max="65535"
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
															required
														/>
													</div>

													{/* Username */}
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															Username
														</label>
														<input
															type="text"
															name="sftp_username"
															value={formData.sftp_username}
															onChange={handleFormChange}
															placeholder="88927ftp"
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
															required
														/>
													</div>

													{/* Password */}
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															Password
														</label>
														<input
															type="password"
															name="sftp_password"
															value={formData.sftp_password}
															onChange={handleFormChange}
															placeholder="Enter SFTP password"
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
															required
														/>
													</div>

													{/* Remote Path */}
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															Remote Path
														</label>
														<input
															type="text"
															name="sftp_remote_path"
															value={formData.sftp_remote_path}
															onChange={handleFormChange}
															placeholder="/"
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
														/>
													</div>

													{/* File Pattern */}
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															File Pattern
														</label>
														<input
															type="text"
															name="sftp_file_pattern"
															value={formData.sftp_file_pattern}
															onChange={handleFormChange}
															placeholder="*.csv, *.xlsx, *.*"
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none"
														/>
													</div>
												</div>

												{/* Test Connection Button */}
												<div className="mt-3">
													<button
														type="button"
														onClick={testSFTPConnection}
														disabled={
															formLoading ||
															!formData.sftp_host ||
															!formData.sftp_username ||
															!formData.sftp_password
														}
														className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm">
														{formLoading
															? "Testing..."
															: "Test SFTP Connection"}
													</button>
												</div>

												{/* Connection Test Result */}
												{sftpConnectionTest.tested && (
													<div className="mt-3">
														<div
															className={`p-3 rounded-lg border text-sm ${
																sftpConnectionTest.success
																	? "bg-green-50 border-green-200 text-green-700"
																	: "bg-red-50 border-red-200 text-red-700"
															}`}>
															<div className="flex items-center space-x-2">
																{sftpConnectionTest.success ? (
																	<CheckCircle className="h-3 w-3 text-green-600" />
																) : (
																	<AlertTriangle className="h-3 w-3 text-red-600" />
																)}
																<span className="font-medium">
																	{sftpConnectionTest.success
																		? "Connection Successful!"
																		: "Connection Failed"}
																</span>
															</div>
															<p className="text-xs mt-1">
																{sftpConnectionTest.message}
															</p>

															{/* File Selection */}
															{sftpConnectionTest.success &&
																sftpConnectionTest.files.length > 0 && (
																	<div className="mt-3">
																		<h5 className="text-xs font-medium mb-2">
																			Available Files (
																			{sftpConnectionTest.files.length} found):
																		</h5>
																		<div className="max-h-32 overflow-y-auto space-y-1">
																			{sftpConnectionTest.files.map(
																				(file: any, index: number) => (
																					<label
																						key={index}
																						className="flex items-center space-x-2 text-xs">
																						<input
																							type="checkbox"
																							checked={selectedSftpFiles.includes(
																								file.filename
																							)}
																							onChange={(e) => {
																								if (e.target.checked) {
																									setSelectedSftpFiles([
																										...selectedSftpFiles,
																										file.filename,
																									]);
																								} else {
																									setSelectedSftpFiles(
																										selectedSftpFiles.filter(
																											(f) => f !== file.filename
																										)
																									);
																								}
																							}}
																							className="rounded border-gray-300"
																						/>
																						<span className="flex-1">
																							{file.filename}
																						</span>
																						<span className="text-gray-500">
																							{file.size
																								? `${(file.size / 1024).toFixed(
																										1
																								  )} KB`
																								: ""}
																						</span>
																					</label>
																				)
																			)}
																		</div>
																		<p className="text-xs text-gray-600 mt-2">
																			Selected: {selectedSftpFiles.length} of{" "}
																			{sftpConnectionTest.files.length} files
																		</p>
																	</div>
																)}
														</div>
													</div>
												)}
											</div>

											{/* Auto-sync Settings */}
											<div>
												<div className="flex items-center space-x-2 mb-2">
													<input
														type="checkbox"
														name="auto_sync_enabled"
														checked={formData.auto_sync_enabled}
														onChange={handleFormChange}
														className="rounded border-gray-300"
													/>
													<label className="text-sm font-medium text-black">
														Enable automatic synchronization
													</label>
												</div>

												{formData.auto_sync_enabled && (
													<div>
														<label className="block text-xs font-medium text-black mb-1">
															Sync Frequency
														</label>
														<select
															name="sync_frequency_hours"
															value={formData.sync_frequency_hours}
															onChange={handleFormChange}
															className="block w-full px-2 py-1.5 text-sm border border-stroke rounded bg-white focus:ring-1 focus:ring-primary focus:border-transparent outline-none">
															<option value={1}>Every Hour</option>
															<option value={6}>Every 6 Hours</option>
															<option value={12}>Every 12 Hours</option>
															<option value={24}>Daily</option>
															<option value={168}>Weekly</option>
														</select>
													</div>
												)}
											</div>
										</div>
									) : null}

									{/* Form Actions */}
								</form>
							</div>

							{/* Sticky Bottom Buttons */}
							<div className="border-t border-stroke p-4 flex-shrink-0">
								<div className="flex space-x-3">
									<button
										type="button"
										onClick={() => setShowCreateForm(false)}
										className="flex-1 px-4 py-2 border border-stroke text-body rounded-lg hover:bg-gray-1 transition-colors">
										Cancel
									</button>
									<button
										type="submit"
										form="create-client-form"
										disabled={formLoading}
										className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50">
										{formLoading ? "Creating..." : "Create Client"}
									</button>
								</div>
							</div>
						</div>
					</div>
				)}

				{/* SFTP Progress Modal */}
				<SftpProgressModal
					isOpen={showProgressModal}
					onClose={() => {
						setShowProgressModal(false);
						// Clear progress state when modal closes
						setProgressClientId("");
						setProgressClientName("");
					}}
					clientId={progressClientId}
					clientName={progressClientName}
				/>
			</main>
		</div>
	);
};

export default SuperAdminDashboard;
