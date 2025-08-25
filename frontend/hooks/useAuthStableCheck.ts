import { useState, useEffect } from "react";

/**
 * Hook to ensure auth is stable before making dashboard API calls
 * Prevents race conditions between login success and dashboard component mounting
 */
export const useAuthStableCheck = (user: any, delay: number = 1500) => {
	const [isAuthStable, setIsAuthStable] = useState(false);

	useEffect(() => {
		if (user?.client_id) {
			console.log(
				"🔒 Auth stable check: User detected, waiting for auth to settle..."
			);

			const timer = setTimeout(() => {
				console.log(
					"✅ Auth stable check: Auth is now stable, enabling API calls"
				);
				setIsAuthStable(true);
			}, delay);

			return () => {
				clearTimeout(timer);
				setIsAuthStable(false);
			};
		} else {
			setIsAuthStable(false);
		}
	}, [user?.client_id, delay]);

	return isAuthStable;
};

export default useAuthStableCheck;
