"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Package,
  AlertTriangle, Brain, CloudRain, RefreshCw, BarChart3, PieChart,
  Search, Bell, Settings, LogOut, Menu, X, Sun, Moon, Pill, LayoutDashboard,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart as RPieChart, Pie, Cell,
} from "recharts";
import { useDashboard } from "@/context/DashboardContext";
import { useTheme } from "next-themes";

// Importer les composants communs
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

const COLORS = ['#0ABAB5', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981', '#EC4899'];

export default function DashboardPage() {
  const router = useRouter();
  const { refreshKey } = useDashboard();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [kpi, setKpi] = useState<any>(null);
  const [charts, setCharts] = useState<any>(null);
  const [season, setSeason] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    loadData();
  }, [refreshKey]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiData, chartsData, seasonData] = await Promise.all([
        api.getDashboardKPIs(),
        api.getSalesCharts(),
        api.getSeasonalAnalysis().catch(() => null),
      ]);
      setKpi(kpiData);
      setCharts(chartsData);
      setSeason(seasonData);
    } catch (err: any) {
      console.error(err);
      setError("Impossible de charger les données. Vérifiez que le backend est lancé.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  const formatFCFA = (v: number) => v ? new Intl.NumberFormat('fr-FR').format(v) + ' FCFA' : '-';
  const formatFCFAShort = (v: number) => {
    if (v >= 1000000) return (v/1000000).toFixed(1) + 'M';
    if (v >= 1000) return (v/1000).toFixed(0) + 'k';
    return v.toString();
  };

  // Navigation locale pour la sidebar mobile
  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Médicaments", href: "/medicines", icon: Pill },
    { label: "Stocks", href: "/inventory", icon: Package },
    { label: "Ventes", href: "/sales", icon: ShoppingCart },
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "Chat IA", href: "/ai/chat", icon: Brain },
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0ABAB5] mx-auto"></div>
          <p className="text-slate-500 dark:text-slate-400">Chargement du tableau de bord...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Card className="p-8 text-center shadow-xl border-0 dark:bg-slate-800">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-400" />
          <p className="text-lg text-slate-700 dark:text-white">{error}</p>
          <Button onClick={loadData} className="mt-4 bg-[#0ABAB5] hover:bg-[#0a9e99]">
            <RefreshCw className="w-4 h-4 mr-2" /> Réessayer
          </Button>
        </Card>
      </div>
    );
  }

  const dailySales = charts?.daily_sales || [];
  const categories = charts?.categories || [];
  const topMedicines = charts?.top_medicines || [];

  const cards = [
    { title: "CA Aujourd'hui", value: formatFCFA(kpi?.ca_today), evolution: kpi?.ca_today_evolution, icon: DollarSign, color: "text-green-400", bg: "from-green-50 to-emerald-50", link: "/sales/today" },
    { title: "Ventes Aujourd'hui", value: kpi?.sales_today ?? "-", icon: ShoppingCart, color: "text-indigo-400", bg: "from-indigo-50 to-purple-50", link: "/sales/today" },
    { title: "Ruptures", value: kpi?.out_of_stock ?? "0", icon: AlertTriangle, color: kpi?.out_of_stock > 0 ? "text-red-400" : "text-green-400", bg: kpi?.out_of_stock > 0 ? "from-red-50 to-rose-50" : "from-green-50 to-emerald-50", link: "/inventory/out-of-stock" },
    { title: "Stock Faible", value: kpi?.low_stock ?? "0", icon: AlertTriangle, color: "text-yellow-400", bg: "from-yellow-50 to-amber-50", link: "/inventory/low-stock" },
    { title: "Expirations", value: kpi?.soon_expired ?? "0", icon: AlertTriangle, color: "text-orange-400", bg: "from-orange-50 to-amber-50", link: "/inventory/expiring-soon" },
    { title: "CA Semaine", value: formatFCFA(kpi?.ca_week), evolution: kpi?.ca_week_evolution, icon: TrendingUp, color: "text-blue-400", bg: "from-blue-50 to-cyan-50" },
    { title: "Valeur Stock", value: formatFCFA(kpi?.stock_value), icon: Package, color: "text-emerald-400", bg: "from-emerald-50 to-green-50" },
    { title: "Profit Estimé", value: formatFCFA(kpi?.estimated_profit), icon: DollarSign, color: "text-teal-400", bg: "from-teal-50 to-cyan-50" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Topbar commune */}
      <Topbar
        onMenuClick={() => setMobileMenuOpen(true)}
        onRefresh={loadData}
      />

      {/* Sidebar desktop (composant commun) */}
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
                  className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left text-gray-300 hover:bg-white/5 hover:text-white"
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
      <main className="pt-16 lg:pl-64 p-4 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Dashboard</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Vue d'ensemble de votre pharmacie</p>
          </div>
          <Button variant="outline" size="sm" onClick={loadData} className="gap-2 dark:border-slate-600 dark:text-slate-300">
            <RefreshCw className="w-4 h-4" /> Actualiser
          </Button>
        </div>

        {/* Le reste du contenu (season, KPI, graphiques, top médicaments) reste identique */}
        {season && (
          <Card className="border-0 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-slate-800 dark:to-slate-800 shadow-sm hover:shadow-md transition-shadow rounded-2xl">
            <CardContent className="flex items-center gap-4 py-4">
              <CloudRain className="w-8 h-8 text-blue-500" />
              <div className="flex-1">
                <p className="font-semibold text-slate-800 dark:text-white">{season.season}</p>
                <div className="flex gap-2 mt-1 flex-wrap">
                  {season.alerts?.map((a: string, i: number) => (
                    <Badge key={i} variant="secondary" className="text-xs bg-white/70 dark:bg-slate-700 dark:text-slate-300">{a}</Badge>
                  ))}
                </div>
              </div>
              <Brain className="w-6 h-6 text-[#0ABAB5]" />
            </CardContent>
          </Card>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {cards.map((card, i) => (
            <Card
              key={i}
              className={`hover:shadow-xl transition-all duration-300 border border-transparent dark:border-slate-700 shadow-sm hover:-translate-y-1 bg-gradient-to-br ${card.bg} dark:bg-none dark:bg-slate-800 ${card.link ? 'cursor-pointer' : ''} rounded-2xl`}
              onClick={() => card.link && router.push(card.link)}
            >
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">{card.title}</span>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-white/50 dark:bg-white/10 ${card.color}`}>
                    <card.icon className="w-4 h-4" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-slate-800 dark:text-white">{card.value}</div>
                {card.evolution !== undefined && card.evolution !== null && (
                  <div className="flex items-center gap-1 mt-2">
                    {card.evolution > 0 ? <TrendingUp className="w-3 h-3 text-green-500" /> : <TrendingDown className="w-3 h-3 text-red-500" />}
                    <span className={`text-xs font-semibold ${card.evolution > 0 ? "text-green-600" : "text-red-600"}`}>
                      {card.evolution > 0 ? "+" : ""}{card.evolution}%
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Graphiques */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white dark:bg-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold text-slate-800 dark:text-white">Ventes des 7 derniers jours</CardTitle>
              <BarChart3 className="w-5 h-5 text-slate-400" />
            </CardHeader>
            <CardContent>
              {dailySales.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dailySales}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="day_name" fontSize={12} stroke="#94a3b8" />
                    <YAxis tickFormatter={formatFCFAShort} fontSize={12} stroke="#94a3b8" />
                    <Tooltip formatter={(v: number) => [formatFCFA(v), "CA"]} />
                    <Bar dataKey="revenue" fill="#0ABAB5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-400 dark:text-slate-500">Aucune vente récente</div>
              )}
            </CardContent>
          </Card>

          <Card className="border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white dark:bg-slate-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold text-slate-800 dark:text-white">Répartition par catégorie</CardTitle>
              <PieChart className="w-5 h-5 text-slate-400" />
            </CardHeader>
            <CardContent>
              {categories.length > 0 ? (
                <div className="flex items-center">
                  <ResponsiveContainer width="60%" height={250}>
                    <RPieChart>
                      <Pie data={categories} cx="50%" cy="50%" outerRadius={80} dataKey="revenue" nameKey="name">
                        {categories.map((_: any, idx: number) => <Cell key={idx} fill={COLORS[idx % COLORS.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v: number) => [formatFCFA(v), "CA"]} />
                    </RPieChart>
                  </ResponsiveContainer>
                  <div className="w-40 space-y-2">
                    {categories.map((cat: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        <span className="text-slate-600 dark:text-slate-300">{cat.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-slate-400 dark:text-slate-500">Aucune donnée</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Top médicaments */}
        <Card className="border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white dark:bg-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-semibold text-slate-800 dark:text-white">🏆 Top 5 des médicaments les plus vendus</CardTitle>
            <ShoppingCart className="w-5 h-5 text-slate-400" />
          </CardHeader>
          <CardContent>
            {topMedicines.length > 0 ? (
              <div className="space-y-3">
                {topMedicines.slice(0, 5).map((med: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-xl hover:bg-white dark:hover:bg-slate-600 transition-colors">
                    <div className="flex items-center gap-4">
                      <span className="text-lg font-bold text-slate-300 dark:text-slate-500 w-6">#{i+1}</span>
                      <div>
                        <p className="font-medium text-sm text-slate-800 dark:text-white">{med.name}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">{med.quantity} vendus</p>
                      </div>
                    </div>
                    <span className="font-semibold text-sm text-[#0ABAB5]">{formatFCFA(med.revenue)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-slate-400 dark:text-slate-500">Aucune vente enregistrée</div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}