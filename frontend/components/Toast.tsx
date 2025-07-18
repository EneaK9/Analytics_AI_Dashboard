import React, { useState, useEffect } from "react";
import { AlertCircle, CheckCircle, Info, X } from "lucide-react";

interface ToastProps {
	message: string;
	type: "success" | "error" | "info" | "warning";
	duration?: number;
	onClose?: () => void;
}

const Toast: React.FC<ToastProps> = ({
	message,
	type,
	duration = 5000,
	onClose,
}) => {
	const [isVisible, setIsVisible] = useState(true);

	useEffect(() => {
		if (duration > 0) {
			const timer = setTimeout(() => {
				setIsVisible(false);
				if (onClose) onClose();
			}, duration);

			return () => clearTimeout(timer);
		}
	}, [duration, onClose]);

	const handleClose = () => {
		setIsVisible(false);
		if (onClose) onClose();
	};

	if (!isVisible) return null;

	const getIcon = () => {
		switch (type) {
			case "success":
				return <CheckCircle className="h-5 w-5 text-green-500" />;
			case "error":
				return <AlertCircle className="h-5 w-5 text-red-500" />;
			case "warning":
				return <AlertCircle className="h-5 w-5 text-yellow-500" />;
			case "info":
			default:
				return <Info className="h-5 w-5 text-blue-500" />;
		}
	};

	const getBackgroundColor = () => {
		switch (type) {
			case "success":
				return "bg-green-50 border-green-200";
			case "error":
				return "bg-red-50 border-red-200";
			case "warning":
				return "bg-yellow-50 border-yellow-200";
			case "info":
			default:
				return "bg-blue-50 border-blue-200";
		}
	};

	return (
		<div
			className={`fixed top-4 right-4 z-50 max-w-md p-4 rounded-lg border ${getBackgroundColor()} shadow-lg animate-in slide-in-from-top-2`}>
			<div className="flex items-start space-x-3">
				{getIcon()}
				<div className="flex-1">
					<p className="text-sm font-medium text-gray-800">{message}</p>
				</div>
				<button
					onClick={handleClose}
					className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors">
					<X className="h-4 w-4" />
				</button>
			</div>
		</div>
	);
};

export default Toast;
