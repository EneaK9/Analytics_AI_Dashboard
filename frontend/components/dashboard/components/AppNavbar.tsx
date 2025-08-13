import * as React from "react";
import { styled } from "@mui/material/styles";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import MuiToolbar from "@mui/material/Toolbar";
import { tabsClasses } from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Avatar from "@mui/material/Avatar";
import MenuRoundedIcon from "@mui/icons-material/MenuRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";
import SideMenuMobile from "./SideMenuMobile";
import MenuButton from "./MenuButton";
import ColorModeIconDropdown from "../../shared-theme/ColorModeIconDropdown";

const Toolbar = styled(MuiToolbar)({
	width: "100%",
	padding: "12px",
	display: "flex",
	flexDirection: "column",
	alignItems: "start",
	justifyContent: "center",
	gap: "12px",
	flexShrink: 0,
	[`& ${tabsClasses.flexContainer}`]: {
		gap: "8px",
		p: "8px",
		pb: 0,
	},
});

interface AppNavbarProps {
	dashboardData?: {
		isAnalyzing: boolean;
		error: string | null;
	};
	user?: {
		company_name: string;
		email: string;
	};
	onRefreshAIData?: () => void;
	onLogout?: () => void;
}

export default function AppNavbar({
	dashboardData,
	user,
	onRefreshAIData,
	onLogout,
}: AppNavbarProps) {
	const [open, setOpen] = React.useState(false);

	const toggleDrawer = (newOpen: boolean) => () => {
		setOpen(newOpen);
	};

	return (
		<AppBar
			position="fixed"
			sx={{
				display: { xs: "auto", md: "none" },
				boxShadow: 0,
				bgcolor: "background.paper",
				backgroundImage: "none",
				borderBottom: "1px solid",
				borderColor: "divider",
				top: "var(--template-frame-height, 0px)",
			}}>
			<Toolbar variant="regular">
				<Stack
					direction="row"
					sx={{
						justifyContent: "space-between",
						alignItems: "center",
						flexGrow: 1,
						width: "100%",
					}}>
					<Stack direction="row" spacing={1} sx={{ justifyContent: "center" }}>
						<SideMenuMobile
							open={open}
							toggleDrawer={toggleDrawer}
							user={user}
						/>
						<MenuButton showBadge aria-label="Open menu">
							<MenuRoundedIcon />
						</MenuButton>
						<Box sx={{ display: { xs: "none", md: "block" } }}>
							<DashboardRoundedIcon />
						</Box>
					</Stack>

					{/* Control buttons for larger screens */}
					<Stack
						direction="row"
						spacing={2}
						sx={{ display: { xs: "none", md: "flex" }, alignItems: "center" }}>
						{/* AI Data Status */}
						<Chip
							icon={
								<Box
									sx={{
										width: 6,
										height: 6,
										bgcolor: dashboardData?.isAnalyzing
											? "warning.main"
											: "success.main",
										borderRadius: "50%",
									}}
								/>
							}
							label={
								dashboardData?.isAnalyzing ? "Loading AI Data" : "Live Data"
							}
							variant="outlined"
							size="small"
						/>

						{/* Refresh AI Data Button */}
						<Button
							onClick={onRefreshAIData}
							disabled={dashboardData?.isAnalyzing}
							variant="contained"
							size="small"
							startIcon={<RefreshRoundedIcon />}
							sx={{ minWidth: "auto" }}>
							{dashboardData?.isAnalyzing ? "Loading..." : "Refresh"}
						</Button>

						{/* User Info */}
						{user && (
							<Stack direction="row" spacing={1} alignItems="center">
								<Avatar
									sx={{
										width: 32,
										height: 32,
										bgcolor: "primary.main",
										fontSize: "0.75rem",
									}}>
									{user.company_name.charAt(0).toUpperCase()}
								</Avatar>
								<Typography
									variant="body2"
									sx={{ 
										display: { xs: "none", sm: "flex" },
										alignItems: "center"
									}}>
									{user.company_name}
								</Typography>
							</Stack>
						)}

						{/* Logout Button */}
						<Button
							onClick={onLogout}
							variant="outlined"
							size="small"
							startIcon={<LogoutRoundedIcon />}
							color="error">
							Logout
						</Button>
					</Stack>

					{/* Mobile menu and color mode for small screens */}
					<Stack
						direction="row"
						spacing={1}
						sx={{ display: { xs: "flex", md: "none" } }}>
						<ColorModeIconDropdown />
					</Stack>
				</Stack>
			</Toolbar>
		</AppBar>
	);
}

export function CustomIcon() {
	return (
		<Box
			sx={{
				width: "1.5rem",
				height: "1.5rem",
				bgcolor: "black",
				borderRadius: "999px",
				display: "flex",
				justifyContent: "center",
				alignItems: "center",
				alignSelf: "center",
				backgroundImage:
					"linear-gradient(135deg, hsl(210, 98%, 60%) 0%, hsl(210, 100%, 35%) 100%)",
				color: "hsla(210, 100%, 95%, 0.9)",
				border: "1px solid",
				borderColor: "hsl(210, 100%, 55%)",
				boxShadow: "inset 0 2px 5px rgba(255, 255, 255, 0.3)",
			}}>
			<DashboardRoundedIcon color="inherit" sx={{ fontSize: "1rem" }} />
		</Box>
	);
}
