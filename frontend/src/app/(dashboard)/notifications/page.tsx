"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bell, CheckCheck, AlertTriangle, Package, Clock, Brain } from "lucide-react";

export default function NotificationsPage() {
  const [notifs, setNotifs] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);

  useEffect(() => { loadNotifs(); }, []);

  const loadNotifs = async () => {
    try {
      const data = await api.getNotifications();
      setNotifs(data.notifications || []);
      setUnread(data.unread_count || 0);
    } catch (err) {
      console.error("Erreur chargement notifications:", err);
    }
  };

  const markAllRead = async () => {
    await api.markAllNotificationsRead();
    loadNotifs();
  };

  const typeIcon = (type: string) => {
    switch (type) {
      case "STOCK_OUT": return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case "STOCK_LOW": return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "EXPIRY_SOON": return <Clock className="w-5 h-5 text-orange-500" />;
      case "OVERSTOCK": return <Package className="w-5 h-5 text-blue-500" />;
      case "AI_PREDICTION": return <Brain className="w-5 h-5 text-purple-500" />;
      default: return <Bell className="w-5 h-5 text-slate-500" />;
    }
  };

  const typeLabel = (type: string) => {
    const labels: Record<string, string> = {
      STOCK_OUT: "Rupture", STOCK_LOW: "Stock faible", EXPIRY_SOON: "Expiration",
      OVERSTOCK: "Surstock", AI_PREDICTION: "IA", TRAINING_COMPLETE: "IA"
    };
    return labels[type] || type;
  };

  return (
    <div className="space-y-6 p-4 md:p-8 bg-slate-50 dark:bg-slate-900 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            Notifications
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">{unread} non lue(s)</p>
        </div>
        {unread > 0 && (
          <Button
            variant="outline"
            onClick={markAllRead}
            className="dark:border-slate-600 dark:text-slate-300"
          >
            <CheckCheck className="w-4 h-4 mr-2" /> Tout marquer comme lu
          </Button>
        )}
      </div>

      <Card className="border-0 shadow-md dark:bg-slate-800 dark:border-slate-700">
        <CardContent className="p-0">
          {notifs.length === 0 ? (
            <p className="text-center text-slate-400 dark:text-slate-500 py-12">Aucune notification</p>
          ) : (
            notifs.map((n: any) => (
              <div
                key={n.id}
                className={`flex items-start gap-4 p-4 border-b last:border-0 ${
                  n.is_read
                    ? "bg-white dark:bg-slate-800"
                    : "bg-blue-50 dark:bg-slate-700/50"
                }`}
              >
                {typeIcon(n.type)}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Badge className="text-xs dark:bg-slate-600 dark:text-slate-200">
                      {typeLabel(n.type)}
                    </Badge>
                    {!n.is_read && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
                  </div>
                  <p className="text-sm mt-1 text-slate-900 dark:text-white">{n.message}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                    {new Date(n.created_at).toLocaleString('fr-FR')}
                  </p>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}