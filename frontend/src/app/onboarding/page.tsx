"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Check, ArrowRight, ArrowLeft } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const totalSteps = 4;

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
      title: "Bienvenue chez DENG PHARMA",
      description: "Votre pharmacie intelligente est prête. Découvrons ensemble ses fonctionnalités.",
      icon: "👋",
    },
    {
      title: "Tableau de bord",
      description: "Suivez vos ventes, stocks et alertes en temps réel.",
      icon: "📊",
    },
    {
      title: "Gestion des stocks",
      description: "Recevez des alertes de rupture et d'expiration, et optimisez vos commandes.",
      icon: "📦",
    },
    {
      title: "IA et prédictions",
      description: "Profitez des prévisions de ventes et des recommandations intelligentes de Réaprovisionnement.",
      icon: "🤖",
    },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-[#0F1A2C] p-4">
      <Card className="w-full max-w-md border-0 shadow-2xl bg-white dark:bg-slate-800">
        <CardHeader className="text-center">
          <div className="text-4xl mb-4">{steps[step].icon}</div>
          <CardTitle className="text-2xl font-bold text-slate-800 dark:text-white">
            {steps[step].title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <Progress value={(step / (totalSteps - 1)) * 100} className="h-1" />
          <p className="text-slate-600 dark:text-slate-300 text-center">
            {steps[step].description}
          </p>
          <div className="flex justify-between">
            {step > 0 ? (
              <Button variant="outline" onClick={() => setStep(step - 1)}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Précédent
              </Button>
            ) : (
              <span />
            )}
            {step < totalSteps - 1 ? (
              <Button onClick={() => setStep(step + 1)}>
                Suivant <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button onClick={handleComplete}>
                Commencer <Check className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}