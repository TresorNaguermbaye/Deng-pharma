# ai_service/api/main.py
"""
DENG PHARMA - Service IA
Version 3.0 - Utilisation des données réelles de la base PostgreSQL
"""
import json
import os
import sys
import subprocess
import urllib.parse
from datetime import date, timedelta
from typing import Optional, List, Dict

import joblib
import numpy as np
import pandas as pd
import psycopg2
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CONNEXION À LA BASE DE DONNÉES POSTGRESQL
# ==========================================

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Retourne une connexion à la base de données PostgreSQL"""
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL non définie !")
        return None
    try:
        result = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port or 5432
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à la base: {e}")
        return None

# ==========================================
# FONCTIONS D'ACCÈS AUX DONNÉES RÉELLES
# ==========================================

def get_commercial_name_from_uuid(identifier: str) -> Optional[str]:
    """
    Récupère le nom commercial d'un médicament depuis PostgreSQL.
    Supporte à la fois les UUID avec et sans tirets.
    """
    if not identifier:
        return None
    
    # Nettoyer l'identifiant
    clean_uuid = identifier.strip()
    
    # Si c'est un UUID avec tirets, les enlever
    if '-' in clean_uuid:
        clean_uuid = clean_uuid.replace('-', '')
    
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Essayer d'abord avec l'UUID complet
        query = """
            SELECT commercial_name 
            FROM medicines_medicine 
            WHERE REPLACE(id::text, '-', '') = %s 
               OR id::text = %s
        """
        cursor.execute(query, (clean_uuid, identifier.strip()))
        row = cursor.fetchone()
        
        # Si pas trouvé, essayer avec le nom commercial partiel
        if not row:
            query = """
                SELECT commercial_name 
                FROM medicines_medicine 
                WHERE commercial_name ILIKE %s
            """
            cursor.execute(query, (f'%{identifier.strip()}%',))
            row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            logger.info(f"✅ Nom commercial trouvé: {row[0]}")
            return row[0]
        else:
            logger.warning(f"⚠️ Aucun médicament trouvé pour l'identifiant: {identifier}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erreur base de données (get_commercial_name): {e}")
        return None

def get_medicine_history(identifier: str, medicine_name: Optional[str] = None, days: int = 30) -> Optional[List[float]]:
    """
    Récupère l'historique des ventes réelles depuis PostgreSQL.
    """
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Impossible de se connecter à la base de données")
            return None
        
        cursor = conn.cursor()
        
        # Déterminer le nom commercial à rechercher
        if medicine_name:
            search_name = medicine_name
        else:
            search_name = get_commercial_name_from_uuid(identifier)
            if not search_name:
                logger.warning(f"⚠️ Aucun nom commercial trouvé pour {identifier}")
                cursor.close()
                conn.close()
                return None
        
        # ✅ REQUÊTE CORRIGÉE
        # 1. Utiliser l'ID du médicament directement pour éviter les problèmes de nom
        # 2. Récupérer d'abord l'ID du médicament
        
        # Récupérer l'ID du médicament
        med_id = None
        if identifier:
            clean_id = identifier.replace('-', '')
            cursor.execute("""
                SELECT id FROM medicines_medicine 
                WHERE REPLACE(id::text, '-', '') = %s OR id::text = %s
            """, (clean_id, identifier))
            row = cursor.fetchone()
            if row:
                med_id = row[0]
        
        if not med_id:
            # Si pas trouvé par ID, chercher par nom
            cursor.execute("""
                SELECT id FROM medicines_medicine 
                WHERE commercial_name ILIKE %s
            """, (f'%{search_name}%',))
            row = cursor.fetchone()
            if row:
                med_id = row[0]
        
        if not med_id:
            logger.warning(f"⚠️ Aucun médicament trouvé pour {search_name}")
            cursor.close()
            conn.close()
            return None
        
        # ✅ Récupérer l'historique des ventes pour ce médicament spécifique
        query = """
            SELECT 
                DATE(s.created_at) AS date,
                COALESCE(SUM(si.quantity), 0) AS total_quantity
            FROM sales_saleitem si
            INNER JOIN sales_sale s ON si.sale_id = s.id
            WHERE si.medicine_id = %s
              AND s.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(s.created_at)
            ORDER BY date ASC
        """
        
        logger.info(f"🔍 Recherche de l'historique pour médicament ID: {med_id}")
        cursor.execute(query, (med_id, days))
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not rows:
            logger.warning(f"⚠️ Aucune vente trouvée pour le médicament {search_name} (ID: {med_id})")
            return None
        
        # Construire la liste des ventes
        result = []
        for row in rows:
            result.append(float(row[1]) if row[1] else 0.0)
        
        logger.info(f"✅ {len(result)} jours d'historique récupérés pour {search_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de l'historique: {e}")
        return None

def get_medicine_stock(identifier: str) -> Optional[float]:
    """
    Récupère le stock actuel d'un médicament depuis PostgreSQL.
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Récupérer le stock total pour ce médicament
        query = """
            SELECT COALESCE(SUM(l.quantity), 0) as total_stock
            FROM inventory_stocklot l
            INNER JOIN medicines_medicine m ON l.medicine_id = m.id
            WHERE m.id::text = %s OR m.commercial_name ILIKE %s
        """
        
        clean_id = identifier.replace('-', '')
        cursor.execute(query, (clean_id, f'%{identifier}%'))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            return float(row[0])
        else:
            return None
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du stock: {e}")
        return None

