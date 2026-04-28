"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Play,
  Pause,
  Cpu,
  FlaskConical,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Plus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { automationApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AutomationRule } from "@/types";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  active: { label: "Aktif", color: "bg-emerald-100 text-emerald-700" },
  paused: { label: "Duraklatıldı", color: "bg-amber-100 text-amber-700" },
  draft: { label: "Taslak", color: "bg-slate-100 text-slate-600" },
};

function RuleCard({ rule }: { rule: AutomationRule }) {
  const [expanded, setExpanded] = useState(false);
  const qc = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: (status: string) => automationApi.toggleRule(rule.id, status),
    onSuccess: (_, status) => {
      toast.success(`Kural ${status === "active" ? "aktifleştirildi" : "duraklatıldı"}`);
      qc.invalidateQueries({ queryKey: ["automation-rules"] });
    },
    onError: () => toast.error("Durum değiştirilemedi"),
  });

  const status = STATUS_LABELS[rule.status] ?? STATUS_LABELS.draft;

  let condition: Record<string, unknown> = {};
  let action: Record<string, unknown> = {};
  try {
    condition = JSON.parse(rule.condition_json);
    action = JSON.parse(rule.action_json);
  } catch {
    /* ignore */
  }

  return (
    <div className="bg-white rounded-xl border border-border p-5">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-blue-50 rounded-lg text-blue-600 shrink-0">
          <Zap className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-slate-900 text-sm">{rule.name}</h3>
            <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
              {status.label}
            </span>
            {rule.is_dry_run && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                <FlaskConical className="h-3 w-3" />
                Dry Run
              </span>
            )}
          </div>
          {rule.description && (
            <p className="text-xs text-muted-foreground mt-1">{rule.description}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {rule.schedule}
            </span>
            <span>{rule.run_count} çalışma</span>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-muted-foreground"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          {rule.status === "active" ? (
            <button
              onClick={() => toggleMutation.mutate("paused")}
              className="p-1.5 rounded-lg hover:bg-amber-50 text-amber-600"
              title="Duraklat"
            >
              <Pause className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={() => toggleMutation.mutate("active")}
              className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600"
              title="Aktifleştir"
            >
              <Play className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-border space-y-3">
          <div>
            <p className="text-xs font-semibold text-slate-700 mb-1">Koşul</p>
            <code className="block text-xs bg-slate-50 rounded-lg p-3 text-slate-700 overflow-x-auto">
              {JSON.stringify(condition, null, 2)}
            </code>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-700 mb-1">Aksiyon</p>
            <code className="block text-xs bg-slate-50 rounded-lg p-3 text-slate-700 overflow-x-auto">
              {JSON.stringify(action, null, 2)}
            </code>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AutomationPage() {
  const qc = useQueryClient();

  const { data: rules = [], isLoading } = useQuery<AutomationRule[]>({
    queryKey: ["automation-rules"],
    queryFn: () => automationApi.listRules().then((r) => r.data),
  });

  const { data: logs = [] } = useQuery<
    { id: number; rule_id: number; action_taken: string; dry_run: boolean; success: boolean; created_at: string }[]
  >({
    queryKey: ["automation-logs"],
    queryFn: () => automationApi.listLogs().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const seedMutation = useMutation({
    mutationFn: () => automationApi.seedTemplates(),
    onSuccess: () => {
      toast.success("5 hazır kural şablonu oluşturuldu");
      qc.invalidateQueries({ queryKey: ["automation-rules"] });
    },
    onError: () => toast.error("Şablonlar oluşturulamadı"),
  });

  return (
    <div>
      <Header title="Otomasyon Motoru" subtitle="Otomatik optimizasyon kuralları" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-border p-4 flex items-center gap-3">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <Play className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {rules.filter((r) => r.status === "active").length}
              </p>
              <p className="text-xs text-muted-foreground">Aktif Kural</p>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-border p-4 flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{rules.length}</p>
              <p className="text-xs text-muted-foreground">Toplam Kural</p>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-border p-4 flex items-center gap-3">
            <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
              <FlaskConical className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {rules.filter((r) => r.is_dry_run).length}
              </p>
              <p className="text-xs text-muted-foreground">Dry Run Modu</p>
            </div>
          </div>
        </div>

        {/* Rules Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Kurallar</h2>
          <div className="flex gap-2">
            {rules.length === 0 && (
              <button
                onClick={() => seedMutation.mutate()}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Zap className="h-4 w-4" />
                Hazır Şablonları Yükle
              </button>
            )}
            <button className="flex items-center gap-2 px-4 py-2 border border-border hover:bg-slate-50 text-sm font-medium rounded-lg transition-colors">
              <Plus className="h-4 w-4" />
              Yeni Kural
            </button>
          </div>
        </div>

        {/* Rules List */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-border p-5 h-24 animate-pulse" />
            ))}
          </div>
        ) : rules.length === 0 ? (
          <div className="bg-white rounded-xl border border-border p-10 text-center">
            <Cpu className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-900">Henüz kural yok</p>
            <p className="text-xs text-muted-foreground mt-1">
              Hazır şablonları yükleyin veya yeni kural oluşturun
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {rules.map((rule) => (
              <RuleCard key={rule.id} rule={rule} />
            ))}
          </div>
        )}

        {/* Audit Log */}
        {logs.length > 0 && (
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-3">Son İşlemler</h2>
            <div className="bg-white rounded-xl border border-border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-slate-50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">İşlem</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Kural</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Mod</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Sonuç</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Zaman</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5 font-medium">{log.action_taken}</td>
                      <td className="px-4 py-2.5 text-muted-foreground">#{log.rule_id}</td>
                      <td className="px-4 py-2.5">
                        {log.dry_run ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">Dry Run</span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Canlı</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        {log.success ? (
                          <CheckCircle className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground text-xs">
                        {new Date(log.created_at).toLocaleString("tr-TR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
