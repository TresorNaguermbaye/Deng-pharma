"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Search, Plus, Filter, ArrowUpDown, MoreHorizontal, Eye, Edit, Trash2, Package, AlertTriangle, ChevronLeft, ChevronRight } from "lucide-react";

export default function MedicinesPage() {
  const router = useRouter();
  const [medicines, setMedicines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!api.getToken()) { router.push("/login"); return; }
    loadMedicines();
  }, [page, search]);

  const loadMedicines = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: page.toString() };
      if (search) params.search = search;
      const data = await api.getMedicines(params);
      setMedicines(data.results || []);
    } catch (err) {
      console.error("Erreur:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatFCFA = (value: number) => new Intl.NumberFormat('fr-FR').format(value) + ' FCFA';

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Médicaments</h1>
          <p className="text-slate-500 mt-1">Gérez votre catalogue</p>
        </div>
        <Button className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white shadow-lg shadow-[#0ABAB5]/25 hover:opacity-90" onClick={() => router.push("/medicines/new")}>
          <Plus className="w-4 h-4 mr-2" /> Ajouter un médicament
        </Button>
      </div>

      <Card className="border-0 shadow-md">
        <CardContent className="py-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input placeholder="Rechercher un médicament..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
          </div>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-md">
        <CardHeader><CardTitle>Liste des médicaments</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            [...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2" />)
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nom commercial</TableHead>
                  <TableHead>DCI</TableHead>
                  <TableHead>Catégorie</TableHead>
                  <TableHead>Prix vente</TableHead>
                  <TableHead>Emplacement</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {medicines.map((med) => (
                  <TableRow key={med.id} className="hover:bg-slate-50">
                    <TableCell className="font-medium">{med.commercial_name}</TableCell>
                    <TableCell className="text-slate-500">{med.dci}</TableCell>
                    <TableCell><Badge variant="outline">{med.category_name || "N/A"}</Badge></TableCell>
                    <TableCell className="font-semibold text-[#0ABAB5]">{formatFCFA(med.selling_price)}</TableCell>
                    <TableCell>{med.location || "-"}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm"><MoreHorizontal className="w-4 h-4" /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => router.push(`/medicines/${med.id}`)}>
                            <Eye className="w-4 h-4 mr-2" /> Voir détails
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => router.push(`/medicines/${med.id}/edit`)}>
                            <Edit className="w-4 h-4 mr-2" /> Modifier
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600" onClick={async () => {
  if (confirm("Supprimer ce médicament ?")) {
    await api.deleteMedicine(med.id);
    loadMedicines();
  }
}}>
  <Trash2 className="w-4 h-4 mr-2" /> Supprimer
</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
