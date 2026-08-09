# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminRole(BasePermission):
    """Accès uniquement aux administrateurs."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class IsGestionnaireRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'GESTIONNAIRE'

class IsPharmacienRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'PHARMACIEN'

class IsAuditeurRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'AUDITEUR'

class IsAdminOrGestionnaire(BasePermission):
    """Admin ou Gestionnaire uniquement."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['ADMIN', 'GESTIONNAIRE']

class AuditeurReadOnly(BasePermission):
    """
    Les auditeurs ont un accès en lecture seule.
    Les autres rôles (gérés par d'autres permissions) n'ont pas de restriction ici.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'AUDITEUR':
            return request.method in SAFE_METHODS
        return True  # Les autres rôles passeront, leur propre permission sera vérifiée ailleurs.