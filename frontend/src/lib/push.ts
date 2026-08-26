// src/lib/push.ts

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function subscribeToPush(api: any) {
  if (!("Notification" in window) || !("serviceWorker" in navigator)) {
    console.warn("Notifications push non supportées");
    return;
  }

  // 1. Demander la permission
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Permission refusée");
  }

  // 2. Attendre que le service worker soit prêt
  const registration = await navigator.serviceWorker.ready;

  // 3. Supprimer une ancienne souscription si elle existe
  const existing = await registration.pushManager.getSubscription();
  if (existing) {
    await existing.unsubscribe();
    console.log("Ancienne souscription push supprimée");
  }

  // 4. Récupérer la clé publique VAPID depuis le backend
const vapidResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/notifications/push/vapid-public-key/`);
  if (!vapidResponse.ok) {
    throw new Error("Impossible de récupérer la clé VAPID");
  }
  const { publicKey } = await vapidResponse.json();

  // 5. S'abonner avec cette clé
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey),
  });

  // 6. Envoyer la souscription au backend
  const token = api.getToken();
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/notifications/subscribe/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(subscription.toJSON()),
  });

  if (!response.ok) {
    throw new Error("Erreur lors de l'enregistrement de la souscription");
  }

  return subscription;
}