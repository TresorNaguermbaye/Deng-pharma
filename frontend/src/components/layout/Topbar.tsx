"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Search, Bell, Menu, X, Sun, Moon, RefreshCw, Settings, LogOut,
} from "lucide-react";

interface TopbarProps {
  onMenuClick?: () => void;   // Pour ouvrir la sidebar mobile depuis le parent
  onRefresh?: () => void;     // Pour rafraîchir les données de la page
}

export function Topbar({ onMenuClick, onRefresh }: TopbarProps) {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearch, setShowSearch] = useState(false);

  // Éviter l'hydratation pour le toggle de thème
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    loadUnread();
    const interval = setInterval(loadUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUnread = async () => {
    try {
      const data = await api.getNotifications();
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      // silencieux
    }
  };

  const handleGlobalSearch = async (value: string) => {
    setSearchTerm(value);
    if (value.length < 2) {
      setSearchResults([]);
      setShowSearch(false);
      return;
    }
    try {
      const data = await api.getMedicines({ search: value });
      setSearchResults(data.results?.slice(0, 5) || []);
      setShowSearch(true);
    } catch (err) {
      setSearchResults([]);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  return (
    <header className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 lg:px-6">
      {/* Logo + Menu mobile */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden"
          onClick={() => onMenuClick && onMenuClick()}
        >
          <Menu className="w-5 h-5" />
        </Button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <span className="font-bold text-slate-800 dark:text-white hidden sm:block">
            DENG PHARMA
          </span>
        </div>
      </div>

      {/* Barre de recherche globale (masquée sur mobile) */}
      <div className="hidden md:block flex-1 max-w-xl mx-4 relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Rechercher un médicament, client..."
            value={searchTerm}
            onChange={(e) => handleGlobalSearch(e.target.value)}
            className="pl-10 bg-slate-50 dark:bg-slate-700 dark:text-white border-slate-200 dark:border-slate-600 focus:bg-white dark:focus:bg-slate-600"
          />
        </div>
        {/* Résultats de recherche */}
        {showSearch && searchResults.length > 0 && (
          <div className="absolute top-full mt-1 left-0 right-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50">
            {searchResults.map((med: any) => (
              <div
                key={med.id}
                className="p-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b last:border-0 flex items-center justify-between"
                onClick={() => {
                  router.push(`/medicines/${med.id}`);
                  setShowSearch(false);
                  setSearchTerm("");
                }}
              >
                <div>
                  <p className="font-medium text-sm text-slate-800 dark:text-white">{med.commercial_name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{med.dci}</p>
                </div>
                <span className="text-sm font-semibold text-[#0ABAB5]">
                  {med.selling_price?.toLocaleString()} FCFA
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notifications + Actualiser + Mode sombre + Profil */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="relative"
          onClick={() => router.push("/notifications")}
        >
          <Bell className="w-5 h-5 text-slate-600 dark:text-slate-300" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </Button>

        {/* Bouton d'actualisation */}
        {onRefresh && (
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            <RefreshCw className="w-5 h-5 text-slate-600 dark:text-slate-300" />
          </Button>
        )}

        {/* Toggle mode sombre */}
        {mounted && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? (
              <Sun className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            ) : (
              <Moon className="w-5 h-5 text-slate-600" />
            )}
          </Button>
        )}

        {/* Menu utilisateur */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center text-sm font-bold text-slate-600 dark:text-slate-300">
              A
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={() => router.push("/settings")}>
              <Settings className="w-4 h-4 mr-2" /> Paramètres
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleLogout} className="text-red-600">
              <LogOut className="w-4 h-4 mr-2" /> Déconnexion
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}