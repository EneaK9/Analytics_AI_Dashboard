import * as React from "react";
import { styled } from "@mui/material/styles";
import Avatar from "@mui/material/Avatar";
import MuiDrawer, { drawerClasses } from "@mui/material/Drawer";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import SelectContent from "./SelectContent";
import MenuContent from "./MenuContent";
import CardAlert from "./CardAlert";
import OptionsMenu from "./OptionsMenu";

const drawerWidth = 240;

const Drawer = styled(MuiDrawer)({
	width: drawerWidth,
	flexShrink: 0,
	boxSizing: "border-box",
	mt: 10,
	[`& .${drawerClasses.paper}`]: {
		width: drawerWidth,
		boxSizing: "border-box",
	},
});

interface SideMenuProps {
	user?: {
		company_name: string;
		email: string;
		client_id: string;
	};
	onDashboardChange?: (dashboardType: string) => void;
	selectedSection?: string;
	onSectionChange?: (section: string) => void;
}

export default function SideMenu({
	user,
	onDashboardChange,
	selectedSection,
	onSectionChange,
}: SideMenuProps) {
	return (
		<Drawer
			variant="permanent"
			sx={{
				display: { xs: "none", md: "block" },
				[`& .${drawerClasses.paper}`]: {
					backgroundColor: "background.paper",
				},
			}}>
			<Box
				sx={{
					display: "flex",
					mt: "calc(var(--template-frame-height, 0px) + 4px)",
					p: 1.5,
				}}>
				<SelectContent user={user} onDashboardChange={onDashboardChange} />
			</Box>
			<Divider />
			<Box
				sx={{
					overflow: "auto",
					height: "100%",
					pb: 8,
				}}>
				<MenuContent
					selectedSection={selectedSection}
					onSectionChange={onSectionChange}
				/>
			</Box>
			<Stack
				direction="row"
				sx={{
					p: 2,
					gap: 1,
					alignItems: "center",
					minHeight: 80,
				}}>
				<Avatar
					sizes="small"
					alt={user?.company_name || "User"}
					src="/favicon.svg"
					sx={{ width: 36, height: 36, bgcolor: "transparent" }}
				/>
				<Box sx={{ mr: "auto", display: "flex", alignItems: "center" }}>
					<Typography
						variant="body2"
						sx={{ fontWeight: 500, lineHeight: "16px" }}>
						Shfa AI
					</Typography>
				</Box>
				{/* Options menu removed; logout is now available from header user menu */}
			</Stack>
		</Drawer>
	);
}
