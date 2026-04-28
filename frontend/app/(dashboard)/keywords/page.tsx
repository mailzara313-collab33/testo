"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { keywordsApi } from "@/lib/api";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";

export default function KeywordsPage() {
  const [accountId, setAccountId] = useState("1234567890");
  const [tab, setTab] = useState<"terms" | "ngrams" | "negatives">("terms");

  const { data: terms = [], isLoading: termsLoading } = useQuery({
    queryKey: ["search-terms", accountId],
    queryFn: () => keywordsApi.searchTerms(accountId).then((r) => r.data),
    enabled: !!accountId && tab === "terms",
  });

  const { data: ngrams = [], isLoading: ngramsLoading } = useQuery({
    queryKey: ["ngrams", accountId],
    queryFn: () => keywordsApi.ngrams(accountId, 2).then((r) => r.data),
    enabled: !!accountId && tab === "ngrams",
  });

  const { data: negatives = [], isLoading: negativesLoading } = useQuery({
    queryKey: ["negatives", accountId],
    queryFn: () => keywordsApi.negativeSuggestions(accountId).then((r) => r.data),
    enabled: !!accountId && tab === "negatives",
  });

  const TABS = [
    { id: "terms", label: "Arama Terimleri" },
    { id: "ngrams", label: "N-gram Analizi" },
    { id: "negatives", label: "Negatif Öneriler" },
  ] as const;

  return (
    <div>
      <Header title="Anahtar Kelime Laboratuvarı" selectedAccount={accountId} onAccountChange={setAccountId} />
      <div className="p-6 space-y-4">
        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                tab === t.id ? "bg-white shadow-sm text-slate-900" : "text-muted-foreground hover:text-slate-900"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Terms Table */}
        {tab === "terms" && (
          <div className="bg-white rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-slate-50">
                  {["Arama Terimi", "Eşleşme", "Kampanya", "Gösterim", "Tıklama", "Harcama", "Dönüşüm", "CTR"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {termsLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i}><td colSpan={8} className="px-4 py-3"><div className="h-4 bg-slate-100 rounded animate-pulse" /></td></tr>
                    ))
                  : terms.map((t: Record<string, unknown>, i: number) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-medium">{String(t.search_term)}</td>
                        <td className="px-4 py-2.5 text-xs text-muted-foreground">{String(t.match_type)}</td>
                        <td className="px-4 py-2.5 text-xs text-muted-foreground max-w-xs truncate">{String(t.campaign_name)}</td>
                        <td className="px-4 py-2.5 text-right">{formatNumber(Number(t.impressions))}</td>
                        <td className="px-4 py-2.5 text-right">{formatNumber(Number(t.clicks))}</td>
                        <td className="px-4 py-2.5 text-right">{formatCurrency(Number(t.cost))}</td>
                        <td className="px-4 py-2.5 text-right">{Number(t.conversions).toFixed(1)}</td>
                        <td className="px-4 py-2.5 text-right">{Number(t.ctr).toFixed(2)}%</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Ngrams Table */}
        {tab === "ngrams" && (
          <div className="bg-white rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-slate-50">
                  {["N-gram", "Gösterim", "Tıklama", "Harcama", "Dönüşüm", "CTR", "CPA"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {ngramsLoading
                  ? Array.from({ length: 6 }).map((_, i) => (
                      <tr key={i}><td colSpan={7} className="px-4 py-3"><div className="h-4 bg-slate-100 rounded animate-pulse" /></td></tr>
                    ))
                  : ngrams.map((n: Record<string, unknown>, i: number) => (
                      <tr key={i} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-medium">{String(n.ngram)}</td>
                        <td className="px-4 py-2.5 text-right">{formatNumber(Number(n.impressions))}</td>
                        <td className="px-4 py-2.5 text-right">{formatNumber(Number(n.clicks))}</td>
                        <td className="px-4 py-2.5 text-right">{formatCurrency(Number(n.cost))}</td>
                        <td className="px-4 py-2.5 text-right">{Number(n.conversions).toFixed(1)}</td>
                        <td className="px-4 py-2.5 text-right">{Number(n.ctr).toFixed(2)}%</td>
                        <td className="px-4 py-2.5 text-right">{formatCurrency(Number(n.cpa))}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Negatives */}
        {tab === "negatives" && (
          <div className="space-y-3">
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
              Aşağıdaki terimler <strong>20+ tıklama</strong> almış ancak <strong>0.5'ten az dönüşüm</strong> üretmiştir.
              Negatif kelime listesine eklemek reklam verimliliğini artırabilir.
            </div>
            <div className="bg-white rounded-xl border border-border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-slate-50">
                    {["Arama Terimi", "Tıklama", "Harcama", "Dönüşüm"].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {negatives.map((n: Record<string, unknown>, i: number) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5 font-medium text-red-600">{String(n.search_term)}</td>
                      <td className="px-4 py-2.5 text-right">{formatNumber(Number(n.clicks))}</td>
                      <td className="px-4 py-2.5 text-right">{formatCurrency(Number(n.cost))}</td>
                      <td className="px-4 py-2.5 text-right">{Number(n.conversions).toFixed(1)}</td>
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
