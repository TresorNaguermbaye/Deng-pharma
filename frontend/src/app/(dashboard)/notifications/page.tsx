"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Bell, CheckCheck, AlertTriangle, Package, Clock, Brain, TrendingUp, Pill, ShoppingCart,
  FileBarChart, BarChart3, Users, Menu, X, LayoutDashboard, LogOut
} from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function NotificationsPage() {
  const router = useRouter();
  const [notifs, setNotifs] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => { loadNotifs(); }, []);

  const loadNotifs = async () => {
    try {
      const data = await api.getNotifications();
      setNotifs(data.notifications || []);
      setUnread(data.unread_count || 0);
    } catch (err) {
      console.error("Erreur chargement notifications:", err);
    }
  };

  const markAllRead = async () => {
    await api.markAllNotificationsRead();
    loadNotifs();
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  const typeIcon = (type: string) => {
    switch (type) {
      case "STOCK_OUT": return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case "STOCK_LOW": return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "EXPIRY_SOON": return <Clock className="w-5 h-5 text-orange-500" />;
      case "OVERSTOCK": return <Package className="w-5 h-5 text-blue-500" />;
      case "AI_PREDICTION": return <Brain className="w-5 h-5 text-purple-500" />;
      default: return <Bell className="w-5 h-5 text-slate-500" />;
    }
  };

  const typeLabel = (type: string) => {
    const labels: Record<string, string> = {
      STOCK_OUT: "Rupture", STOCK_LOW: "Stock faible", EXPIRY_SOON: "Expiration",
      OVERSTOCK: "Surstock", AI_PREDICTION: "IA", TRAINING_COMPLETE: "IA"
    };
    return labels[type] || type;
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
                    item.href === "/notifications" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
              Notifications
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">{unread} non lue(s)</p>
          </div>
          {unread > 0 && (
            <Button
              variant="outline"
              onClick={markAllRead}
              className="dark:border-slate-600 dark:text-slate-300 w-full sm:w-auto"
            >
              <CheckCheck className="w-4 h-4 mr-2" /> Tout marquer comme lu
            </Button>
          )}
        </div>

        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="p-0">
            {notifs.length === 0 ? (
              <p className="text-center text-slate-400 dark:text-slate-500 py-12">Aucune notification</p>
            ) : (
              notifs.map((n: any) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-4 p-4 border-b last:border-0 ${
                    n.is_read
                      ? "bg-white dark:bg-slate-800"
                      : "bg-blue-50 dark:bg-slate-700/50"
                  }`}
                >
                  {typeIcon(n.type)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Badge className="text-xs dark:bg-slate-600 dark:text-slate-200">
                        {typeLabel(n.type)}
                      </Badge>
                      {!n.is_read && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
                    </div>
                    <p className="text-sm mt-1 text-slate-900 dark:text-white">{n.message}</p>
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                      {new Date(n.created_at).toLocaleString('fr-FR')}
                    </p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}