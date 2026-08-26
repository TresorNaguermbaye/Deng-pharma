# backend/apps/accounts/views.py
import logging

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from .models import User, UserProfile
from .serializers import (
    UserSerializer,
    UserMeSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les utilisateurs (réservé aux administrateurs).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
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
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        profile, created = UserProfile.objects.get_or_create(user=user)
        if 'langue' in request.data:
            profile.langue = request.data['langue']
        if 'devise' in request.data:
            profile.devise = request.data['devise']
        if 'email_notifications' in request.data:
            profile.email_notifications = self._to_bool(request.data['email_notifications'])
        if 'push_notifications' in request.data:
            profile.push_notifications = self._to_bool(request.data['push_notifications'])
        profile.save()

        serializer = UserMeSerializer(user, context={'request': request})
        return Response(serializer.data)

    def _to_bool(self, value):
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
    """Demande de réinitialisation : génère un token standard et envoie un email."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

            subject = "Réinitialisation de votre mot de passe - DENG PHARMA"
            message = f"""
Bonjour {user.username},

Cliquez sur le lien suivant pour réinitialiser votre mot de passe :
{reset_url}

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
"""
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            except Exception as e:
                logger.error(f"Erreur envoi email réinitialisation: {e}")
                return Response({'error': "Erreur lors de l'envoi de l'email."}, status=500)

        return Response({'success': 'Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.'})


class PasswordResetConfirmView(APIView):
    """Réinitialise le mot de passe avec uid et token standards."""
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([uid, token, new_password]):
            return Response({'error': 'Paramètres manquants.'}, status=400)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        token_generator = PasswordResetTokenGenerator()
        if user is None or not token_generator.check_token(user, token):
            return Response({'error': 'Lien de réinitialisation invalide ou expiré.'}, status=400)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'success': 'Mot de passe réinitialisé avec succès.'})


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
        admin_user = User.objects.filter(role='ADMIN', profile__photo__isnull=False).first()
        if admin_user and admin_user.profile.photo:
            logo_url = request.build_absolute_uri(admin_user.profile.photo.url)
            return Response({"logo_url": logo_url})
        return Response({"logo_url": None})