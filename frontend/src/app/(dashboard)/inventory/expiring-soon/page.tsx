"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Menu, X, LayoutDashboard, Pill, Package, ShoppingCart,
  FileBarChart, BarChart3, Brain, Bell, Users, LogOut, TrendingUp
} from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function ExpiringSoonPage() {
  const router = useRouter();
  const [lots, setLots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    api.getExpiringSoon()
      .then(data => {
        setLots(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erreur chargement expirations:", err);
        setLoading(false);
      });
  }, []);

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
                    item.href === "/inventory/expiring-soon" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
          Expirations proches (90 jours)
        </h1>
        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">
              {lots.length} lot(s) concerné(s)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 dark:bg-slate-700" />
            ) : (
              <Table className="w-full table-fixed">
                <TableHeader>
                  <TableRow className="border-slate-200 dark:border-slate-700">
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/4">Médicament</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/5">Lot</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/6">Quantité</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/5">Expire le</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/6">Jours restants</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lots.map((lot: any) => (
                    <TableRow
                      key={lot.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700"
                    >
                      <TableCell className="font-medium text-slate-900 dark:text-white truncate text-xs sm:text-sm">
                        {lot.medicine}
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
                        {lot.batch}
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
                        {lot.quantity}
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
                        {new Date(lot.expiry_date).toLocaleDateString('fr-FR')}
                      </TableCell>
                      <TableCell>
                        <Badge variant={lot.days_left < 30 ? "destructive" : "secondary"} className="text-xs">
                          {lot.days_left} jours
                        </Badge>
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