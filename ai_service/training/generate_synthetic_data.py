# ai_service/training/generate_synthetic_data.py
"""
Génère un jeu de données synthétique de ventes pour entraîner le modèle XGBoost.
À utiliser uniquement pour initialiser le pipeline MLOps.
En production, on utilisera les données réelles de la base.
"""
import os
import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

# Chemin de sortie
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(DATA_DIR, 'synthetic_sales.csv')

def generate_synthetic_data(days=365, n_medicines=50):
    """Génère des ventes quotidiennes synthétiques pour n_medicines."""
    # Noms de médicaments fictifs
    med_names = [
        "Paracétamol 500mg", "Amoxicilline 500mg", "Ibuprofène 400mg",
        "Arthéméther 20mg", "Quinine 300mg", "SRO Poudre",
        "Vaccin Méningite", "Amoxicilline 250mg", "Ciprofloxacine 500mg",
        "Diclofénac 50mg", "Vitamine C 1000mg", "Fer + Folate",
        "Artésunate 100mg", "Azithromycine 250mg", "Prednisone 20mg",
        "Métronidazole 500mg", "Chlorphéniramine 4mg", "Dextrométhorphane 15mg",
        "Oméprazole 20mg", "Salbutamol 100mcg"
    ][:n_medicines]

    # Générateur de dates
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)

    data = []
    for med_id, name in enumerate(med_names, start=1):
        base_sales = random.uniform(20, 80)  # ventes moyennes
        price = random.uniform(500, 5000)
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            # Saisonnalité : +50% en saison des pluies (juin-octobre)
            month = current_date.month
            seasonal_factor = 1.5 if month in [6,7,8,9,10] else 1.0
            # Effet weekend : +20% samedi
            dow = current_date.weekday()
            weekend_factor = 1.2 if dow == 5 else 1.0
            # Bruit aléatoire
            noise = np.random.normal(1.0, 0.3)
            sales = max(0, int(base_sales * seasonal_factor * weekend_factor * noise))
            data.append({
                'medicine_id': f'MED{med_id:03d}',
                'commercial_name': name,
                'price': price,
                'date': current_date.isoformat(),
                'sales': sales
            })

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Données synthétiques générées : {OUTPUT_CSV}")
    print(f"   {len(df)} lignes, {df['medicine_id'].nunique()} médicaments, {df['date'].nunique()} jours.")

if __name__ == "__main__":
    generate_synthetic_data()