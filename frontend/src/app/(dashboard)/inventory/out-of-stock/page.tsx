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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Produits en rupture</h1>
          <p className="text-slate-500 mt-1">Réapprovisionnement basé sur l'IA</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadItems}>
          <RefreshCw className="w-4 h-4 mr-2" /> Actualiser
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{items.length} médicament(s) en rupture</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Médicament</TableHead>
                  <TableHead>Catégorie</TableHead>
                  <TableHead>Commande IA</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item: any) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.name}</TableCell>
                    <TableCell>{item.category}</TableCell>
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
                        >
                          {recommending === item.id ? "..." : "Recalculer"}
                        </Button>
                        <Button size="sm" onClick={() => handleOrder(item.id, item.recommended_order)}>
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
