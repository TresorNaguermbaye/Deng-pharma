# backend/apps/accounts/views.py
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetToken
import uuid

from .models import User, UserProfile
from .serializers import (
    UserSerializer,
    UserMeSerializer,
    ChangePasswordSerializer,
)

class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les utilisateurs (réservé aux administrateurs).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]  # Seul l'admin peut gérer les utilisateurs

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtrage optionnel par rôle
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

class MeView(APIView):
    """Récupère ou met à jour le profil de l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        # Mise à jour des champs de base
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        # Mise à jour ou création du profil étendu
        profile, created = UserProfile.objects.get_or_create(user=user)
        if 'langue' in request.data:
            profile.langue = request.data['langue']
        if 'devise' in request.data:
            profile.devise = request.data['devise']
        # Conversion des booléens (peuvent arriver comme string "true"/"false")
        if 'email_notifications' in request.data:
            profile.email_notifications = self._to_bool(request.data['email_notifications'])
        if 'push_notifications' in request.data:
            profile.push_notifications = self._to_bool(request.data['push_notifications'])
        profile.save()

        serializer = UserMeSerializer(user, context={'request': request})
        return Response(serializer.data)

    def _to_bool(self, value):
        """Convertit une valeur en booléen, qu'elle soit bool, string ou int."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        if isinstance(value, int):
            return value != 0
        return False

class ChangePasswordView(APIView):
    """Change le mot de passe de l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"error": "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                validate_password(serializer.validated_data['new_password'], user)
            except ValidationError as e:
                return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"success": "Mot de passe modifié avec succès."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UploadPhotoView(APIView):
    """Upload de la photo de profil."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
            profile.save()
            return Response({"photo_url": request.build_absolute_uri(profile.photo.url)}, status=status.HTTP_200_OK)
        return Response({"error": "Aucun fichier photo fourni."}, status=status.HTTP_400_BAD_REQUEST)



class PasswordResetRequestView(APIView):
    """Demande de réinitialisation : génère un token et envoie un email."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Supprimer les anciens tokens non utilisés pour cet utilisateur
            PasswordResetToken.objects.filter(user=user, is_used=False).delete()
            # Créer un nouveau token
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=1)  # valable 1 heure
            )
            # Construire le lien de réinitialisation
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
            subject = "Réinitialisation de votre mot de passe DENG PHARMA"
            message = f"""
Bonjour {user.first_name or user.username},

Vous avez demandé la réinitialisation de votre mot de passe.
Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe (valable 1 heure) :

{reset_url}

Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

Cordialement,
L'équipe DENG PHARMA
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        # Toujours renvoyer le même message (sécurité)
        return Response({"message": "Si un compte existe, un email de réinitialisation a été envoyé."})

class PasswordResetConfirmView(APIView):
    """Réinitialisation du mot de passe avec token."""
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token_str or not new_password:
            return Response({"error": "Token et nouveau mot de passe requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Token invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        if not token.is_valid():
            return Response({"error": "Token invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        user = token.user
        user.set_password(new_password)
        user.save()

        # Marquer le token comme utilisé
        token.is_used = True
        token.save()

        return Response({"success": "Mot de passe mis à jour avec succès."})



class CompleteOnboardingView(APIView):
    """Marque l'onboarding comme terminé pour l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.has_completed_onboarding = True
        user.save(update_fields=['has_completed_onboarding'])
        return Response({"status": "onboarding completed"})

class PharmacyLogoView(APIView):
    """Renvoie l'URL du logo de la pharmacie (photo du premier admin)."""
    permission_classes = [AllowAny]

    def get(self, request):
        # Récupère le premier utilisateur avec rôle ADMIN ayant une photo de profil
        admin_user = User.objects.filter(role='ADMIN', profile__photo__isnull=False).first()
        if admin_user and admin_user.profile.photo:
            logo_url = request.build_absolute_uri(admin_user.profile.photo.url)
            return Response({"logo_url": logo_url})
        return Response({"logo_url": None})
