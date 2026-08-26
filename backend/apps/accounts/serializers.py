# backend/apps/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'last_login', 'is_active']
        read_only_fields = ['last_login']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data, password=password)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    
class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur du profil étendu (photo, langue, devise, notifications)."""
    class Meta:
        model = UserProfile
        fields = ['photo', 'langue', 'devise', 'email_notifications', 'push_notifications']

class UserMeSerializer(serializers.ModelSerializer):
    """Sérialiseur complet pour l'utilisateur connecté (profil + préférences)."""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'has_completed_onboarding', 'profile', 'full_name'
        ]
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
        # Vous pouvez ajouter ici la validation de robustesse si nécessaire :
        # validate_password(data['new_password'], self.context['request'].user)
        return data