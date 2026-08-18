"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Download, PackageCheck } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [receiving, setReceiving] = useState(false);
  const router = useRouter();

  const loadOrders = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.getOrders();
      const list = Array.isArray(data) ? data : data.results || [];
      setOrders(list);
    } catch (err) {
      console.error(err);
      setError("Impossible de charger les commandes.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadOrders(); }, []);

  const handleDownloadPdf = async (orderId: number | string) => {
    try {
      const blob = await api.downloadOrderPdf(orderId);
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `bon_commande_${orderId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error(err);
      alert("Impossible de télécharger le PDF.");
    }
  };

  const handleOpenReceive = (order: any) => {
    setSelectedOrder(order);
  };

  const handleReceiveSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedOrder) return;
    setReceiving(true);
    const form = e.currentTarget;
    const formData = new FormData(form);
    const payload = {
      batch_number: formData.get("batch_number") as string,
      expiry_date: formData.get("expiry_date") as string,
      purchase_price_per_unit: parseFloat(formData.get("purchase_price_per_unit") as string),
      quantity_received: parseInt(formData.get("quantity_received") as string, 10),
    };
    try {
      await api.receiveOrder(selectedOrder.id, payload);
      setSelectedOrder(null);
      loadOrders();
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la réception.");
    } finally {
      setReceiving(false);
    }
  };

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Bons de commande
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Liste des commandes fournisseurs
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadOrders}
          className="dark:border-slate-600 dark:text-slate-300"
        >
          Actualiser
        </Button>
      </div>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">
            {orders.length} commande(s)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-64 dark:bg-slate-700" />
          ) : error ? (
            <p className="text-red-500">{error}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 dark:border-slate-700">
                  <TableHead className="text-slate-500 dark:text-slate-400">ID</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Médicament</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Quantité</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Statut</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Date</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order: any) => (
                  <TableRow
                    key={order.id}
                    className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                  >
                    <TableCell className="text-slate-500 dark:text-slate-400">{order.id}</TableCell>
                    <TableCell className="font-medium text-slate-900 dark:text-white">
                      {order.medicine_name}
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {order.quantity_ordered}
                    </TableCell>
                    <TableCell>
                      <Badge variant={order.status === "PENDING" ? "default" : "secondary"}>
                        {order.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 dark:text-slate-400">
                      {new Date(order.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadPdf(order.id)}
                          className="dark:border-slate-600 dark:text-slate-300"
                        >
                          <Download className="w-4 h-4 mr-2" /> PDF
                        </Button>
                        {order.status === "PENDING" && (
                          <Button size="sm" onClick={() => handleOpenReceive(order)}>
                            <PackageCheck className="w-4 h-4 mr-2" /> Réceptionner
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {orders.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={6}
                      className="text-center text-slate-500 dark:text-slate-400"
                    >
                      Aucune commande trouvée.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selectedOrder && (
        <Dialog open={!!selectedOrder} onOpenChange={(open) => !open && setSelectedOrder(null)}>
          <DialogContent className="dark:bg-slate-800 dark:border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-900 dark:text-white">
                Réceptionner la commande #{selectedOrder.id}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleReceiveSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="batch_number" className="text-slate-500 dark:text-slate-400">
                  Numéro de lot
                </Label>
                <Input
                  id="batch_number"
                  name="batch_number"
                  required
                  className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="expiry_date" className="text-slate-500 dark:text-slate-400">
                  Date d'expiration
                </Label>
                <Input
                  id="expiry_date"
                  name="expiry_date"
                  type="date"
                  required
                  className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="purchase_price_per_unit" className="text-slate-500 dark:text-slate-400">
                  Prix d'achat unitaire
                </Label>
                <Input
                  id="purchase_price_per_unit"
                  name="purchase_price_per_unit"
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="quantity_received" className="text-slate-500 dark:text-slate-400">
                  Quantité reçue
                </Label>
                <Input
                  id="quantity_received"
                  name="quantity_received"
                  type="number"
                  min="1"
                  required
                  className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
                />
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedOrder(null)}
                  className="dark:border-slate-600 dark:text-slate-300"
                >
                  Annuler
                </Button>
                <Button type="submit" disabled={receiving}>
                  {receiving ? "..." : "Confirmer la réception"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}