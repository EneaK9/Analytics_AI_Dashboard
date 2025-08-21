import React, { Component, ErrorInfo, ReactNode } from "react";
import * as Sentry from "@sentry/nextjs";

interface Props {
	children: ReactNode;
	fallback?: ReactNode;
}

interface State {
	hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
	public state: State = {
		hasError: false,
	};

	public static getDerivedStateFromError(_: Error): State {
		// Update state so the next render will show the fallback UI.
		return { hasError: true };
	}

	public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
		console.error("Uncaught error:", error, errorInfo);

		// Send error to Sentry
		Sentry.withScope((scope) => {
			scope.setTag("component", "ErrorBoundary");
			scope.setLevel("error");
			scope.setContext("errorInfo", {
				componentStack: errorInfo.componentStack,
			});
			Sentry.captureException(error);
		});
	}

	public render() {
		if (this.state.hasError) {
			// You can render any custom fallback UI
			return (
				this.props.fallback || (
					<div className="flex items-center justify-center min-h-screen bg-gray-100">
						<div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md mx-auto">
							<h2 className="text-2xl font-bold text-red-600 mb-4">
								Oops! Something went wrong
							</h2>
							<p className="text-gray-600 mb-6">
								We're sorry for the inconvenience. Our team has been notified
								about this error.
							</p>
							<button
								className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
								onClick={() => this.setState({ hasError: false })}>
								Try again
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
