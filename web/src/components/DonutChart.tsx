"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const DONUT_COLORS = [
  "var(--accent)",
  "var(--warning)",
  "var(--danger)",
  "var(--success)",
  "var(--muted)",
  "var(--text)",
];

export type DonutSlice = {
  name: string;
  value: number;
};

export function DonutChart({
  data,
  innerRadius = 50,
  outerRadius = 80,
  height = 200,
}: {
  data: DonutSlice[];
  innerRadius?: number;
  outerRadius?: number;
  height?: number;
}) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "var(--surface-overlay)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              fontSize: "0.85rem",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
