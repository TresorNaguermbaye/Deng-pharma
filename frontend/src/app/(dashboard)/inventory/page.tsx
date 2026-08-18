"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Package, AlertTriangle, Clock } from "lucide-react";

export default function InventoryPage() {
  const [lots, setLots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadStocks(); }, []);

  const loadStocks = async () => {
    try {
      const data = await api.getMedicines();
      setLots(data.results || []);
    } catch (err) {
      console.error("Erreur stocks:", err);
    } finally {
      setLoading(false);
    }
  };

  const getExpiryStatus = (med: any) => {
    if (!med.min_stock) return "OK";
    if (med.stock_status === "OUT") return "EXPIRED";
    if (med.stock_status === "LOW") return "SOON";
    return "OK";
  };

  const statusBadge = (status: string) => {
    switch (status) {
      case "EXPIRED":
        return <Badge className="bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300">Expiré</Badge>;
      case "SOON":
        return <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300">Bientôt</Badge>;
      default:
        return <Badge className="bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300">OK</Badge>;
    }
  };

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Stocks</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez vos lots et surveillez les expirations</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card className="border-0 shadow-md bg-gradient-to-br from-blue-50 to-cyan-50 dark:bg-none dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="py-4 flex items-center gap-3">
            <Package className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Lots actifs</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{lots.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-yellow-50 to-amber-50 dark:bg-none dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="py-4 flex items-center gap-3">
            <Clock className="w-8 h-8 text-yellow-500" />
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Expiration proche</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{lots.filter(l => getExpiryStatus(l) === "SOON").length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-red-50 to-rose-50 dark:bg-none dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="py-4 flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Alertes</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{lots.filter(l => getExpiryStatus(l) !== "OK").length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">État des stocks</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            [...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2 dark:bg-slate-700" />)
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 dark:border-slate-700">
                  <TableHead className="text-slate-500 dark:text-slate-400">Médicament</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Stock min</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Stock max</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Niveau</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lots.map((med, i) => (
                  <TableRow key={i} className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700">
                    <TableCell className="font-medium text-slate-900 dark:text-white">{med.commercial_name}</TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">{med.min_stock}</TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">{med.max_stock}</TableCell>
                    <TableCell className="w-40">
                      <Progress value={med.min_stock ? Math.min(100, (med.min_stock / med.max_stock) * 100) : 50} className="h-2" />
                    </TableCell>
                    <TableCell>{statusBadge(getExpiryStatus(med))}</TableCell>
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