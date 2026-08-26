import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import PushSubscription

def send_push_notification(user, title, body):
    """Envoie une notification push à l'utilisateur."""
    subscriptions = PushSubscription.objects.filter(user=user)
    payload = json.dumps({"title": title, "body": body})   # <-- conversion en chaîne JSON
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=payload,   # <-- on passe la chaîne JSON
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"}
            )
        except WebPushException as ex:
            print(f"Erreur push pour {user.username}: {ex}")