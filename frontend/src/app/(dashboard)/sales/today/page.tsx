"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function TodaySalesPage() {
  const [sales, setSales] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTodaySales()
      .then(data => {
        setSales(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erreur chargement ventes du jour:", err);
        setLoading(false);
      });
  }, []);

  const formatCFA = (v: number) => v.toLocaleString('fr-FR') + ' FCFA';

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
        Ventes du jour
      </h1>
      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">
            {sales.length} vente(s) aujourd'hui
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64 dark:bg-slate-700" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 dark:border-slate-700">
                  <TableHead className="text-slate-500 dark:text-slate-400">#</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Client</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Articles</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Total</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Paiement</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Heure</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sales.map((s: any) => (
                  <TableRow
                    key={s.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700"
                  >
                    <TableCell className="text-slate-500 dark:text-slate-400">{s.id}</TableCell>
                    <TableCell className="text-slate-900 dark:text-white">{s.customer}</TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {s.items.map((i: any) => `${i.medicine} x${i.quantity}`).join(', ')}
                    </TableCell>
                    <TableCell className="font-bold text-slate-900 dark:text-white">{formatCFA(s.total)}</TableCell>
                    <TableCell>
                      <Badge className="dark:bg-slate-700 dark:text-slate-300">{s.payment}</Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">{s.time}</TableCell>
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