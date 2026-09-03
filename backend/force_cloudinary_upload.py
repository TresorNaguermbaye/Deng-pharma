import os
import django
import requests
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import UserProfile
from django.core.files import File
from django.contrib.auth import get_user_model

User = get_user_model()

print("🔄 Upload forcé sur Cloudinary...")

user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ Aucun superutilisateur trouvé !")
    exit(1)

profile, created = UserProfile.objects.get_or_create(user=user)

# Logo par défaut
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/4315/4315609.png"

print(f"📥 Téléchargement depuis: {LOGO_URL}")

try:
    response = requests.get(LOGO_URL, timeout=10)
    if response.status_code == 200:
        if profile.photo:
            profile.photo.delete()
        profile.photo.save("logo_deng_pharma.png", File(BytesIO(response.content)), save=True)
        print(f"✅ Logo uploadé sur Cloudinary !")
        print(f"🔗 URL: {profile.photo.url}")
    else:
        print(f"❌ Erreur de téléchargement: {response.status_code}")
except Exception as e:
    print(f"❌ Erreur: {e}")