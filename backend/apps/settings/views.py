# apps/settings/views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings

from .models import SiteSettings


class UploadLogoView(APIView):
    """Upload du logo"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Vérifier les permissions
        if not request.user.is_staff and request.user.role != 'ADMIN':
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier le fichier
        image_file = request.FILES.get('logo')
        if not image_file:
            return Response(
                {'error': 'Aucun fichier fourni'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier le type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response(
                {'error': 'Format non supporté'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier la taille (5MB max)
        if image_file.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'Fichier trop volumineux (max 5MB)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            site_settings = SiteSettings.get_settings()
            
            # Supprimer l'ancien logo
            if site_settings.logo:
                old_path = site_settings.logo.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Sauvegarder le nouveau
            site_settings.logo = image_file
            site_settings.save()
            
            return Response({
                'success': True,
                'message': 'Logo mis à jour avec succès',
                'logo_url': site_settings.logo.url
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetSiteSettingsView(APIView):
    """Récupère les paramètres du site"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        site_settings = SiteSettings.get_settings()
        
        return Response({
            'site_name': site_settings.site_name,
            'slogan': site_settings.slogan,
            'logo_url': site_settings.logo.url if site_settings.logo else None,
            'phone': site_settings.phone,
            'address': site_settings.address
        })