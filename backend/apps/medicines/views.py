# backend/apps/medicines/views.py
from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Medicine, Category
from apps.accounts.permissions import IsAdminOrReadOnly
from .serializers import (
    MedicineListSerializer,
    MedicineDetailSerializer,
    CategorySerializer
)
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsAdminOrReadOnly
from apps.accounts.permissions import AuditeurReadOnly

class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD complet pour les catégories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
class MedicineViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les médicaments avec recherche, filtres et pagination.
    """
    queryset = Medicine.objects.select_related('category').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    # Filtres et recherche
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__id', 'manufacturer']  # Filtres exacts
    search_fields = ['commercial_name', 'dci', 'barcode', 'description']  # Recherche texte
    ordering_fields = ['commercial_name', 'selling_price', 'created_at']
    ordering = ['commercial_name']  # Tri par défaut

    def get_serializer_class(self):
        """Utilise le sérialiseur détaillé pour les actions de détail"""
        if self.action in ['create','retrieve', 'update', 'partial_update']:
            return MedicineDetailSerializer
        return MedicineListSerializer