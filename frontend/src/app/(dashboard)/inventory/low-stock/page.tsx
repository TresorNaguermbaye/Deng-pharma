"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw } from "lucide-react";

export default function LowStockPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [recommending, setRecommending] = useState<string | null>(null);

  useEffect(() => { loadItems(); }, []);

  const loadItems = async () => {
    setLoading(true);
    const data = await api.getLowStock();
    // Récupérer les recommandations IA pour chaque médicament
    const withRecommendations = await Promise.all(
      data.map(async (item: any) => {
        try {

          const rec = await api.recommendStock(item.id);  
         

          return { ...item, recommended_order: rec.recommended_order || item.to_order };
        } catch {
          return item;
        }
      })
    );
    setItems(withRecommendations);
    setLoading(false);
  };

  const handleRecommend = async (medicineId: string) => {
    setRecommending(medicineId);
    try {
      const res = await fetch(`/api/ai/recommend-stock/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify({ medicine_id: medicineId }),
      });
      const rec = await res.json();
      setItems(prev =>
        prev.map(item =>
          item.id === medicineId ? { ...item, recommended_order: rec.recommended_order } : item
        )
      );
    } catch (err) {
      console.error(err);
    } finally {
      setRecommending(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Stock faible</h1>
          <p className="text-slate-500 mt-1">Réapprovisionnement basé sur l'IA</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadItems}>
          <RefreshCw className="w-4 h-4 mr-2" /> Actualiser
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{items.length} médicament(s) sous le seuil minimum</CardTitle>
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
                  <TableHead>Stock actuel</TableHead>
                  <TableHead>Stock min</TableHead>
                  <TableHead>Commande IA</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item: any) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.name}</TableCell>
                    <TableCell>{item.category}</TableCell>
                    <TableCell className="text-red-600 font-bold">
                      {item.current_stock}
                    </TableCell>
                    <TableCell>{item.min_stock}</TableCell>
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
                        <Button size="sm">Commander</Button>
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
