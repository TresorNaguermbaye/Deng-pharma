"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Package,
  BarChart3, PieChart, Target, Activity, Percent,
  Menu, X, LayoutDashboard, Pill, FileBarChart, Bell, Users, LogOut, Brain
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart as RPieChart, Pie, Cell,
} from "recharts";
import { useTheme } from "next-themes";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

const COLORS = [
  "#0ABAB5", "#3B82F6", "#8B5CF6", "#F59E0B", "#EF4444", "#10B981",
  "#EC4899", "#6366F1", "#14B8A6", "#F97316",
];

export default function AnalyticsPage() {
  const router = useRouter();
  const [kpi, setKpi] = useState<any>(null);
  const [charts, setCharts] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { theme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiData, chartsData] = await Promise.all([
        api.getDashboardKPIs(),
        api.getSalesCharts().catch(() => null),
      ]);
      setKpi(kpiData);
      setCharts(chartsData);
    } catch (err) {
      console.error("Erreur chargement analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  // Navigation locale pour la sidebar mobile
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

  const formatFCFA = (v: number) =>
    v ? new Intl.NumberFormat("fr-FR").format(v) + " FCFA" : "0 FCFA";
  const formatNumber = (v: number) =>
    v ? new Intl.NumberFormat("fr-FR").format(v) : "0";

  const dailySales = charts?.daily_sales || [];
  const categories = charts?.categories || [];

  const totalSales = dailySales.reduce((sum: number, d: any) => sum + d.orders, 0);
  const totalRevenue = dailySales.reduce((sum: number, d: any) => sum + d.revenue, 0);
  const averageBasket = totalSales > 0 ? totalRevenue / totalSales : 0;
  const marginRate = kpi?.estimated_profit && kpi?.ca_month
    ? ((kpi.estimated_profit / kpi.ca_month) * 100)
    : 0;
  const outOfStockRate = kpi?.total_medicines
    ? ((kpi.out_of_stock / kpi.total_medicines) * 100)
    : 0;
  const stockTurnover = kpi?.ca_month && kpi?.stock_value
    ? (kpi.ca_month / kpi.stock_value).toFixed(1)
    : "0";

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
        <Topbar onMenuClick={() => setMobileMenuOpen(true)} />
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
                      item.href === "/analytics" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
        <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-6">
          <Skeleton className="h-8 w-64" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-80 rounded-xl" />
            <Skeleton className="h-80 rounded-xl" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Topbar onMenuClick={() => setMobileMenuOpen(true)} />
      <Sidebar />
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
                    item.href === "/analytics" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
      <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-6">
        {/* Titre */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Analytics</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Analysez vos performances et tendances</p>
        </div>

        {/* KPIs principaux */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard title="CA Mensuel" value={formatFCFA(kpi?.ca_month || 0)} icon={<DollarSign className="w-5 h-5" />} bg="from-green-50 to-emerald-50" color="text-green-600" />
          <KpiCard title="Ventes Aujourd'hui" value={formatNumber(kpi?.sales_today)} icon={<ShoppingCart className="w-5 h-5" />} bg="from-blue-50 to-cyan-50" color="text-blue-600" />
          <KpiCard title="Valeur du Stock" value={formatFCFA(kpi?.stock_value)} icon={<Package className="w-5 h-5" />} bg="from-purple-50 to-violet-50" color="text-purple-600" />
          <KpiCard title="Profit Estimé" value={formatFCFA(kpi?.estimated_profit)} icon={<TrendingUp className="w-5 h-5" />} bg="from-yellow-50 to-amber-50" color="text-yellow-600" />
        </div>

        {/* KPI avancés */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard title="Panier moyen" value={formatFCFA(averageBasket)} icon={<Target className="w-5 h-5" />} bg="from-rose-50 to-pink-50" color="text-pink-600" />
          <KpiCard title="Taux de marge" value={`${marginRate.toFixed(1)}%`} icon={<Percent className="w-5 h-5" />} bg="from-indigo-50 to-blue-50" color="text-indigo-600" />
          <KpiCard title="Rotation du stock" value={stockTurnover} icon={<Activity className="w-5 h-5" />} bg="from-cyan-50 to-teal-50" color="text-cyan-600" />
          <KpiCard title="Taux de rupture" value={`${outOfStockRate.toFixed(1)}%`} icon={<Target className="w-5 h-5" />} bg="from-orange-50 to-red-50" color="text-red-600" />
        </div>

        {/* Graphiques */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-slate-900 dark:text-white">Ventes des 7 derniers jours</CardTitle>
              <BarChart3 className="w-5 h-5 text-slate-400" />
            </CardHeader>
            <CardContent>
              {dailySales.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={dailySales}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="day_name" fontSize={12} stroke={theme === "dark" ? "#94a3b8" : "#64748b"} />
                    <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} fontSize={12} stroke={theme === "dark" ? "#94a3b8" : "#64748b"} />
                    <Tooltip formatter={(v: number) => [formatFCFA(v), "Chiffre d'affaires"]} contentStyle={{ backgroundColor: theme === "dark" ? "#1e293b" : "#fff", border: "none", borderRadius: "8px", color: theme === "dark" ? "#fff" : "#000" }} />
                    <Bar dataKey="revenue" fill="#0ABAB5" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[350px] flex items-center justify-center text-slate-400 dark:text-slate-500">Aucune vente enregistrée</div>
              )}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg text-slate-900 dark:text-white">Répartition par catégorie</CardTitle>
              <PieChart className="w-5 h-5 text-slate-400" />
            </CardHeader>
            <CardContent>
              {categories.length > 0 ? (
                <div className="flex items-center">
                  <ResponsiveContainer width="60%" height={300}>
                    <RPieChart>
                      <Pie data={categories} cx="50%" cy="50%" outerRadius={100} dataKey="revenue" nameKey="name" label={false}>
                        {categories.map((_: any, idx: number) => <Cell key={idx} fill={COLORS[idx % COLORS.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v: number) => [formatFCFA(v), "CA"]} contentStyle={{ backgroundColor: theme === "dark" ? "#1e293b" : "#fff", border: "none", borderRadius: "8px", color: theme === "dark" ? "#fff" : "#000" }} />
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
                <div className="h-[300px] flex items-center justify-center text-slate-400 dark:text-slate-500">Aucune vente enregistrée</div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

/** Petite carte KPI réutilisable */
function KpiCard({
  title,
  value,
  icon,
  bg,
  color,
}: {
  title: string;
  value: string | number;
  icon: ReactNode;
  bg: string;
  color: string;
}) {
  return (
    <Card className={`border-0 shadow-md bg-gradient-to-br ${bg} dark:bg-none dark:bg-slate-800 dark:border-slate-700`}>
      <CardContent className="p-4 flex items-center gap-3">
        <div className={`p-2 rounded-full bg-white dark:bg-white/10 ${color}`}>
          {icon}
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{title}</p>
          <p className="text-xl font-bold text-slate-800 dark:text-white">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}