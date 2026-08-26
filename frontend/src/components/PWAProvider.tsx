"use client";

import { useEffect } from "react";
import { registerServiceWorker } from "@/lib/registerSW";

export default function PWAProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    registerServiceWorker();
  }, []);

  return <>{children}</>;
}