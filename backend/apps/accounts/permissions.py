from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """Autorise uniquement les utilisateurs ayant le rôle ADMIN."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'
    
class IsGestionnaire(BasePermission):
    """Autorise les gestionnaires et les administrateurs."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['ADMIN', 'GESTIONNAIRE']

class IsPharmacien(BasePermission):
    """Autorise les pharmaciens, gestionnaires et admins."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['ADMIN', 'GESTIONNAIRE', 'PHARMACIEN']

class IsAuditeur(BasePermission):
    """Autorise les auditeurs (lecture seule) et les administrateurs."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'ADMIN':
            return True
        if request.user.role == 'AUDITEUR' and request.method in SAFE_METHODS:
            return True
        return False

class AuditeurReadOnly(BasePermission):
    """Autorise les auditeurs en lecture seule, pas d'écriture."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'AUDITEUR':
            return request.method in SAFE_METHODS
        return True  # les autres rôles peuvent tout faire (selon leurs autres permissions)

class IsAdminOrReadOnly(BasePermission):
    """Lecture pour tous les utilisateurs authentifiés, écriture réservée aux admins/gestionnaires."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ['ADMIN', 'GESTIONNAIRE']

class CanManageSales(BasePermission):
    """Autorise la création de ventes pour pharmacien/gestionnaire/admin, lecture pour tous les authentifiés."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ['ADMIN', 'GESTIONNAIRE', 'PHARMACIEN']

class CanManageOrders(BasePermission):
    """Lecture pour tous les authentifiés, création/réception réservée aux admins/gestionnaires."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ['ADMIN', 'GESTIONNAIRE']
