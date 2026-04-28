"use client";

import { cn } from "@/lib/utils";
import type { HeatmapCell } from "@/types";

const DAYS = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function getColor(value: number, max: number): string {
  const ratio = Math.min(value / max, 1);
  if (ratio < 0.25) return "bg-blue-50";
  if (ratio < 0.5) return "bg-blue-200";
  if (ratio < 0.75) return "bg-blue-400";
  return "bg-blue-600";
}

interface HeatmapProps {
  data: HeatmapCell[];
}

export function HourlyHeatmap({ data }: HeatmapProps) {
  const byKey: Record<string, number> = {};
  for (const cell of data) {
    byKey[`${cell.day}-${cell.hour}`] = cell.value;
  }
  const max = Math.max(...data.map((c) => c.value), 1);

  return (
    <div className="bg-white rounded-xl border border-border p-5">
      <h2 className="text-sm font-semibold text-slate-900 mb-4">
        Saatlik Performans Haritası (ROAS bazlı)
      </h2>
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Hour labels */}
          <div className="flex gap-0.5 ml-10 mb-1">
            {HOURS.map((h) => (
              <div
                key={h}
                className="w-7 text-center text-[10px] text-muted-foreground"
              >
                {h % 3 === 0 ? `${h}:00` : ""}
              </div>
            ))}
          </div>
          {/* Grid */}
          {DAYS.map((day, d) => (
            <div key={d} className="flex items-center gap-0.5 mb-0.5">
              <span className="w-9 text-xs text-muted-foreground text-right pr-2">{day}</span>
              {HOURS.map((h) => {
                const v = byKey[`${d}-${h}`] ?? 0;
                return (
                  <div
                    key={h}
                    title={`${day} ${h}:00 – ROAS: ${v.toFixed(2)}`}
                    className={cn("w-7 h-5 rounded-sm heatmap-cell", getColor(v, max))}
                  />
                );
              })}
            </div>
          ))}
          {/* Legend */}
          <div className="flex items-center gap-2 mt-3 ml-10">
            <span className="text-[10px] text-muted-foreground">Düşük</span>
            {["bg-blue-50", "bg-blue-200", "bg-blue-400", "bg-blue-600"].map((c) => (
              <div key={c} className={cn("w-5 h-3 rounded-sm", c)} />
            ))}
            <span className="text-[10px] text-muted-foreground">Yüksek</span>
          </div>
        </div>
      </div>
    </div>
  );
}
