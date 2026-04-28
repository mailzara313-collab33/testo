"use client";

import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { usersApi } from "@/lib/api";
import { UserCircle } from "lucide-react";

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  admin: { label: "Admin", color: "bg-red-100 text-red-700" },
  account_manager: { label: "Hesap Müd.", color: "bg-blue-100 text-blue-700" },
  viewer: { label: "Görüntüleyici", color: "bg-slate-100 text-slate-600" },
};

export default function UsersPage() {
  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list().then((r) => r.data),
  });

  return (
    <div>
      <Header title="Kullanıcılar" />
      <div className="p-6">
        <div className="bg-white rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-slate-50">
                {["Kullanıcı", "E-posta", "Rol", "2FA", "Durum", "Kayıt Tarihi"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading
                ? Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i}><td colSpan={6} className="px-4 py-3"><div className="h-4 bg-slate-100 rounded animate-pulse" /></td></tr>
                  ))
                : (users as Record<string, unknown>[]).map((u) => {
                    const role = ROLE_LABELS[String(u.role)] ?? { label: String(u.role), color: "bg-slate-100" };
                    return (
                      <tr key={String(u.id)} className="hover:bg-slate-50">
                        <td className="px-4 py-3 flex items-center gap-2">
                          <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs font-bold">
                            {String(u.full_name)[0]?.toUpperCase()}
                          </div>
                          {String(u.full_name)}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{String(u.email)}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${role.color}`}>{role.label}</span>
                        </td>
                        <td className="px-4 py-3 text-xs">{u.is_2fa_enabled ? "✓" : "—"}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs ${u.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                            {u.is_active ? "Aktif" : "Devre Dışı"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">
                          {new Date(String(u.created_at)).toLocaleDateString("tr-TR")}
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
