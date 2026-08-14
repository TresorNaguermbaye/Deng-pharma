"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Search, Bell, Menu, X
} from "lucide-react";

export function Topbar() {
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    loadUnread();
    const interval = setInterval(loadUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUnread = async () => {
    try {
      const data = await api.getNotifications();
      setUnreadCount(data.unread_count || 0);
    } catch (err) {}
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

  return (
    <header className="h-16 bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 lg:px-6">
      {/* Logo + Menu mobile */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <span className="font-bold text-slate-800 hidden sm:block">DENG PHARMA</span>
        </div>
      </div>

      {/* Barre de recherche globale */}
      <div className="flex-1 max-w-xl mx-4 relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Rechercher un médicament, client..."
            value={searchTerm}
            onChange={(e) => handleGlobalSearch(e.target.value)}
            className="pl-10 bg-gray-50 border-gray-200 focus:bg-white"
          />
        </div>
        {/* Résultats de recherche */}
        {showSearch && searchResults.length > 0 && (
          <div className="absolute top-full mt-1 left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
            {searchResults.map((med: any) => (
              <div
                key={med.id}
                className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-0 flex items-center justify-between"
                onClick={() => {
                  router.push(`/medicines/${med.id}`);
                  setShowSearch(false);
                  setSearchTerm("");
                }}
              >
                <div>
                  <p className="font-medium text-sm">{med.commercial_name}</p>
                  <p className="text-xs text-slate-500">{med.dci}</p>
                </div>
                <span className="text-sm font-semibold text-[#0ABAB5]">{med.selling_price?.toLocaleString()} FCFA</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notifications + Profil */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="relative"
          onClick={() => router.push("/notifications")}
        >
          <Bell className="w-5 h-5 text-slate-600" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </Button>
        <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center text-sm font-bold text-slate-600">
          A
        </div>
      </div>
    </header>
  );
}
