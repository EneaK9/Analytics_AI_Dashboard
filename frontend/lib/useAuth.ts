import { useState, useEffect } from "react";
import {
	isAuthenticated,
	logout,
	getCurrentToken,
	isSuperadminRoute,
} from "./auth";

interface UseAuthReturn {
	isLoggedIn: boolean;
	userType: "client" | "superadmin" | null;
	token: string | null;
	logout: () => void;
	checkAuth: () => void;
}

/**
 * Hook for managing authentication state
 * Automatically handles session expiration and provides logout functionality
 */
export const useAuth = (): UseAuthReturn => {
	const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
	const [userType, setUserType] = useState<"client" | "superadmin" | null>(
		null
	);
	const [token, setToken] = useState<string | null>(null);

	const checkAuth = () => {
		const currentToken = getCurrentToken();
		const authenticated = isAuthenticated();
		const currentUserType = isSuperadminRoute() ? "superadmin" : "client";

		setIsLoggedIn(authenticated);
		setToken(currentToken);
		setUserType(authenticated ? currentUserType : null);
	};

	useEffect(() => {
		// Check auth status on mount
		checkAuth();

		// Listen for storage changes (useful for multi-tab scenarios)
		const handleStorageChange = (e: StorageEvent) => {
			if (e.key === "access_token" || e.key === "superadmin_token") {
				checkAuth();
			}
		};

		window.addEventListener("storage", handleStorageChange);

		return () => {
			window.removeEventListener("storage", handleStorageChange);
		};
	}, []);

	return {
		isLoggedIn,
		userType,
		token,
		logout,
		checkAuth,
	};
};
