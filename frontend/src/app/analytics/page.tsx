"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, DollarSign, ShoppingCart, Package, AlertTriangle, BarChart3 } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function AnalyticsPage() {
  const router = useRouter();
  const [kpi, setKpi] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!api.getToken()) { router.push("/login"); return; }
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.getDashboardKPIs();
      setKpi(data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const formatFCFA = (v: number) => v ? new Intl.NumberFormat('fr-FR').format(v) + ' FCFA' : '0 FCFA';

  // Données simulées pour les graphiques
  const weeklyData = [
    { day: "Lun", sales: 450000, orders: 34 },
    { day: "Mar", sales: 380000, orders: 28 },
    { day: "Mer", sales: 520000, orders: 42 },
    { day: "Jeu", sales: 410000, orders: 31 },
    { day: "Ven", sales: 480000, orders: 38 },
    { day: "Sam", sales: 220000, orders: 15 },
    { day: "Dim", sales: 150000, orders: 10 },
  ];

  const categoryData = [
    { name: "Antalgique", value: 35, color: "#0ABAB5" },
    { name: "Antibiotique", value: 25, color: "#3B82F6" },
    { name: "Antipaludéen", value: 20, color: "#8B5CF6" },
    { name: "Réhydratation", value: 12, color: "#F59E0B" },
    { name: "Autres", value: 8, color: "#EF4444" },
  ];

  const monthlyTrend = [
    { month: "Jan", revenue: 12500000 },
    { month: "Fév", revenue: 11800000 },
    { month: "Mar", revenue: 13200000 },
    { month: "Avr", revenue: 14100000 },
    { month: "Mai", revenue: 13800000 },
    { month: "Juin", revenue: 15200000 },
    { month: "Juil", revenue: 16800000 },
    { month: "Aoû", revenue: 17500000 },
  ];

  if (loading) return <div className="p-8"><Skeleton className="h-96 w-full rounded-xl" /></div>;

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Analytics</h1>
        <p className="text-slate-500 mt-1">Analysez vos performances et tendances</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-0 shadow-md bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="py-4 flex items-center gap-3">
            <DollarSign className="w-8 h-8 text-green-500" />
            <div><p className="text-sm text-slate-500">CA Mensuel</p><p className="text-xl font-bold">{formatFCFA(kpi?.ca_month || 0)}</p></div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-blue-50 to-cyan-50">
          <CardContent className="py-4 flex items-center gap-3">
            <ShoppingCart className="w-8 h-8 text-blue-500" />
            <div><p className="text-sm text-slate-500">Ventes Aujourd'hui</p><p className="text-xl font-bold">{kpi?.sales_today || 0}</p></div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-purple-50 to-violet-50">
          <CardContent className="py-4 flex items-center gap-3">
            <Package className="w-8 h-8 text-purple-500" />
            <div><p className="text-sm text-slate-500">Valeur Stock</p><p className="text-xl font-bold">{formatFCFA(kpi?.stock_value || 0)}</p></div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-yellow-50 to-amber-50">
          <CardContent className="py-4 flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-yellow-500" />
            <div><p className="text-sm text-slate-500">Profit Estimé</p><p className="text-xl font-bold">{formatFCFA(kpi?.estimated_profit || 0)}</p></div>
          </CardContent>
        </Card>
      </div>

      {/* Graphiques */}
      <Tabs defaultValue="revenue">
        <TabsList>
          <TabsTrigger value="revenue"><TrendingUp className="w-4 h-4 mr-2" />Chiffre d'Affaires</TabsTrigger>
          <TabsTrigger value="sales"><ShoppingCart className="w-4 h-4 mr-2" />Ventes</TabsTrigger>
          <TabsTrigger value="categories"><BarChart3 className="w-4 h-4 mr-2" />Catégories</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="mt-4">
          <Card className="border-0 shadow-md">
            <CardHeader><CardTitle>Évolution du CA Mensuel</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={monthlyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(v) => (v/1000000).toFixed(0) + 'M'} />
                  <Tooltip formatter={(v: number) => [formatFCFA(v), "CA"]} />
                  <Bar dataKey="revenue" fill="#0ABAB5" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sales" className="mt-4">
          <Card className="border-0 shadow-md">
            <CardHeader><CardTitle>Ventes de la Semaine</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="day" />
                  <YAxis yAxisId="left" tickFormatter={(v) => (v/1000).toFixed(0) + 'k'} />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Line yAxisId="left" type="monotone" dataKey="sales" stroke="#0ABAB5" strokeWidth={3} dot={{ fill: '#0ABAB5', r: 6 }} name="CA (FCFA)" />
                  <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#8B5CF6" strokeWidth={3} dot={{ fill: '#8B5CF6', r: 6 }} name="Commandes" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-0 shadow-md">
              <CardHeader><CardTitle>Ventes par Catégorie</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <PieChart>
                    <Pie data={categoryData} cx="50%" cy="50%" outerRadius={120} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {categoryData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card className="border-0 shadow-md">
              <CardHeader><CardTitle>Répartition</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {categoryData.map((cat) => (
                  <div key={cat.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }} />
                      <span className="text-sm">{cat.name}</span>
                    </div>
                    <span className="font-semibold">{cat.value}%</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
