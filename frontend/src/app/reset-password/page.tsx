"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function ResetPasswordPage() {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  // Extraire uid et token de l'URL
  const queryString = typeof window !== "undefined" ? window.location.search : "";
  const params = new URLSearchParams(queryString);
  const uid = params.get("uid") || "";
  const token = params.get("token") || "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!uid || !token) {
      toast.error("Lien de réinitialisation invalide.");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      const response = await api.confirmPasswordReset(uid, token, newPassword);
      console.log("Réponse backend:", response);
      toast.success("Mot de passe réinitialisé avec succès !");
      setTimeout(() => {
        window.location.href = "/login";
      }, 1500);
    } catch (error: any) {
      console.error("Erreur réinitialisation:", error);
      toast.error(error?.message || "Erreur lors de la réinitialisation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-[#0F1A2C] p-4">
      <Card className="w-full max-w-md border-0 shadow-2xl bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-slate-900 dark:text-white">
            Définir un nouveau mot de passe
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="new_password" className="text-slate-700 dark:text-slate-300">Nouveau mot de passe</Label>
              <Input
                id="new_password"
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600"
                placeholder="Au moins 8 caractères"
              />
            </div>
            <div>
              <Label htmlFor="confirm_password" className="text-slate-700 dark:text-slate-300">Confirmer le mot de passe</Label>
              <Input
                id="confirm_password"
                type="password"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600"
                placeholder="Répéter le mot de passe"
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
              {loading ? "Réinitialisation..." : "Confirmer le nouveau mot de passe"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}