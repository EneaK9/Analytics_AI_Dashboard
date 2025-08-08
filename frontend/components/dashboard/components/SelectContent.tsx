import * as React from "react";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import ListItemText from "@mui/material/ListItemText";
import DashboardIcon from "@mui/icons-material/Dashboard";



interface DashboardOption {
	id: string;
	title: string;
	subtitle: string;
	icon: React.ReactNode;
	template_type: string;
	color: string;
	isActive: boolean;
	customTemplateData?: any; // For AI-generated custom templates
}

interface SelectContentProps {
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
	onDashboardChange?: (dashboardId: string) => void;
}

export default function SelectContent({
	user,
	onDashboardChange,
}: SelectContentProps) {
	const [dashboardOptions, setDashboardOptions] = React.useState<
		DashboardOption[]
	>([]);
	const [loading, setLoading] = React.useState(true);

	// Generate dashboard options based on client data and AI analysis
	const generateDashboardOptions = React.useCallback(async () => {
		if (!user?.client_id) {
			setLoading(false);
			return;
		}

		console.log(
			`🎨 Using STANDARD dashboard templates for client ${user.client_id}`
		);

		// Always use the standard templates (main, business, performance)
		const standardOptions = createFallbackDashboards(user.company_name);
		setDashboardOptions(standardOptions);
		setLoading(false);
	}, [user?.client_id, user?.company_name]);

	// 🚀 NEW: Generate dashboard options from AI-generated custom templates
	const generateCustomDashboardOptions = async (
		customTemplates: any[],
		businessDNA: any,
		companyName: string
	): Promise<DashboardOption[]> => {
		const templates: DashboardOption[] = [];

		// Main dashboard (only dashboard available)
		templates.push({
			id: "0",
			title: companyName || "Analytics Dashboard",
			subtitle: "Main Overview",
			icon: <DashboardIcon />,
			template_type: "main",
			color: "primary.main",
			isActive: true,
		});

		console.log(
			`🎨 Generated ${templates.length} dashboard option (main only)`
		);
		return templates;
	};

	// Create fallback dashboards when API fails
	const createFallbackDashboards = (companyName: string): DashboardOption[] => {
		return [
			{
				id: "0",
				title: companyName || "Analytics Dashboard",
				subtitle: "Main Overview",
				icon: <DashboardIcon />,
				template_type: "main",
				color: "primary.main",
				isActive: true,
			},
		];
	};

	// Load dashboard options on mount and notify parent of main dashboard
	React.useEffect(() => {
		generateDashboardOptions();
	}, [generateDashboardOptions]);

	// Notify parent component about the main dashboard when data loads
	React.useEffect(() => {
		if (!loading && dashboardOptions.length > 0 && onDashboardChange) {
			const mainDashboard = dashboardOptions[0];
			console.log(
				`🔄 Loading dashboard: ${mainDashboard.title} (${mainDashboard.template_type})`
			);
			onDashboardChange(mainDashboard.template_type);
		}
	}, [loading, dashboardOptions, onDashboardChange]);

	if (loading) {
		return (
			<Box sx={{ display: "flex", alignItems: "center", gap: 1, p: 1 }}>
				<Avatar sx={{ width: 36, height: 36, bgcolor: "grey.300" }}>
					<DashboardIcon />
				</Avatar>
				<ListItemText
					primary="Loading..."
					secondary="Generating dashboard"
				/>
			</Box>
		);
	}

	// Get the main dashboard option (there should only be one)
	const mainDashboard = dashboardOptions[0];

	if (!mainDashboard) {
		return null;
	}

	return (
		<Box sx={{ 
			display: "flex", 
			alignItems: "center", 
			gap: 1, 
			p: 1,
			width: "100%",
			minHeight: 64 
		}}>
			<Avatar sx={{ width: 36, height: 36, bgcolor: mainDashboard.color }}>
				{mainDashboard.icon}
			</Avatar>
			<ListItemText 
				primary={mainDashboard.title} 
				secondary={mainDashboard.subtitle}
				sx={{
					flex: 1,
					'& .MuiListItemText-primary': {
						whiteSpace: 'normal',
						wordWrap: 'break-word',
					},
					'& .MuiListItemText-secondary': {
						whiteSpace: 'normal',
						wordWrap: 'break-word',
					}
				}}
			/>
		</Box>
	);
}
