"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Save } from "lucide-react";

export default function NewMedicinePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    commercial_name: "",
    dci: "",
    barcode: "",
    category: "",
    manufacturer: "",
    purchase_price: "",
    selling_price: "",
    location: "",
    min_stock: "10",
    max_stock: "100",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createMedicine({
        ...form,
        purchase_price: parseFloat(form.purchase_price),
        selling_price: parseFloat(form.selling_price),
        min_stock: parseInt(form.min_stock),
        max_stock: parseInt(form.max_stock),
      });
      router.push("/medicines");
    } catch (err) {
      console.error("Erreur création:", err);
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="p-8 space-y-6 max-w-2xl mx-auto">
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Retour
      </Button>

      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle className="text-2xl">Nouveau médicament</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nom commercial *</Label>
                <Input required value={form.commercial_name} onChange={e => updateField("commercial_name", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>DCI *</Label>
                <Input required value={form.dci} onChange={e => updateField("dci", e.target.value)} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Code-barres *</Label>
                <Input required value={form.barcode} onChange={e => updateField("barcode", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Fabricant</Label>
                <Input value={form.manufacturer} onChange={e => updateField("manufacturer", e.target.value)} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Prix d'achat (FCFA)</Label>
                <Input type="number" value={form.purchase_price} onChange={e => updateField("purchase_price", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Prix de vente (FCFA) *</Label>
                <Input type="number" required value={form.selling_price} onChange={e => updateField("selling_price", e.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Emplacement</Label>
              <Input value={form.location} onChange={e => updateField("location", e.target.value)} placeholder="Rayon A1" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Stock minimum</Label>
                <Input type="number" value={form.min_stock} onChange={e => updateField("min_stock", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Stock maximum</Label>
                <Input type="number" value={form.max_stock} onChange={e => updateField("max_stock", e.target.value)} />
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={loading} className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
                <Save className="w-4 h-4 mr-2" />
                {loading ? "Enregistrement..." : "Enregistrer"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Annuler</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
