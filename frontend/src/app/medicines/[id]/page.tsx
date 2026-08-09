"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Edit, Trash2, Package, AlertTriangle } from "lucide-react";

export default function MedicineDetailPage() {
  const router = useRouter();
  const { id } = useParams();
  const [medicine, setMedicine] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMedicine();
  }, [id]);

  const loadMedicine = async () => {
    try {
      const data = await api.getMedicines();
      const med = data.results?.find((m: any) => m.id === id);
      setMedicine(med);
    } catch (err) {
      console.error("Erreur:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8"><Skeleton className="h-64 w-full rounded-xl" /></div>;
  if (!medicine) return <div className="p-8 text-center text-red-500">Médicament non trouvé</div>;

  return (
    <div className="p-8 space-y-6">
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Retour
      </Button>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{medicine.commercial_name}</h1>
          <p className="text-slate-500 mt-1">DCI: {medicine.dci}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Edit className="w-4 h-4 mr-2" /> Modifier</Button>
          <Button variant="outline" className="text-red-600 border-red-300"><Trash2 className="w-4 h-4 mr-2" /> Supprimer</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-0 shadow-md">
          <CardHeader><CardTitle className="text-lg">Informations générales</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div><span className="text-slate-500">Code-barres :</span> <span className="font-mono">{medicine.barcode}</span></div>
            <div><span className="text-slate-500">Catégorie :</span> <Badge variant="outline">{medicine.category_name || "N/A"}</Badge></div>
            <div><span className="text-slate-500">Emplacement :</span> {medicine.location || "-"}</div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md">
          <CardHeader><CardTitle className="text-lg">Prix</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div><span className="text-slate-500">Prix de vente :</span> <span className="font-bold text-[#0ABAB5] text-xl">{medicine.selling_price?.toLocaleString()} FCFA</span></div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-md">
          <CardHeader><CardTitle className="text-lg">Stock</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-500" />
              <span className="font-bold">{medicine.min_stock} - {medicine.max_stock} unités</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
