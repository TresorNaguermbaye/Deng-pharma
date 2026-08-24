"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
import {
  Bell, Package, Clock, Brain, TrendingUp, Pill, ShoppingCart, FileBarChart, BarChart3, Users, UserPlus,
  Search, MoreHorizontal, Edit, Trash2, Menu, X, LogOut, LayoutDashboard
} from "lucide-react";

import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "PHARMACIEN" });
  const [saving, setSaving] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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

  const roleBadge = (role: string) => {
    const styles: Record<string, string> = {
      ADMIN: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
      GESTIONNAIRE: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
      PHARMACIEN: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
      AUDITEUR: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
    };
    return <Badge className={`text-xs px-2 py-0.5 ${styles[role]}`}>{role}</Badge>;
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
                    item.href === "/admin/users" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Utilisateurs</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez les comptes et les rôles</p>
          </div>
          <Button className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white w-full sm:w-auto" onClick={openNew}>
            <UserPlus className="w-4 h-4 mr-2" />Nouvel utilisateur
          </Button>
        </div>

        {/* Dialogue de création/modification */}
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

        {/* Recherche */}
        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="py-3 px-3 sm:py-4 sm:px-4">
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

        {/* Tableau des utilisateurs (sans colonne Email) */}
        <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl text-slate-900 dark:text-white">Liste ({users.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              [...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-full mb-2 dark:bg-slate-700" />)
            ) : users.length === 0 ? (
              <p className="text-center text-slate-400 dark:text-slate-500 py-8">Aucun</p>
            ) : (
              <Table className="w-full table-fixed">
                <TableHeader>
                  <TableRow className="border-slate-200 dark:border-slate-700">
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-2/5">Utilisateur</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/5">Rôle</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/5">Statut</TableHead>
                    <TableHead className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 w-1/5">Actions</TableHead>
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
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-slate-200 dark:bg-slate-600 rounded-full flex items-center justify-center font-bold text-xs sm:text-sm text-slate-700 dark:text-white">
                              {user.username?.[0]?.toUpperCase()}
                            </div>
                            <span className="truncate text-xs sm:text-sm">{user.username}</span>
                          </div>
                        </TableCell>
                        <TableCell>{roleBadge(user.role)}</TableCell>
                        <TableCell>
                          {user.is_active ? (
                            <Badge className="bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300 text-xs px-2 py-0.5">Actif</Badge>
                          ) : (
                            <Badge className="bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 text-xs px-2 py-0.5">Inactif</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="p-1">
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
      </main>
    </div>
  );
}