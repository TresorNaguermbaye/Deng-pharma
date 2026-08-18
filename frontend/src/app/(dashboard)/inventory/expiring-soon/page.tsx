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

  useEffect(() => {
    api.getExpiringSoon()
      .then(data => {
        setLots(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erreur chargement expirations:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
        Expirations proches (90 jours)
      </h1>
      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">
            {lots.length} lot(s) concerné(s)
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
                  <TableHead className="text-slate-500 dark:text-slate-400">Lot</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Quantité</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Expire le</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Jours restants</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lots.map((lot: any) => (
                  <TableRow
                    key={lot.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700"
                  >
                    <TableCell className="font-medium text-slate-900 dark:text-white">
                      {lot.medicine}
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {lot.batch}
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {lot.quantity}
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {new Date(lot.expiry_date).toLocaleDateString('fr-FR')}
                    </TableCell>
                    <TableCell>
                      <Badge variant={lot.days_left < 30 ? "destructive" : "secondary"}>
                        {lot.days_left} jours
                      </Badge>
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