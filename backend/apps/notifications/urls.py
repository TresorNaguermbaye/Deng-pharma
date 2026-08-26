from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, SubscribePushView, VapidPublicKeyView

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('subscribe/', SubscribePushView.as_view(), name='subscribe-push'),

    path('push/vapid-public-key/', VapidPublicKeyView.as_view(), name='vapid-public-key'),
    path('push/subscribe/', SubscribePushView.as_view(), name='push-subscribe'),
]
