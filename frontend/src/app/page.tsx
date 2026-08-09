"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, DollarSign, ShoppingCart, Package, AlertTriangle, Brain, CloudRain, LogOut, Pill, BarChart3  } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [kpi, setKpi] = useState<any>(null);
  const [season, setSeason] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = api.getToken();
    if (!token) { router.push("/login"); return; }
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiData, seasonData] = await Promise.all([
        api.getDashboardKPIs(),
        api.getSeasonalAnalysis().catch(() => null),
      ]);
      setKpi(kpiData);
      setSeason(seasonData);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleLogout = () => { localStorage.removeItem("auth_token"); router.push("/login"); };
  const formatFCFA = (v: number) => v ? new Intl.NumberFormat('fr-FR').format(v) + ' FCFA' : '-';

  
  const navItems = [
  { label: "Dashboard", href: "/", icon: TrendingUp },
  { label: "Médicaments", href: "/medicines", icon: Pill },
  { label: "Stocks", href: "/inventory", icon: Package },
  { label: "Ventes", href: "/sales", icon: ShoppingCart },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Chat IA", href: "/ai/chat", icon: Brain },
  ];
  if (loading) return <div className="p-8"><Skeleton className="h-8 w-64 mb-4" /><div className="grid grid-cols-4 gap-4">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div></div>;

  const cards = [
    { title: "CA Aujourd'hui", value: formatFCFA(kpi?.ca_today), evolution: kpi?.ca_today_evolution, icon: DollarSign, color: "text-green-400" },
    { title: "CA Semaine", value: formatFCFA(kpi?.ca_week), evolution: kpi?.ca_week_evolution, icon: TrendingUp, color: "text-blue-400" },
    { title: "CA Mois", value: formatFCFA(kpi?.ca_month), icon: TrendingUp, color: "text-purple-400" },
    { title: "Ventes Aujourd'hui", value: kpi?.sales_today ?? "-", icon: ShoppingCart, color: "text-indigo-400" },
    { title: "Valeur Stock", value: formatFCFA(kpi?.stock_value), icon: Package, color: "text-emerald-400" },
    { title: "Ruptures", value: kpi?.out_of_stock ?? "-", icon: AlertTriangle, color: kpi?.out_of_stock > 0 ? "text-red-400" : "text-green-400" },
    { title: "Stock Faible", value: kpi?.low_stock ?? "-", icon: AlertTriangle, color: "text-yellow-400" },
    { title: "Profit Estimé", value: formatFCFA(kpi?.estimated_profit), icon: DollarSign, color: "text-teal-400" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-[#0F1A2C] text-white min-h-screen p-6 space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#0ABAB5] rounded-lg flex items-center justify-center font-bold text-xl">D</div>
          <div><h1 className="font-bold">DENG PHARMA</h1><p className="text-xs text-gray-400">v2.0</p></div>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <button key={item.href} onClick={() => router.push(item.href)} className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left text-gray-300 hover:bg-white/10 hover:text-white transition-all">
              <item.icon className="w-5 h-5" /> {item.label}
            </button>
          ))}
        </nav>
        <Button variant="ghost" onClick={handleLogout} className="w-full text-gray-400 hover:text-white"><LogOut className="w-4 h-4 mr-2" /> Déconnexion</Button>
      </div>

      {/* Main */}
      <div className="flex-1 p-8 space-y-6">
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>

        {season && (
          <Card className="border-0 bg-gradient-to-r from-blue-50 to-cyan-50 shadow-md">
            <CardContent className="flex items-center gap-4 py-4">
              <CloudRain className="w-8 h-8 text-blue-500" />
              <div className="flex-1"><p className="font-semibold">{season.season}</p><div className="flex gap-2 mt-1 flex-wrap">{season.alerts?.map((a: string, i: number) => <Badge key={i} variant="secondary" className="text-xs">{a}</Badge>)}</div></div>
              <Brain className="w-6 h-6 text-[#0ABAB5]" />
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map((card, i) => (
            <Card key={i} className="hover:shadow-lg transition-all border-0 shadow-md hover:-translate-y-1">
              <CardHeader className="flex flex-row items-center justify-between pb-2"><CardTitle className="text-sm text-slate-500">{card.title}</CardTitle><card.icon className={`w-5 h-5 ${card.color}`} /></CardHeader>
              <CardContent><div className="text-2xl font-bold text-slate-800">{card.value}</div>{card.evolution !== undefined && card.evolution !== null && <div className="flex items-center gap-1 mt-1">{card.evolution > 0 ? <TrendingUp className="w-4 h-4 text-green-500" /> : <TrendingDown className="w-4 h-4 text-red-500" />}<span className={card.evolution > 0 ? "text-green-500 text-sm" : "text-red-500 text-sm"}>{card.evolution > 0 ? "+" : ""}{card.evolution}%</span></div>}</CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
