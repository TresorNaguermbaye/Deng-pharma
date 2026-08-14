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
          <Sidebar />
          <main className="flex-1 ml-64 p-6">{children}</main>
        </div>
      </div>
    </DashboardProvider>
  );
}
