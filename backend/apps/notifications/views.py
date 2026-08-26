# apps/notifications/views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from .models import Notification, PushSubscription


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = None  # Vous pouvez définir un sérialiseur plus tard
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request):
        notifs = self.get_queryset()[:50]
        data = [{
            'id': n.id,
            'type': n.type,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifs]
        unread = self.get_queryset().filter(is_read=False).count()
        return Response({'notifications': data, 'unread_count': unread})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'status': 'ok'})


class VapidPublicKeyView(APIView):
    """Renvoie la clé publique VAPID pour le frontend."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'publicKey': settings.VAPID_PUBLIC_KEY})


class SubscribePushView(APIView):
    """
    Enregistre une souscription push pour l'utilisateur connecté.
    Supprime toutes les souscriptions précédentes de cet utilisateur
    pour éviter les doublons ou les conflits de clés.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get('endpoint')
        keys = request.data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not all([endpoint, p256dh, auth]):
            return Response({"error": "Paramètres manquants"}, status=400)

        # 1. Supprimer toutes les anciennes souscriptions de cet utilisateur
        PushSubscription.objects.filter(user=request.user).delete()

        # 2. Créer la nouvelle souscription
        PushSubscription.objects.create(
            user=request.user,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth
        )
        return Response({"success": True})