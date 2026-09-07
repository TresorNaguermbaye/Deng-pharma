# apps/settings/urls.py
from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('upload-logo/', views.UploadLogoView.as_view(), name='upload-logo'),
    path('settings/', views.GetSiteSettingsView.as_view(), name='site-settings'),
]