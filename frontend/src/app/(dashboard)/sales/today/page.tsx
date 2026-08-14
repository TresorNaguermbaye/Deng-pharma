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
  useEffect(() => { api.getTodaySales().then(data => { setSales(data); setLoading(false); }); }, []);
  const formatCFA = (v: number) => v.toLocaleString('fr-FR') + ' FCFA';
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Ventes du jour</h1>
      <Card>
        <CardHeader><CardTitle>{sales.length} vente(s) aujourd'hui</CardTitle></CardHeader>
        <CardContent>
          {loading ? <Skeleton className="h-64" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>#</TableHead><TableHead>Client</TableHead><TableHead>Articles</TableHead><TableHead>Total</TableHead><TableHead>Paiement</TableHead><TableHead>Heure</TableHead></TableRow></TableHeader>
              <TableBody>
                {sales.map((s: any) => (
                  <TableRow key={s.id}>
                    <TableCell>{s.id}</TableCell>
                    <TableCell>{s.customer}</TableCell>
                    <TableCell>{s.items.map((i:any) => `${i.medicine} x${i.quantity}`).join(', ')}</TableCell>
                    <TableCell className="font-bold">{formatCFA(s.total)}</TableCell>
                    <TableCell><Badge>{s.payment}</Badge></TableCell>
                    <TableCell>{s.time}</TableCell>
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