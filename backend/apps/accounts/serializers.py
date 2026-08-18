# backend/apps/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile

class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste et la gestion des utilisateurs (admin)."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'last_login', 'is_active']
        read_only_fields = ['last_login']

class UserAccountSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les informations de base de l'utilisateur connecté.
    (Ancien UserProfileSerializer renommé pour éviter la confusion avec le profil étendu)
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'last_login']
        read_only_fields = ['id', 'role', 'is_active', 'last_login']

class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le profil étendu (préférences, photo)."""
    class Meta:
        model = UserProfile
        fields = ['photo', 'langue', 'devise', 'email_notifications', 'push_notifications']

class UserMeSerializer(serializers.ModelSerializer):
    """Sérialiseur complet pour l'utilisateur connecté, incluant le profil étendu."""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'has_completed_onboarding', 'profile', 'full_name']
        read_only_fields = ['id', 'username', 'role', 'has_completed_onboarding']

    def get_full_name(self, obj):
        return obj.get_full_name()

class ChangePasswordSerializer(serializers.Serializer):
    """Sérialiseur pour le changement de mot de passe."""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        # Optionnel : valider la robustesse du mot de passe
        # validate_password(data['new_password'], self.context['request'].user)
        return data