import axios from "axios";

// Create axios instance
const api = axios.create({
	baseURL:
		process.env.NODE_ENV === "production"
			? "/api"
			: "http://localhost:8000/api",
	timeout: 30000,
});

// Flag to prevent multiple redirects
let isRedirecting = false;

// Request interceptor to add token to headers
api.interceptors.request.use(
	(config) => {
		// Check if we're on a superadmin page
		const isSupeadminPage =
			typeof window !== "undefined" &&
			window.location.pathname.startsWith("/superadmin");

		// Get appropriate token
		const token = isSupeadminPage
			? localStorage.getItem("superadmin_token")
			: localStorage.getItem("access_token");

		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		return config;
	},
	(error) => {
		return Promise.reject(error);
	}
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
	(response) => {
		return response;
	},
	async (error) => {
		const originalRequest = error.config;

		// Check if error is 401 (Unauthorized)
		if (
			error.response?.status === 401 &&
			!originalRequest._retry &&
			!isRedirecting
		) {
			originalRequest._retry = true;
			isRedirecting = true;

			// Determine if we're on a superadmin page
			const isSupeadminPage =
				typeof window !== "undefined" &&
				window.location.pathname.startsWith("/superadmin");

			if (isSupeadminPage) {
				// Clear superadmin token and redirect to superadmin login
				localStorage.removeItem("superadmin_token");

				// Show user-friendly message
				console.warn("🔐 Superadmin session expired. Redirecting to login...");

				// Show toast notification if possible
				if (typeof window !== "undefined") {
					// Create a temporary toast notification
					const toastElement = document.createElement("div");
					toastElement.className =
						"fixed top-4 right-4 z-50 max-w-md p-4 rounded-lg border bg-yellow-50 border-yellow-200 shadow-lg";
					toastElement.innerHTML = `
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">Session expired. Redirecting to login...</p>
              </div>
            </div>
          `;
					document.body.appendChild(toastElement);

					// Remove toast after 3 seconds
					setTimeout(() => {
						if (document.body.contains(toastElement)) {
							document.body.removeChild(toastElement);
						}
					}, 3000);
				}

				// Redirect to superadmin login after a short delay
				setTimeout(() => {
					if (typeof window !== "undefined") {
						window.location.href = "/superadmin/login";
					}
				}, 1500);
			} else {
				// Clear client token and redirect to client login
				localStorage.removeItem("access_token");

				// Show user-friendly message
				console.warn("🔐 Session expired. Redirecting to login...");

				// Show toast notification if possible
				if (typeof window !== "undefined") {
					// Create a temporary toast notification
					const toastElement = document.createElement("div");
					toastElement.className =
						"fixed top-4 right-4 z-50 max-w-md p-4 rounded-lg border bg-yellow-50 border-yellow-200 shadow-lg";
					toastElement.innerHTML = `
            <div class="flex items-start space-x-3">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">Session expired. Redirecting to login...</p>
              </div>
            </div>
          `;
					document.body.appendChild(toastElement);

					// Remove toast after 3 seconds
					setTimeout(() => {
						if (document.body.contains(toastElement)) {
							document.body.removeChild(toastElement);
						}
					}, 3000);
				}

				// Redirect to client login after a short delay
				setTimeout(() => {
					if (typeof window !== "undefined") {
						window.location.href = "/login";
					}
				}, 1500);
			}

			// Reset flag after a delay
			setTimeout(() => {
				isRedirecting = false;
			}, 2000);

			return Promise.reject(error);
		}

		return Promise.reject(error);
	}
);

export default api;
