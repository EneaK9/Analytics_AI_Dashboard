import React from "react";
import Link from "next/link";

interface DropdownItemProps {
	tag?: "a" | "button" | "link";
	href?: string;
	onClick?: () => void;
	onItemClick?: () => void;
	baseClassName?: string;
	className?: string;
	children: React.ReactNode;
}

export const DropdownItem: React.FC<DropdownItemProps> = ({
	tag = "button",
	href,
	onClick,
	onItemClick,
	baseClassName = "block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-gray-300",
	className = "",
	children,
}) => {
	const combinedClasses = `${baseClassName} ${className}`.trim();

	const handleClick = (event: React.MouseEvent) => {
		if (tag === "button") {
			event.preventDefault();
		}
		if (onClick) onClick();
		if (onItemClick) onItemClick();
	};

	if (tag === "link" && href) {
		return (
			<Link href={href} className={combinedClasses} onClick={handleClick}>
				{children}
			</Link>
		);
	}

	if (tag === "a" && href) {
		return (
			<a href={href} className={combinedClasses} onClick={handleClick}>
				{children}
			</a>
		);
	}

	return (
		<button onClick={handleClick} className={combinedClasses}>
			{children}
		</button>
	);
};
