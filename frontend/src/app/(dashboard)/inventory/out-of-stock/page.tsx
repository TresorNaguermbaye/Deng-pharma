"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw } from "lucide-react";

export default function OutOfStockPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [recommending, setRecommending] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => { loadItems(); }, []);

  const loadItems = async () => {
    setLoading(true);
    try {
      const data = await api.getOutOfStock();
      const withRecommendations = await Promise.all(
        data.map(async (item: any) => {
          try {
            const rec = await api.recommendStock(item.id);
            return { ...item, recommended_order: rec.recommended_order || item.recommended_order };
          } catch {
            return item;
          }
        })
      );
      setItems(withRecommendations);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRecommend = async (medicineId: string) => {
    setRecommending(medicineId);
    try {
      const rec = await api.recommendStock(medicineId);
      setItems(prev =>
        prev.map(i =>
          i.id === medicineId ? { ...i, recommended_order: rec.recommended_order } : i
        )
      );
    } catch (err) {
      console.error(err);
    } finally {
      setRecommending(null);
    }
  };

  const handleOrder = async (medicineId: string, recommendedQty: number) => {
    try {
      await api.createOrder(medicineId, recommendedQty, null);
      // Redirection vers la page des bons de commande
      router.push("/orders");
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la commande");
    }
  };

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Produits en rupture
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Réapprovisionnement basé sur l'IA
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadItems}
          className="gap-2 dark:border-slate-600 dark:text-slate-300"
        >
          <RefreshCw className="w-4 h-4 mr-2" /> Actualiser
        </Button>
      </div>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">
            {items.length} médicament(s) en rupture
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64 dark:bg-slate-700" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 dark:border-slate-700">
                  <TableHead className="text-slate-500 dark:text-slate-400">Médicament</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Catégorie</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Commande IA</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item: any) => (
                  <TableRow
                    key={item.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700"
                  >
                    <TableCell className="font-medium text-slate-900 dark:text-white">
                      {item.name}
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {item.category}
                    </TableCell>
                    <TableCell className="font-bold text-green-600">
                      {item.recommended_order} unités
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRecommend(item.id)}
                          disabled={recommending === item.id}
                          className="dark:border-slate-600 dark:text-slate-300"
                        >
                          {recommending === item.id ? "..." : "Recalculer"}
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleOrder(item.id, item.recommended_order)}
                        >
                          Commander
                        </Button>
                      </div>
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