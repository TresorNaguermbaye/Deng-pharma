"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Check, ArrowRight, ArrowLeft, Hand, LayoutDashboard, Package, Brain, Loader2
} from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const totalSteps = 4;

  // Protection de route : vérifier l'authentification et l'état d'onboarding
  useEffect(() => {
    let isMounted = true;
    async function checkAccess() {
      const token = api.getToken();
      if (!token) {
        router.push("/login");
        return;
      }
      try {
        const me = await api.getMe();
        if (isMounted && me.has_completed_onboarding) {
          router.push("/");
        }
      } catch (err) {
        console.error("Erreur vérification onboarding", err);
        router.push("/login");
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    checkAccess();
    return () => { isMounted = false; };
  }, [router]);

  const handleComplete = async () => {
    try {
      await api.completeOnboarding();
      router.push("/");
    } catch (error) {
      console.error("Erreur lors de la complétion", error);
    }
  };

  const steps = [
    {
      icon: Hand,
      title: "Bienvenue chez DENG PHARMA",
      description: "Votre pharmacie intelligente est prête. Découvrons ensemble ses fonctionnalités.",
    },
    {
      icon: LayoutDashboard,
      title: "Tableau de bord",
      description: "Suivez vos ventes, stocks et alertes en temps réel.",
    },
    {
      icon: Package,
      title: "Gestion des stocks",
      description: "Recevez des alertes de rupture et d'expiration, et optimisez vos commandes.",
    },
    {
      icon: Brain,
      title: "IA et prédictions",
      description: "Profitez des prévisions de ventes et des recommandations intelligentes de réapprovisionnement.",
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-[#0F1A2C]">
        <Loader2 className="w-10 h-10 text-[#0ABAB5] animate-spin" />
      </div>
    );
  }

  const CurrentIcon = steps[step].icon;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-[#0F1A2C] p-4">
      <Card className="w-full max-w-md border-0 shadow-2xl bg-white dark:bg-slate-800 rounded-2xl overflow-hidden">
        <CardHeader className="text-center pb-0">
          <div className="w-20 h-20 mx-auto bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-2xl flex items-center justify-center shadow-lg mb-4">
            <CurrentIcon className="w-10 h-10 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold text-slate-800 dark:text-white">
            {steps[step].title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 p-6">
          <Progress value={(step / (totalSteps - 1)) * 100} className="h-2" />
          <p className="text-slate-600 dark:text-slate-300 text-center leading-relaxed">
            {steps[step].description}
          </p>
          <div className="flex justify-between items-center">
            {step > 0 ? (
              <Button
                variant="outline"
                onClick={() => setStep(step - 1)}
                className="dark:border-slate-600 dark:text-slate-300"
              >
                <ArrowLeft className="w-4 h-4 mr-2" /> Précédent
              </Button>
            ) : (
              <span />
            )}
            {step < totalSteps - 1 ? (
              <Button onClick={() => setStep(step + 1)} className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
                Suivant <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button onClick={handleComplete} className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
                Commencer <Check className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}