"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { subDays } from "date-fns";
import {
  DollarSign,
  MousePointerClick,
  ShoppingCart,
  Target,
  TrendingUp,
  Eye,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { KPICard } from "@/components/dashboard/kpi-card";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { SpendPieChart } from "@/components/dashboard/spend-pie";
import { HourlyHeatmap } from "@/components/dashboard/heatmap";
import { dashboardApi } from "@/lib/api";
import { formatCurrency, formatNumber, formatPct, toISODate } from "@/lib/utils";
import type { DashboardData } from "@/types";

const PRESETS = [
  { label: "Bugün", value: "today" },
  { label: "Son 7 Gün", value: "7d" },
  { label: "Son 30 Gün", value: "30d" },
  { label: "Son 90 Gün", value: "90d" },
];

function getPresetDates(p: string) {
  const to = new Date();
  switch (p) {
    case "today": return { from: to, to };
    case "7d": return { from: subDays(to, 6), to };
    case "30d": return { from: subDays(to, 29), to };
    case "90d": return { from: subDays(to, 89), to };
    default: return { from: subDays(to, 29), to };
  }
}

export default function DashboardPage() {
  const [preset, setPreset] = useState("30d");
  const [accountId, setAccountId] = useState<string>("");
  const { from, to } = getPresetDates(preset);

  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ["dashboard", accountId, preset],
    queryFn: () =>
      dashboardApi
        .get({
          account_id: accountId || undefined,
          date_from: toISODate(from),
          date_to: toISODate(to),
        })
        .then((r) => r.data),
  });

  return (
    <div>
      <Header
        title="Genel Bakış"
        subtitle="Tüm hesaplar"
        selectedAccount={accountId}
        onAccountChange={setAccountId}
      />

      <div className="p-6 space-y-6">
        {/* Date presets */}
        <div className="flex gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPreset(p.value)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                preset === p.value
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-border text-slate-600 hover:bg-slate-50"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-border p-5 h-28 animate-pulse" />
            ))}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
            Veri yüklenirken hata oluştu. Backend çalışıyor mu?
          </div>
        )}

        {data && (
          <>
            {/* KPI Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <KPICard
                title="Toplam Harcama"
                data={data.kpis.cost}
                format={formatCurrency}
                icon={DollarSign}
                iconColor="text-blue-600"
              />
              <KPICard
                title="Dönüşüm"
                data={data.kpis.conversions}
                format={(v) => formatNumber(v, 0)}
                icon={ShoppingCart}
                iconColor="text-emerald-600"
              />
              <KPICard
                title="ROAS"
                data={data.kpis.roas}
                format={(v) => `${v.toFixed(2)}x`}
                icon={TrendingUp}
                iconColor="text-purple-600"
              />
              <KPICard
                title="CPA"
                data={data.kpis.cpa}
                format={formatCurrency}
                icon={Target}
                iconColor="text-orange-600"
                invertTrend
              />
              <KPICard
                title="Tıklama"
                data={data.kpis.clicks}
                format={(v) => formatNumber(v, 0)}
                icon={MousePointerClick}
                iconColor="text-sky-600"
              />
              <KPICard
                title="Gösterim"
                data={data.kpis.impressions}
                format={(v) => formatNumber(v, 0)}
                icon={Eye}
                iconColor="text-indigo-600"
              />
              <KPICard
                title="CTR"
                data={data.kpis.ctr}
                format={(v) => `${v.toFixed(2)}%`}
                icon={TrendingUp}
                iconColor="text-teal-600"
              />
              <KPICard
                title="Ort. TBM"
                data={data.kpis.cpc}
                format={formatCurrency}
                icon={DollarSign}
                iconColor="text-rose-600"
                invertTrend
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <PerformanceChart data={data.time_series} />
              </div>
              <SpendPieChart data={data.spend_by_campaign} />
            </div>

            {/* Heatmap */}
            <HourlyHeatmap data={data.hourly_heatmap} />
          </>
        )}
      </div>
    </div>
  );
}
