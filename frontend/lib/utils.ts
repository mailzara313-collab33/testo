import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, subDays } from "date-fns";
import { tr } from "date-fns/locale";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, currency = "TRY"): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat("tr-TR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPct(value: number): string {
  return `%${value.toFixed(1)}`;
}

export function formatDate(date: Date | string): string {
  return format(new Date(date), "d MMM yyyy", { locale: tr });
}

export function formatDateRange(from: Date, to: Date): string {
  return `${format(from, "d MMM", { locale: tr })} – ${format(to, "d MMM yyyy", { locale: tr })}`;
}

export function getDateRange(preset: string): { from: Date; to: Date } {
  const to = new Date();
  switch (preset) {
    case "today":
      return { from: to, to };
    case "yesterday":
      return { from: subDays(to, 1), to: subDays(to, 1) };
    case "7d":
      return { from: subDays(to, 6), to };
    case "30d":
      return { from: subDays(to, 29), to };
    case "90d":
      return { from: subDays(to, 89), to };
    default:
      return { from: subDays(to, 29), to };
  }
}

export function toISODate(date: Date): string {
  return format(date, "yyyy-MM-dd");
}

export function changePctColor(pct: number): string {
  if (pct > 0) return "text-emerald-600";
  if (pct < 0) return "text-red-500";
  return "text-muted-foreground";
}

export function changePctIcon(pct: number): string {
  if (pct > 0) return "↑";
  if (pct < 0) return "↓";
  return "–";
}

export const CAMPAIGN_STATUS_LABELS: Record<string, string> = {
  ENABLED: "Aktif",
  PAUSED: "Duraklatıldı",
  REMOVED: "Kaldırıldı",
};

export const CAMPAIGN_TYPE_LABELS: Record<string, string> = {
  SEARCH: "Arama",
  DISPLAY: "Görüntülü",
  SHOPPING: "Alışveriş",
  PERFORMANCE_MAX: "Performance Max",
  VIDEO: "Video",
  DEMAND_GEN: "Demand Gen",
  APP: "Uygulama",
};
