"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { DashboardProvider } from "@/context/DashboardContext";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      router.push("/login");
    } else {
      setAuthenticated(true);
    }
  }, []);

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-400">Vérification de l'authentification...</p>
      </div>
    );
  }

return (
  <DashboardProvider>
    <div className="min-h-screen bg-slate-50">
      <Topbar />
      <div className="flex pt-16">
        {/* La sidebar est masquée sur mobile grâce à hidden lg:block */}
        <div className="hidden lg:block">
          <Sidebar />
        </div>
        <main className="flex-1 ml-0 lg:ml-64 p-0 md:p-6">{children}</main>
      </div>
    </div>
  </DashboardProvider>
);
}
