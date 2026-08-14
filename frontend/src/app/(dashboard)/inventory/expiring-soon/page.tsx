"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function ExpiringSoonPage() {
  const [lots, setLots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.getExpiringSoon().then(data => { setLots(data); setLoading(false); }); }, []);
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Expirations proches (90 jours)</h1>
      <Card>
        <CardHeader><CardTitle>{lots.length} lot(s) concerné(s)</CardTitle></CardHeader>
        <CardContent>
          {loading ? <Skeleton className="h-64" /> : (
            <Table>
              <TableHeader><TableRow><TableHead>Médicament</TableHead><TableHead>Lot</TableHead><TableHead>Quantité</TableHead><TableHead>Expire le</TableHead><TableHead>Jours restants</TableHead></TableRow></TableHeader>
              <TableBody>
                {lots.map((lot: any) => (
                  <TableRow key={lot.id}>
                    <TableCell className="font-medium">{lot.medicine}</TableCell>
                    <TableCell>{lot.batch}</TableCell>
                    <TableCell>{lot.quantity}</TableCell>
                    <TableCell>{new Date(lot.expiry_date).toLocaleDateString('fr-FR')}</TableCell>
                    <TableCell><Badge variant={lot.days_left < 30 ? "destructive" : "secondary"}>{lot.days_left} jours</Badge></TableCell>
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