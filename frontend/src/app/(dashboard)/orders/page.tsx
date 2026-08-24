"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Download, PackageCheck,
  Menu, X, LayoutDashboard, Pill, Package, ShoppingCart,
  FileBarChart, BarChart3, Brain, Bell, Users, LogOut, TrendingUp
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [receiving, setReceiving] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  // Navigation locale pour la sidebar mobile
  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Médicaments", href: "/medicines", icon: Pill },
    { label: "Stocks", href: "/inventory", icon: Package },
    { label: "Ventes", href: "/sales", icon: ShoppingCart },
    { label: "Rapports", href: "/reports", icon: FileBarChart },
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "Chat IA", href: "/ai/chat", icon: Brain },
    { label: "IA Prédictions", href: "/ai/predictions", icon: Brain },
    { label: "Notifications", href: "/notifications", icon: Bell },
    { label: "Utilisateurs", href: "/admin/users", icon: Users },
  ];

  // Fonction pour déterminer la couleur du point selon le statut
  const statusColor = (status: string) => {
    switch (status) {
      case "PENDING": return "bg-yellow-500";
      case "RECEIVED": return "bg-green-500";
      case "CANCELLED": return "bg-red-500";
      default: return "bg-slate-400";
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Topbar */}
      <Topbar onMenuClick={() => setMobileMenuOpen(true)} />

      {/* Sidebar desktop */}
      <Sidebar />

      {/* Sidebar mobile */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <aside className="fixed left-0 top-0 bottom-0 w-64 bg-[#0F1A2C] text-white p-6 flex flex-col">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#0ABAB5] rounded-xl flex items-center justify-center font-bold text-xl">D</div>
                <span className="font-bold">DENG PHARMA</span>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setMobileMenuOpen(false)} className="text-white">
                <X className="w-5 h-5" />
              </Button>
            </div>
            <nav className="flex-1 space-y-1">
              {navItems.map((item) => (
                <button
                  key={item.href}
                  onClick={() => { router.push(item.href); setMobileMenuOpen(false); }}
                  className={`flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left ${
                    item.href === "/orders" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </button>
              ))}
            </nav>
            <Button variant="ghost" onClick={handleLogout} className="text-gray-300 hover:text-white mt-4">
              <LogOut className="w-4 h-4 mr-2" /> Déconnexion
            </Button>
          </aside>
        </div>
      )}

      {/* Contenu principal */}
      <main className="pt-20 lg:pl-64 p-4 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
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
            className="dark:border-slate-600 dark:text-slate-300 w-full sm:w-auto"
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
          <CardContent className="p-2 sm:p-4">
            {loading ? (
              <Skeleton className="h-64 dark:bg-slate-700" />
            ) : error ? (
              <p className="text-red-500">{error}</p>
            ) : (
              <Table className="w-full table-fixed">
                <TableHeader>
                  <TableRow className="border-slate-200 dark:border-slate-700">
                    <TableHead className="w-1/12 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">ID</TableHead>
                    <TableHead className="w-4/12 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">
                      <span className="sm:hidden">Méd.</span>
                      <span className="hidden sm:inline">Médicament</span>
                    </TableHead>
                    <TableHead className="w-1/12 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">
                      <span className="sm:hidden">Qté</span>
                      <span className="hidden sm:inline">Quantité</span>
                    </TableHead>
                    {/* Colonne Statut réduite */}
                    <TableHead className="w-[6%] text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2 pr-3 sm:pr-6">Statut</TableHead>
                    <TableHead className="w-3/12 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2 pl-3 sm:pl-6">Date</TableHead>
                    <TableHead className="w-2/12 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((order: any) => (
                    <TableRow
                      key={order.id}
                      className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                    >
                      <TableCell className="text-slate-500 dark:text-slate-400 text-[10px] sm:text-sm p-1 sm:p-2">{order.id}</TableCell>
                      <TableCell className="font-medium text-slate-900 dark:text-white truncate text-[10px] sm:text-sm p-1 sm:p-2">
                        {order.medicine_name}
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-[10px] sm:text-sm p-1 sm:p-2">
                        {order.quantity_ordered}
                      </TableCell>
                      {/* Point coloré avec tooltip */}
                      <TableCell className="p-1 sm:p-2 pr-3 sm:pr-6">
                        <span
                          className={`inline-block w-2.5 h-2.5 rounded-full ${statusColor(order.status)}`}
                          title={order.status}
                        />
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400 text-[10px] sm:text-sm p-1 sm:p-2 pl-3 sm:pl-6">
                        {new Date(order.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="p-1 sm:p-2">
                        <div className="flex gap-1 sm:gap-2 justify-end">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDownloadPdf(order.id)}
                            className="dark:border-slate-600 dark:text-slate-300 p-1.5 sm:p-2"
                            title="Télécharger PDF"
                            aria-label="Télécharger PDF"
                          >
                            <Download className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                          </Button>
                          {order.status === "PENDING" && (
                            <Button
                              size="sm"
                              onClick={() => handleOpenReceive(order)}
                              className="p-1.5 sm:p-2"
                              title="Réceptionner"
                              aria-label="Réceptionner"
                            >
                              <PackageCheck className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  {orders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-slate-500 dark:text-slate-400 text-[10px] sm:text-sm">
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
      </main>
    </div>
  );
}