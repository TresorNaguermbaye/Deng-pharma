"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Brain, TrendingUp, TrendingDown, BarChart3, Target, RefreshCw, Zap } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";

export default function AIPredictionsPage() {
  const [medicines, setMedicines] = useState<any[]>([]);
  const [selectedMed, setSelectedMed] = useState<string>("");
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMeds, setLoadingMeds] = useState(true);

  useEffect(() => {
    loadMedicines();
  }, []);

  const loadMedicines = async () => {
    try {
      const data = await api.getMedicines();
      setMedicines(data.results || []);
      if (data.results?.length > 0) {
        setSelectedMed(data.results[0].id);
      }
    } catch (err) { console.error(err); }
    finally { setLoadingMeds(false); }
  };





  const loadPredictions = async () => {
  if (!selectedMed) return;
  setLoading(true);
  const medObj = medicines.find(m => m.id === selectedMed);
  console.log("Medicament sélectionné:", medObj);   // ← à ajouter
  try {
    const data = await api.predictSalesByName(
      selectedMed,
      medObj?.commercial_name || "",
      7
    );
    console.log("Réponse API:", data);   // ← à ajouter
    setPredictions(data.predictions || []);
  } catch (err) { console.error(err); }
  finally { setLoading(false); }
};



  useEffect(() => {
    if (selectedMed) loadPredictions();
  }, [selectedMed]);

  const formatFCFA = (v: number) => v ? new Intl.NumberFormat('fr-FR').format(v) + ' FCFA' : '-';
  const selectedMedicineName = medicines.find(m => m.id === selectedMed)?.commercial_name || "";

  // Calculs pour les KPIs
  const totalPredicted = predictions.reduce((sum, p) => sum + p.predicted_sales, 0);
  const avgPredicted = predictions.length > 0 ? totalPredicted / predictions.length : 0;
  const trend = predictions.length >= 2 ? predictions[predictions.length-1].predicted_sales - predictions[0].predicted_sales : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <Brain className="w-8 h-8 text-[#0ABAB5]" /> Prédictions IA
        </h1>
        <p className="text-slate-500 mt-1">Prévisions de ventes basées sur l'intelligence artificielle</p>
      </div>

      {/* Sélection du médicament */}
      <Card className="border-0 shadow-md">
        <CardContent className="py-4">
          <div className="flex items-end gap-4">
            <div className="flex-1 space-y-2">
              <Label>Sélectionnez un médicament</Label>
              {loadingMeds ? (
                <Skeleton className="h-10 w-full" />
              ) : (
                <Select value={selectedMed} onValueChange={setSelectedMed}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choisir un médicament..." />
                  </SelectTrigger>
                  <SelectContent>
                    {medicines.map((med) => (
                      <SelectItem key={med.id} value={med.id}>
                        {med.commercial_name} ({med.dci})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <Button onClick={loadPredictions} disabled={loading} className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualiser
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
          <div className="lg:col-span-3"><Skeleton className="h-96 rounded-xl" /></div>
        </div>
      ) : predictions.length > 0 ? (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-0 shadow-md bg-gradient-to-br from-blue-50 to-cyan-50">
              <CardContent className="p-4 flex items-center gap-3">
                <Target className="w-8 h-8 text-blue-500" />
                <div>
                  <p className="text-sm text-slate-500">Total prévu (7 jours)</p>
                  <p className="text-2xl font-bold text-slate-800">{totalPredicted.toFixed(0)} unités</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-0 shadow-md bg-gradient-to-br from-purple-50 to-violet-50">
              <CardContent className="p-4 flex items-center gap-3">
                <BarChart3 className="w-8 h-8 text-purple-500" />
                <div>
                  <p className="text-sm text-slate-500">Moyenne / jour</p>
                  <p className="text-2xl font-bold text-slate-800">{avgPredicted.toFixed(0)} unités</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-0 shadow-md bg-gradient-to-br from-green-50 to-emerald-50">
              <CardContent className="p-4 flex items-center gap-3">
                {trend >= 0 ? <TrendingUp className="w-8 h-8 text-green-500" /> : <TrendingDown className="w-8 h-8 text-red-500" />}
                <div>
                  <p className="text-sm text-slate-500">Tendance</p>
                  <p className={`text-2xl font-bold ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {trend >= 0 ? '+' : ''}{trend.toFixed(0)} unités
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Graphique */}
          <Card className="border-0 shadow-md">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-[#0ABAB5]" />
                Prévisions pour {selectedMedicineName}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart key={selectedMed} data={predictions} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ABAB5" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0ABAB5" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tickFormatter={(d) => new Date(d).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' })} fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(1)} unités`, "Prévision"]}
                    labelFormatter={(label) => new Date(label).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
                  />
                  <Area type="monotone" dataKey="predicted_sales" stroke="#0ABAB5" strokeWidth={3} fill="url(#colorPred)" />
                  <Line type="monotone" dataKey="upper_bound" stroke="#10B981" strokeWidth={1} strokeDasharray="5 5" dot={false} />
                  <Line type="monotone" dataKey="lower_bound" stroke="#F59E0B" strokeWidth={1} strokeDasharray="5 5" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex items-center justify-center gap-6 mt-2 text-xs text-slate-500">
                <div className="flex items-center gap-1"><div className="w-3 h-0.5 bg-[#0ABAB5] rounded" /> Prévision</div>
                <div className="flex items-center gap-1"><div className="w-3 h-0.5 bg-[#10B981] rounded" style={{ borderTop: '1px dashed #10B981' }} /> Borne sup.</div>
                <div className="flex items-center gap-1"><div className="w-3 h-0.5 bg-[#F59E0B] rounded" style={{ borderTop: '1px dashed #F59E0B' }} /> Borne inf.</div>
              </div>
            </CardContent>
          </Card>

          {/* Tableau des prévisions */}
          <Card className="border-0 shadow-md">
            <CardHeader><CardTitle className="text-lg">Détail des prévisions</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {predictions.map((p, i) => (
                  <div key={i} className="bg-slate-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-500">{new Date(p.date).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' })}</p>
                    <p className="text-xl font-bold text-slate-800 mt-1">{p.predicted_sales.toFixed(0)}</p>
                    <p className="text-xs text-slate-400">{p.lower_bound.toFixed(0)} - {p.upper_bound.toFixed(0)}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card className="border-0 shadow-md">
          <CardContent className="flex items-center justify-center py-16 text-slate-400">
            Sélectionnez un médicament pour voir les prédictions
          </CardContent>
        </Card>
      )}
    </div>
  );
}
