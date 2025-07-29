import * as React from "react";
import { styled } from "@mui/material/styles";
import Avatar from "@mui/material/Avatar";
import Chip from "@mui/material/Chip";
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
				`🎨 Generating CUSTOM dashboard options for client ${user.client_id}`
			);

			// 🚀 NEW: Generate custom intelligent templates
			const customTemplatesResponse = await api.post(
				"/dashboard/generate-custom",
				{
					template_count: 3,
					force_regenerate: false,
					business_context_override: null,
				}
			);

			console.log(
				"🤖 Custom templates response:",
				customTemplatesResponse.data
			);

			if (
				customTemplatesResponse.data.success &&
				customTemplatesResponse.data.generated_templates
			) {
				// Create dashboard options from AI-generated custom templates
				const customTemplates = await generateCustomDashboardOptions(
					customTemplatesResponse.data.generated_templates,
					customTemplatesResponse.data.business_dna,
					user.company_name
				);
				setDashboardOptions(customTemplates);
			} else {
				// Fallback to old template system if custom generation fails
				console.warn("⚠️ Custom template generation failed, using fallback");
				const fallbackOptions = createFallbackDashboards(user.company_name);
				setDashboardOptions(fallbackOptions);
			}
			setLoading(false);
		} catch (error) {
			console.error("Failed to generate custom dashboard options:", error);
			// Create fallback options
			const fallbackOptions = createFallbackDashboards(user.company_name);
			setDashboardOptions(fallbackOptions);
			setLoading(false);
		}
	}, [user?.client_id, user?.company_name]);

	// 🚀 NEW: Generate dashboard options from AI-generated custom templates
	const generateCustomDashboardOptions = async (
		customTemplates: any[],
		businessDNA: any,
		companyName: string
	): Promise<DashboardOption[]> => {
		const templates: DashboardOption[] = [];

		// Main dashboard (always present - but now AI-enhanced)
		templates.push({
			id: "0",
			title: companyName || "Analytics Dashboard",
			subtitle: "AI-Enhanced Overview",
			icon: <DashboardIcon />,
			template_type: "main",
			color: "primary.main",
			isActive: true,
		});

		// Add AI-generated custom templates
		customTemplates.forEach((template, index) => {
			templates.push({
				id: (index + 1).toString(),
				title:
					template.smart_name?.primary_name || `Custom Template ${index + 1}`,
				subtitle: template.smart_name?.description || "AI-Generated Dashboard",
				icon: index === 0 ? <AssessmentIcon /> : <InsightsIcon />,
				template_type: `custom_${index + 1}`,
				color: index === 0 ? "success.main" : "info.main",
				isActive: false,
				// Store custom template data for later use
				customTemplateData: template,
			});
		});

		console.log(
			`🎨 Generated ${templates.length} dashboard options with AI intelligence`
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
				<MenuItem
					value=""
					sx={{ display: "flex", alignItems: "center", gap: 1 }}>
					<Avatar sx={{ width: 36, height: 36, bgcolor: "grey.300" }}>
						<DashboardIcon />
					</Avatar>
					<ListItemText
						primary="Loading..."
						secondary="Generating dashboards"
					/>
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
				<MenuItem
					key={option.id}
					value={option.id}
					selected={option.isActive}
					sx={{
						display: "flex",
						alignItems: "center",
						gap: 1,
						width: "100%",
						padding: 1,
					}}>
					<Avatar sx={{ width: 36, height: 36, bgcolor: option.color }}>
						{option.icon}
					</Avatar>
					<ListItemText primary={option.title} secondary={option.subtitle} />
					{option.isActive && (
						<Chip size="small" color="primary" label="Active" />
					)}
				</MenuItem>
			))}
		</Select>
	);
}
