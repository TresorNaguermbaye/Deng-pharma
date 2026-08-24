# ai_service/api/main.py
"""
DENG PHARMA - Service IA
API de prévision des ventes, détection ruptures, recommandations
Modèle XGBoost entraîné sur dataset Tchadien
"""
import json
from venv import logger

import requests
import subprocess
import sys

import shap
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import joblib
import os
from datetime import date, timedelta
import sqlite3

# Chemin vers la base de données SQLite de Django
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'db.sqlite3')

# ==========================================
# CHARGEMENT DU MODÈLE
# ==========================================
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

print("🚀 Démarrage de DENG PHARMA IA...")
print(f"📁 Dossier modèles : {MODELS_DIR}")

model = None
features_list = None

try:
    model_path = os.path.join(MODELS_DIR, 'xgboost_tchad.pkl')
    features_path = os.path.join(MODELS_DIR, 'features.pkl')
    model = joblib.load(model_path)
    features_list = joblib.load(features_path)
    print(f"✅ Modèle chargé : xgboost_tchad.pkl")
    print(f"📊 Features : {features_list}")
except FileNotFoundError as e:
    print(f"⚠️  Modèle non trouvé : {e}")
    print("   Lancez d'abord l'entraînement dans le notebook Jupyter")

# ==========================================
# APPLICATION FASTAPI
# ==========================================
app = FastAPI(
    title="DENG PHARMA - Service IA Tchad",
    description="""
    API intelligente de gestion pharmaceutique.
    
    ## Fonctionnalités :
    - **Prévision des ventes** : prédit les ventes pour les N prochains jours
    - **Détection ruptures/surstocks** : analyse le risque de rupture
    - **Recommandations de commandes** : calcule la quantité optimale à commander
    - **Score de criticité** : évalue l'importance des médicaments
    - **Analyse saisonnière** : conseils selon la saison (pluies/sèche)
    - **Chatbot assistant** : répond aux questions sur la gestion
    """,
    version="2.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ==========================================
# MODÈLES DE DONNÉES
# ==========================================
class PredictionRequest(BaseModel):
    medicine_id: str = "MED003"
    medicine_name: Optional[str] = None   # <-- ajout pour recevoir le nom commercial
    days_ahead: int = 7

class StockAnalysisRequest(BaseModel):
    medicine_id: str
    current_stock: float
    category: Optional[str] = None

class OrderRecommendationRequest(BaseModel):
    medicine_id: str
    current_stock: float
    lead_time_days: int = 7
    service_level: float = 0.95

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = {}

# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/")
def root():
    return {
        "service": "DENG PHARMA IA",
        "version": "2.0.0",
        "model_loaded": model is not None,
        "endpoints": ["/predict", "/analyze/stock", "/recommend/order", "/criticality", "/seasonal-analysis", "/chat"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "features": features_list
    }




@app.get("/model-performance")
def model_performance():
    """Retourne les métriques réelles sauvegardées lors du dernier entraînement."""
    try:
        metrics_path = os.path.join(MODELS_DIR, 'metrics.json')
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        return metrics
    except FileNotFoundError:
        return {
            "error": "Métriques non disponibles. Réentraînez le modèle.",
            "mae": None,
            "rmse": None,
            "mape": None,
            "model_version": None
        }


@app.post("/train")
def train_model_endpoint():
    """Lance l'entraînement du modèle en arrière-plan."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'training', 'train_model.py')
        subprocess.Popen([sys.executable, script_path])
        return {"status": "Entraînement lancé en arrière-plan"}
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du lancement : {e}")
    
# ---------- FONCTIONS UTILITAIRES POUR L'HISTORIQUE ----------


def get_commercial_name_from_uuid(medicine_uuid: str) -> Optional[str]:
    """Retourne le nom commercial à partir d'un UUID Django (sans tirets en base)."""
    conn = sqlite3.connect(DB_PATH)
    # Enlever les tirets car la base stocke l'UUID sans tirets (char(32))
    clean_uuid = medicine_uuid.replace('-', '')
    query = "SELECT commercial_name FROM medicines_medicine WHERE id = ?"
    cursor = conn.execute(query, (clean_uuid,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_medicine_history(identifier: str, medicine_name: Optional[str] = None, days: int = 30):
    conn = sqlite3.connect(DB_PATH)
    # Si un nom est fourni, on l'utilise directement
    if medicine_name:
        search_name = medicine_name
    else:
        # Sinon, essayer de retrouver le nom via l'UUID
        search_name = get_commercial_name_from_uuid(identifier)
        if not search_name:
            conn.close()
            return None

    query = """
        SELECT DATE(s.created_at) AS date, SUM(si.quantity) AS sales
        FROM sales_saleitem si
        JOIN sales_sale s ON si.sale_id = s.id
        JOIN medicines_medicine m ON si.medicine_id = m.id
        WHERE m.commercial_name = ?
        GROUP BY DATE(s.created_at)
        ORDER BY date DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(search_name, days))
    conn.close()
    if df.empty:
        return None
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return [float(x) for x in df['sales'].tolist()]



@app.post("/predict")
def predict_sales(request: PredictionRequest):
    if model is None:
        raise HTTPException(503, "Modèle non disponible.")

    today = date.today()
    predictions = []


    history = get_medicine_history(
    identifier=request.medicine_id,
    medicine_name=request.medicine_name,
    days=30
    )

    print(f"DEBUG: medicine_name reçu = '{request.medicine_name}', historique trouvé = {history is not None}, longueur = {len(history) if history else 0}")

    # Définir les lags à partir de l'historique, ou utiliser les valeurs par défaut
    base = 45.0
    season_factor = 1.5 if today.month in [6, 7, 8, 9, 10] else 1.0
    default_lag = base * season_factor

    if history and len(history) > 0:
        # Utiliser les données réelles, même si peu nombreuses
        lag_1 = history[-1] if len(history) >= 1 else default_lag
        lag_7 = history[-7] if len(history) >= 7 else (sum(history[-len(history):]) / len(history))
        lag_30 = history[0] if len(history) >= 1 else base
        rolling_mean_7 = sum(history[-min(7, len(history)):]) / min(7, len(history))
        rolling_mean_30 = sum(history) / len(history)
    else:
        lag_1 = default_lag
        lag_7 = default_lag
        lag_30 = base
        rolling_mean_7 = default_lag
        rolling_mean_30 = base

    for i in range(request.days_ahead):
        pred_date = today + timedelta(days=i+1)
        dow = pred_date.weekday()
        features = {
            'day_of_week': dow,
            'month': pred_date.month,
            'is_weekend': 1 if dow >= 5 else 0,
            'season': 1 if pred_date.month in [6, 7, 8, 9, 10] else 0,
            'lag_1': lag_1,
            'lag_7': lag_7,
            'lag_30': lag_30,
            'rolling_mean_7': rolling_mean_7,
            'rolling_mean_30': rolling_mean_30,
            'price': 2500
        }
        X = pd.DataFrame([features])[features_list]
        pred = float(model.predict(X)[0])
        pred = max(0.0, pred)
        lower = max(0.0, pred * 0.7)
        upper = pred * 1.3

        predictions.append({
            "date": pred_date.isoformat(),
            "predicted_sales": round(pred, 1),
            "lower_bound": round(lower, 1),
            "upper_bound": round(upper, 1)
        })

        # Mise à jour récursive des lags
        lag_30 = lag_7
        lag_7 = lag_1
        lag_1 = pred
        rolling_mean_30 = (rolling_mean_30 * 29 + lag_30) / 30.0
        rolling_mean_7 = (rolling_mean_7 * 6 + lag_1) / 7.0

    return {
        "medicine_id": request.medicine_id,
        "predictions": predictions,
        "model_version": "v2.0-personalized"
    }





# ---------- ANALYSE DE STOCK ----------
@app.post("/analyze/stock")
def analyze_stock(request: StockAnalysisRequest):
    """Analyse le risque de rupture ou surstock"""
    daily_demand = np.random.randint(20, 60)
    stock_days = request.current_stock / max(daily_demand, 1)
    
    if stock_days < 7:
        status = "RISQUE_RUPTURE"
        message = f"⚠️ Rupture probable dans {stock_days:.0f} jours"
        risk = 90
    elif stock_days < 14:
        status = "SURVEILLANCE"
        message = f"👀 Stock faible : {stock_days:.0f} jours restants"
        risk = 50
    elif stock_days > 60:
        status = "SURSTOCK"
        message = f"📦 Surstock : {stock_days:.0f} jours de stock"
        risk = 10
    else:
        status = "OK"
        message = f"✅ Stock normal : {stock_days:.0f} jours"
        risk = 5
    
    return {
        "medicine_id": request.medicine_id,
        "current_stock": request.current_stock,
        "daily_demand_estimated": daily_demand,
        "days_of_stock": round(stock_days, 1),
        "rupture_risk_percent": risk,
        "status": status,
        "message": message
    }

# ---------- RECOMMANDATION DE COMMANDE ----------
@app.post("/recommend/order")
def recommend_order(request: OrderRecommendationRequest):
    """Recommande la quantité optimale à commander"""
    daily_demand = np.random.uniform(15, 40)
    z_score = 1.65 if request.service_level == 0.95 else 1.28
    safety_stock = z_score * (daily_demand * 0.3) * np.sqrt(request.lead_time_days)
    reorder_point = daily_demand * request.lead_time_days + safety_stock
    order_quantity = max(0, reorder_point - request.current_stock)
    
    return {
        "medicine_id": request.medicine_id,
        "current_stock": request.current_stock,
        "recommended_order": round(order_quantity),
        "reorder_point": round(reorder_point),
        "safety_stock": round(safety_stock),
        "estimated_daily_demand": round(daily_demand, 1),
        "lead_time_days": request.lead_time_days,
        "message": f"📦 Commander {round(order_quantity)} unités" if order_quantity > 0 else "✅ Stock suffisant"
    }

# ---------- SCORE DE CRITICITÉ ----------
@app.get("/criticality")
def get_criticality(medicine_id: str = "MED003"):
    """Retourne le score de criticité"""
    scores = {
        "MED001": 85, "MED002": 75, "MED003": 95, "MED004": 85, "MED005": 65,
        "MED006": 55, "MED007": 75, "MED008": 90, "MED009": 80, "MED010": 85,
        "MED011": 95, "MED012": 75, "MED013": 45, "MED014": 55, "MED015": 65
    }
    score = scores.get(medicine_id, 50)
    
    if score >= 85: level, color = "CRITIQUE", "red"
    elif score >= 70: level, color = "ÉLEVÉ", "orange"
    elif score >= 50: level, color = "MOYEN", "yellow"
    else: level, color = "FAIBLE", "green"
    
    return {"medicine_id": medicine_id, "criticality_score": score, "level": level, "color": color}

# ---------- ANALYSE SAISONNIÈRE ----------
@app.get("/seasonal-analysis")
def seasonal_analysis():
    """Analyse saisonnière pour le Tchad"""
    today = date.today()
    is_rainy = today.month in [6,7,8,9,10]
    
    return {
        "date": today.isoformat(),
        "season": "Saison des pluies 🌧️" if is_rainy else "Saison sèche ☀️",
        "alerts": [
            "🦟 Pic de paludisme : renforcer antipaludéens" if is_rainy else "🏥 Saison méningite : prévoir vaccins",
            "💧 Maladies hydriques : stocker SRO" if is_rainy else "🫁 Infections respiratoires : antibiotiques"
        ],
        "priority_categories": ["Antipaludéens", "Réhydratation", "Antibiotiques"] if is_rainy else ["Vaccins", "Respiratoire", "Antibiotiques"]
    }





@app.get("/shap-analysis")
def shap_analysis(medicine_id: str):
    """Retourne l'importance des variables (SHAP) pour un médicament."""
    if model is None:
        raise HTTPException(503, "Modèle non disponible.")

    history = get_medicine_history(identifier=medicine_id, days=30)
    if not history or len(history) < 5:
        return {"error": "Pas assez d'historique pour calculer SHAP."}

    # Préparer les features basées sur le dernier jour de l'historique
    hist = history[-30:] if len(history) >= 30 else history
    if len(hist) < 30:
        hist = [45.0] * (30 - len(hist)) + hist  # valeur par défaut

    lag_1 = hist[-1]
    lag_7 = hist[-7]
    lag_30 = hist[0]
    rolling_mean_7 = sum(hist[-7:]) / 7
    rolling_mean_30 = sum(hist) / 30

    last_date = date.today() - timedelta(days=1)
    dow = last_date.weekday()
    month = last_date.month
    is_weekend = 1 if dow >= 5 else 0
    season = 1 if month in [6,7,8,9,10] else 0

    features = {
        'day_of_week': dow,
        'month': month,
        'is_weekend': is_weekend,
        'season': season,
        'lag_1': lag_1,
        'lag_7': lag_7,
        'lag_30': lag_30,
        'rolling_mean_7': rolling_mean_7,
        'rolling_mean_30': rolling_mean_30,
        'price': 2500
    }

    X = pd.DataFrame([features])[features_list]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    feature_importance = []
    for i, name in enumerate(features_list):
        feature_importance.append({
            "name": name,
            "importance": float(shap_values[0][i])
        })

    return {
        "medicine_id": medicine_id,
        "features": feature_importance
    }



# ---------- CHATBOT ASSISTANT ----------
@app.post("/chat")
def chat(request: ChatRequest):
    """Assistant IA pour la pharmacie"""
    msg = request.message.lower()
    
    reponses = {
        "rupture": "📊 Pour analyser un risque de rupture, utilisez /analyze/stock avec l'ID et le stock actuel.",
        "commander": "📦 Pour une recommandation de commande, utilisez /recommend/order.",
        "prévision": "📈 Pour les prévisions de ventes, utilisez /predict.",
        "paludisme": "🦟 En saison des pluies (juin-octobre), prévoyez un stock renforcé d'antipaludéens et de moustiquaires.",
        "méningite": "🏥 La méningite sévit en saison sèche (février-avril). Vérifiez vos stocks de vaccins.",
        "saison": "🌧️ Saison des pluies : juin-octobre (paludisme, diarrhées)\n☀️ Saison sèche : novembre-mai (méningite, infections respiratoires)",
    }
    
    for key, reponse in reponses.items():
        if key in msg:
            return {"reply": reponse, "timestamp": date.today().isoformat()}
    
    return {"reply": "Je peux vous aider sur : prévisions, ruptures, commandes, criticité, saisons. Que voulez-vous savoir ?", "timestamp": date.today().isoformat()}

print("\n✅ API DENG PHARMA prête !")
print("📖 Documentation : http://127.0.0.1:8001/docs")

