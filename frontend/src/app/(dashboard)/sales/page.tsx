"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, Plus, Minus, Trash2, ShoppingCart, Receipt, Download } from "lucide-react";
import { useDashboard } from "@/context/DashboardContext";

interface CartItem { id: string; name: string; price: number; quantity: number; }

export default function SalesPage() {
  const { triggerRefresh } = useDashboard();
  const [search, setSearch] = useState("");
  const [medicines, setMedicines] = useState<any[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [customerName, setCustomerName] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [discount, setDiscount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [lastSaleId, setLastSaleId] = useState<number | null>(null);

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
      const token = api.getToken();
      const response = await fetch(`http://127.0.0.1:8000/api/sales/sales/${saleId}/invoice/`, { headers: { 'Authorization': `Bearer ${token}` } });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `facture_${saleId}.pdf`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(url);
    } catch (err) { console.error(err); }
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
      triggerRefresh();            // 🔥 Déclenche la mise à jour du dashboard
      setCart([]);
      setCustomerName("");
      setDiscount(0);
      setMedicines([]);
      setSearch("");
      setTimeout(() => downloadInvoice(result.id), 500);
    } catch (err) { console.error(err); alert("Erreur"); }
    finally { setSubmitting(false); }
  };

  const formatFCFA = (v: number) => new Intl.NumberFormat('fr-FR').format(v) + ' FCFA';

  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-slate-900">Ventes</h1><p className="text-slate-500 mt-1">Gérez vos ventes et générez des factures</p></div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card className="border-0 shadow-md">
            <CardHeader><CardTitle className="flex items-center gap-2"><ShoppingCart className="w-5 h-5" /> Panier</CardTitle></CardHeader>
            <CardContent>
              {cart.length === 0 ? (
                <p className="text-center text-slate-400 py-8">Panier vide. Recherchez un médicament.</p>
              ) : (
                <Table>
                  <TableHeader><TableRow><TableHead>Médicament</TableHead><TableHead>Prix</TableHead><TableHead>Qté</TableHead><TableHead>Total</TableHead><TableHead></TableHead></TableRow></TableHeader>
                  <TableBody>
                    {cart.map(item => (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.name}</TableCell>
                        <TableCell>{formatFCFA(item.price)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" onClick={() => updateQuantity(item.id, -1)}><Minus className="w-3 h-3" /></Button>
                            <span className="w-8 text-center">{item.quantity}</span>
                            <Button variant="outline" size="sm" onClick={() => updateQuantity(item.id, 1)}><Plus className="w-3 h-3" /></Button>
                          </div>
                        </TableCell>
                        <TableCell className="font-semibold">{formatFCFA(item.price * item.quantity)}</TableCell>
                        <TableCell><Button variant="ghost" size="sm" className="text-red-500" onClick={() => removeFromCart(item.id)}><Trash2 className="w-4 h-4" /></Button></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {cart.length > 0 && (
                <div className="border-t pt-4 mt-4 space-y-2 text-right">
                  <p className="text-slate-500">Sous-total : {formatFCFA(subtotal)}</p>
                  <div className="flex items-center justify-end gap-2"><Label>Remise :</Label><Input type="number" value={discount} onChange={e => setDiscount(Number(e.target.value))} className="w-32" /><span>FCFA</span></div>
                  <p className="text-xl font-bold text-[#0ABAB5]">Total : {formatFCFA(total)}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="border-0 shadow-md">
            <CardHeader><CardTitle>Client & Paiement</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2"><Label>Nom du client</Label><Input value={customerName} onChange={e => setCustomerName(e.target.value)} placeholder="Client comptoir" /></div>
              <div className="space-y-2"><Label>Mode de paiement</Label>
                <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CASH">Espèces</SelectItem><SelectItem value="CARD">Carte bancaire</SelectItem><SelectItem value="MOBILE">Mobile Money</SelectItem><SelectItem value="OTHER">Autre</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button className="w-full bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white" onClick={handleSubmitSale} disabled={submitting || cart.length === 0}>
                <Receipt className="w-4 h-4 mr-2" />{submitting ? "Enregistrement..." : "Valider la vente"}
              </Button>
              {lastSaleId && (
                <Button variant="outline" className="w-full mt-2 text-[#0ABAB5] border-[#0ABAB5]" onClick={() => downloadInvoice(lastSaleId)}>
                  <Download className="w-4 h-4 mr-2" />Télécharger la facture
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-md">
            <CardHeader><CardTitle>Recherche médicament</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Nom ou DCI..." onKeyDown={e => e.key === 'Enter' && handleSearch()} />
                <Button onClick={handleSearch}><Search className="w-4 h-4" /></Button>
              </div>
              {medicines.length > 0 && (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {medicines.map(med => (
                    <div key={med.id} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100" onClick={() => addToCart(med)}>
                      <div><p className="font-medium text-sm">{med.commercial_name}</p><p className="text-xs text-slate-500">{formatFCFA(med.selling_price)}</p></div>
                      <Plus className="w-4 h-4 text-[#0ABAB5]" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
