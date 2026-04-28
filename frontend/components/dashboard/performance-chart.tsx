"use client";

import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";
import { tr } from "date-fns/locale";
import type { TimeSeriesPoint } from "@/types";
import { formatCurrency, formatNumber } from "@/lib/utils";

interface PerformanceChartProps {
  data: TimeSeriesPoint[];
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  const formatted = data.map((p) => ({
    ...p,
    dateLabel: format(parseISO(p.date), "d MMM", { locale: tr }),
  }));

  return (
    <div className="bg-white rounded-xl border border-border p-5">
      <h2 className="text-sm font-semibold text-slate-900 mb-4">Harcama ve Dönüşüm Trendi</h2>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={formatted} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="dateLabel"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickLine={false}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `₺${(v / 1000).toFixed(0)}k`}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
            formatter={(value: number, name: string) => {
              if (name === "Harcama") return [formatCurrency(value), name];
              if (name === "Dönüşüm") return [formatNumber(value, 1), name];
              return [value, name];
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar
            yAxisId="left"
            dataKey="cost"
            name="Harcama"
            fill="#3b82f6"
            opacity={0.8}
            radius={[3, 3, 0, 0]}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="conversions"
            name="Dönüşüm"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
