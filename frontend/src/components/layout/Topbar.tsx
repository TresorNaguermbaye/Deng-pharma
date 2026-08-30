"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import GlobalSearch from "@/components/GlobalSearch";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Search, Bell, Menu, Sun, Moon, RefreshCw, Settings, LogOut,
} from "lucide-react";
import Logo from "../logo";

interface TopbarProps {
  onMenuClick?: () => void;
  onRefresh?: () => void;
}

export function Topbar({ onMenuClick, onRefresh }: TopbarProps) {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

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

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  return (
    <header className="h-16 md:h-28 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-2 md:px-4 lg:px-6">
      {/* Partie gauche : logo seul (sans hamburger) */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-3">
          <Logo className="w-15 h-15 md:w-30 md:h-30 rounded-xl object-cover" />
        </div>
      </div>

      {/* Partie droite : recherche + icônes + hamburger */}
      <div className="flex items-center gap-1 md:gap-2">
        {/* Bouton de recherche globale (masqué sur mobile) */}
        <button
          onClick={() => window.dispatchEvent(new Event('open-global-search'))}
          className="hidden md:flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition"
        >
          <Search className="w-4 h-4" />
          <span>Recherche globale...</span>
          <kbd className="ml-auto text-xs bg-white dark:bg-slate-800 px-2 py-0.5 rounded">Ctrl K</kbd>
        </button>

        {/* Notifications */}
        <Button
          variant="ghost"
          size="sm"
          className="relative p-1 md:p-2"
          onClick={() => router.push("/notifications")}
        >
          <Bell className="w-5 h-5 text-slate-600 dark:text-slate-300" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 md:w-5 md:h-5 flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </Button>

        {/* Actualiser */}
        {onRefresh && (
          <Button variant="ghost" size="sm" className="p-1 md:p-2" onClick={onRefresh}>
            <RefreshCw className="w-5 h-5 text-slate-600 dark:text-slate-300" />
          </Button>
        )}

        {/* Mode sombre */}
        {mounted && (
          <Button
            variant="ghost"
            size="sm"
            className="p-1 md:p-2"
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
            <button className="w-7 h-7 md:w-8 md:h-8 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center text-xs md:text-sm font-bold text-slate-600 dark:text-slate-300">
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

        {/* Hamburger à l'extrême droite, visible uniquement sur mobile */}
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden p-1 md:p-2"
          onClick={() => onMenuClick && onMenuClick()}
        >
          <Menu className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}