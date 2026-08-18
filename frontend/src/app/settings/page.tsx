"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
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

export default function SettingsPage() {
  const { token } = useAuth();

  const { data: me, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const res = await axios.get("http://localhost:8000/api/auth/me/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      return res.data;
    },
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
    mutationFn: async (values: ProfileFormValues) => {
      const res = await axios.put("http://localhost:8000/api/auth/me/", values, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return res.data;
    },
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
    mutationFn: async (values: PasswordFormValues) => {
      const res = await axios.post("http://localhost:8000/api/auth/change-password/", values, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return res.data;
    },
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
    formData.append("photo", file);
    try {
      await axios.post("http://localhost:8000/api/auth/upload-photo/", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });
      toast.success("Photo mise à jour");
      window.location.reload();
    } catch {
      toast.error("Erreur lors de l'upload");
    }
  };

  if (isLoading) return <div>Chargement...</div>;

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Paramètres</h1>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList>
          <TabsTrigger value="profile">Profil</TabsTrigger>
          <TabsTrigger value="password">Mot de passe</TabsTrigger>
          <TabsTrigger value="preferences">Préférences</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Informations personnelles</CardTitle>
              <CardDescription>Mettez à jour votre nom, email et photo.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={me?.profile?.photo || ""} />
                  <AvatarFallback>
                    {me?.first_name?.[0]}
                    {me?.last_name?.[0]}
                  </AvatarFallback>
                </Avatar>
                <label className="cursor-pointer">
                  <span className="bg-secondary text-secondary-foreground px-4 py-2 rounded-md text-sm">
                    Changer la photo
                  </span>
                  <input type="file" accept="image/*" className="hidden" onChange={handlePhotoUpload} />
                </label>
              </div>

              <form onSubmit={profileForm.handleSubmit(onSubmitProfile)} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">Prénom</Label>
                    <Input id="first_name" {...profileForm.register("first_name")} />
                    {profileForm.formState.errors.first_name && (
                      <p className="text-red-500 text-sm">{profileForm.formState.errors.first_name.message}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="last_name">Nom</Label>
                    <Input id="last_name" {...profileForm.register("last_name")} />
                    {profileForm.formState.errors.last_name && (
                      <p className="text-red-500 text-sm">{profileForm.formState.errors.last_name.message}</p>
                    )}
                  </div>
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" {...profileForm.register("email")} />
                  {profileForm.formState.errors.email && (
                    <p className="text-red-500 text-sm">{profileForm.formState.errors.email.message}</p>
                  )}
                </div>
                <Button type="submit" disabled={updateProfileMutation.isPending}>
                  {updateProfileMutation.isPending ? "Enregistrement..." : "Enregistrer"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="password">
          <Card>
            <CardHeader>
              <CardTitle>Changer le mot de passe</CardTitle>
              <CardDescription>Utilisez un mot de passe fort et unique.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={passwordForm.handleSubmit(onSubmitPassword)} className="space-y-4">
                <div>
                  <Label htmlFor="old_password">Ancien mot de passe</Label>
                  <Input id="old_password" type="password" {...passwordForm.register("old_password")} />
                  {passwordForm.formState.errors.old_password && (
                    <p className="text-red-500 text-sm">{passwordForm.formState.errors.old_password.message}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="new_password">Nouveau mot de passe</Label>
                  <Input id="new_password" type="password" {...passwordForm.register("new_password")} />
                  {passwordForm.formState.errors.new_password && (
                    <p className="text-red-500 text-sm">{passwordForm.formState.errors.new_password.message}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="confirm_password">Confirmer le nouveau mot de passe</Label>
                  <Input id="confirm_password" type="password" {...passwordForm.register("confirm_password")} />
                  {passwordForm.formState.errors.confirm_password && (
                    <p className="text-red-500 text-sm">{passwordForm.formState.errors.confirm_password.message}</p>
                  )}
                </div>
                <Button type="submit" disabled={changePasswordMutation.isPending}>
                  {changePasswordMutation.isPending ? "Modification..." : "Modifier le mot de passe"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences">
          <Card>
            <CardHeader>
              <CardTitle>Préférences</CardTitle>
              <CardDescription>Personnalisez votre expérience.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Langue</Label>
                  <Select
                    value={profileForm.watch("langue")}
                    onValueChange={(value) => profileForm.setValue("langue", value as "fr" | "en")}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sélectionner une langue" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fr">Français</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Devise</Label>
                  <Select
                    value={profileForm.watch("devise")}
                    onValueChange={(value) => profileForm.setValue("devise", value as "FCFA" | "EUR" | "USD")}
                  >
                    <SelectTrigger>
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
                  <Label>Notifications par email</Label>
                  <p className="text-sm text-muted-foreground">Recevoir les alertes par email.</p>
                </div>
                <Switch
                  checked={profileForm.watch("email_notifications")}
                  onCheckedChange={(checked) => profileForm.setValue("email_notifications", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Notifications push</Label>
                  <p className="text-sm text-muted-foreground">Recevoir les notifications dans le navigateur.</p>
                </div>
                <Switch
                  checked={profileForm.watch("push_notifications")}
                  onCheckedChange={(checked) => profileForm.setValue("push_notifications", checked)}
                />
              </div>
              <Button onClick={profileForm.handleSubmit(onSubmitProfile)} disabled={updateProfileMutation.isPending}>
                Enregistrer les préférences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}