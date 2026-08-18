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
    const styles: Record<string, string> = {
      ADMIN: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
      GESTIONNAIRE: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
      PHARMACIEN: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
      AUDITEUR: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
    };
    return <Badge className={styles[role]}>{role}</Badge>;
  };

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Utilisateurs</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez les comptes et les rôles</p>
        </div>
        <Button className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white" onClick={openNew}>
          <UserPlus className="w-4 h-4 mr-2" />Nouvel utilisateur
        </Button>
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="dark:bg-slate-800 dark:border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-900 dark:text-white">
              {editingUser ? "Modifier l'utilisateur" : "Nouvel utilisateur"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-slate-500 dark:text-slate-400">Nom d'utilisateur *</Label>
              <Input
                required
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-500 dark:text-slate-400">Email</Label>
              <Input
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-500 dark:text-slate-400">
                Mot de passe {editingUser ? "(laisser vide)" : "*"}
              </Label>
              <Input
                type="password"
                required={!editingUser}
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                className="dark:bg-slate-700 dark:text-white dark:border-slate-600"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-500 dark:text-slate-400">Rôle</Label>
              <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                <SelectTrigger className="dark:bg-slate-700 dark:text-white dark:border-slate-600">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="dark:bg-slate-800 dark:border-slate-700">
                  <SelectItem value="PHARMACIEN">Pharmacien</SelectItem>
                  <SelectItem value="GESTIONNAIRE">Gestionnaire</SelectItem>
                  <SelectItem value="AUDITEUR">Auditeur</SelectItem>
                  <SelectItem value="ADMIN">Administrateur</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={saving} className="bg-[#0ABAB5] text-white">
                {saving ? "..." : editingUser ? "Modifier" : "Créer"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                className="dark:border-slate-600 dark:text-slate-300"
              >
                Annuler
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardContent className="py-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Rechercher..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-10 bg-slate-50 dark:bg-slate-700 dark:text-white border-slate-200 dark:border-slate-600 focus:bg-white dark:focus:bg-slate-600"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-900 dark:text-white">Liste ({users.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            [...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2 dark:bg-slate-700" />)
          ) : users.length === 0 ? (
            <p className="text-center text-slate-400 dark:text-slate-500 py-8">Aucun</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 dark:border-slate-700">
                  <TableHead className="text-slate-500 dark:text-slate-400">Utilisateur</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Email</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Rôle</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Statut</TableHead>
                  <TableHead className="text-slate-500 dark:text-slate-400">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users
                  .filter(
                    (u: any) =>
                      u.username?.toLowerCase().includes(search.toLowerCase()) ||
                      u.email?.toLowerCase().includes(search.toLowerCase())
                  )
                  .map((user: any) => (
                    <TableRow
                      key={user.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700"
                    >
                      <TableCell className="font-medium text-slate-900 dark:text-white">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-slate-200 dark:bg-slate-600 rounded-full flex items-center justify-center font-bold text-sm text-slate-700 dark:text-white">
                            {user.username?.[0]?.toUpperCase()}
                          </div>
                          {user.username}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500 dark:text-slate-400">{user.email || "-"}</TableCell>
                      <TableCell>{roleBadge(user.role)}</TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge className="bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300">Actif</Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300">Inactif</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="dark:bg-slate-800 dark:border-slate-700">
                            <DropdownMenuItem
                              onClick={() => openEdit(user)}
                              className="dark:text-slate-300 dark:hover:bg-slate-700"
                            >
                              <Edit className="w-4 h-4 mr-2" />Modifier
                            </DropdownMenuItem>
                            {user.is_active ? (
                              <DropdownMenuItem
                                className="text-red-600 dark:text-red-400"
                                onClick={() => handleDelete(user)}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />Désactiver
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                className="text-green-600 dark:text-green-400"
                                onClick={async () => {
                                  await api.activateUser(user.id);
                                  loadUsers();
                                }}
                              >
                                <UserPlus className="w-4 h-4 mr-2" />Réactiver
                              </DropdownMenuItem>
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