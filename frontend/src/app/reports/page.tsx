"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";
import {
  Download, FileText, FileSpreadsheet, Package, AlertTriangle, Users,
  TrendingUp, Menu, X, FileBarChart, LayoutDashboard, Pill, ShoppingCart,
  BarChart3, Brain, Bell, LogOut
} from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

export default function ReportsPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [salesStartDate, setSalesStartDate] = useState<string>("");
  const [salesEndDate, setSalesEndDate] = useState<string>("");

  const handleDownload = async (kind: string, format: 'pdf' | 'excel', params?: Record<string, string>) => {
    try {
      const blob = await api.downloadReport(kind, format, params);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_${kind}_${format}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`Rapport ${kind} téléchargé`);
    } catch (error: any) {
      console.error("Erreur téléchargement", error);
      toast.error(`Erreur: ${error.message}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  // Navigation locale pour la sidebar mobile (identique aux autres pages)
  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Médicaments", href: "/medicines", icon: Pill },
    { label: "Stocks", href: "/inventory", icon: Package },
    { label: "Ventes", href: "/sales", icon: ShoppingCart },
    { label: "Rapports", href: "/reports", icon: FileBarChart },
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "Chat IA", href: "/ai/chat", icon: Brain },
    { label: "IA Prédictions", href: "/ai/predictions", icon: Brain },
    { label: "Notifications", href: "/notifications", icon: Bell },
    { label: "Utilisateurs", href: "/admin/users", icon: Users },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Topbar */}
      <Topbar onMenuClick={() => setMobileMenuOpen(true)} />

      {/* Sidebar desktop */}
      <Sidebar />

      {/* Sidebar mobile */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <aside className="fixed left-0 top-0 bottom-0 w-64 bg-[#0F1A2C] text-white p-6 flex flex-col">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#0ABAB5] rounded-xl flex items-center justify-center font-bold text-xl">D</div>
                <span className="font-bold">DENG PHARMA</span>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setMobileMenuOpen(false)} className="text-white">
                <X className="w-5 h-5" />
              </Button>
            </div>
            <nav className="flex-1 space-y-1">
              {navItems.map((item) => (
                <button
                  key={item.href}
                  onClick={() => { router.push(item.href); setMobileMenuOpen(false); }}
                  className={`flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left ${
                    item.href === "/reports" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </button>
              ))}
            </nav>
            <Button variant="ghost" onClick={handleLogout} className="text-gray-300 hover:text-white mt-4">
              <LogOut className="w-4 h-4 mr-2" /> Déconnexion
            </Button>
          </aside>
        </div>
      )}

      {/* Contenu principal */}
      <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Rapports</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Téléchargez les rapports de votre pharmacie au format PDF ou Excel.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6">
          {/* Rapport Ventes */}
          <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base sm:text-lg font-semibold flex items-center gap-2">
                <FileBarChart className="w-5 h-5 text-[#0ABAB5]" /> Ventes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 sm:space-y-4">
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Historique des ventes avec possibilité de filtrer par période.
              </p>
              <div className="grid grid-cols-2 gap-2 sm:gap-4">
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Date début</label>
                  <Input
                    type="date"
                    value={salesStartDate}
                    onChange={(e) => setSalesStartDate(e.target.value)}
                    className="dark:bg-slate-700 dark:text-white text-xs sm:text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Date fin</label>
                  <Input
                    type="date"
                    value={salesEndDate}
                    onChange={(e) => setSalesEndDate(e.target.value)}
                    className="dark:bg-slate-700 dark:text-white text-xs sm:text-sm"
                  />
                </div>
              </div>
              <div className="flex gap-2 sm:gap-3">
                <Button
                  onClick={() => handleDownload('sales', 'pdf', {
                    ...(salesStartDate && { start_date: salesStartDate }),
                    ...(salesEndDate && { end_date: salesEndDate }),
                  })}
                  className="flex-1 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white text-xs sm:text-sm"
                >
                  <Download className="w-4 h-4 mr-1 sm:mr-2" /> PDF
                </Button>
                <Button
                  onClick={() => handleDownload('sales', 'excel', {
                    ...(salesStartDate && { start_date: salesStartDate }),
                    ...(salesEndDate && { end_date: salesEndDate }),
                  })}
                  variant="outline"
                  className="flex-1 text-xs sm:text-sm"
                >
                  <FileSpreadsheet className="w-4 h-4 mr-1 sm:mr-2" /> Excel
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Rapport Stocks */}
          <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base sm:text-lg font-semibold flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-500" /> Stocks
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 sm:space-y-4">
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                État actuel des stocks et des lots.
              </p>
              <div className="flex gap-2 sm:gap-3">
                <Button
                  onClick={() => handleDownload('stock', 'pdf')}
                  className="flex-1 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white text-xs sm:text-sm"
                >
                  <Download className="w-4 h-4 mr-1 sm:mr-2" /> PDF
                </Button>
                <Button
                  onClick={() => handleDownload('stock', 'excel')}
                  variant="outline"
                  className="flex-1 text-xs sm:text-sm"
                >
                  <FileSpreadsheet className="w-4 h-4 mr-1 sm:mr-2" /> Excel
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Rapport Alertes */}
          <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base sm:text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-500" /> Alertes
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 sm:space-y-4">
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Notifications de ruptures, stock faible, expirations.
              </p>
              <div className="flex gap-2 sm:gap-3">
                <Button
                  onClick={() => handleDownload('alerts', 'pdf')}
                  className="flex-1 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white text-xs sm:text-sm"
                >
                  <Download className="w-4 h-4 mr-1 sm:mr-2" /> PDF
                </Button>
                <Button
                  onClick={() => handleDownload('alerts', 'excel')}
                  variant="outline"
                  className="flex-1 text-xs sm:text-sm"
                >
                  <FileSpreadsheet className="w-4 h-4 mr-1 sm:mr-2" /> Excel
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Rapport Utilisateurs (admin seulement) */}
          <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base sm:text-lg font-semibold flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-500" /> Utilisateurs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 sm:space-y-4">
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Liste des utilisateurs et de leurs rôles (admin uniquement).
              </p>
              <div className="flex gap-2 sm:gap-3">
                <Button
                  onClick={() => handleDownload('users', 'pdf')}
                  className="flex-1 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white text-xs sm:text-sm"
                >
                  <Download className="w-4 h-4 mr-1 sm:mr-2" /> PDF
                </Button>
                <Button
                  onClick={() => handleDownload('users', 'excel')}
                  variant="outline"
                  className="flex-1 text-xs sm:text-sm"
                >
                  <FileSpreadsheet className="w-4 h-4 mr-1 sm:mr-2" /> Excel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}