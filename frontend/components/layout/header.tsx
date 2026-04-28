"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, RefreshCw, Search } from "lucide-react";
import { automationApi, accountsApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Account } from "@/types";

interface HeaderProps {
  title: string;
  subtitle?: string;
  selectedAccount?: string;
  onAccountChange?: (id: string) => void;
}

export function Header({ title, subtitle, selectedAccount, onAccountChange }: HeaderProps) {
  const [showAlerts, setShowAlerts] = useState(false);

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((r) => r.data),
  });

  const { data: alerts } = useQuery({
    queryKey: ["alerts", "unread"],
    queryFn: () => automationApi.listAlerts(undefined, true).then((r) => r.data),
    refetchInterval: 60_000,
  });

  const unreadCount = alerts?.length ?? 0;

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-border px-6 py-4 flex items-center gap-4">
      {/* Title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-lg font-semibold text-slate-900 truncate">{title}</h1>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </div>

      {/* Account Selector */}
      {onAccountChange && (
        <select
          value={selectedAccount ?? ""}
          onChange={(e) => onAccountChange(e.target.value)}
          className="text-sm border border-input rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="">Tüm Hesaplar</option>
          {accounts?.map((acc) => (
            <option key={acc.customer_id} value={acc.customer_id}>
              {acc.name}
            </option>
          ))}
        </select>
      )}

      {/* Alerts bell */}
      <button
        onClick={() => setShowAlerts(!showAlerts)}
        className="relative p-2 rounded-lg hover:bg-muted transition-colors"
      >
        <Bell className="h-5 w-5 text-slate-600" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>
    </header>
  );
}
