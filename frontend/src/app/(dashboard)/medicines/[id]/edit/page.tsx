"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Save, Trash2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export default function EditMedicinePage() {
  const router = useRouter();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [form, setForm] = useState<any>({
    commercial_name: "",
    dci: "",
    barcode: "",
    category: null,
    manufacturer: "",
    purchase_price: "",
    selling_price: "",
    location: "",
    min_stock: "10",
    max_stock: "100",
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
      toast.error("Erreur lors du chargement");
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
      toast.success("Médicament modifié avec succès");
      router.push("/medicines");
    } catch (err) {
      console.error("Erreur:", err);
      toast.error("Erreur lors de la modification");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Supprimer définitivement ce médicament ?")) return;
    setDeleting(true);
    try {
      await api.deleteMedicine(id as string);
      toast.success("Médicament supprimé");
      router.push("/medicines");
    } catch (err) {
      console.error("Erreur:", err);
      toast.error("Erreur lors de la suppression");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 p-8">
        <div className="max-w-2xl mx-auto space-y-6">
          <Skeleton className="h-10 w-32 bg-slate-800" />
          <Skeleton className="h-96 w-full rounded-xl bg-slate-800" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* BOUTON RETOUR */}
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour
        </Button>

        {/* CARTE PRINCIPALE */}
        <Card className="border border-slate-800 shadow-2xl bg-slate-900/80 backdrop-blur-sm rounded-2xl overflow-hidden">
          {/* EN-TÊTE */}
          <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800 bg-gradient-to-r from-slate-900 to-slate-800/50 px-6 py-4">
            <div>
              <CardTitle className="text-2xl font-bold text-white">
                Modifier le médicament
              </CardTitle>
              <p className="text-sm text-slate-400 mt-1">
                Modifiez les informations ci-dessous
              </p>
            </div>
            <Button
              variant="outline"
              className="text-red-400 border-red-500/30 hover:bg-red-500/10 hover:border-red-500/50 transition-all"
              onClick={handleDelete}
              disabled={deleting}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {deleting ? "Suppression..." : "Supprimer"}
            </Button>
          </CardHeader>

          {/* CONTENU */}
          <CardContent className="p-6">
            <form onSubmit={handleSave} className="space-y-6">
              {/* SECTION 1 : Informations principales */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-[#0ABAB5] uppercase tracking-wider">
                  Informations principales
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">
                      Nom commercial <span className="text-[#0ABAB5]">*</span>
                    </Label>
                    <Input
                      required
                      value={form.commercial_name}
                      onChange={(e) =>
                        setForm({ ...form, commercial_name: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                      placeholder="Ex: Paracétamol 500mg"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">
                      DCI <span className="text-[#0ABAB5]">*</span>
                    </Label>
                    <Input
                      required
                      value={form.dci}
                      onChange={(e) =>
                        setForm({ ...form, dci: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                      placeholder="Ex: Paracétamol"
                    />
                  </div>
                </div>
              </div>

              {/* SECTION 2 : Identification */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-[#0ABAB5] uppercase tracking-wider">
                  Identification
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">
                      Code-barres <span className="text-[#0ABAB5]">*</span>
                    </Label>
                    <Input
                      required
                      value={form.barcode}
                      onChange={(e) =>
                        setForm({ ...form, barcode: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                      placeholder="Ex: 3400930000000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Fabricant</Label>
                    <Input
                      value={form.manufacturer}
                      onChange={(e) =>
                        setForm({ ...form, manufacturer: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                      placeholder="Ex: Sanofi"
                    />
                  </div>
                </div>
              </div>

              {/* SECTION 3 : Prix */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-[#0ABAB5] uppercase tracking-wider">
                  Prix (FCFA)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Prix d'achat</Label>
                    <Input
                      type="number"
                      value={form.purchase_price}
                      onChange={(e) =>
                        setForm({ ...form, purchase_price: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Prix de vente</Label>
                    <Input
                      type="number"
                      value={form.selling_price}
                      onChange={(e) =>
                        setForm({ ...form, selling_price: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>

              {/* SECTION 4 : Stock */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-[#0ABAB5] uppercase tracking-wider">
                  Gestion du stock
                </h3>
                <div className="space-y-2">
                  <Label className="text-slate-300">Emplacement</Label>
                  <Input
                    value={form.location}
                    onChange={(e) =>
                      setForm({ ...form, location: e.target.value })
                    }
                    className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                    placeholder="Ex: Rayon A - Étagère 3"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Stock minimum</Label>
                    <Input
                      type="number"
                      value={form.min_stock}
                      onChange={(e) =>
                        setForm({ ...form, min_stock: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Stock maximum</Label>
                    <Input
                      type="number"
                      value={form.max_stock}
                      onChange={(e) =>
                        setForm({ ...form, max_stock: e.target.value })
                      }
                      className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#0ABAB5] focus:ring-[#0ABAB5]/20 transition-colors"
                    />
                  </div>
                </div>
              </div>

              {/* BOUTONS D'ACTION */}
              <div className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-slate-800">
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 hover:from-[#0a9e99] hover:to-blue-700 text-white font-semibold px-6 py-2 rounded-xl shadow-lg shadow-[#0ABAB5]/20 transition-all duration-300 disabled:opacity-50"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? "Enregistrement..." : "Enregistrer"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                  className="border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Annuler
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}