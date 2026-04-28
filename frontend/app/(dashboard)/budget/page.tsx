"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { campaignsApi } from "@/lib/api";
import { formatCurrency, formatNumber, toISODate } from "@/lib/utils";
import { subDays } from "date-fns";
import { Wallet, TrendingUp, AlertTriangle } from "lucide-react";

export default function BudgetPage() {
  const [accountId, setAccountId] = useState("1234567890");

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ["budget-campaigns", accountId],
    queryFn: () =>
      campaignsApi
        .list({
          account_id: accountId,
          date_from: toISODate(subDays(new Date(), 29)),
          date_to: toISODate(new Date()),
          sort_by: "cost",
          sort_dir: "desc",
          page_size: 50,
        })
        .then((r) => r.data),
    enabled: !!accountId,
  });

  const totalSpend = campaigns.reduce((s: number, c: Record<string, number>) => s + c.cost, 0);
  const totalBudget = campaigns.reduce((s: number, c: Record<string, number>) => s + (c.daily_budget ?? 0) * 30, 0);
  const pacingPct = totalBudget ? (totalSpend / totalBudget) * 100 : 0;

  return (
    <div>
      <Header title="Bütçe Takibi" selectedAccount={accountId} onAccountChange={setAccountId} />
      <div className="p-6 space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-border p-5">
            <div className="flex items-center gap-2 mb-2">
              <Wallet className="h-4 w-4 text-blue-600" />
              <p className="text-sm font-medium text-muted-foreground">Toplam Harcama</p>
            </div>
            <p className="text-2xl font-bold">{formatCurrency(totalSpend)}</p>
          </div>
          <div className="bg-white rounded-xl border border-border p-5">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-emerald-600" />
              <p className="text-sm font-medium text-muted-foreground">Aylık Bütçe (tahmini)</p>
            </div>
            <p className="text-2xl font-bold">{formatCurrency(totalBudget)}</p>
          </div>
          <div className="bg-white rounded-xl border border-border p-5">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className={`h-4 w-4 ${pacingPct > 90 ? "text-red-500" : "text-amber-500"}`} />
              <p className="text-sm font-medium text-muted-foreground">Pacing</p>
            </div>
            <p className={`text-2xl font-bold ${pacingPct > 90 ? "text-red-600" : "text-slate-900"}`}>
              %{pacingPct.toFixed(1)}
            </p>
          </div>
        </div>

        {/* Campaign Pacing Table */}
        <div className="bg-white rounded-xl border border-border overflow-hidden">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-slate-900">Kampanya Bütçe Durumu</h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-slate-50">
                {["Kampanya", "Günlük Bütçe", "30g Harcama", "Tahmini Aylık", "Pacing", "Durum"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading
                ? Array.from({ length: 6 }).map((_, i) => (
                    <tr key={i}><td colSpan={6} className="px-4 py-3"><div className="h-4 bg-slate-100 rounded animate-pulse" /></td></tr>
                  ))
                : (campaigns as Record<string, unknown>[]).map((c) => {
                    const dailyBudget = Number(c.daily_budget ?? 0);
                    const monthlyBudget = dailyBudget * 30;
                    const pacing = monthlyBudget ? (Number(c.cost) / monthlyBudget) * 100 : 0;
                    const status = pacing > 95 ? { label: "Kritik", color: "bg-red-100 text-red-700" }
                      : pacing > 80 ? { label: "Dikkat", color: "bg-amber-100 text-amber-700" }
                      : { label: "Normal", color: "bg-emerald-100 text-emerald-700" };
                    return (
                      <tr key={String(c.campaign_id)} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-medium max-w-xs truncate">{String(c.campaign_name)}</td>
                        <td className="px-4 py-2.5">{formatCurrency(dailyBudget)}</td>
                        <td className="px-4 py-2.5">{formatCurrency(Number(c.cost))}</td>
                        <td className="px-4 py-2.5">{formatCurrency(monthlyBudget)}</td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-slate-100 rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${pacing > 95 ? "bg-red-500" : pacing > 80 ? "bg-amber-500" : "bg-emerald-500"}`}
                                style={{ width: `${Math.min(pacing, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground w-10">{pacing.toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-2.5">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            {status.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
