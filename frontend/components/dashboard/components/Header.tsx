import * as React from "react";
import Stack from "@mui/material/Stack";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import AccountCircleRoundedIcon from "@mui/icons-material/AccountCircleRounded";
import CustomDatePicker, { DateRange, DateSelection } from "./CustomDatePicker";
import NavbarBreadcrumbs from "./NavbarBreadcrumbs";
import ColorModeIconDropdown from "../../shared-theme/ColorModeIconDropdown";
import { logout } from "../../../lib/auth";

import Search from "./Search";

interface HeaderProps {
    onDateRangeChange?: (dateRange: DateRange) => void;
    onSearch?: (query: string) => void;
}

export default function Header({ onDateRangeChange, onSearch }: HeaderProps) {
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleUserMenuClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => setAnchorEl(null);
    const handleLogout = () => {
        handleClose();
        logout();
    };
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
                <Search onSearch={onSearch} />
                <CustomDatePicker onDateRangeChange={onDateRangeChange} />
				{/* Theme toggle now takes the place of notifications */}
				<ColorModeIconDropdown />
				{/* User menu added in the former theme button position */}
				<IconButton size="small" onClick={handleUserMenuClick} aria-controls={open ? 'user-menu' : undefined} aria-haspopup="true" aria-expanded={open ? 'true' : undefined}>
					<AccountCircleRoundedIcon />
				</IconButton>
				<Menu id="user-menu" anchorEl={anchorEl} open={open} onClose={handleClose} onClick={handleClose} transformOrigin={{ horizontal: 'right', vertical: 'top' }} anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}>
					<MenuItem onClick={handleLogout}>Logout</MenuItem>
				</Menu>
			</Stack>
		</Stack>
	);
}
