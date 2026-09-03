"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Search, Plus, Minus, Trash2, ShoppingCart, Receipt, Download,
  Menu, X, LayoutDashboard, Pill, Package, FileBarChart, BarChart3,
  Brain, Bell, Users, LogOut, TrendingUp
} from "lucide-react";
import { useDashboard } from "@/context/DashboardContext";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

interface CartItem { id: string; name: string; price: number; quantity: number; }

export default function SalesPage() {
  const { triggerRefresh } = useDashboard();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [medicines, setMedicines] = useState<any[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [customerName, setCustomerName] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [discount, setDiscount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [lastSaleId, setLastSaleId] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSearch = async () => {
    if (!search.trim()) return;
    try {
      const data = await api.getMedicines({ search });
      setMedicines(data.results || []);
    } catch (err) { console.error(err); }
  };

  const addToCart = (med: any) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === med.id);
      if (existing) return prev.map(item => item.id === med.id ? { ...item, quantity: item.quantity + 1 } : item);
      return [...prev, { id: med.id, name: med.commercial_name, price: med.selling_price, quantity: 1 }];
    });
  };

  const removeFromCart = (id: string) => setCart(prev => prev.filter(item => item.id !== id));
  const updateQuantity = (id: string, delta: number) => {
    setCart(prev => prev.map(item => {
      if (item.id === id) { const newQty = item.quantity + delta; return newQty > 0 ? { ...item, quantity: newQty } : item; }
      return item;
    }).filter(item => item.quantity > 0));
  };

  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const total = Math.max(0, subtotal - discount);

