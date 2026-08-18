"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Pill, Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/auth/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      
      const data = await response.json();
      console.log("Réponse login:", data);
      
      if (data.access) {
        localStorage.setItem('auth_token', data.access);
        console.log("Token sauvegardé:", data.access.substring(0, 20) + "...");
        router.push("/");
      } else {
        setError("Identifiants incorrects. Détail: " + JSON.stringify(data));
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
            <div className="w-16 h-16 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Pill className="w-8 h-8 text-white" />
            </div>
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