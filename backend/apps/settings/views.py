# apps/settings/views.py
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import SiteSettings
import logging

logger = logging.getLogger(__name__)


class UploadLogoView(APIView):
    """Upload du logo"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # ✅ LOG pour déboguer
        logger.info(f"📤 Upload logo - Utilisateur: {request.user.email}")
        logger.info(f"📤 Fichiers reçus: {request.FILES.keys()}")
        logger.info(f"📤 Données reçues: {request.data.keys()}")
        
        # Vérifier les permissions
        if not request.user.is_staff and request.user.role != 'ADMIN':
            logger.warning(f"⛔ Permission refusée pour {request.user.email}")
            return Response(
                {'error': 'Seuls les administrateurs peuvent modifier le logo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ✅ Vérifier si le fichier est dans request.FILES
        image_file = request.FILES.get('logo')
        if not image_file:
            logger.warning("❌ Aucun fichier trouvé dans la requête")
            return Response(
                {'error': 'Aucun fichier fourni. Assurez-vous d\'utiliser le champ "logo" dans FormData.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ Vérifier le type de fichier
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp', 'image/svg+xml']
        content_type = image_file.content_type
        logger.info(f"📄 Type de fichier: {content_type}")
        
        if content_type not in allowed_types:
            return Response(
                {'error': f'Format non supporté: {content_type}. Utilisez: {", ".join(allowed_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ Vérifier la taille (5MB max)
        if image_file.size > 5 * 1024 * 1024:
            return Response(
                {'error': f'Fichier trop volumineux: {image_file.size} octets (max 5MB)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            site_settings = SiteSettings.get_settings()
            
            # Supprimer l'ancien logo
            if site_settings.logo:
                old_path = site_settings.logo.path
                if os.path.exists(old_path):
                    os.remove(old_path)
                    logger.info(f"🗑️ Ancien logo supprimé: {old_path}")
            
            # Sauvegarder le nouveau
            site_settings.logo = image_file
            site_settings.save()
            
            logger.info(f"✅ Logo mis à jour: {site_settings.logo.url}")
            
            return Response({
                'success': True,
                'message': 'Logo mis à jour avec succès',
                'logo_url': site_settings.logo.url
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Erreur upload: {str(e)}")
            return Response(
                {'error': f'Erreur lors de l\'upload: {str(e)}'},
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