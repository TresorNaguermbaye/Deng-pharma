"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import FloatingChat from "./FloatingChat";

// Pages publiques où on NE veut PAS le chat flottant
const EXCLUDED_PATHS = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/onboarding",
];

export default function FloatingChatWrapper() {
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Vérifie le token (côté client uniquement)
  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    setIsAuthenticated(!!token);
  }, [pathname]);

  // Vérifie si la page est exclue
  const isExcluded = EXCLUDED_PATHS.some(
    (path) => pathname === path || pathname.startsWith(path + "/")
  );

  // Ne pas afficher si : page exclue OU pas authentifié
  if (isExcluded || !isAuthenticated) return null;

  return <FloatingChat />;
}