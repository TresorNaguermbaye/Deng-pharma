"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Pill, Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [rememberMe, setRememberMe] = useState(false);
  const [mounted, setMounted] = useState(false); // 👈 nouvel état pour l'hydratation

  // Marquer comme monté côté client
  useEffect(() => {
    setMounted(true);
  }, []);

  // Récupérer le logo de la pharmacie depuis l'API publique
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/auth/pharmacy-logo/')
      .then((res) => res.json())
      .then((data) => setLogoUrl(data.logo_url))
      .catch(() => setLogoUrl(null));
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.login(username, password);

      if (!data.access) {
        setError("Identifiants incorrects. Détail: " + JSON.stringify(data));
        setLoading(false);
        return;
      }

      // Gérer la préférence "Se souvenir de moi"
      if (rememberMe) {
        localStorage.setItem('remember_me', 'true');
      } else {
        localStorage.removeItem('remember_me');
      }

      // Récupérer les informations de l'utilisateur
      const me = await api.getMe();

      // Rediriger selon l'état d'onboarding
      if (me.has_completed_onboarding === false) {
        router.push("/onboarding");
      } else {
        router.push("/");
      }
    } catch (err: any) {
      setError("Erreur: " + err.message);
      console.error("Erreur login:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-[#0F1A2C] p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-[#0ABAB5] rounded-full opacity-10 blur-3xl" />
      </div>

      <Card className="w-full max-w-md border-0 shadow-2xl bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm relative z-10 dark:border dark:border-slate-700">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            {/* Affichage conditionnel pour éviter l'hydratation */}
            {mounted && logoUrl ? (
              <img
                src={logoUrl}
                alt="Logo pharmacie"
                className="w-35 h-35 rounded-2xl object-cover shadow-lg"
              />
            ) : (
              <div className="w-16 h-16 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                <Pill className="w-8 h-8 text-white" />
              </div>
            )}
          </div>
          <CardTitle className="text-2xl font-bold text-slate-800 dark:text-white">DENG PHARMA</CardTitle>
          <CardDescription className="text-slate-500 dark:text-slate-400">Connexion à la plateforme</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-700 dark:text-slate-300">Nom d'utilisateur</Label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="h-12 dark:bg-slate-700 dark:text-white dark:border-slate-600"
                placeholder="Votre nom d'utilisateur"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700 dark:text-slate-300">Mot de passe</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-12 dark:bg-slate-700 dark:text-white dark:border-slate-600"
                placeholder="Votre mot de passe"
              />
            </div>

            {/* Case "Se souvenir de moi" + lien mot de passe oublié */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-300"
                />
                Se souvenir de moi
              </label>
              <Link href="/forgot-password" className="text-sm text-[#0ABAB5] hover:underline">
                Mot de passe oublié ?
              </Link>
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-300 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Connexion...
                </>
              ) : (
                "Se connecter"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}