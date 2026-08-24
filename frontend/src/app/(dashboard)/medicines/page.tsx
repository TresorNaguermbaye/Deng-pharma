"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import {
  Search, Plus, MoreHorizontal, Eye, Edit, Trash2,
  Menu, X, Pill, LayoutDashboard, ShoppingCart, Package,
  BarChart3, Brain, LogOut,
  TrendingUp,
  Bell,
  FileBarChart,
  Users
} from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function MedicinesPage() {
  const router = useRouter();
  const [medicines, setMedicines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    loadMedicines();
  }, [page, search]);

  const loadMedicines = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: page.toString() };
      if (search) params.search = search;
      const data = await api.getMedicines(params);
      setMedicines(data.results || []);
    } catch (err) {
      console.error("Erreur:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  const formatFCFA = (value: number) => new Intl.NumberFormat('fr-FR').format(value) + ' FCFA';

  // Navigation locale pour la sidebar mobile
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
];;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0ABAB5] mx-auto"></div>
          <p className="text-slate-500 dark:text-slate-400">Chargement des médicaments...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Topbar commune (avec logo et hamburger à droite) */}
      <Topbar
        onMenuClick={() => setMobileMenuOpen(true)}
        onRefresh={loadMedicines}
      />

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
                    item.href === "/medicines" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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

      {/* Contenu principal : aucun espace inutile sur mobile */}
      <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Médicaments</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez votre catalogue</p>
          </div>
          <Button
            className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white shadow-lg shadow-[#0ABAB5]/25 hover:opacity-90 w-full sm:w-auto"
            onClick={() => router.push("/medicines/new")}
          >
            <Plus className="w-4 h-4 mr-2" /> Ajouter un médicament
          </Button>
        </div>

        {/* Recherche */}
        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="py-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Rechercher un médicament..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-slate-50 dark:bg-slate-700 dark:text-white border-slate-200 dark:border-slate-600 focus:bg-white dark:focus:bg-slate-600"
              />
            </div>
          </CardContent>
        </Card>

        {/* Tableau responsive sans scroll horizontal */}
        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">Liste des médicaments</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              [...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2 dark:bg-slate-700" />)
            ) : (
              <Table className="w-full">
                <TableHeader>
                  <TableRow className="border-slate-200 dark:border-slate-700">
                    <TableHead className="text-slate-500 dark:text-slate-400">Nom</TableHead>
                    <TableHead className="hidden md:table-cell text-slate-500 dark:text-slate-400">DCI</TableHead>
                    <TableHead className="hidden md:table-cell text-slate-500 dark:text-slate-400">Catégorie</TableHead>
                    <TableHead className="text-slate-500 dark:text-slate-400">Prix</TableHead>
                    <TableHead className="hidden md:table-cell text-slate-500 dark:text-slate-400">Emplacement</TableHead>
                    <TableHead className="text-slate-500 dark:text-slate-400">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {medicines.map((med) => (
                    <TableRow key={med.id} className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700">
                      <TableCell className="font-medium text-slate-900 dark:text-white">{med.commercial_name}</TableCell>
                      <TableCell className="hidden md:table-cell text-slate-500 dark:text-slate-400">{med.dci}</TableCell>
                      <TableCell className="hidden md:table-cell">
                        <Badge variant="outline" className="dark:text-slate-300 dark:border-slate-600">
                          {med.category_name || "N/A"}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-semibold text-[#0ABAB5]">{formatFCFA(med.selling_price)}</TableCell>
                      <TableCell className="hidden md:table-cell text-slate-500 dark:text-slate-400">{med.location || "-"}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="p-2">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="dark:bg-slate-800 dark:border-slate-700">
                            <DropdownMenuItem onClick={() => router.push(`/medicines/${med.id}`)} className="dark:text-slate-300 dark:hover:bg-slate-700">
                              <Eye className="w-4 h-4 mr-2" /> Voir détails
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => router.push(`/medicines/${med.id}/edit`)} className="dark:text-slate-300 dark:hover:bg-slate-700">
                              <Edit className="w-4 h-4 mr-2" /> Modifier
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-red-600 dark:text-red-400" onClick={async () => {
                              if (confirm("Supprimer ce médicament ?")) {
                                await api.deleteMedicine(med.id);
                                loadMedicines();
                              }
                            }}>
                              <Trash2 className="w-4 h-4 mr-2" /> Supprimer
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}