"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { accountsApi } from "@/lib/api";
import { Building2, RefreshCw } from "lucide-react";
import type { Account } from "@/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export default function AccountsPage() {
  const qc = useQueryClient();
  const { data: accounts = [], isLoading } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((r) => r.data),
  });

  const syncMutation = useMutation({
    mutationFn: (id: number) => accountsApi.sync(id),
    onSuccess: () => {
      toast.success("Hesap senkronize edildi");
      qc.invalidateQueries({ queryKey: ["accounts"] });
    },
    onError: () => toast.error("Senkronizasyon başarısız"),
  });

  return (
    <div>
      <Header title="Google Ads Hesapları" />
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {isLoading
            ? Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-border p-5 h-32 animate-pulse" />
              ))
            : accounts.map((acc) => (
                <div key={acc.id} className="bg-white rounded-xl border border-border p-5">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-blue-50 rounded-lg text-blue-600 shrink-0">
                      <Building2 className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-slate-900 text-sm truncate">{acc.name}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">ID: {acc.customer_id}</p>
                      {acc.label && (
                        <span className="mt-1 inline-block px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs">
                          {acc.label}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => syncMutation.mutate(acc.id)}
                      className="p-1.5 rounded-lg hover:bg-slate-100 text-muted-foreground transition-colors"
                      title="Senkronize Et"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
                    <span>{acc.currency_code}</span>
                    {acc.is_manager && (
                      <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">MCC</span>
                    )}
                    <span className={`px-2 py-0.5 rounded-full ${acc.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100"}`}>
                      {acc.is_active ? "Aktif" : "Devre Dışı"}
                    </span>
                  </div>
                </div>
              ))}
        </div>
      </div>
    </div>
  );
}
