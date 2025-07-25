import * as React from "react";
import { PieChart } from "@mui/x-charts/PieChart";
import { useDrawingArea } from "@mui/x-charts/hooks";
import { styled } from "@mui/material/styles";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import LinearProgress, {
	linearProgressClasses,
} from "@mui/material/LinearProgress";

import {
	IndiaFlag,
	UsaFlag,
	BrazilFlag,
	GlobeFlag,
} from "../internals/components/CustomIcons";

// Default colors for the chart
const defaultColors = [
	"hsl(220, 20%, 65%)",
	"hsl(220, 20%, 42%)",
	"hsl(220, 20%, 35%)",
	"hsl(220, 20%, 25%)",
	"hsl(220, 20%, 15%)",
	"hsl(220, 20%, 10%)",
];

// Default flag mapping (fallback to GlobeFlag if not found)
const flagMap: { [key: string]: React.ReactElement } = {
	India: <IndiaFlag />,
	USA: <UsaFlag />,
	Brazil: <BrazilFlag />,
	Other: <GlobeFlag />,
};

interface DataItem {
	label: string;
	value: number;
}

interface ChartUserByCountryProps {
	title?: string;
	data?: DataItem[];
	showTotal?: boolean;
	totalLabel?: string;
	height?: number;
	width?: number;
}

interface StyledTextProps {
	variant: "primary" | "secondary";
}

const StyledText = styled("text", {
	shouldForwardProp: (prop) => prop !== "variant",
})<StyledTextProps>(({ theme }) => ({
	textAnchor: "middle",
	dominantBaseline: "central",
	fill: (theme.vars || theme).palette.text.secondary,
	variants: [
		{
			props: {
				variant: "primary",
			},
			style: {
				fontSize: theme.typography.h5.fontSize,
			},
		},
		{
			props: ({ variant }) => variant !== "primary",
			style: {
				fontSize: theme.typography.body2.fontSize,
			},
		},
		{
			props: {
				variant: "primary",
			},
			style: {
				fontWeight: theme.typography.h5.fontWeight,
			},
		},
		{
			props: ({ variant }) => variant !== "primary",
			style: {
				fontWeight: theme.typography.body2.fontWeight,
			},
		},
	],
}));

interface PieCenterLabelProps {
	primaryText: string;
	secondaryText: string;
}

function PieCenterLabel({ primaryText, secondaryText }: PieCenterLabelProps) {
	const { width, height, left, top } = useDrawingArea();
	const primaryY = top + height / 2 - 10;
	const secondaryY = primaryY + 24;

	return (
		<React.Fragment>
			<StyledText variant="primary" x={left + width / 2} y={primaryY}>
				{primaryText}
			</StyledText>
			<StyledText variant="secondary" x={left + width / 2} y={secondaryY}>
				{secondaryText}
			</StyledText>
		</React.Fragment>
	);
}

export default function ChartUserByCountry({
	title = "Users by country",
	data,
	showTotal = true,
	totalLabel = "Total",
	height = 260,
	width = 260,
}: ChartUserByCountryProps) {
	// Use provided data or fall back to defaults
	const inputData = data || [
		{ label: "India", value: 50000 },
		{ label: "USA", value: 35000 },
		{ label: "Brazil", value: 10000 },
		{ label: "Other", value: 5000 },
	];

	// Calculate total and percentages
	const total = inputData.reduce((sum, item) => sum + item.value, 0);

	// Format total for display
	const formatNumber = (num: number): string => {
		if (num >= 1000000) {
			return `${(num / 1000000).toFixed(1)}M`;
		} else if (num >= 1000) {
			return `${(num / 1000).toFixed(1)}K`;
		}
		return num.toString();
	};

	// Prepare chart data with colors
	const chartData = inputData.map((item, index) => ({
		...item,
		color: defaultColors[index % defaultColors.length],
	}));

	// Prepare legend data with percentages
	const legendData = inputData.map((item, index) => ({
		name: item.label,
		value: item.value,
		percentage: Math.round((item.value / total) * 100),
		flag: flagMap[item.label] || <GlobeFlag />,
		color: defaultColors[index % defaultColors.length],
	}));

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
					{title}
				</Typography>
				<Box sx={{ display: "flex", alignItems: "center" }}>
					<PieChart
						colors={chartData.map((item) => item.color)}
						margin={{
							left: 80,
							right: 80,
							top: 80,
							bottom: 80,
						}}
						series={[
							{
								data: chartData,
								innerRadius: 75,
								outerRadius: 100,
								paddingAngle: 0,
								highlightScope: { fade: "global", highlight: "item" },
							},
						]}
						height={height}
						width={width}
						hideLegend>
						{showTotal && (
							<PieCenterLabel
								primaryText={formatNumber(total)}
								secondaryText={totalLabel}
							/>
						)}
					</PieChart>
				</Box>
				{legendData.map((item, index) => (
					<Stack
						key={index}
						direction="row"
						sx={{ alignItems: "center", gap: 2, pb: 2 }}>
						{item.flag}
						<Stack sx={{ gap: 1, flexGrow: 1 }}>
							<Stack
								direction="row"
								sx={{
									justifyContent: "space-between",
									alignItems: "center",
									gap: 2,
								}}>
								<Typography variant="body2" sx={{ fontWeight: "500" }}>
									{item.name}
								</Typography>
								<Typography variant="body2" sx={{ color: "text.secondary" }}>
									{item.percentage}%
								</Typography>
							</Stack>
							<LinearProgress
								variant="determinate"
								aria-label={`${item.name} percentage`}
								value={item.percentage}
								sx={{
									[`& .${linearProgressClasses.bar}`]: {
										backgroundColor: item.color,
									},
								}}
							/>
						</Stack>
					</Stack>
				))}
			</CardContent>
		</Card>
	);
}
