import { cn, changePctColor, changePctIcon } from "@/lib/utils";
import type { KPIData } from "@/types";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  data: KPIData;
  format: (v: number) => string;
  icon: LucideIcon;
  iconColor?: string;
  invertTrend?: boolean; // true for CPA: lower is better
}

export function KPICard({
  title,
  data,
  format,
  icon: Icon,
  iconColor = "text-blue-600",
  invertTrend = false,
}: KPICardProps) {
  const pct = data.change_pct;
  const isPositive = invertTrend ? pct < 0 : pct > 0;
  const trendColor = pct === 0
    ? "text-muted-foreground"
    : isPositive
    ? "text-emerald-600"
    : "text-red-500";

  return (
    <div className="bg-white rounded-xl border border-border p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <div className={cn("p-2 rounded-lg bg-slate-50", iconColor)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{format(data.value)}</p>
        <div className="flex items-center gap-1 mt-1">
          <span className={cn("text-xs font-medium", trendColor)}>
            {changePctIcon(invertTrend ? -pct : pct)} {Math.abs(pct)}%
          </span>
          <span className="text-xs text-muted-foreground">önceki dönem</span>
        </div>
      </div>
    </div>
  );
}
