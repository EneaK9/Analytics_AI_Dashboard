import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
	children: ReactNode;
	fallback?: ReactNode;
}

interface State {
	hasError: boolean;
	error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
	public state: State = {
		hasError: false,
	};

	public static getDerivedStateFromError(error: Error): State {
		return { hasError: true, error };
	}

	public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
		console.error("ErrorBoundary caught an error:", error, errorInfo);

		// Check if this is an authentication error
		if (
			error.message?.includes("Authentication failed") ||
			error.message?.includes("401") ||
			error.message?.includes("403")
		) {
			console.log(
				"🔒 Auth error caught by ErrorBoundary - letting axios interceptor handle logout"
			);
			// Don't handle auth errors here - let axios interceptor handle them
			return;
		}
	}

	public render() {
		if (this.state.hasError) {
			// Check if this is an auth error - if so, don't show error UI
			if (
				this.state.error?.message?.includes("Authentication failed") ||
				this.state.error?.message?.includes("401") ||
				this.state.error?.message?.includes("403")
			) {
				// Return null to hide the component during auth redirect
				return null;
			}

			return (
				this.props.fallback || (
					<div className="flex items-center justify-center min-h-[200px] p-4">
						<div className="text-center">
							<div className="text-red-500 text-lg font-medium mb-2">
								Something went wrong
							</div>
							<div className="text-gray-600 text-sm mb-4">
								{this.state.error?.message || "An unexpected error occurred"}
							</div>
							<button
								className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
								onClick={() => window.location.reload()}>
								Refresh Page
							</button>
						</div>
					</div>
				)
			);
		}

		return this.props.children;
	}
}

export default ErrorBoundary;
