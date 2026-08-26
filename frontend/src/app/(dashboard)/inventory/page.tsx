"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Package, AlertTriangle, Clock, Boxes,
  Menu, X, Pill, LayoutDashboard, ShoppingCart,
  BarChart3, Brain, LogOut,
  TrendingUp, Bell, FileBarChart, Users
} from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function InventoryPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    api.getInventorySummary()
      .then((data) => setSummary(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  // Navigation locale pour la sidebar mobile (identique aux autres pages)
  const navItems = [
    { label: "Dashboard", href: "/", icon: TrendingUp },
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

  // Définition des statuts possibles
  const statusMap: Record<string, { label: string; badgeClass: string }> = {
    OUT: { label: "Rupture", badgeClass: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300" },
    LOW: { label: "Stock faible", badgeClass: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" },
    OVER: { label: "Surstock", badgeClass: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
    OK: { label: "OK", badgeClass: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" },
  };

  const statusBadge = (status: string) => {
    const config = statusMap[status] || statusMap.OK;
    return <Badge className={config.badgeClass}>{config.label}</Badge>;
  };

  const getStockPercent = (med: any) => {
    if (!med.max_stock || med.max_stock === 0) return 0;
    return Math.min(100, Math.round((med.remaining_stock / med.max_stock) * 100));
  };

  const filteredMedicines = filterStatus
    ? summary.filter((med) => med.status === filterStatus)
    : summary;

  const countByStatus = (status: string) => summary.filter((med) => med.status === status).length;

  const handleFilter = (status: string | null) => {
    setFilterStatus((prev) => (prev === status ? null : status));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0ABAB5] mx-auto"></div>
          <p className="text-slate-500 dark:text-slate-400">Chargement des stocks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Topbar commune */}
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
                    item.href === "/inventory" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </button>
              ))}
            </nav>
            <Button variant="ghost" onClick={handleLogout} className="text-gray-300 hover:text-white">
              <LogOut className="w-4 h-4 mr-2" /> Déconnexion
            </Button>
          </aside>
        </div>
      )}

      {/* Contenu principal */}
      <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Stocks</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez vos lots et surveillez les expirations</p>
        </div>

        {/* Cartes KPI cliquables */}
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
          {/* Tous les médicaments */}
          <button
            onClick={() => handleFilter(null)}
            className={`text-left cursor-pointer transition-transform hover:scale-[1.02] ${filterStatus === null ? 'ring-2 ring-blue-400' : ''}`}
          >
            <Card className="border-0 shadow-md bg-gradient-to-br from-blue-50 to-cyan-50 dark:bg-none dark:bg-slate-800 dark:border-slate-700 h-full">
              <CardContent className="py-3 px-3 sm:py-4 sm:px-4 flex items-center gap-2 sm:gap-3">
                <Boxes className="w-6 h-6 sm:w-8 sm:h-8 text-blue-500" />
                <div>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">Médicaments</p>
                  <p className="text-lg sm:text-2xl font-bold text-slate-900 dark:text-white">{summary.length}</p>
                </div>
              </CardContent>
            </Card>
          </button>

          {/* Stock faible */}
          <button
            onClick={() => handleFilter("LOW")}
            className={`text-left cursor-pointer transition-transform hover:scale-[1.02] ${filterStatus === "LOW" ? 'ring-2 ring-yellow-400' : ''}`}
          >
            <Card className="border-0 shadow-md bg-gradient-to-br from-yellow-50 to-amber-50 dark:bg-none dark:bg-slate-800 dark:border-slate-700 h-full">
              <CardContent className="py-3 px-3 sm:py-4 sm:px-4 flex items-center gap-2 sm:gap-3">
                <Clock className="w-6 h-6 sm:w-8 sm:h-8 text-yellow-500" />
                <div>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">Stock faible</p>
                  <p className="text-lg sm:text-2xl font-bold text-slate-900 dark:text-white">{countByStatus("LOW")}</p>
                </div>
              </CardContent>
            </Card>
          </button>

          {/* Ruptures */}
          <button
            onClick={() => handleFilter("OUT")}
            className={`text-left cursor-pointer transition-transform hover:scale-[1.02] ${filterStatus === "OUT" ? 'ring-2 ring-red-400' : ''}`}
          >
            <Card className="border-0 shadow-md bg-gradient-to-br from-red-50 to-rose-50 dark:bg-none dark:bg-slate-800 dark:border-slate-700 h-full">
              <CardContent className="py-3 px-3 sm:py-4 sm:px-4 flex items-center gap-2 sm:gap-3">
                <AlertTriangle className="w-6 h-6 sm:w-8 sm:h-8 text-red-500" />
                <div>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">Ruptures</p>
                  <p className="text-lg sm:text-2xl font-bold text-slate-900 dark:text-white">{countByStatus("OUT")}</p>
                </div>
              </CardContent>
            </Card>
          </button>

          {/* Surstock */}
          <button
            onClick={() => handleFilter("OVER")}
            className={`text-left cursor-pointer transition-transform hover:scale-[1.02] ${filterStatus === "OVER" ? 'ring-2 ring-blue-400' : ''}`}
          >
            <Card className="border-0 shadow-md bg-gradient-to-br from-slate-100 to-slate-200 dark:bg-none dark:bg-slate-800 dark:border-slate-700 h-full">
              <CardContent className="py-3 px-3 sm:py-4 sm:px-4 flex items-center gap-2 sm:gap-3">
                <Package className="w-6 h-6 sm:w-8 sm:h-8 text-slate-500" />
                <div>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">Surstock</p>
                  <p className="text-lg sm:text-2xl font-bold text-slate-900 dark:text-white">{countByStatus("OVER")}</p>
                </div>
              </CardContent>
            </Card>
          </button>
        </div>

        {/* Tableau des stocks */}
        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl text-slate-900 dark:text-white">
              {filterStatus ? "Médicaments filtrés" : "État des stocks par médicament"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              [...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2 dark:bg-slate-700" />)
            ) : (
              <Table className="w-full table-fixed">
                <TableHeader>
                  <TableRow className="border-slate-200 dark:border-slate-700">
                    <TableHead className="w-1/4 text-xs sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">
                      <span className="sm:hidden">Méd.</span>
                      <span className="hidden sm:inline">Médicament</span>
                    </TableHead>
                    <TableHead className="w-1/6 text-xs sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">
                      <span className="sm:hidden">Qté</span>
                      <span className="hidden sm:inline">Qté restante</span>
                    </TableHead>
                    <TableHead className="w-1/6 text-xs sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Min</TableHead>
                    <TableHead className="w-1/6 text-xs sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Max</TableHead>
                    <TableHead className="w-1/6 text-xs sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Niveau</TableHead>
                    <TableHead className="w-1/6 text-xs sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Statut</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredMedicines.map((med) => (
                    <TableRow key={med.id} className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700">
                      <TableCell className="font-medium text-slate-900 dark:text-white text-xs sm:text-sm truncate">{med.commercial_name}</TableCell>
                      <TableCell className="text-slate-900 dark:text-white font-semibold text-xs sm:text-sm">{med.remaining_stock}</TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">{med.min_stock}</TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">{med.max_stock}</TableCell>
                      <TableCell className="p-1 sm:p-2">
                        <Progress value={getStockPercent(med)} className="h-1.5 sm:h-2" />
                      </TableCell>
                      <TableCell className="p-1 sm:p-2">
                        <Badge className={`text-xs ${statusMap[med.status]?.badgeClass || ''}`}>{statusMap[med.status]?.label}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredMedicines.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
                        Aucun médicament pour ce filtre.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}