"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { UserPlus, Edit, Trash2, Search, MoreHorizontal } from "lucide-react";

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "PHARMACIEN" });
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await api.getUsers();
      setUsers(data.results || data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const openNew = () => { setEditingUser(null); setForm({ username: "", email: "", password: "", role: "PHARMACIEN" }); setShowDialog(true); };
  const openEdit = (user: any) => { setEditingUser(user); setForm({ username: user.username, email: user.email || "", password: "", role: user.role }); setShowDialog(true); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editingUser) await api.updateUser(editingUser.id, { ...form, password: form.password || undefined });
      else await api.createUser(form);
      setShowDialog(false); loadUsers();
    } catch (err) { console.error(err); alert("Erreur"); }
    finally { setSaving(false); }
  };

  const handleDelete = async (user: any) => {
    if (!confirm(`Désactiver "${user.username}" ?`)) return;
    await api.deleteUser(user.id);
    loadUsers();
  };

  const roleBadge = (role: string) => {
    const styles: Record<string, string> = { ADMIN: "bg-red-100 text-red-700", GESTIONNAIRE: "bg-blue-100 text-blue-700", PHARMACIEN: "bg-green-100 text-green-700", AUDITEUR: "bg-purple-100 text-purple-700" };
    return <Badge className={styles[role]}>{role}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-3xl font-bold text-slate-900">Utilisateurs</h1><p className="text-slate-500 mt-1">Gérez les comptes et les rôles</p></div>
        <Button className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white" onClick={openNew}><UserPlus className="w-4 h-4 mr-2" />Nouvel utilisateur</Button>
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editingUser ? "Modifier l'utilisateur" : "Nouvel utilisateur"}</DialogTitle></DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2"><Label>Nom d'utilisateur *</Label><Input required value={form.username} onChange={e => setForm({...form, username: e.target.value})} /></div>
            <div className="space-y-2"><Label>Email</Label><Input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} /></div>
            <div className="space-y-2"><Label>Mot de passe {editingUser ? "(laisser vide)" : "*"}</Label><Input type="password" required={!editingUser} value={form.password} onChange={e => setForm({...form, password: e.target.value})} /></div>
            <div className="space-y-2"><Label>Rôle</Label>
              <Select value={form.role} onValueChange={(v) => setForm({...form, role: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="PHARMACIEN">Pharmacien</SelectItem><SelectItem value="GESTIONNAIRE">Gestionnaire</SelectItem><SelectItem value="AUDITEUR">Auditeur</SelectItem><SelectItem value="ADMIN">Administrateur</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={saving} className="bg-[#0ABAB5] text-white">{saving ? "..." : editingUser ? "Modifier" : "Créer"}</Button>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Annuler</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Card className="border-0 shadow-md"><CardContent className="py-4"><div className="relative"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><Input placeholder="Rechercher..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10" /></div></CardContent></Card>

      <Card className="border-0 shadow-md">
        <CardHeader><CardTitle>Liste ({users.length})</CardTitle></CardHeader>
        <CardContent>
          {loading ? [...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2" />) : users.length === 0 ? <p className="text-center text-slate-400 py-8">Aucun</p> : (
            <Table>
              <TableHeader><TableRow><TableHead>Utilisateur</TableHead><TableHead>Email</TableHead><TableHead>Rôle</TableHead><TableHead>Statut</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {users.filter((u: any) => u.username?.toLowerCase().includes(search.toLowerCase()) || u.email?.toLowerCase().includes(search.toLowerCase())).map((user: any) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium"><div className="flex items-center gap-3"><div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center font-bold text-sm">{user.username?.[0]?.toUpperCase()}</div>{user.username}</div></TableCell>
                    <TableCell className="text-slate-500">{user.email || "-"}</TableCell>
                    <TableCell>{roleBadge(user.role)}</TableCell>
                    <TableCell>{user.is_active ? <Badge className="bg-green-100 text-green-700">Actif</Badge> : <Badge className="bg-red-100 text-red-700">Inactif</Badge>}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild><Button variant="ghost" size="sm"><MoreHorizontal className="w-4 h-4" /></Button></DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(user)}><Edit className="w-4 h-4 mr-2" />Modifier</DropdownMenuItem>
                          {user.is_active ? (
                            <DropdownMenuItem className="text-red-600" onClick={() => handleDelete(user)}><Trash2 className="w-4 h-4 mr-2" />Désactiver</DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem className="text-green-600" onClick={async () => { await api.activateUser(user.id); loadUsers(); }}><UserPlus className="w-4 h-4 mr-2" />Réactiver</DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
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
