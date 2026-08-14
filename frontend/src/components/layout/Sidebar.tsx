"use client";

import { useRouter, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  TrendingUp, Pill, Package, ShoppingCart, BarChart3,
  Brain, Users, Bell, LogOut
} from "lucide-react";

const navItems = [
  { label: "Dashboard", href: "/", icon: TrendingUp },
  { label: "Médicaments", href: "/medicines", icon: Pill },
  { label: "Stocks", href: "/inventory", icon: Package },
  { label: "Ventes", href: "/sales", icon: ShoppingCart },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Chat IA", href: "/ai/chat", icon: Brain },
  { label: "IA Prédictions", href: "/ai/predictions", icon: Brain },
  { label: "Notifications", href: "/notifications", icon: Bell },
  
  { label: "Utilisateurs", href: "/admin/users", icon: Users },
];

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-[#0F1A2C] text-white fixed left-0 top-16 bottom-0 z-30 hidden lg:flex flex-col">
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={cn(
                "flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left text-sm font-medium transition-all",
                isActive
                  ? "bg-[#0ABAB5] text-white shadow-lg shadow-[#0ABAB5]/25"
                  : "text-gray-300 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-700">
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="w-full text-gray-400 hover:text-white justify-start"
        >
          <LogOut className="w-4 h-4 mr-2" /> Déconnexion
        </Button>
      </div>
    </aside>
  );
}
