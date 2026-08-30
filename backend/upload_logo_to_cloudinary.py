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

print("🔄 Upload du logo vers Cloudinary...")

# 1. Vérifier que Cloudinary est bien configuré
print(f"📁 DEFAULT_FILE_STORAGE: {django.conf.settings.DEFAULT_FILE_STORAGE}")

# 2. Récupérer le superutilisateur
user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ Aucun superutilisateur trouvé !")
    exit(1)

print(f"👤 Superutilisateur: {user.username}")

# 3. Récupérer ou créer le profil
profile, created = UserProfile.objects.get_or_create(user=user)

# 4. URL d'un logo par défaut (tu peux changer)
LOGO_URL = "https://i.imgur.com/5X7u8KQ.png"  # Logo par défaut DENG PHARMA
# Si tu as une autre URL, mets-la ici

print(f"📥 Téléchargement du logo depuis: {LOGO_URL}")

try:
    response = requests.get(LOGO_URL, timeout=10)
    if response.status_code == 200:
        # Créer un fichier à partir de l'image
        image_content = BytesIO(response.content)
        filename = "logo_deng_pharma.png"
        
        # Sauvegarder le logo (Cloudinary sera utilisé si configuré)
        profile.photo.save(filename, File(image_content), save=True)
        print(f"✅ Logo uploadé avec succès !")
        print(f"🔗 URL: {profile.photo.url}")
    else:
        print(f"❌ Erreur de téléchargement: {response.status_code}")
except Exception as e:
    print(f"❌ Erreur: {e}")