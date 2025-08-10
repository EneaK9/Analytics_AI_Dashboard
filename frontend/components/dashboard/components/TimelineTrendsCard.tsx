import * as React from "react";
import Card from "@mui/material/Card";
import CardHeader from "@mui/material/CardHeader";
import CardContent from "@mui/material/CardContent";
import { LineChart } from "@mui/x-charts/LineChart";

type TimelineItem = {
  date: string;
  llm_analysis?: {
    kpis?: Array<{ display_name?: string; name?: string; value?: number | string }>;
  };
  total_records?: number;
};

interface TimelineTrendsCardProps {
  timeline: TimelineItem[];
  maxSeries?: number;
  title?: string;
  subtitle?: string;
}

export default function TimelineTrendsCard({
  timeline,
  maxSeries = 5,
  title = "Timeline Trends",
  subtitle = "Daily KPIs over selected range",
}: TimelineTrendsCardProps) {
  const { categories, series } = React.useMemo(() => {
    const dates: string[] = [];
    const kpiSeriesMap: Record<string, number[]> = {};

    for (const dayEntry of timeline || []) {
      const date = dayEntry.date;
      const analysis = dayEntry.llm_analysis || {};
      dates.push(date);
      if (analysis.kpis && Array.isArray(analysis.kpis)) {
        for (const kpi of analysis.kpis) {
          const key = kpi.display_name || (kpi as any).name || "KPI";
          const raw = (kpi as any).value;
          const num = typeof raw === "number" ? raw : parseFloat(String(raw ?? 0));
          if (!kpiSeriesMap[key]) kpiSeriesMap[key] = [];
          kpiSeriesMap[key].push(isNaN(num) ? 0 : num);
        }
      }
    }

    // Clamp series to a reasonable number for readability
    const allSeries = Object.entries(kpiSeriesMap).map(([name, data]) => ({ name, data }));
    const limited = allSeries.slice(0, Math.max(1, maxSeries));
    return { categories: dates, series: limited };
  }, [timeline, maxSeries]);

  if (!timeline || timeline.length === 0 || series.length === 0) return null;

  return (
    <Card sx={{ overflowX: 'auto' }}>
      <CardHeader title={title} subheader={subtitle} />
      <CardContent>
        <LineChart
          xAxis={[{ scaleType: "point", data: categories }]}
          series={series.map((s) => ({ data: s.data, label: s.name }))}
          height={360}
          margin={{ left: 60, right: 20, top: 20, bottom: 40 }}
          sx={{
            width: '100%',
            minWidth: Math.max(600, categories.length * 80),
            '& .MuiChartsLegend-root': { mb: 1 },
          }}
        />
      </CardContent>
    </Card>
  );
}


