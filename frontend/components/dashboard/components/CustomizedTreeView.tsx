import * as React from "react";
import clsx from "clsx";
import { animated, useSpring } from "@react-spring/web";
import { TransitionProps } from "@mui/material/transitions";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Collapse from "@mui/material/Collapse";
import Typography from "@mui/material/Typography";
import { RichTreeView } from "@mui/x-tree-view/RichTreeView";
import {
	useTreeItem,
	UseTreeItemParameters,
} from "@mui/x-tree-view/useTreeItem";
import {
	TreeItemContent,
	TreeItemIconContainer,
	TreeItemLabel,
	TreeItemRoot,
} from "@mui/x-tree-view/TreeItem";
import { TreeItemIcon } from "@mui/x-tree-view/TreeItemIcon";
import { TreeItemProvider } from "@mui/x-tree-view/TreeItemProvider";
import { TreeViewBaseItem } from "@mui/x-tree-view/models";
import { useTheme } from "@mui/material/styles";

type Color = "blue" | "green";

type ExtendedTreeItemProps = {
	color?: Color;
	id: string;
	label: string;
};

interface CustomizedTreeViewProps {
	clientData?: any[];
	dataColumns?: string[];
}

export default function CustomizedTreeView({
	clientData = [],
	dataColumns = [],
}: CustomizedTreeViewProps) {
	const theme = useTheme();

	// Generate tree items from real data
	const generateTreeItems = (): TreeViewBaseItem<ExtendedTreeItemProps>[] => {
		if (!clientData || clientData.length === 0 || !dataColumns.length) {
			return [
				{
					id: "1",
					label: "No Data Available",
					color: "blue",
				},
			];
		}

		const items: TreeViewBaseItem<ExtendedTreeItemProps>[] = [];

		// Create main data categories
		items.push({
			id: "1",
			label: `Data Overview (${clientData.length} records)`,
			children: [
				{
					id: "1.1",
					label: `Columns (${dataColumns.length})`,
					color: "green",
					children: dataColumns.slice(0, 6).map((column, index) => ({
						id: `1.1.${index + 1}`,
						label: column,
						color: "blue" as Color,
					})),
				},
				{
					id: "1.2",
					label: "Sample Records",
					color: "green",
					children: clientData.slice(0, 3).map((record, index) => ({
						id: `1.2.${index + 1}`,
						label: `Record ${index + 1}`,
						color: "blue" as Color,
					})),
				},
			],
		});

		// Add data insights
		items.push({
			id: "2",
			label: "Data Insights",
			children: [
				{
					id: "2.1",
					label: `Total Records: ${clientData.length}`,
					color: "green",
				},
				{
					id: "2.2",
					label: `Unique Columns: ${dataColumns.length}`,
					color: "green",
				},
				{
					id: "2.3",
					label: "Data Types",
					color: "green",
					children: dataColumns.slice(0, 4).map((column, index) => {
						const sampleValue = clientData[0]?.[column];
						const dataType = typeof sampleValue;
						return {
							id: `2.3.${index + 1}`,
							label: `${column}: ${dataType}`,
							color: "blue" as Color,
						};
					}),
				},
			],
		});

		return items;
	};

	const ITEMS = generateTreeItems();

	function DotIcon({ color }: { color: string }) {
		return (
			<Box sx={{ marginRight: 1, display: "flex", alignItems: "center" }}>
				<svg width={6} height={6}>
					<circle cx={3} cy={3} r={3} fill={color} />
				</svg>
			</Box>
		);
	}

	const AnimatedCollapse = animated(Collapse);

	function TransitionComponent(props: TransitionProps) {
		const style = useSpring({
			to: {
				opacity: props.in ? 1 : 0,
				transform: `translate3d(0,${props.in ? 0 : 20}px,0)`,
			},
		});

		return <AnimatedCollapse style={style} {...props} />;
	}

	interface CustomLabelProps {
		children: React.ReactNode;
		color?: Color;
		expandable?: boolean;
	}

	function CustomLabel({
		color,
		expandable,
		children,
		...other
	}: CustomLabelProps) {
		const theme = useTheme();
		const colors = {
			blue: (theme.vars || theme).palette.primary.main,
			green: (theme.vars || theme).palette.success.main,
		};

		const iconColor = color ? colors[color] : null;
		return (
			<TreeItemLabel {...other} sx={{ display: "flex", alignItems: "center" }}>
				{iconColor && <DotIcon color={iconColor} />}
				<Typography
					className="labelText"
					variant="body2"
					sx={{ color: "text.primary" }}>
					{children}
				</Typography>
			</TreeItemLabel>
		);
	}

	interface CustomTreeItemProps
		extends Omit<UseTreeItemParameters, "rootRef">,
			Omit<React.HTMLAttributes<HTMLLIElement>, "onFocus"> {}

	const CustomTreeItem = React.forwardRef(function CustomTreeItem(
		props: CustomTreeItemProps,
		ref: React.Ref<HTMLLIElement>
	) {
		const { id, itemId, label, disabled, children, ...other } = props;

		const {
			getRootProps,
			getContentProps,
			getIconContainerProps,
			getLabelProps,
			getGroupTransitionProps,
			status,
			publicAPI,
		} = useTreeItem({ id, itemId, children, label, disabled, rootRef: ref });

		const item = publicAPI.getItem(itemId);
		const color = item?.color;
		return (
			<TreeItemProvider id={id} itemId={itemId}>
				<TreeItemRoot {...getRootProps(other)}>
					<TreeItemContent
						{...getContentProps({
							className: clsx("content", {
								expanded: status.expanded,
								selected: status.selected,
								focused: status.focused,
								disabled: status.disabled,
							}),
						})}>
						{status.expandable && (
							<TreeItemIconContainer {...getIconContainerProps()}>
								<TreeItemIcon status={status} />
							</TreeItemIconContainer>
						)}

						<CustomLabel {...getLabelProps({ color })} />
					</TreeItemContent>
					{children && (
						<TransitionComponent
							{...getGroupTransitionProps({ className: "groupTransition" })}
						/>
					)}
				</TreeItemRoot>
			</TreeItemProvider>
		);
	});

	return (
		<Card
			variant="outlined"
			sx={{
				display: "flex",
				flexDirection: "column",
				gap: "8px",
				flexGrow: 1,
			}}>
			<CardContent>
				<Typography component="h2" variant="subtitle2">
					Data Structure
				</Typography>
				<RichTreeView
					items={ITEMS}
					aria-label="client-data-structure"
					multiSelect
					defaultExpandedItems={["1", "1.1"]}
					defaultSelectedItems={["1.1", "1.1.1"]}
					sx={{
						m: "0 -8px",
						pb: "8px",
						height: "fit-content",
						flexGrow: 1,
						overflowY: "auto",
					}}
					slots={{ item: CustomTreeItem }}
				/>
			</CardContent>
		</Card>
	);
}
