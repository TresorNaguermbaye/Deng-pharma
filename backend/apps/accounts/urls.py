from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView, TokenRefreshView
from .views import ChangePasswordView, CompleteOnboardingView, MeView, UploadPhotoView, UserViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')


urlpatterns = [
    # Routes JWT existantes (simplifiées ici)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Nouvelles routes
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('upload-photo/', UploadPhotoView.as_view(), name='upload-photo'),
    path('onboarding/complete/', CompleteOnboardingView.as_view(), name='complete-onboarding'),

    # Inclut les routes du routeur (users)
    path('', include(router.urls)),
]