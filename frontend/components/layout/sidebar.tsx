"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Building2,
  ChevronDown,
  Cpu,
  FileText,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Megaphone,
  Settings,
  Target,
  Users,
  Wallet,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";

const NAV_ITEMS = [
  {
    label: "Genel Bakış",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Kampanyalar",
    href: "/campaigns",
    icon: Megaphone,
  },
  {
    label: "Anahtar Kelimeler",
    href: "/keywords",
    icon: KeyRound,
  },
  {
    label: "Otomasyon",
    href: "/automation",
    icon: Cpu,
  },
  {
    label: "Bütçe Takibi",
    href: "/budget",
    icon: Wallet,
  },
  {
    label: "Raporlar",
    href: "/reports",
    icon: FileText,
  },
];

const BOTTOM_ITEMS = [
  { label: "Hesaplar", href: "/accounts", icon: Building2 },
  { label: "Kullanıcılar", href: "/users", icon: Users },
  { label: "Ayarlar", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-slate-900 text-white">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-slate-700">
        <div className="p-1.5 bg-blue-600 rounded-lg">
          <BarChart3 className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight">AdOps</p>
          <p className="text-xs text-slate-400 leading-tight">Command Center</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Platform
        </p>
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}

        <div className="pt-4">
          <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Yönetim
          </p>
          {BOTTOM_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* User */}
      <div className="px-3 py-4 border-t border-slate-700">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-800 cursor-pointer group">
          <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold shrink-0">
            {user?.full_name?.[0]?.toUpperCase() ?? "A"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name ?? "Admin"}</p>
            <p className="text-xs text-slate-400 truncate">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            title="Çıkış"
            className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
