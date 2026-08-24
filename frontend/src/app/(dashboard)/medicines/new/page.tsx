"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  ArrowLeft, Save,
  Menu, X, LayoutDashboard, Pill, Package, ShoppingCart,
  FileBarChart, BarChart3, Brain, Bell, Users, LogOut, TrendingUp
} from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function NewMedicinePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<any[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [form, setForm] = useState({
    commercial_name: "",
    dci: "",
    barcode: "",
    category: "",
    manufacturer: "",
    purchase_price: "",
    selling_price: "",
    location: "",
    min_stock: "10",
    max_stock: "100",
  });

  useEffect(() => {
    api.getCategories().then(data => {
      setCategories(data.results || data || []);
    }).catch(console.error);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createMedicine({
        ...form,
        purchase_price: parseFloat(form.purchase_price) || 0,
        selling_price: parseFloat(form.selling_price) || 0,
        min_stock: parseInt(form.min_stock) || 10,
        max_stock: parseInt(form.max_stock) || 100,
        category: form.category || null,
      });
      router.push("/medicines");
    } catch (err) {
      console.error("Erreur création:", err);
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
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
                    item.href === "/medicines/new" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
      <main className="pt-20 lg:pl-64 p-4 md:p-8">
        <div className="max-w-2xl mx-auto space-y-6">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Retour
          </Button>

          <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="text-2xl text-slate-900 dark:text-white">Nouveau médicament</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Nom commercial *</Label>
                    <Input required value={form.commercial_name} onChange={e => updateField("commercial_name", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">DCI *</Label>
                    <Input required value={form.dci} onChange={e => updateField("dci", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Code-barres *</Label>
                    <Input required value={form.barcode} onChange={e => updateField("barcode", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Fabricant</Label>
                    <Input value={form.manufacturer} onChange={e => updateField("manufacturer", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-slate-500 dark:text-slate-400">Catégorie</Label>
                  <Select value={form.category} onValueChange={(value) => updateField("category", value)}>
                    <SelectTrigger className="dark:bg-slate-700 dark:text-white dark:border-slate-600">
                      <SelectValue placeholder="Sélectionner une catégorie..." />
                    </SelectTrigger>
                    <SelectContent className="dark:bg-slate-800 dark:border-slate-700">
                      {categories.map((cat: any) => (
                        <SelectItem key={cat.id} value={cat.id.toString()}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Prix d'achat (FCFA)</Label>
                    <Input type="number" value={form.purchase_price} onChange={e => updateField("purchase_price", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Prix de vente (FCFA) *</Label>
                    <Input type="number" required value={form.selling_price} onChange={e => updateField("selling_price", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-slate-500 dark:text-slate-400">Emplacement</Label>
                  <Input value={form.location} onChange={e => updateField("location", e.target.value)} placeholder="Rayon A1" className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Stock minimum</Label>
                    <Input type="number" value={form.min_stock} onChange={e => updateField("min_stock", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-500 dark:text-slate-400">Stock maximum</Label>
                    <Input type="number" value={form.max_stock} onChange={e => updateField("max_stock", e.target.value)} className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button type="submit" disabled={loading} className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
                    <Save className="w-4 h-4 mr-2" />
                    {loading ? "Enregistrement..." : "Enregistrer"}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => router.back()} className="dark:border-slate-600 dark:text-slate-300">Annuler</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}