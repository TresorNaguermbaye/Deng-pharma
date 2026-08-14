"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Save, Trash2 } from "lucide-react";

export default function EditMedicinePage() {
  const router = useRouter();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [form, setForm] = useState<any>({
    commercial_name: "", dci: "", barcode: "", category: null,
    manufacturer: "", purchase_price: "", selling_price: "",
    location: "", min_stock: "10", max_stock: "100",
  });

  useEffect(() => {
    loadMedicine();
  }, [id]);

  const loadMedicine = async () => {
    try {
      const data = await api.getMedicines();
      const med = data.results?.find((m: any) => m.id === id);
      if (med) {
        setForm({
          commercial_name: med.commercial_name || "",
          dci: med.dci || "",
          barcode: med.barcode || "",
          manufacturer: med.manufacturer || "",
          purchase_price: med.purchase_price || "",
          selling_price: med.selling_price || "",
          location: med.location || "",
          min_stock: med.min_stock || 10,
          max_stock: med.max_stock || 100,
        });
      }
    } catch (err) {
      console.error("Erreur:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateMedicine(id as string, {
        ...form,
        purchase_price: parseFloat(form.purchase_price) || 0,
        selling_price: parseFloat(form.selling_price) || 0,
        min_stock: parseInt(form.min_stock) || 10,
        max_stock: parseInt(form.max_stock) || 100,
      });
      router.push("/medicines");
    } catch (err) {
      console.error("Erreur:", err);
      alert("Erreur lors de la modification");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Supprimer définitivement ce médicament ?")) return;
    setDeleting(true);
    try {
      await api.deleteMedicine(id as string);
      router.push("/medicines");
    } catch (err) {
      console.error("Erreur:", err);
      alert("Erreur lors de la suppression");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <div className="p-8"><Skeleton className="h-64 w-full rounded-xl" /></div>;

  return (
    <div className="p-8 space-y-6 max-w-2xl mx-auto">
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Retour
      </Button>

      <Card className="border-0 shadow-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-2xl">Modifier le médicament</CardTitle>
          <Button variant="outline" className="text-red-600 border-red-300" onClick={handleDelete} disabled={deleting}>
            <Trash2 className="w-4 h-4 mr-2" />
            {deleting ? "Suppression..." : "Supprimer"}
          </Button>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nom commercial *</Label>
                <Input required value={form.commercial_name} onChange={e => setForm({...form, commercial_name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>DCI *</Label>
                <Input required value={form.dci} onChange={e => setForm({...form, dci: e.target.value})} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Code-barres *</Label>
                <Input required value={form.barcode} onChange={e => setForm({...form, barcode: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Fabricant</Label>
                <Input value={form.manufacturer} onChange={e => setForm({...form, manufacturer: e.target.value})} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Prix d'achat (FCFA)</Label>
                <Input type="number" value={form.purchase_price} onChange={e => setForm({...form, purchase_price: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Prix de vente (FCFA)</Label>
                <Input type="number" value={form.selling_price} onChange={e => setForm({...form, selling_price: e.target.value})} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Emplacement</Label>
              <Input value={form.location} onChange={e => setForm({...form, location: e.target.value})} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Stock minimum</Label>
                <Input type="number" value={form.min_stock} onChange={e => setForm({...form, min_stock: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Stock maximum</Label>
                <Input type="number" value={form.max_stock} onChange={e => setForm({...form, max_stock: e.target.value})} />
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={saving} className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white">
                <Save className="w-4 h-4 mr-2" />
                {saving ? "Enregistrement..." : "Enregistrer"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Annuler</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
