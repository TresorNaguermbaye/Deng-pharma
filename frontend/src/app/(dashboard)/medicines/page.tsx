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
import { Search, Plus, MoreHorizontal, Eye, Edit, Trash2 } from "lucide-react";

export default function MedicinesPage() {
  const router = useRouter();
  const [medicines, setMedicines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => { loadMedicines(); }, [page, search]);

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
    <div className="space-y-6 bg-slate-50 dark:bg-slate-900 min-h-screen p-4 md:p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Médicaments</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez votre catalogue</p>
        </div>
        <Button className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white shadow-lg shadow-[#0ABAB5]/25 hover:opacity-90" onClick={() => router.push("/medicines/new")}>
          <Plus className="w-4 h-4 mr-2" /> Ajouter un médicament
        </Button>
      </div>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardContent className="py-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Rechercher un médicament..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-slate-50 dark:bg-slate-700 dark:text-white border-slate-200 dark:border-slate-600 focus:bg-white dark:focus:bg-slate-600"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">Liste des médicaments</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            [...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2 dark:bg-slate-700" />)
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 dark:border-slate-700">
                  <TableHead className="text-slate-500 dark:text-slate-400">Nom commercial</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">DCI</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Catégorie</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Prix vente</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Emplacement</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {medicines.map((med) => (
                  <TableRow key={med.id} className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700">
                    <TableCell className="font-medium text-slate-900 dark:text-white">{med.commercial_name}</TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">{med.dci}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="dark:text-slate-300 dark:border-slate-600">
                        {med.category_name || "N/A"}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-semibold text-[#0ABAB5]">{formatFCFA(med.selling_price)}</TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">{med.location || "-"}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="dark:bg-slate-800 dark:border-slate-700">
                          <DropdownMenuItem
                            onClick={() => router.push(`/medicines/${med.id}`)}
                            className="dark:text-slate-300 dark:hover:bg-slate-700"
                          >
                            <Eye className="w-4 h-4 mr-2" /> Voir détails
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => router.push(`/medicines/${med.id}/edit`)}
                            className="dark:text-slate-300 dark:hover:bg-slate-700"
                          >
                            <Edit className="w-4 h-4 mr-2" /> Modifier
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600 dark:text-red-400"
                            onClick={async () => {
                              if (confirm("Supprimer ce médicament ?")) {
                                await api.deleteMedicine(med.id);
                                loadMedicines();
                              }
                            }}
                          >
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