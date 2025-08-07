import React, { useState, useEffect } from "react";
import {
	X,
	Download,
	CheckCircle,
	AlertCircle,
	Clock,
	FileText,
} from "lucide-react";
import { api } from "@/lib/axios";

interface SftpProgress {
	client_id: string;
	status: string;
	total_files: number;
	completed_files: number;
	current_file: string;
	total_bytes: number;
	downloaded_bytes: number;
	error_message: string;
	start_time: number;
	estimated_completion: number;
	progress_percentage: number;
	completed_at?: string;
}

interface SftpProgressModalProps {
	isOpen: boolean;
	onClose: () => void;
	clientId: string;
	clientName: string;
}

const SftpProgressModal: React.FC<SftpProgressModalProps> = ({
	isOpen,
	onClose,
	clientId,
	clientName,
}) => {
	const [progress, setProgress] = useState<SftpProgress | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");

	useEffect(() => {
		if (isOpen) {
			if (clientId) {
				// Use provided client ID
				fetchProgress();
				const interval = setInterval(fetchProgress, 2000); // Poll every 2 seconds
				return () => clearInterval(interval);
			} else {
				// Auto-detect latest SFTP client
				findLatestSftpClient();
			}
		}
	}, [isOpen, clientId]);

	const findLatestSftpClient = async () => {
		try {
			setLoading(true);
			// Get latest clients to find most recent SFTP client
			const response = await api.get("/superadmin/clients");
			const clients = response.data;

			// Find the most recent client (they're ordered by created_at desc)
			const latestClient = clients.find(
				(client: any) =>
					client.company_name && client.email && !client.has_schema
			);

			if (latestClient) {
				// Try to fetch progress for this client
				const progressResponse = await api.get(
					`/sftp/progress/${latestClient.client_id}`
				);
				setProgress(progressResponse.data);
				setError("");

				// Start polling for this client
				const interval = setInterval(
					() => fetchProgressForClient(latestClient.client_id),
					2000
				);
				setTimeout(() => clearInterval(interval), 300000); // Stop after 5 minutes
			} else {
				setError("No active SFTP downloads found");
			}
		} catch (err: any) {
			setError("Failed to find active SFTP downloads");
		} finally {
			setLoading(false);
		}
	};

	const fetchProgress = async () => {
		if (!clientId) return;
		try {
			setLoading(true);
			const response = await api.get(`/sftp/progress/${clientId}`);
			setProgress(response.data);
			setError("");
		} catch (err: any) {
			if (err.response?.status !== 404) {
				setError("Failed to fetch progress");
			}
		} finally {
			setLoading(false);
		}
	};

	const fetchProgressForClient = async (targetClientId: string) => {
		try {
			const response = await api.get(`/sftp/progress/${targetClientId}`);
			setProgress(response.data);
			setError("");
		} catch (err: any) {
			// Silently fail for polling
		}
	};

	const formatBytes = (bytes: number) => {
		if (bytes === 0) return "0 Bytes";
		const k = 1024;
		const sizes = ["Bytes", "KB", "MB", "GB"];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
	};

	const formatTime = (seconds: number) => {
		if (seconds < 60) return `${Math.round(seconds)}s`;
		if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
		return `${Math.round(seconds / 3600)}h`;
	};

	const getStatusIcon = (status: string) => {
		switch (status) {
			case "downloading":
				return <Download className="h-5 w-5 text-blue-600 animate-pulse" />;
			case "processing":
				return <Clock className="h-5 w-5 text-yellow-600 animate-spin" />;
			case "completed":
				return <CheckCircle className="h-5 w-5 text-green-600" />;
			case "failed":
				return <AlertCircle className="h-5 w-5 text-red-600" />;
			default:
				return <FileText className="h-5 w-5 text-gray-600" />;
		}
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case "downloading":
				return "text-blue-600 bg-blue-50";
			case "processing":
				return "text-yellow-600 bg-yellow-50";
			case "completed":
				return "text-green-600 bg-green-50";
			case "failed":
				return "text-red-600 bg-red-50";
			default:
				return "text-gray-600 bg-gray-50";
		}
	};

	if (!isOpen) return null;

	return (
		<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
				{/* Header */}
				<div className="flex items-center justify-between p-6 border-b">
					<h3 className="text-lg font-semibold text-gray-900">
						SFTP Download Progress
					</h3>
					<button
						onClick={onClose}
						className="text-gray-400 hover:text-gray-600 transition-colors">
						<X className="h-5 w-5" />
					</button>
				</div>

				{/* Content */}
				<div className="p-6">
					{loading && !progress ? (
						<div className="flex items-center justify-center py-8">
							<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
							<span className="ml-3 text-gray-600">Loading progress...</span>
						</div>
					) : error ? (
						<div className="text-center py-8">
							<AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
							<p className="text-red-600">{error}</p>
							<button
								onClick={fetchProgress}
								className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
								Retry
							</button>
						</div>
					) : progress ? (
						<div className="space-y-6">
							{/* Client Info */}
							<div>
								<h4 className="text-sm font-medium text-gray-700">Client</h4>
								<p className="text-lg text-gray-900">{clientName}</p>
							</div>

							{/* Status */}
							<div className="flex items-center space-x-3">
								{getStatusIcon(progress.status)}
								<div>
									<span
										className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
											progress.status
										)}`}>
										{progress.status.charAt(0).toUpperCase() +
											progress.status.slice(1)}
									</span>
								</div>
							</div>

							{/* Progress Bar */}
							{progress.status === "downloading" &&
								progress.total_bytes > 0 && (
									<div>
										<div className="flex justify-between text-sm text-gray-600 mb-1">
											<span>Download Progress</span>
											<span>{progress.progress_percentage}%</span>
										</div>
										<div className="w-full bg-gray-200 rounded-full h-2">
											<div
												className="bg-blue-600 h-2 rounded-full transition-all duration-300"
												style={{
													width: `${progress.progress_percentage}%`,
												}}></div>
										</div>
										<div className="flex justify-between text-xs text-gray-500 mt-1">
											<span>
												{formatBytes(progress.downloaded_bytes)} /{" "}
												{formatBytes(progress.total_bytes)}
											</span>
											{progress.estimated_completion > 0 && (
												<span>
													ETA:{" "}
													{formatTime(
														progress.estimated_completion - Date.now() / 1000
													)}
												</span>
											)}
										</div>
									</div>
								)}

							{/* Files Progress */}
							<div className="grid grid-cols-2 gap-4 text-sm">
								<div>
									<span className="text-gray-600">Files:</span>
									<span className="ml-2 font-medium">
										{progress.completed_files} / {progress.total_files}
									</span>
								</div>
								<div>
									<span className="text-gray-600">Status:</span>
									<span className="ml-2 font-medium capitalize">
										{progress.status.replace("_", " ")}
									</span>
								</div>
							</div>

							{/* Current File */}
							{progress.current_file && (
								<div>
									<span className="text-gray-600 text-sm">Current file:</span>
									<p className="font-mono text-sm bg-gray-100 p-2 rounded mt-1 break-all">
										{progress.current_file}
									</p>
								</div>
							)}

							{/* Error Message */}
							{progress.error_message && (
								<div className="bg-red-50 border border-red-200 rounded-lg p-3">
									<h5 className="text-sm font-medium text-red-800 mb-1">
										Error
									</h5>
									<p className="text-sm text-red-700">
										{progress.error_message}
									</p>
								</div>
							)}

							{/* Completed Message */}
							{progress.status === "completed" && (
								<div className="bg-green-50 border border-green-200 rounded-lg p-3">
									<h5 className="text-sm font-medium text-green-800 mb-1">
										✅ Download Complete
									</h5>
									<p className="text-sm text-green-700">
										Successfully downloaded and processed {progress.total_files}{" "}
										files.
										{progress.completed_at && (
											<span className="block mt-1">
												Completed at:{" "}
												{new Date(progress.completed_at).toLocaleString()}
											</span>
										)}
									</p>
								</div>
							)}
						</div>
					) : (
						<div className="text-center py-8">
							<FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
							<p className="text-gray-600">No download progress found</p>
							<p className="text-sm text-gray-500 mt-2">
								The download may have completed or not started yet.
							</p>
						</div>
					)}
				</div>

				{/* Footer */}
				<div className="flex justify-end p-6 border-t bg-gray-50">
					<button
						onClick={onClose}
						className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors">
						Close
					</button>
				</div>
			</div>
		</div>
	);
};

export default SftpProgressModal;
