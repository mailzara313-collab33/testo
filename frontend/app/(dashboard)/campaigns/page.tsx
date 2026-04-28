"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { subDays } from "date-fns";
import {
  Pause,
  Play,
  DollarSign,
  ChevronUp,
  ChevronDown,
  Filter,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { campaignsApi } from "@/lib/api";
import {
  formatCurrency,
  formatNumber,
  formatPct,
  toISODate,
  CAMPAIGN_STATUS_LABELS,
  CAMPAIGN_TYPE_LABELS,
  cn,
} from "@/lib/utils";
import type { Campaign } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  ENABLED: "bg-emerald-100 text-emerald-700",
  PAUSED: "bg-amber-100 text-amber-700",
  REMOVED: "bg-slate-100 text-slate-500",
};

interface ConfirmModal {
  open: boolean;
  campaign: Campaign | null;
  action: "pause" | "enable" | null;
  newBudget?: number;
}

export default function CampaignsPage() {
  const [accountId, setAccountId] = useState("1234567890");
  const [sortBy, setSortBy] = useState("cost");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [confirm, setConfirm] = useState<ConfirmModal>({
    open: false,
    campaign: null,
    action: null,
  });
  const [budgetModal, setBudgetModal] = useState<{ open: boolean; campaign: Campaign | null }>({
    open: false,
    campaign: null,
  });
  const [newBudget, setNewBudget] = useState("");
  const [budgetReason, setBudgetReason] = useState("");

  const qc = useQueryClient();

  const { data: campaigns = [], isLoading } = useQuery<Campaign[]>({
    queryKey: ["campaigns", accountId, sortBy, sortDir, statusFilter],
    queryFn: () =>
      campaignsApi
        .list({
          account_id: accountId,
          date_from: toISODate(subDays(new Date(), 29)),
          date_to: toISODate(new Date()),
          status: statusFilter || undefined,
          sort_by: sortBy,
          sort_dir: sortDir,
        })
        .then((r) => r.data),
    enabled: !!accountId,
  });

  const actionMutation = useMutation({
    mutationFn: ({ campaign, action }: { campaign: Campaign; action: string }) =>
      campaignsApi.action(campaign.campaign_id, accountId, action),
    onSuccess: (_, vars) => {
      toast.success(`Kampanya ${vars.action === "pause" ? "duraklatıldı" : "aktifleştirildi"}`);
      qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: () => toast.error("İşlem başarısız"),
  });

  const budgetMutation = useMutation({
    mutationFn: ({ campaign, budget }: { campaign: Campaign; budget: number }) =>
      campaignsApi.updateBudget(campaign.campaign_id, accountId, budget, budgetReason),
    onSuccess: () => {
      toast.success("Bütçe güncellendi");
      setBudgetModal({ open: false, campaign: null });
      setNewBudget("");
      setBudgetReason("");
      qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: () => toast.error("Bütçe güncellenemedi"),
  });

  function handleSort(col: string) {
    if (sortBy === col) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(col);
      setSortDir("desc");
    }
  }

  function SortIcon({ col }: { col: string }) {
    if (sortBy !== col) return <ChevronUp className="h-3 w-3 opacity-30" />;
    return sortDir === "desc" ? (
      <ChevronDown className="h-3 w-3" />
    ) : (
      <ChevronUp className="h-3 w-3" />
    );
  }

  return (
    <div>
      <Header
        title="Kampanyalar"
        subtitle="Son 30 gün"
        selectedAccount={accountId}
        onAccountChange={setAccountId}
      />

      <div className="p-6">
        {/* Filters */}
        <div className="flex items-center gap-3 mb-4">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-input rounded-lg px-3 py-1.5 bg-white"
          >
            <option value="">Tüm Durumlar</option>
            <option value="ENABLED">Aktif</option>
            <option value="PAUSED">Duraklatıldı</option>
          </select>
          <span className="ml-auto text-sm text-muted-foreground">
            {campaigns.length} kampanya
          </span>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-slate-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Kampanya</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Durum</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Tip</th>
                  {[
                    { key: "cost", label: "Harcama" },
                    { key: "impressions", label: "Gösterim" },
                    { key: "clicks", label: "Tıklama" },
                    { key: "ctr", label: "CTR" },
                    { key: "conversions", label: "Dönüşüm" },
                    { key: "roas", label: "ROAS" },
                    { key: "cpa", label: "CPA" },
                  ].map((col) => (
                    <th
                      key={col.key}
                      className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground cursor-pointer hover:text-slate-900 select-none"
                      onClick={() => handleSort(col.key)}
                    >
                      <span className="flex items-center justify-end gap-1">
                        {col.label}
                        <SortIcon col={col.key} />
                      </span>
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground">İşlem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {isLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 11 }).map((_, j) => (
                          <td key={j} className="px-4 py-3">
                            <div className="h-4 bg-slate-100 rounded animate-pulse" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : campaigns.map((c) => (
                      <tr key={c.campaign_id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-slate-900 max-w-xs truncate">
                          {c.campaign_name}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-full text-xs font-medium",
                              STATUS_COLORS[c.status] ?? "bg-slate-100 text-slate-600"
                            )}
                          >
                            {CAMPAIGN_STATUS_LABELS[c.status] ?? c.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">
                          {CAMPAIGN_TYPE_LABELS[c.campaign_type] ?? c.campaign_type}
                        </td>
                        <td className="px-4 py-3 text-right font-medium">{formatCurrency(c.cost)}</td>
                        <td className="px-4 py-3 text-right text-muted-foreground">{formatNumber(c.impressions)}</td>
                        <td className="px-4 py-3 text-right text-muted-foreground">{formatNumber(c.clicks)}</td>
                        <td className="px-4 py-3 text-right text-muted-foreground">{c.ctr}%</td>
                        <td className="px-4 py-3 text-right text-muted-foreground">{formatNumber(c.conversions, 1)}</td>
                        <td className={cn(
                          "px-4 py-3 text-right font-medium",
                          c.roas >= 3 ? "text-emerald-600" : c.roas >= 1 ? "text-amber-600" : "text-red-500"
                        )}>
                          {c.roas.toFixed(2)}x
                        </td>
                        <td className="px-4 py-3 text-right text-muted-foreground">{formatCurrency(c.cpa)}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {c.status === "ENABLED" ? (
                              <button
                                onClick={() => setConfirm({ open: true, campaign: c, action: "pause" })}
                                className="p-1.5 rounded-lg hover:bg-amber-50 text-amber-600 transition-colors"
                                title="Duraklat"
                              >
                                <Pause className="h-3.5 w-3.5" />
                              </button>
                            ) : (
                              <button
                                onClick={() => setConfirm({ open: true, campaign: c, action: "enable" })}
                                className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600 transition-colors"
                                title="Başlat"
                              >
                                <Play className="h-3.5 w-3.5" />
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setBudgetModal({ open: true, campaign: c });
                                setNewBudget(c.daily_budget?.toFixed(0) ?? "");
                              }}
                              className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-600 transition-colors"
                              title="Bütçe Düzenle"
                            >
                              <DollarSign className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Confirm Action Modal */}
      {confirm.open && confirm.campaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm mx-4">
            <h3 className="font-semibold text-slate-900 mb-2">
              {confirm.action === "pause" ? "Kampanyayı Duraklat" : "Kampanyayı Başlat"}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              <strong>{confirm.campaign.campaign_name}</strong> kampanyasını{" "}
              {confirm.action === "pause" ? "duraklatmak" : "başlatmak"} istediğinize emin misiniz?
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setConfirm({ open: false, campaign: null, action: null })}
                className="px-4 py-2 text-sm rounded-lg border border-border hover:bg-slate-50"
              >
                İptal
              </button>
              <button
                disabled={actionMutation.isPending}
                onClick={() => {
                  if (confirm.campaign && confirm.action) {
                    actionMutation.mutate({ campaign: confirm.campaign, action: confirm.action });
                    setConfirm({ open: false, campaign: null, action: null });
                  }
                }}
                className={cn(
                  "px-4 py-2 text-sm rounded-lg font-medium text-white flex items-center gap-2",
                  confirm.action === "pause"
                    ? "bg-amber-600 hover:bg-amber-700"
                    : "bg-emerald-600 hover:bg-emerald-700"
                )}
              >
                {actionMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Onayla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Budget Modal */}
      {budgetModal.open && budgetModal.campaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm mx-4">
            <h3 className="font-semibold text-slate-900 mb-1">Günlük Bütçe Güncelle</h3>
            <p className="text-sm text-muted-foreground mb-4">{budgetModal.campaign.campaign_name}</p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Yeni Günlük Bütçe (₺)</label>
                <input
                  type="number"
                  value={newBudget}
                  onChange={(e) => setNewBudget(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg text-sm"
                  placeholder="0"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Gerekçe (opsiyonel)</label>
                <input
                  type="text"
                  value={budgetReason}
                  onChange={(e) => setBudgetReason(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg text-sm"
                  placeholder="Sezon artışı, promosyon..."
                />
              </div>
            </div>
            <div className="flex gap-2 justify-end mt-4">
              <button
                onClick={() => setBudgetModal({ open: false, campaign: null })}
                className="px-4 py-2 text-sm rounded-lg border border-border hover:bg-slate-50"
              >
                İptal
              </button>
              <button
                disabled={budgetMutation.isPending || !newBudget}
                onClick={() => {
                  if (budgetModal.campaign) {
                    budgetMutation.mutate({
                      campaign: budgetModal.campaign,
                      budget: parseFloat(newBudget),
                    });
                  }
                }}
                className="px-4 py-2 text-sm rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50"
              >
                {budgetMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Güncelle
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
