import * as React from "react";
import { styled } from "@mui/material/styles";
import Avatar from "@mui/material/Avatar";
import Chip from "@mui/material/Chip";
import MuiListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import MuiSelect from "@mui/material/Select";
import MuiMenuItem from "@mui/material/MenuItem";
import { SelectChangeEvent } from "@mui/material/Select";
import BarChartIcon from "@mui/icons-material/BarChart";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import InsightsIcon from "@mui/icons-material/Insights";
import AssessmentIcon from "@mui/icons-material/Assessment";
import api from "../../../lib/axios";

const Select = styled(MuiSelect)({
	border: "none",
	"&:before": {
		display: "none",
	},
	"&:after": {
		display: "none",
	},
	"& .MuiSelect-select": {
		display: "flex",
		alignItems: "center",
		gap: "8px",
		paddingLeft: 0,
	},
});

const ListItem = styled(MuiListItem)({
	padding: 0,
});

const MenuItem = styled(MuiMenuItem)({
	gap: "8px",
});

interface DashboardOption {
	id: string;
	title: string;
	subtitle: string;
	icon: React.ReactNode;
	template_type: string;
	color: string;
	isActive: boolean;
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
	const [selectedDashboard, setSelectedDashboard] = React.useState("0");
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

		try {
			console.log(
				`🎨 Generating dashboard options for client ${user.client_id}`
			);

			// Get available templates from backend
			const templatesResponse = await api.get("/dashboard/templates");
			console.log("📋 Templates response:", templatesResponse.data);

			const { available_templates, recommended_template, client_data_columns } =
				templatesResponse.data;

			// Generate dashboard options based on available templates and data
			const dashboardTemplates = await generateDashboardTemplatesFromBackend(
				available_templates,
				recommended_template,
				client_data_columns,
				user.company_name
			);

			setDashboardOptions(dashboardTemplates);
			setLoading(false);
		} catch (error) {
			console.error("Failed to generate dashboard options:", error);
			// Create fallback options
			const fallbackOptions = createFallbackDashboards(user.company_name);
			setDashboardOptions(fallbackOptions);
			setLoading(false);
		}
	}, [user?.client_id, user?.company_name]);

	// Generate dashboard templates from backend response
	const generateDashboardTemplatesFromBackend = async (
		availableTemplates: any,
		recommendedTemplate: string,
		dataColumns: string[],
		companyName: string
	): Promise<DashboardOption[]> => {
		const templates: DashboardOption[] = [];

		// Main dashboard (always present - original)
		templates.push({
			id: "0",
			title: companyName || "Analytics Dashboard",
			subtitle: "Main Overview",
			icon: <DashboardIcon />,
			template_type: "main",
			color: "primary.main",
			isActive: true,
		});

		// Template 1: Data Template (shows actual data)
		templates.push({
			id: "1",
			title: "Data Analytics",
			subtitle: "Raw Data & Tables",
			icon: <AssessmentIcon />,
			template_type: "sales",
			color: "success.main",
			isActive: false,
		});

		// Template 2: Charts Template (Material UI charts)
		templates.push({
			id: "2",
			title: "Visual Analytics",
			subtitle: "Charts & Insights",
			icon: <InsightsIcon />,
			template_type: "operations",
			color: "info.main",
			isActive: false,
		});

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
			{
				id: "1",
				title: "Business Intelligence",
				subtitle: "Key Metrics",
				icon: <TrendingUpIcon />,
				template_type: "business",
				color: "success.main",
				isActive: false,
			},
			{
				id: "2",
				title: "Performance Hub",
				subtitle: "Analytics Center",
				icon: <InsightsIcon />,
				template_type: "performance",
				color: "info.main",
				isActive: false,
			},
		];
	};

	// Load dashboard options on mount
	React.useEffect(() => {
		generateDashboardOptions();
	}, [generateDashboardOptions]);

	const handleChange = async (event: SelectChangeEvent) => {
		const newDashboardId = event.target.value as string;
		setSelectedDashboard(newDashboardId);

		// Update active state
		setDashboardOptions((prev) =>
			prev.map((option) => ({
				...option,
				isActive: option.id === newDashboardId,
			}))
		);

		// Notify parent component about dashboard change
		if (onDashboardChange) {
			const selectedOption = dashboardOptions.find(
				(opt) => opt.id === newDashboardId
			);
			if (selectedOption) {
				console.log(
					`🔄 Switching to dashboard: ${selectedOption.title} (${selectedOption.template_type})`
				);
				onDashboardChange(selectedOption.template_type);
			}
		}
	};

	if (loading) {
		return (
			<Select value="" displayEmpty disabled fullWidth>
				<MenuItem value="">
					<ListItem>
						<ListItemButton>
							<Avatar sx={{ width: 36, height: 36, bgcolor: "grey.300" }}>
								<DashboardIcon />
							</Avatar>
							<ListItemText
								primary="Loading..."
								secondary="Generating dashboards"
							/>
						</ListItemButton>
					</ListItem>
				</MenuItem>
			</Select>
		);
	}

	return (
		<Select
			labelId="dashboard-select"
			id="dashboard-simple-select"
			value={selectedDashboard}
			onChange={handleChange}
			displayEmpty
			inputProps={{ "aria-label": "Select dashboard" }}
			fullWidth>
			{dashboardOptions.map((option) => (
				<MenuItem key={option.id} value={option.id}>
					<ListItem>
						<ListItemButton selected={option.isActive}>
							<Avatar sx={{ width: 36, height: 36, bgcolor: option.color }}>
								{option.icon}
							</Avatar>
							<ListItemText
								primary={option.title}
								secondary={option.subtitle}
							/>
							{option.isActive && (
								<Chip size="small" color="primary" label="Active" />
							)}
						</ListItemButton>
					</ListItem>
				</MenuItem>
			))}
		</Select>
	);
}
