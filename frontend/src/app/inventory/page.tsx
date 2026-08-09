"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Package, AlertTriangle, Clock } from "lucide-react";

export default function InventoryPage() {
  const router = useRouter();
  const [lots, setLots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!api.getToken()) { router.push("/login"); return; }
    loadStocks();
  }, []);

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
      case "EXPIRED": return <Badge className="bg-red-100 text-red-700">Expiré</Badge>;
      case "SOON": return <Badge className="bg-yellow-100 text-yellow-700">Bientôt</Badge>;
      default: return <Badge className="bg-green-100 text-green-700">OK</Badge>;
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Stocks</h1>
        <p className="text-slate-500 mt-1">Gérez vos lots et surveillez les expirations</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="border-0 shadow-md bg-gradient-to-br from-blue-50 to-cyan-50">
          <CardContent className="py-4 flex items-center gap-3">
            <Package className="w-8 h-8 text-blue-500" />
            <div><p className="text-sm text-slate-500">Lots actifs</p><p className="text-2xl font-bold">{lots.length}</p></div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-yellow-50 to-amber-50">
          <CardContent className="py-4 flex items-center gap-3">
            <Clock className="w-8 h-8 text-yellow-500" />
            <div><p className="text-sm text-slate-500">Expiration proche</p><p className="text-2xl font-bold">{lots.filter(l => getExpiryStatus(l) === "SOON").length}</p></div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-md bg-gradient-to-br from-red-50 to-rose-50">
          <CardContent className="py-4 flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div><p className="text-sm text-slate-500">Alertes</p><p className="text-2xl font-bold">{lots.filter(l => getExpiryStatus(l) !== "OK").length}</p></div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader><CardTitle>État des stocks</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            [...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2" />)
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Médicament</TableHead>
                  <TableHead>Stock min</TableHead>
                  <TableHead>Stock max</TableHead>
                  <TableHead>Niveau</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lots.map((med, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium">{med.commercial_name}</TableCell>
                    <TableCell>{med.min_stock}</TableCell>
                    <TableCell>{med.max_stock}</TableCell>
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