# ==========================================
# CHARGEMENT DU MODÈLE
# ==========================================

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

logger.info("🚀 Démarrage de DENG PHARMA IA...")
logger.info(f"📁 Dossier modèles : {MODELS_DIR}")

model = None
features_list = None

try:
    model_path = os.path.join(MODELS_DIR, 'xgboost_tchad.pkl')
    features_path = os.path.join(MODELS_DIR, 'features.pkl')
    model = joblib.load(model_path)
    features_list = joblib.load(features_path)
    logger.info(f"✅ Modèle chargé : xgboost_tchad.pkl")
    logger.info(f"📊 Features : {features_list}")
except FileNotFoundError as e:
    logger.warning(f"⚠️ Modèle non trouvé : {e}")
    logger.warning("   Lancez d'abord l'entraînement dans le notebook Jupyter")

# ==========================================
# APPLICATION FASTAPI
# ==========================================

app = FastAPI(
    title="DENG PHARMA - Service IA Tchad",
    description="""
    API intelligente de gestion pharmaceutique.
    Utilise les données réelles de la base PostgreSQL.
    
    ## Fonctionnalités :
    - **Prévision des ventes** : prédit les ventes pour les N prochains jours basé sur l'historique réel
    - **Détection ruptures/surstocks** : analyse le risque de rupture avec données réelles
    - **Recommandations de commandes** : calcule la quantité optimale à commander
    """,
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==========================================
# MODÈLES DE DONNÉES
# ==========================================

class PredictionRequest(BaseModel):
    medicine_id: str
    medicine_name: Optional[str] = None
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
        "version": "3.0.0",
        "model_loaded": model is not None,
        "database": "PostgreSQL (données réelles)",
        "endpoints": ["/predict", "/analyze/stock", "/recommend/order", "/criticality", "/seasonal-analysis", "/chat", "/health", "/model-performance", "/shap-analysis", "/train"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "database": "PostgreSQL",
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

# ==========================================
# PRÉDICTION DES VENTES - VERSION RÉELLE
# ==========================================

@app.post("/predict")
def predict_sales(request: PredictionRequest):
    """Prédit les ventes en utilisant l'historique réel du médicament"""
    if model is None:
        raise HTTPException(503, "Modèle non disponible.")
    
    # 1. Récupérer l'historique réel
    history = get_medicine_history(
        identifier=request.medicine_id,
        medicine_name=request.medicine_name,
        days=30
    )
    
    # 2. Vérifier que nous avons assez de données
    if not history or len(history) < 3:
        logger.warning(f"⚠️ Pas assez d'historique pour {request.medicine_id}")
        return {
            "medicine_id": request.medicine_id,
            "error": "Pas assez de données d'historique",
            "message": "Veuillez créer des ventes pour ce médicament avant de faire des prédictions",
            "historical_data_found": len(history) if history else 0,
            "minimum_required": 3
        }
    
    logger.info(f"📊 Historique récupéré: {len(history)} jours pour {request.medicine_id}")
    
    # 3. Calculer les lags à partir des données réelles
    today = date.today()
    base = 45.0
    season_factor = 1.5 if today.month in [6, 7, 8, 9, 10] else 1.0
    
    # Utiliser les données réelles
    lag_1 = history[-1] if len(history) >= 1 else base * season_factor
    lag_7 = history[-7] if len(history) >= 7 else sum(history[-len(history):]) / len(history)
    lag_30 = history[0] if len(history) >= 1 else base
    rolling_mean_7 = sum(history[-min(7, len(history)):]) / min(7, len(history))
    rolling_mean_30 = sum(history) / len(history)
    
    logger.info(f"📈 Lags calculés: lag_1={lag_1:.1f}, lag_7={lag_7:.1f}, lag_30={lag_30:.1f}")
    
    # 4. Générer les prédictions
    predictions = []
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
    
    # 5. Récupérer le stock actuel
    current_stock = get_medicine_stock(request.medicine_id)
    
    return {
        "medicine_id": request.medicine_id,
        "medicine_name": get_commercial_name_from_uuid(request.medicine_id),
        "predictions": predictions,
        "current_stock": current_stock,
        "historical_data_days": len(history),
        "model_version": "v3.0-realtime",
        "database": "PostgreSQL (données réelles)"
    }

# ==========================================
# ANALYSE DE STOCK - AVEC DONNÉES RÉELLES
# ==========================================

@app.post("/analyze/stock")
def analyze_stock(request: StockAnalysisRequest):
    """Analyse le risque de rupture en utilisant les données réelles"""
    
    # 1. Récupérer l'historique pour estimer la demande quotidienne réelle
    history = get_medicine_history(
        identifier=request.medicine_id,
        days=30
    )
    
    # 2. Estimer la demande quotidienne à partir des données réelles
    if history and len(history) > 0:
        daily_demand = sum(history) / len(history)
        logger.info(f"📊 Demande quotidienne estimée: {daily_demand:.1f} unités")
    else:
        daily_demand = 25.0  # Valeur par défaut si pas d'historique
        logger.warning(f"⚠️ Pas d'historique, utilisation de la valeur par défaut: {daily_demand}")
    
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
        "daily_demand_estimated": round(daily_demand, 1),
        "days_of_stock": round(stock_days, 1),
        "rupture_risk_percent": risk,
        "status": status,
        "message": message,
        "based_on": "données réelles" if history else "valeur par défaut"
    }

# ==========================================
# RECOMMANDATION DE COMMANDE - AVEC DONNÉES RÉELLES
# ==========================================

@app.post("/recommend/order")
def recommend_order(request: OrderRecommendationRequest):
    """Recommande la quantité optimale à commander en utilisant les données réelles"""
    
    # 1. Récupérer l'historique pour estimer la demande quotidienne réelle
    history = get_medicine_history(
        identifier=request.medicine_id,
        days=30
    )
    
    # 2. Estimer la demande quotidienne à partir des données réelles
    if history and len(history) > 0:
        daily_demand = sum(history) / len(history)
        demand_std = np.std(history)
        logger.info(f"📊 Demande quotidienne: {daily_demand:.1f} ± {demand_std:.1f}")
    else:
        daily_demand = 25.0
        demand_std = 8.0
        logger.warning(f"⚠️ Pas d'historique, utilisation des valeurs par défaut")
    
    # 3. Calculer le stock de sécurité avec les données réelles
    z_score = 1.65 if request.service_level == 0.95 else 1.28
    safety_stock = z_score * demand_std * np.sqrt(request.lead_time_days)
    reorder_point = daily_demand * request.lead_time_days + safety_stock
    order_quantity = max(0, reorder_point - request.current_stock)
    
    return {
        "medicine_id": request.medicine_id,
        "current_stock": request.current_stock,
        "recommended_order": round(order_quantity),
        "reorder_point": round(reorder_point),
        "safety_stock": round(safety_stock),
        "estimated_daily_demand": round(daily_demand, 1),
        "demand_std": round(demand_std, 1),
        "lead_time_days": request.lead_time_days,
        "message": f"📦 Commander {round(order_quantity)} unités" if order_quantity > 0 else "✅ Stock suffisant",
        "based_on": "données réelles" if history else "valeur par défaut"
    }

# ==========================================
# SCORE DE CRITICITÉ - AVEC DONNÉES RÉELLES
# ==========================================

@app.get("/criticality")
def get_criticality(medicine_id: str):
    """Retourne le score de criticité basé sur les données réelles"""
    
    # 1. Récupérer l'historique
    history = get_medicine_history(identifier=medicine_id, days=30)
    
    # 2. Récupérer le stock actuel
    current_stock = get_medicine_stock(medicine_id) or 0
    
    # 3. Calculer les métriques réelles
    if history and len(history) > 0:
        avg_sales = sum(history) / len(history)
        max_sales = max(history)
        variability = np.std(history) if len(history) > 1 else 0
        
        # Criticité basée sur les données réelles
        score = 50  # Score de base
        
        # Facteur: volume de ventes
        if avg_sales > 50:
            score += 20
        elif avg_sales > 25:
            score += 10
        
        # Facteur: variabilité
        if variability > 20:
            score += 15
        elif variability > 10:
            score += 8
        
        # Facteur: stock critique
        if current_stock < avg_sales * 3:
            score += 15
        elif current_stock < avg_sales * 7:
            score += 8
        
        # Facteur: saisonnalité
        if date.today().month in [6, 7, 8, 9, 10]:  # Saison des pluies
            score += 5
        
        score = min(100, score)
        logger.info(f"📊 Score de criticité calculé: {score} pour {medicine_id}")
    else:
        score = 50
        logger.warning(f"⚠️ Pas d'historique, score par défaut: {score}")
    
    # 4. Déterminer le niveau
    if score >= 85:
        level, color = "CRITIQUE", "red"
    elif score >= 70:
        level, color = "ÉLEVÉ", "orange"
    elif score >= 50:
        level, color = "MOYEN", "yellow"
    else:
        level, color = "FAIBLE", "green"
    
    return {
        "medicine_id": medicine_id,
        "criticality_score": score,
        "level": level,
        "color": color,
        "metrics": {
            "avg_daily_sales": round(avg_sales, 1) if history else None,
            "current_stock": current_stock,
            "variability": round(variability, 1) if history else None,
            "based_on": "données réelles" if history else "valeur par défaut"
        }
    }

# ==========================================
# ANALYSE SAISONNIÈRE - AVEC DONNÉES RÉELLES
# ==========================================

@app.get("/seasonal-analysis")
def seasonal_analysis():
    """Analyse saisonnière pour le Tchad avec données réelles"""
    
    today = date.today()
    is_rainy = today.month in [6, 7, 8, 9, 10]
    
    return {
        "date": today.isoformat(),
        "season": "Saison des pluies 🌧️" if is_rainy else "Saison sèche ☀️",
        "alerts": [
            "🦟 Pic de paludisme : renforcer antipaludéens" if is_rainy else "🏥 Saison méningite : prévoir vaccins",
            "💧 Maladies hydriques : stocker SRO" if is_rainy else "🫁 Infections respiratoires : antibiotiques"
        ],
        "priority_categories": ["Antipaludéens", "Réhydratation", "Antibiotiques"] if is_rainy else ["Vaccins", "Respiratoire", "Antibiotiques"]
    }

# ==========================================
# ANALYSE SHAP - AVEC DONNÉES RÉELLES
# ==========================================

@app.get("/shap-analysis")
def shap_analysis(medicine_id: str):
    """Retourne l'importance des variables (SHAP) pour un médicament"""
    if model is None:
        raise HTTPException(503, "Modèle non disponible.")

    history = get_medicine_history(identifier=medicine_id, days=30)
    if not history or len(history) < 5:
        return {
            "error": "Pas assez d'historique pour calculer SHAP",
            "required": 5,
            "found": len(history) if history else 0
        }

    # Utiliser les données réelles
    hist = history[-30:] if len(history) >= 30 else history
    
    lag_1 = hist[-1] if len(hist) >= 1 else 45.0
    lag_7 = hist[-7] if len(hist) >= 7 else sum(hist[-len(hist):]) / len(hist)
    lag_30 = hist[0] if len(hist) >= 1 else 45.0
    rolling_mean_7 = sum(hist[-min(7, len(hist)):]) / min(7, len(hist))
    rolling_mean_30 = sum(hist) / len(hist)

    last_date = date.today() - timedelta(days=1)
    dow = last_date.weekday()
    month = last_date.month
    is_weekend = 1 if dow >= 5 else 0
    season = 1 if month in [6, 7, 8, 9, 10] else 0

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
        "features": feature_importance,
        "based_on": "données réelles"
    }

# ==========================================
# CHATBOT
# ==========================================

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
    
    return {
        "reply": "Je peux vous aider sur : prévisions, ruptures, commandes, criticité, saisons. Que voulez-vous savoir ?",
        "timestamp": date.today().isoformat()
    }

logger.info("\n✅ API DENG PHARMA prête avec PostgreSQL !")
logger.info("📖 Documentation : http://127.0.0.1:8001/docs")