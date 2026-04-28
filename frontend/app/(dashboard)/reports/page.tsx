"use client";

import { Header } from "@/components/layout/header";
import { FileText, Download, Mail, Calendar } from "lucide-react";

const REPORT_TYPES = [
  {
    title: "Haftalık Performans Raporu",
    description: "Geçen haftanın tüm KPI'larını içeren PDF rapor",
    icon: FileText,
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  {
    title: "Aylık Özet Raporu",
    description: "Aylık trend analizi ve önerilerle birlikte white-label PDF",
    icon: Calendar,
    color: "text-purple-600",
    bg: "bg-purple-50",
  },
  {
    title: "Excel Dışa Aktarım",
    description: "Tüm kampanya, reklam grubu ve anahtar kelime metrikleri",
    icon: Download,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    title: "Otomatik E-posta Raporu",
    description: "Müşterinize her hafta otomatik rapor gönder",
    icon: Mail,
    color: "text-orange-600",
    bg: "bg-orange-50",
  },
];

export default function ReportsPage() {
  return (
    <div>
      <Header title="Raporlar" subtitle="Otomatik ve manuel raporlama" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {REPORT_TYPES.map((r) => (
            <div key={r.title} className="bg-white rounded-xl border border-border p-6 flex items-start gap-4">
              <div className={`p-3 rounded-xl ${r.bg} ${r.color} shrink-0`}>
                <r.icon className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-900 text-sm">{r.title}</h3>
                <p className="text-xs text-muted-foreground mt-1">{r.description}</p>
                <button className="mt-3 px-4 py-1.5 bg-slate-900 hover:bg-slate-700 text-white text-xs font-medium rounded-lg transition-colors">
                  Oluştur
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <h3 className="font-semibold text-blue-900 text-sm mb-1">Sprint 7'de tamamlanacak</h3>
          <p className="text-xs text-blue-700">
            PDF (WeasyPrint), Excel (openpyxl) ve otomatik e-posta gönderimi bu sayfada
            aktifleştirilecek. Şu an altyapı hazır, API entegrasyonu bekleniyor.
          </p>
        </div>
      </div>
    </div>
  );
}