const downloadInvoice = async (saleId: number) => {
  try {
    const blob = await api.downloadInvoice(saleId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `facture_${saleId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    alert("Erreur lors du téléchargement");
  }
};

  const handleSubmitSale = async () => {
    if (cart.length === 0) return alert("Ajoutez au moins un médicament");
    setSubmitting(true);
    try {
      const result = await api.createSale({
        customer_name: customerName || null,
        discount, payment_method: paymentMethod,
        items: cart.map(item => ({ medicine: item.id, quantity: item.quantity, unit_price: item.price }))
      });
      setLastSaleId(result.id);
      triggerRefresh();
      setCart([]);
      setCustomerName("");
      setDiscount(0);
      setMedicines([]);
      setSearch("");
      setTimeout(() => downloadInvoice(result.id), 500);
    } catch (err) { console.error(err); alert("Erreur"); }
    finally { setSubmitting(false); }
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

  const formatFCFA = (v: number) => new Intl.NumberFormat('fr-FR').format(v) + ' FCFA';

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
                    item.href === "/sales" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Ventes</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez vos ventes et générez des factures</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                  <ShoppingCart className="w-5 h-5" /> Panier
                </CardTitle>
              </CardHeader>
              <CardContent>
                {cart.length === 0 ? (
                  <p className="text-center text-slate-400 dark:text-slate-500 py-8">Panier vide. Recherchez un médicament.</p>
                ) : (
                  <Table className="w-full table-fixed">
                    <TableHeader>
                      <TableRow className="border-slate-200 dark:border-slate-700">
                        <TableHead className="w-2/5 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Médicament</TableHead>
                        <TableHead className="w-1/5 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Prix</TableHead>
                        <TableHead className="w-1/5 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Qté</TableHead>
                        <TableHead className="w-1/5 text-[10px] sm:text-sm text-slate-500 dark:text-slate-400 p-1 sm:p-2">Total</TableHead>
                        <TableHead className="w-8 p-1 sm:p-2"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cart.map(item => (
                        <TableRow key={item.id} className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700">
                          <TableCell className="font-medium text-slate-900 dark:text-white truncate text-[10px] sm:text-sm p-1 sm:p-2">{item.name}</TableCell>
                          <TableCell className="text-slate-500 dark:text-slate-400 text-[10px] sm:text-sm p-1 sm:p-2">{formatFCFA(item.price)}</TableCell>
                          <TableCell className="p-1 sm:p-2">
                            <div className="flex items-center gap-1 sm:gap-2">
                              <Button variant="outline" size="sm" onClick={() => updateQuantity(item.id, -1)} className="p-1 sm:p-2 dark:border-slate-600 dark:text-slate-300"><Minus className="w-3 h-3" /></Button>
                              <span className="w-6 text-center text-slate-900 dark:text-white text-[10px] sm:text-sm">{item.quantity}</span>
                              <Button variant="outline" size="sm" onClick={() => updateQuantity(item.id, 1)} className="p-1 sm:p-2 dark:border-slate-600 dark:text-slate-300"><Plus className="w-3 h-3" /></Button>
                            </div>
                          </TableCell>
                          <TableCell className="font-semibold text-slate-900 dark:text-white text-[10px] sm:text-sm p-1 sm:p-2">{formatFCFA(item.price * item.quantity)}</TableCell>
                          <TableCell className="p-1 sm:p-2"><Button variant="ghost" size="sm" className="text-red-500 p-1" onClick={() => removeFromCart(item.id)}><Trash2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" /></Button></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
                {cart.length > 0 && (
                  <div className="border-t border-slate-200 dark:border-slate-700 pt-4 mt-4 space-y-2 text-right">
                    <p className="text-slate-500 dark:text-slate-400 text-sm">Sous-total : {formatFCFA(subtotal)}</p>
                    <div className="flex items-center justify-end gap-2">
                      <Label className="text-slate-500 dark:text-slate-400 text-sm">Remise :</Label>
                      <Input type="number" value={discount} onChange={e => setDiscount(Number(e.target.value))} className="w-24 sm:w-32 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                      <span className="text-slate-500 dark:text-slate-400 text-sm">FCFA</span>
                    </div>
                    <p className="text-xl font-bold text-[#0ABAB5]">Total : {formatFCFA(total)}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Client & Paiement</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <Label className="text-slate-500 dark:text-slate-400">Nom du client</Label>
                  <Input value={customerName} onChange={e => setCustomerName(e.target.value)} placeholder="Client comptoir" className="dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-500 dark:text-slate-400">Mode de paiement</Label>
                  <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                    <SelectTrigger className="dark:bg-slate-700 dark:text-white dark:border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="dark:bg-slate-800 dark:border-slate-700">
                      <SelectItem value="CASH">Espèces</SelectItem>
                      <SelectItem value="CARD">Carte bancaire</SelectItem>
                      <SelectItem value="MOBILE">Mobile Money</SelectItem>
                      <SelectItem value="OTHER">Autre</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button className="w-full bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white" onClick={handleSubmitSale} disabled={submitting || cart.length === 0}>
                  <Receipt className="w-4 h-4 mr-2" />{submitting ? "Enregistrement..." : "Valider la vente"}
                </Button>
                {lastSaleId && (
                  <Button variant="outline" className="w-full mt-2 text-[#0ABAB5] border-[#0ABAB5] dark:bg-transparent" onClick={() => downloadInvoice(lastSaleId)}>
                    <Download className="w-4 h-4 mr-2" />Télécharger la facture
                  </Button>
                )}
              </CardContent>
            </Card>

            <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Recherche médicament</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Nom ou DCI..."
                    onKeyDown={e => e.key === 'Enter' && handleSearch()}
                    className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
                  />
                  <Button onClick={handleSearch}><Search className="w-4 h-4" /></Button>
                </div>
                {medicines.length > 0 && (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {medicines.map(med => (
                      <div
                        key={med.id}
                        className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-700 rounded-lg cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-600"
                        onClick={() => addToCart(med)}
                      >
                        <div>
                          <p className="font-medium text-sm text-slate-900 dark:text-white">{med.commercial_name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{formatFCFA(med.selling_price)}</p>
                        </div>
                        <Plus className="w-4 h-4 text-[#0ABAB5]" />
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}