"use client";
import ShapChart from "@/components/ia/ShapChart";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Topbar } from "@/components/layout/Topbar";
import { Sidebar } from "@/components/layout/Sidebar";
import {
  Menu, X, Brain, Target, AlertTriangle, Activity, TrendingUp, BarChart3,
  LayoutDashboard, Pill, Package, ShoppingCart, FileBarChart, Bell, Users, LogOut
} from "lucide-react";
import { subscribeToPush } from "@/lib/push"; // <-- import ajouté

const profileSchema = z.object({
  first_name: z.string().min(2, "Prénom requis"),
  last_name: z.string().min(2, "Nom requis"),
  email: z.string().email("Email invalide"),
  langue: z.enum(["fr", "en"]),
  devise: z.enum(["FCFA", "EUR", "USD"]),
  email_notifications: z.boolean(),
  push_notifications: z.boolean(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const passwordSchema = z.object({
  old_password: z.string().min(1, "Ancien mot de passe requis"),
  new_password: z.string().min(8, "Le mot de passe doit contenir au moins 8 caractères"),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Les mots de passe ne correspondent pas",
  path: ["confirm_password"],
});

type PasswordFormValues = z.infer<typeof passwordSchema>;

function MetricRow({ label, value, unit = "" }: { label: string; value?: string | number; unit?: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-slate-600 dark:text-slate-300">{label}</span>
      <span className="text-lg font-bold text-slate-900 dark:text-white">
        {value ?? "N/A"}{unit && <span className="text-sm font-medium ml-1">{unit}</span>}
      </span>
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [selectedMedicine, setSelectedMedicine] = useState<string>("");
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [trainingMessage, setTrainingMessage] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Récupérer le profil utilisateur
  const { data: me, isLoading: meLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => api.getMe(),
  });

  // Récupérer les médicaments
  const { data: medicinesData, isLoading: medsLoading } = useQuery({
    queryKey: ["medicines"],
    queryFn: () => api.getMedicines(),
  });
  const medicines = medicinesData?.results || medicinesData || [];

  // Récupérer les performances du modèle
  const { data: modelPerf, isLoading: perfLoading } = useQuery({
    queryKey: ["model-performance"],
    queryFn: () => api.getIAModelPerformance(),
  });

  // Récupérer les prédictions quand un médicament est sélectionné
  const { data: predictionData, isLoading: predLoading } = useQuery({
    queryKey: ["prediction", selectedMedicine],
    queryFn: () => api.getIAPredict(selectedMedicine, 7),
    enabled: !!selectedMedicine,
  });

  // Charger SHAP avec useQuery
  const { data: shapData, isLoading: shapLoading } = useQuery({
    queryKey: ["shap", selectedMedicine],
    queryFn: () => api.getIAShap(selectedMedicine),
    enabled: !!selectedMedicine,
  });

  const profileForm = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: {
      first_name: me?.first_name || "",
      last_name: me?.last_name || "",
      email: me?.email || "",
      langue: me?.profile?.langue || "fr",
      devise: me?.profile?.devise || "FCFA",
      email_notifications: me?.profile?.email_notifications ?? true,
      push_notifications: me?.profile?.push_notifications ?? true,
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: (values: ProfileFormValues) => api.updateMe(values),
    onSuccess: () => toast.success("Profil mis à jour"),
    onError: () => toast.error("Erreur lors de la mise à jour"),
  });

  const onSubmitProfile = (values: ProfileFormValues) => {
    updateProfileMutation.mutate(values);
  };

  const passwordForm = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
  });

  const changePasswordMutation = useMutation({
    mutationFn: (values: PasswordFormValues) => api.changePassword(values),
    onSuccess: () => {
      toast.success("Mot de passe modifié");
      passwordForm.reset();
    },
    onError: () => toast.error("Erreur lors du changement de mot de passe"),
  });

  const onSubmitPassword = (values: PasswordFormValues) => {
    changePasswordMutation.mutate(values);
  };

  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('photo', file);
    try {
      await api.uploadPhoto(formData);
      toast.success('Photo mise à jour');
      window.location.reload();
    } catch {
      toast.error('Erreur lors de l\'upload');
    }
  };

  const handleTrainModel = async () => {
    setTrainingLoading(true);
    setTrainingMessage(null);
    try {
      const response = await api.trainModel();
      if (response?.status === "Entraînement lancé en arrière-plan") {
        setTrainingMessage("Entraînement lancé avec succès.");
        toast.success("Entraînement lancé");
      } else {
        setTrainingMessage(response?.error || "Erreur lors du lancement.");
        toast.error("Erreur");
      }
    } catch (error: any) {
      console.error("Erreur entraînement:", error);
      setTrainingMessage(error?.message || "Erreur réseau ou serveur.");
      toast.error("Erreur");
    } finally {
      setTrainingLoading(false);
    }
  };

  // Nouvelle fonction pour activer les notifications push
  const handleEnablePush = async () => {
    try {
      await subscribeToPush(api);
      toast.success("Notifications push activées avec succès");
    } catch (error: any) {
      console.error("Erreur push:", error);
      toast.error(error.message || "Impossible d'activer les notifications push");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  // Navigation locale pour la sidebar mobile (identique aux autres pages)
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

  if (meLoading) return <div>Chargement...</div>;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Topbar onMenuClick={() => setMobileMenuOpen(true)} />
      <Sidebar />

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
                    item.href === "/settings" ? "text-white bg-white/10" : "text-gray-300 hover:bg-white/5 hover:text-white"
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

      <main className="pt-16 lg:pl-64 p-4 md:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Paramètres</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Gérez votre profil, vos préférences et le modèle IA</p>
          </div>
        </div>

        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700 rounded-lg p-1 gap-1">
            <TabsTrigger value="profile" className="data-[state=active]:bg-[#0ABAB5] data-[state=active]:text-white rounded-lg px-4 py-2">Profil</TabsTrigger>
            <TabsTrigger value="password" className="data-[state=active]:bg-[#0ABAB5] data-[state=active]:text-white rounded-lg px-4 py-2">Mot de passe</TabsTrigger>
            <TabsTrigger value="preferences" className="data-[state=active]:bg-[#0ABAB5] data-[state=active]:text-white rounded-lg px-4 py-2">Préférences</TabsTrigger>
            {me?.role === "ADMIN" && (
              <TabsTrigger value="ai" className="data-[state=active]:bg-[#0ABAB5] data-[state=active]:text-white rounded-lg px-4 py-2">IA</TabsTrigger>
            )}
          </TabsList>

          {/* Onglet Profil */}
          <TabsContent value="profile" className="mt-6">
            <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Informations personnelles</CardTitle>
                <CardDescription>Mettez à jour votre nom, email et photo.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center space-x-6">
                  <Avatar className="h-24 w-24 ring-4 ring-[#0ABAB5]/20">
                    <AvatarImage src={me?.profile?.photo || ""} />
                    <AvatarFallback className="text-2xl">
                      {me?.first_name?.[0]}
                      {me?.last_name?.[0]}
                    </AvatarFallback>
                  </Avatar>
                  <label className="cursor-pointer">
                    <span className="bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 px-4 py-2 rounded-lg text-sm hover:bg-slate-200 dark:hover:bg-slate-600 transition">
                      Changer la photo
                    </span>
                    <input type="file" accept="image/*" className="hidden" onChange={handlePhotoUpload} />
                  </label>
                </div>

                <form onSubmit={profileForm.handleSubmit(onSubmitProfile)} className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div>
                      <Label htmlFor="first_name" className="text-slate-700 dark:text-slate-300">Prénom</Label>
                      <Input id="first_name" {...profileForm.register("first_name")} className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                      {profileForm.formState.errors.first_name && (
                        <p className="text-red-500 text-sm">{profileForm.formState.errors.first_name.message}</p>
                      )}
                    </div>
                    <div>
                      <Label htmlFor="last_name" className="text-slate-700 dark:text-slate-300">Nom</Label>
                      <Input id="last_name" {...profileForm.register("last_name")} className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                      {profileForm.formState.errors.last_name && (
                        <p className="text-red-500 text-sm">{profileForm.formState.errors.last_name.message}</p>
                      )}
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="email" className="text-slate-700 dark:text-slate-300">Email</Label>
                    <Input id="email" type="email" {...profileForm.register("email")} className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                    {profileForm.formState.errors.email && (
                      <p className="text-red-500 text-sm">{profileForm.formState.errors.email.message}</p>
                    )}
                  </div>
                  <Button type="submit" disabled={updateProfileMutation.isPending} className="bg-[#0ABAB5] hover:bg-[#0a9e99] text-white px-6">
                    {updateProfileMutation.isPending ? "Enregistrement..." : "Enregistrer"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet Mot de passe */}
          <TabsContent value="password" className="mt-6">
            <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Changer le mot de passe</CardTitle>
                <CardDescription>Utilisez un mot de passe fort et unique.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={passwordForm.handleSubmit(onSubmitPassword)} className="space-y-5">
                  <div>
                    <Label htmlFor="old_password" className="text-slate-700 dark:text-slate-300">Ancien mot de passe</Label>
                    <Input id="old_password" type="password" {...passwordForm.register("old_password")} className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                    {passwordForm.formState.errors.old_password && (
                      <p className="text-red-500 text-sm">{passwordForm.formState.errors.old_password.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="new_password" className="text-slate-700 dark:text-slate-300">Nouveau mot de passe</Label>
                    <Input id="new_password" type="password" {...passwordForm.register("new_password")} className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                    {passwordForm.formState.errors.new_password && (
                      <p className="text-red-500 text-sm">{passwordForm.formState.errors.new_password.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="confirm_password" className="text-slate-700 dark:text-slate-300">Confirmer le nouveau mot de passe</Label>
                    <Input id="confirm_password" type="password" {...passwordForm.register("confirm_password")} className="mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600" />
                    {passwordForm.formState.errors.confirm_password && (
                      <p className="text-red-500 text-sm">{passwordForm.formState.errors.confirm_password.message}</p>
                    )}
                  </div>
                  <Button type="submit" disabled={changePasswordMutation.isPending} className="bg-[#0ABAB5] hover:bg-[#0a9e99] text-white px-6">
                    {changePasswordMutation.isPending ? "Modification..." : "Modifier le mot de passe"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet Préférences */}
          <TabsContent value="preferences" className="mt-6">
            <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Préférences</CardTitle>
                <CardDescription>Personnalisez votre expérience.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-slate-700 dark:text-slate-300">Langue</Label>
                    <Select
                      value={profileForm.watch("langue")}
                      onValueChange={(value) => profileForm.setValue("langue", value as "fr" | "en")}
                    >
                      <SelectTrigger className="w-full mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600">
                        <SelectValue placeholder="Sélectionner une langue" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fr">Français</SelectItem>
                        <SelectItem value="en">English</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-700 dark:text-slate-300">Devise</Label>
                    <Select
                      value={profileForm.watch("devise")}
                      onValueChange={(value) => profileForm.setValue("devise", value as "FCFA" | "EUR" | "USD")}
                    >
                      <SelectTrigger className="w-full mt-1 dark:bg-slate-700 dark:text-white dark:border-slate-600">
                        <SelectValue placeholder="Sélectionner une devise" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FCFA">FCFA</SelectItem>
                        <SelectItem value="EUR">Euro (€)</SelectItem>
                        <SelectItem value="USD">Dollar US ($)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-slate-700 dark:text-slate-300">Notifications par email</Label>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Recevoir les alertes par email.</p>
                  </div>
                  <Switch
                    checked={profileForm.watch("email_notifications")}
                    onCheckedChange={(checked) => profileForm.setValue("email_notifications", checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-slate-700 dark:text-slate-300">Notifications push</Label>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Recevoir les notifications dans le navigateur.</p>
                  </div>
                  <Switch
                    checked={profileForm.watch("push_notifications")}
                    onCheckedChange={(checked) => profileForm.setValue("push_notifications", checked)}
                  />
                </div>

                {/* Nouveau bouton pour activer réellement les notifications push */}
                <div className="pt-2">
                  <Button
                    type="button"
                    onClick={handleEnablePush}
                    className="bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white w-full sm:w-auto"
                  >
                    Activer les notifications push
                  </Button>
                </div>

                <Button onClick={profileForm.handleSubmit(onSubmitProfile)} disabled={updateProfileMutation.isPending} className="bg-[#0ABAB5] hover:bg-[#0a9e99] text-white px-6">
                  Enregistrer les préférences
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Onglet IA */}
          {me?.role === "ADMIN" && (
            <TabsContent value="ai" className="mt-6">
              <Card className="border-0 shadow-md rounded-2xl bg-white dark:bg-slate-800 overflow-hidden">
                <CardHeader className="bg-gradient-to-r from-[#0F1A2C] to-[#0ABAB5] text-white p-6">
                  <div className="flex items-center gap-3">
                    <Brain className="w-8 h-8 text-[#0ABAB5]" />
                    <div>
                      <CardTitle className="text-white text-2xl">Gestion du modèle IA</CardTitle>
                      <CardDescription className="text-gray-300">Performances, prédictions et entraînement</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-6 space-y-8">
                  {/* Indice de confiance */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                      <Target className="w-5 h-5 text-[#0ABAB5]" /> Indice de confiance
                    </h3>
                    {perfLoading ? (
                      <p className="text-slate-500 dark:text-slate-400">Chargement des métriques...</p>
                    ) : modelPerf ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-slate-700 dark:to-slate-700 p-6 rounded-2xl shadow-sm border border-blue-100 dark:border-slate-600">
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-bold text-blue-600 dark:text-blue-300 uppercase tracking-wider">Test</h4>
                            <Activity className="w-5 h-5 text-blue-400" />
                          </div>
                          <MetricRow label="MAE" value={modelPerf.test?.mae?.toFixed(2)} />
                          <MetricRow label="RMSE" value={modelPerf.test?.rmse?.toFixed(2)} />
                          <MetricRow label="MAPE" value={modelPerf.test?.mape?.toFixed(1)} unit="%" />
                          <MetricRow label="R²" value={modelPerf.test?.r2?.toFixed(3)} />
                        </div>
                        <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-slate-700 dark:to-slate-700 p-6 rounded-2xl shadow-sm border border-purple-100 dark:border-slate-600">
                          <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-bold text-purple-600 dark:text-purple-300 uppercase tracking-wider">Validation</h4>
                            <TrendingUp className="w-5 h-5 text-purple-400" />
                          </div>
                          <MetricRow label="MAE" value={modelPerf.validation?.mae?.toFixed(2)} />
                          <MetricRow label="RMSE" value={modelPerf.validation?.rmse?.toFixed(2)} />
                          <MetricRow label="MAPE" value={modelPerf.validation?.mape?.toFixed(1)} unit="%" />
                          <MetricRow label="R²" value={modelPerf.validation?.r2?.toFixed(3)} />
                        </div>
                      </div>
                    ) : (
                      <p className="text-slate-500 dark:text-slate-400">Métriques non disponibles.</p>
                    )}
                    {modelPerf && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-4">
                        Version <span className="font-semibold">{modelPerf.model_version}</span> | Entraîné le {modelPerf.trained_at}
                      </p>
                    )}
                  </div>

                  {/* Prédictions */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-[#0ABAB5]" /> Prédictions par médicament
                    </h3>
                    <select
                      className="w-full md:w-1/2 p-3 border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm focus:ring-2 focus:ring-[#0ABAB5] focus:border-transparent transition"
                      value={selectedMedicine}
                      onChange={(e) => setSelectedMedicine(e.target.value)}
                      disabled={medsLoading || medicines.length === 0}
                    >
                      <option value="" disabled>
                        {medsLoading ? "Chargement des médicaments..." : medicines.length === 0 ? "Aucun médicament disponible" : "Choisir un médicament"}
                      </option>
                      {medicines.map((med) => (
                        <option key={med.id} value={med.id}>
                          {med.commercial_name}
                        </option>
                      ))}
                    </select>

                    <div className="mt-6 bg-slate-50 dark:bg-slate-700/50 p-4 rounded-2xl">
                      {predLoading ? (
                        <p className="text-slate-500 dark:text-slate-400 text-center py-8">Chargement des prédictions...</p>
                      ) : predictionData && predictionData.predictions ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <AreaChart data={predictionData.predictions} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <defs>
                              <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#0ABAB5" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#0ABAB5" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 12 }} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                            <RechartsTooltip
                              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                              labelStyle={{ fontWeight: 'bold', color: '#0F1A2C' }}
                            />
                            <Legend verticalAlign="top" height={36} />
                            <Area
                              type="monotone"
                              dataKey="predicted_sales"
                              stroke="#0ABAB5"
                              strokeWidth={3}
                              fillOpacity={1}
                              fill="url(#colorPred)"
                              name="Ventes prévues"
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      ) : (
                        <p className="text-slate-500 dark:text-slate-400 text-center py-8">
                          Sélectionnez un médicament pour voir les prédictions.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* SHAP */}
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-2">Explicabilité (SHAP)</h3>
                    {shapLoading ? (
                      <p className="text-muted-foreground">Chargement SHAP...</p>
                    ) : shapData ? (
                      <ShapChart data={shapData} />
                    ) : (
                      <p className="text-muted-foreground">Sélectionnez un médicament pour voir l'importance des variables.</p>
                    )}
                  </div>

                  {/* Bouton entraînement */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    <Button
                      onClick={handleTrainModel}
                      disabled={trainingLoading}
                      className="bg-gradient-to-r from-[#0ABAB5] to-[#0a9e99] hover:from-[#0a9e99] hover:to-[#0ABAB5] text-white px-6 py-2 rounded-xl shadow-lg shadow-[#0ABAB5]/20 transition-all duration-300 disabled:opacity-60"
                    >
                      {trainingLoading ? (
                        <span className="flex items-center gap-2">
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Lancement en cours...
                        </span>
                      ) : (
                        "Lancer l'entraînement maintenant"
                      )}
                    </Button>
                    {trainingMessage && (
                      <p className="text-sm text-slate-600 dark:text-slate-300">{trainingMessage}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </main>
    </div>
  );
}
