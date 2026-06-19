"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export type PipelineStageRow = {
  stage: string;
  label: string;
  count: number;
  value: number;
};

export function PipelineFunnel({
  data,
  metric = "count",
}: {
  data: PipelineStageRow[];
  metric?: "count" | "value";
}) {
  const chartData = data.map((d) => ({
    label: d.label,
    _value: metric === "count" ? d.count : d.value,
  }));

  const maxVal = Math.max(...chartData.map((d) => d._value), 1);

  return (
    <div style={{ width: "100%", height: 220 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "var(--muted)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={60}
          />
          <YAxis hide domain={[0, maxVal]} />
          <Tooltip
            contentStyle={{
              background: "var(--surface-overlay)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              fontSize: "0.85rem",
            }}
          />
          <Bar dataKey="_value" fill="var(--accent)" radius={[4, 4, 0, 0]} maxBarSize={48} name={metric === "count" ? "Prospects" : "Value (USD)"} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
