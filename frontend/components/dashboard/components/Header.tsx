import * as React from "react";
import Stack from "@mui/material/Stack";
import NotificationsRoundedIcon from "@mui/icons-material/NotificationsRounded";
import CustomDatePicker, { DateRange } from "./CustomDatePicker";
import NavbarBreadcrumbs from "./NavbarBreadcrumbs";
import MenuButton from "./MenuButton";
import ColorModeIconDropdown from "../../shared-theme/ColorModeIconDropdown";

import Search from "./Search";

interface HeaderProps {
	onDateRangeChange?: (dateRange: DateRange) => void;
}

export default function Header({ onDateRangeChange }: HeaderProps) {
	return (
		<Stack
			direction="row"
			sx={{
				display: { xs: "none", md: "flex" },
				width: "100%",
				alignItems: { xs: "flex-start", md: "center" },
				justifyContent: "space-between",
				maxWidth: { sm: "100%", md: "1700px" },
				pt: 1.5,
			}}
			spacing={2}>
			<NavbarBreadcrumbs />
			<Stack direction="row" sx={{ gap: 1 }}>
				<Search />
				<CustomDatePicker onDateRangeChange={onDateRangeChange} />
				<MenuButton showBadge aria-label="Open notifications">
					<NotificationsRoundedIcon />
				</MenuButton>
				<ColorModeIconDropdown />
			</Stack>
		</Stack>
	);
}
