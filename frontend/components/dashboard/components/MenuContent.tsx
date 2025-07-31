import * as React from "react";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import AnalyticsRoundedIcon from "@mui/icons-material/AnalyticsRounded";
import PeopleRoundedIcon from "@mui/icons-material/PeopleRounded";
import AssignmentRoundedIcon from "@mui/icons-material/AssignmentRounded";
import TableViewIcon from "@mui/icons-material/TableView";
import SettingsRoundedIcon from "@mui/icons-material/SettingsRounded";
import InfoRoundedIcon from "@mui/icons-material/InfoRounded";
import HelpRoundedIcon from "@mui/icons-material/HelpRounded";

interface MenuContentProps {
	selectedSection?: string;
	onSectionChange?: (section: string) => void;
}

const mainListItems = [
	{ text: "Home", icon: <HomeRoundedIcon />, id: "home" },
	// { text: "Analytics", icon: <AnalyticsRoundedIcon />, id: "analytics" },
	{ text: "Data Tables", icon: <TableViewIcon />, id: "data-tables" },
	// { text: "Clients", icon: <PeopleRoundedIcon />, id: "clients" },
	// { text: "Tasks", icon: <AssignmentRoundedIcon />, id: "tasks" },
];

const secondaryListItems = [
	{ text: "Settings", icon: <SettingsRoundedIcon />, id: "settings" },
	{ text: "About", icon: <InfoRoundedIcon />, id: "about" },
	{ text: "Feedback", icon: <HelpRoundedIcon />, id: "feedback" },
];

export default function MenuContent({
	selectedSection = "home",
	onSectionChange,
}: MenuContentProps) {
	return (
		<Stack sx={{ flexGrow: 1, p: 1, justifyContent: "space-between" }}>
			<List dense>
				{mainListItems.map((item, index) => (
					<ListItem key={index} disablePadding sx={{ display: "block" }}>
						<ListItemButton
							selected={selectedSection === item.id}
							onClick={() => onSectionChange?.(item.id)}>
							<ListItemIcon>{item.icon}</ListItemIcon>
							<ListItemText primary={item.text} />
						</ListItemButton>
					</ListItem>
				))}
			</List>
			<List dense>
				{secondaryListItems.map((item, index) => (
					<ListItem key={index} disablePadding sx={{ display: "block" }}>
						<ListItemButton
							selected={selectedSection === item.id}
							onClick={() => onSectionChange?.(item.id)}>
							<ListItemIcon>{item.icon}</ListItemIcon>
							<ListItemText primary={item.text} />
						</ListItemButton>
					</ListItem>
				))}
			</List>
		</Stack>
	);
}
