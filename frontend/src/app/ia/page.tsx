"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import {
  Menu, X, LayoutDashboard, Pill, Package, ShoppingCart,
  FileBarChart, BarChart3, Brain, Bell, Users, LogOut, TrendingUp
} from "lucide-react";

export default function IADashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [medicines, setMedicines] = useState<any[]>([]);
  const [selectedMedicine, setSelectedMedicine] = useState<string>("");
  const [predictionData, setPredictionData] = useState<any>(null);
  const [stockAnalysis, setStockAnalysis] = useState<any>(null);
  const [orderRecommendation, setOrderRecommendation] = useState<any>(null);
  const [seasonalData, setSeasonalData] = useState<any>(null);
  const [criticality, setCriticality] = useState<any>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Charger la liste des médicaments
  useEffect(() => {
    api.getMedicines()
      .then((data: any) => setMedicines(data.results || data))
      .catch(console.error);
  }, []);

  // Charger l'analyse saisonnière globale
  useEffect(() => {
    api.getIASeasonalAnalysis()
      .then((data: any) => setSeasonalData(data))
      .catch(console.error);
  }, []);

  // Charger les données IA pour le médicament sélectionné
  useEffect(() => {
    if (!selectedMedicine) return;
    const med = medicines.find((m) => m.id === selectedMedicine);
    if (!med) return;

    // Prédictions
    api.getIAPredict(med.id, 7)
      .then((data: any) => setPredictionData(data))
      .catch(console.error);

    // Analyse de stock : il faut d'abord obtenir le stock actuel du médicament
    api.getMedicines({ medicine: med.id })
      .then(async (medicinesData: any) => {
        const totalStock = med.stock_total || 0;
        const stockAnalysisData = await api.getIAStockAnalysis(med.id, totalStock);
        setStockAnalysis(stockAnalysisData);

        const orderRecData = await api.getIAOrderRecommendation(med.id, totalStock);
        setOrderRecommendation(orderRecData);
      })
      .catch(console.error);

    // Criticité
    api.getIACriticality(med.id)
      .then((data: any) => setCriticality(data))
      .catch(console.error);
  }, [selectedMedicine, medicines]);

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
                    item.href === "/ai/predictions" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
      <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-6">
        <div className="container mx-auto space-y-6">
          <h1 className="text-3xl font-bold">Dashboard IA</h1>
          <p className="text-muted-foreground">
            Prévisions, analyse de stock et recommandations intelligentes.
          </p>

          {/* Sélecteur de médicament */}
          <select
            className="w-full md:w-1/3 p-2 border rounded-md dark:bg-slate-700 dark:text-white dark:border-slate-600"
            onChange={(e) => setSelectedMedicine(e.target.value)}
            value={selectedMedicine}
          >
            <option value="" disabled>Sélectionner un médicament</option>
            {medicines.map((med) => (
              <option key={med.id} value={med.id}>
                {med.commercial_name}
              </option>
            ))}
          </select>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Carte de prédiction */}
            <Card>
              <CardHeader>
                <CardTitle>Prévision des ventes (7 jours)</CardTitle>
                <CardDescription>Prévisions issues du service IA</CardDescription>
              </CardHeader>
              <CardContent>
                {predictionData ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={predictionData.predictions || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="predicted_sales" stroke="#0ABAB5" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-muted-foreground">Sélectionnez un médicament.</p>
                )}
              </CardContent>
            </Card>

            {/* Analyse de stock */}
            <Card>
              <CardHeader>
                <CardTitle>Analyse de stock</CardTitle>
                <CardDescription>Risque de rupture ou surstock</CardDescription>
              </CardHeader>
              <CardContent>
                {stockAnalysis ? (
                  <div className="space-y-2">
                    <p>Statut : {stockAnalysis.status || "N/A"}</p>
                    <p>Recommandation : {stockAnalysis.recommendation || "Aucune"}</p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Sélectionnez un médicament.</p>
                )}
              </CardContent>
            </Card>

            {/* Recommandation de commande */}
            <Card>
              <CardHeader>
                <CardTitle>Recommandation de commande</CardTitle>
                <CardDescription>Quantité suggérée à commander</CardDescription>
              </CardHeader>
              <CardContent>
                {orderRecommendation ? (
                  <div className="space-y-2">
                    <p>Quantité recommandée : {orderRecommendation.quantity_to_order || "N/A"}</p>
                    <p>Délai de livraison : {orderRecommendation.lead_time_days || "N/A"} jours</p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Sélectionnez un médicament.</p>
                )}
              </CardContent>
            </Card>

            {/* Criticité */}
            <Card>
              <CardHeader>
                <CardTitle>Score de criticité</CardTitle>
                <CardDescription>Importance du médicament</CardDescription>
              </CardHeader>
              <CardContent>
                {criticality ? (
                  <div className="space-y-2">
                    <p>Score : {criticality.score || "N/A"}</p>
                    <p>Catégorie : {criticality.category || "N/A"}</p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Sélectionnez un médicament.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Analyse saisonnière */}
          <Card>
            <CardHeader>
              <CardTitle>Analyse saisonnière</CardTitle>
              <CardDescription>Tendances globales</CardDescription>
            </CardHeader>
            <CardContent>
              {seasonalData ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={seasonalData.seasonal_factors || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="factor" fill="#0F1A2C" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-muted-foreground">Chargement...</p>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}