# ai_service/api/main.py
"""
DENG PHARMA - Service IA
API de prévision des ventes, détection ruptures, recommandations
Modèle XGBoost entraîné sur dataset Tchadien
Version PostgreSQL pour production
"""
import json
import os
import sys
import subprocess
import urllib.parse
from datetime import date, timedelta
from typing import Optional, List, Dict
import re

import joblib
import numpy as np
import pandas as pd
import psycopg2
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq


# ==========================================
# CONFIGURATION GROQ
# ==========================================

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = None

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialisé avec succès !")
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
else:
    print("⚠️ GROQ_API_KEY non définie, le chatbot utilisera le mode basique.")



# ==========================================
# CONNEXION À LA BASE DE DONNÉES POSTGRESQL
# ==========================================

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Retourne une connexion à la base de données PostgreSQL"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL non définie !")
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
        print(f"❌ Erreur de connexion à la base: {e}")
        return None

def get_commercial_name_from_uuid(identifier: str) -> Optional[str]:
    """Récupère le nom commercial d'un médicament depuis PostgreSQL"""
    if not identifier:
        return None
    
    clean_uuid = identifier.strip()
    
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        query = "SELECT commercial_name FROM medicines_medicine WHERE id = %s"
        cursor.execute(query, (clean_uuid,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return row[0]
    except Exception as e:
        print(f"❌ Erreur base de données (get_commercial_name): {e}")
    
    return None

def get_medicine_history(identifier: str, medicine_name: Optional[str] = None, days: int = 30):
    """Récupère l'historique des ventes depuis PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        if medicine_name:
            search_name = medicine_name
        else:
            search_name = get_commercial_name_from_uuid(identifier)
            if not search_name:
                cursor.close()
                conn.close()
                return None
        
        query = """
            SELECT DATE(s.created_at) AS date, COALESCE(SUM(si.quantity), 0) AS sales
            FROM sales_saleitem si
            JOIN sales_sale s ON si.sale_id = s.id
            JOIN medicines_medicine m ON si.medicine_id = m.id
            WHERE m.commercial_name = %s
            GROUP BY DATE(s.created_at)
            ORDER BY date DESC
            LIMIT %s
        """
        cursor.execute(query, (search_name, days))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return None
        
        result = []
        for row in reversed(rows):
            result.append(float(row[1]) if row[1] else 0.0)
        
        return result
    except Exception as e:
        print(f"❌ Erreur historique: {e}")
        return None

# ==========================================
# FONCTIONS CHATBOT
# ==========================================

# ==========================================
# CHATBOT AVEC GROQ
# ==========================================

SYSTEM_PROMPT = """Tu es l'assistant IA de DENG PHARMA, une pharmacie intelligente au Tchad.

Tu as accès aux données suivantes (en temps réel via des fonctions) :
- Stock des médicaments
- Ruptures de stock
- Prévisions de ventes (modèle XGBoost)
- Chiffre d'affaires
- Expirations
- Recommandations de commandes

Instructions :
1. Réponds en français, de manière professionnelle et concise.
2. Si l'utilisateur demande une information spécifique (stock, rupture, prévision), utilise les données disponibles.
3. Si tu ne connais pas la réponse, dis-le honnêtement et propose de l'aide.
4. Sois amical mais professionnel (tutoiement).
5. Pour les chiffres, utilise le format FCFA.
6. Si l'utilisateur dit "bonjour", "salut", réponds poliment.

Règles :
- Ne jamais inventer de données.
- Si une donnée est manquante, propose une alternative.
- Reste dans le contexte pharmaceutique.
- Sois concis (max 3-4 phrases).
"""

@app.post("/chat")
def chat(request: ChatRequest):
    """Chatbot intelligent avec Groq LLM"""
    
    # Fallback si Groq n'est pas configuré
    if not groq_client or not GROQ_API_KEY:
        return {
            "reply": "⚠️ Le chatbot avancé n'est pas disponible. Veuillez configurer GROQ_API_KEY.",
            "timestamp": date.today().isoformat(),
            "source": "fallback"
        }
    
    try:
        # Construire le message
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        # Appeler l'API Groq
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Modèle le plus performant
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
            stop=None
        )
        
        reply = response.choices[0].message.content
        
        return {
            "reply": reply,
            "timestamp": date.today().isoformat(),
            "source": "groq"
        }
        
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return {
            "reply": "❌ Désolé, une erreur est survenue. Veuillez réessayer.",
            "timestamp": date.today().isoformat(),
            "source": "error"
        }

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
    print(f"⚠️ Modèle non trouvé : {e}")
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
    medicine_id: str = "MED003"
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
        "version": "2.0.0",
        "model_loaded": model is not None,
        "database": "PostgreSQL",
        "endpoints": [
            "/predict",
            "/analyze/stock",
            "/recommend/order",
            "/criticality",
            "/seasonal-analysis",
            "/chat",
            "/health",
            "/model-performance",
            "/shap-analysis",
            "/train"
        ]
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
# PRÉDICTION DES VENTES
# ==========================================

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

    print(f"DEBUG: medicine_name = '{request.medicine_name}', historique = {len(history) if history else 0}")

    base = 45.0
    season_factor = 1.5 if today.month in [6, 7, 8, 9, 10] else 1.0
    default_lag = base * season_factor

    if history and len(history) > 0:
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

        lag_30 = lag_7
        lag_7 = lag_1
        lag_1 = pred
        rolling_mean_30 = (rolling_mean_30 * 29 + lag_30) / 30.0
        rolling_mean_7 = (rolling_mean_7 * 6 + lag_1) / 7.0

    return {
        "medicine_id": request.medicine_id,
        "predictions": predictions,
        "model_version": "v2.0-personalized",
        "database": "PostgreSQL"
    }

# ==========================================
# ANALYSE DE STOCK
# ==========================================

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

# ==========================================
# RECOMMANDATION DE COMMANDE
# ==========================================

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

# ==========================================
# SCORE DE CRITICITÉ
# ==========================================

@app.get("/criticality")
def get_criticality(medicine_id: str = "MED003"):
    """Retourne le score de criticité"""
    scores = {
        "MED001": 85, "MED002": 75, "MED003": 95, "MED004": 85, "MED005": 65,
        "MED006": 55, "MED007": 75, "MED008": 90, "MED009": 80, "MED010": 85,
        "MED011": 95, "MED012": 75, "MED013": 45, "MED014": 55, "MED015": 65
    }
    score = scores.get(medicine_id, 50)
    
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
        "color": color
    }

# ==========================================
# ANALYSE SAISONNIÈRE
# ==========================================

@app.get("/seasonal-analysis")
def seasonal_analysis():
    """Analyse saisonnière pour le Tchad"""
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
# ANALYSE SHAP
# ==========================================

@app.get("/shap-analysis")
def shap_analysis(medicine_id: str):
    """Retourne l'importance des variables (SHAP) pour un médicament."""
    if model is None:
        raise HTTPException(503, "Modèle non disponible.")

    history = get_medicine_history(identifier=medicine_id, days=30)
    if not history or len(history) < 5:
        return {"error": "Pas assez d'historique pour calculer SHAP."}

    hist = history[-30:] if len(history) >= 30 else history
    if len(hist) < 30:
        hist = [45.0] * (30 - len(hist)) + hist

    lag_1 = hist[-1]
    lag_7 = hist[-7]
    lag_30 = hist[0]
    rolling_mean_7 = sum(hist[-7:]) / 7
    rolling_mean_30 = sum(hist) / 30

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
        "features": feature_importance
    }

# ==========================================
# CHATBOT INTELLIGENT
# ==========================================

def handle_stock_query(entities: Dict) -> Dict:
    """Répond à une question sur le stock"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Quel médicament vous intéresse ?", "timestamp": date.today().isoformat()}
    
    stock = get_medicine_stock_by_name(med_name)
    if stock is None:
        return {"reply": f"❌ Je n'ai pas trouvé de médicament '{med_name}'.", "timestamp": date.today().isoformat()}
    
    if stock == 0:
        emoji, status = "🚨", "⚠️ **Rupture de stock !**"
    elif stock < 10:
        emoji, status = "⚠️", f"⚠️ **Stock très bas** ({stock:.0f} unités)"
    elif stock < 30:
        emoji, status = "📦", f"📦 **Stock modéré** ({stock:.0f} unités)"
    else:
        emoji, status = "✅", f"✅ **Stock suffisant** ({stock:.0f} unités)"
    
    suggestion = "\n💡 **Suggestion :** Pensez à commander bientôt." if stock < 10 else ""
    
    return {
        "reply": f"{emoji} **{med_name.capitalize()}** : {status}{suggestion}",
        "timestamp": date.today().isoformat()
    }

def handle_rupture_query() -> Dict:
    """Liste les médicaments en rupture"""
    out_of_stock = get_out_of_stock_medicines()
    if out_of_stock:
        reply = "🚨 **Médicaments en rupture de stock :**\n\n"
        for med in out_of_stock:
            reply += f"  • ❌ {med}\n"
        reply += "\n⚠️ **Action :** Passez commande immédiatement !"
    else:
        reply = "✅ **Aucun médicament en rupture.** Tout va bien !"
    return {"reply": reply, "timestamp": date.today().isoformat()}

def handle_prediction_query(entities: Dict) -> Dict:
    """Donne une prévision de vente"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Pour quel médicament voulez-vous une prévision ?", "timestamp": date.today().isoformat()}
    
    history = get_medicine_history_by_name(med_name, days=30)
    if not history or len(history) < 3:
        return {
            "reply": f"⚠️ Pas assez de données pour **{med_name}**. Il faut au moins 3 jours d'historique.",
            "timestamp": date.today().isoformat()
        }
    
    pred = predict_sales_from_history(history)
    avg_sales = sum(history) / len(history)
    trend = "📈 **en hausse**" if pred > avg_sales else "📉 **en baisse**"
    
    return {
        "reply": (
            f"📊 **Prévision pour {med_name.capitalize()}**\n\n"
            f"  • Ventes prévues : **{pred:.0f}** unités\n"
            f"  • Moyenne historique : **{avg_sales:.0f}** unités\n"
            f"  • Tendance : {trend}\n"
            f"  • Basé sur {len(history)} jours de données"
        ),
        "timestamp": date.today().isoformat()
    }

def handle_revenue_query(entities: Dict) -> Dict:
    """Calcule le chiffre d'affaires"""
    period = int(entities.get("period", "7"))
    revenue = get_revenue_period(period)
    prev_revenue = get_revenue_period(period, offset=period)
    evolution = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    emoji = "📈" if evolution >= 0 else "📉"
    
    return {
        "reply": (
            f"💰 **Chiffre d'affaires**\n\n"
            f"  • Période : **{period}** jours\n"
            f"  • Total : **{revenue:,.0f}** FCFA\n"
            f"  • Évolution : {emoji} **{evolution:+.1f}%**"
        ),
        "timestamp": date.today().isoformat()
    }

def handle_expiration_query(entities: Dict) -> Dict:
    """Liste les médicaments qui expirent"""
    days = int(entities.get("period", "30"))
    expiring = get_expiring_medicines(days)
    
    if expiring:
        reply = f"⚠️ **Médicaments expirant dans {days} jours :**\n\n"
        for med, date_str in expiring[:10]:
            reply += f"  • {med} (expire le {date_str})\n"
        if len(expiring) > 10:
            reply += f"\n... et {len(expiring) - 10} autres."
    else:
        reply = f"✅ Aucun médicament n'expire dans les {days} jours."
    return {"reply": reply, "timestamp": date.today().isoformat()}

def handle_order_query(entities: Dict) -> Dict:
    """Recommande une commande"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Pour quel médicament voulez-vous une recommandation ?", "timestamp": date.today().isoformat()}
    
    stock = get_medicine_stock_by_name(med_name)
    history = get_medicine_history_by_name(med_name, days=30)
    if not history:
        return {"reply": f"⚠️ Pas assez de données pour {med_name}.", "timestamp": date.today().isoformat()}
    
    avg_daily = sum(history) / len(history)
    recommended = max(0, (avg_daily * 14) - stock)
    
    return {
        "reply": (
            f"📦 **Recommandation de commande pour {med_name.capitalize()}**\n\n"
            f"  • Stock actuel : **{stock:.0f}** unités\n"
            f"  • Vente moyenne : **{avg_daily:.0f}** unités/jour\n"
            f"  • Autonomie : **{stock / avg_daily:.0f}** jours\n"
            f"  • **Quantité recommandée : {recommended:.0f}** unités"
        ),
        "timestamp": date.today().isoformat()
    }

def handle_sales_query(entities: Dict) -> Dict:
    """Donne des informations sur les ventes"""
    med_name = entities.get("medicine_name")
    if med_name:
        history = get_medicine_history_by_name(med_name, days=30)
        if history:
            total = sum(history)
            avg = total / len(history)
            return {
                "reply": (
                    f"📊 **Ventes de {med_name.capitalize()}**\n\n"
                    f"  • Total (30 jours) : **{total:.0f}** unités\n"
                    f"  • Moyenne : **{avg:.0f}** unités/jour\n"
                    f"  • Meilleur jour : **{max(history):.0f}** unités"
                ),
                "timestamp": date.today().isoformat()
            }
        else:
            return {"reply": f"❌ Aucune vente enregistrée pour {med_name}.", "timestamp": date.today().isoformat()}
    else:
        return {"reply": "❓ Pour quel médicament voulez-vous les ventes ?", "timestamp": date.today().isoformat()}

def handle_help() -> Dict:
    """Affiche l'aide"""
    return {
        "reply": (
            "🤖 **Aide - DENG PHARMA Assistant**\n\n"
            "Je peux répondre à vos questions sur :\n\n"
            "  • 📦 **Stock** : 'Stock de Paracétamol'\n"
            "  • 🚨 **Ruptures** : 'Quels médicaments sont en rupture ?'\n"
            "  • 📈 **Prévisions** : 'Prévision pour Amoxicilline'\n"
            "  • 💰 **Chiffre d'affaires** : 'CA du mois'\n"
            "  • ⚠️ **Expirations** : 'Expirations dans 30 jours'\n"
            "  • 📦 **Commande** : 'Commander Amoxicilline'\n\n"
            "Que puis-je faire pour vous ? 😊"
        ),
        "timestamp": date.today().isoformat()
    }

def handle_fallback(msg: str) -> Dict:
    """Réponse par défaut"""
    return {
        "reply": (
            "🤔 Je n'ai pas bien compris votre demande.\n\n"
            "💡 Essayez de préciser votre question :\n"
            "  • 'Stock de Paracétamol'\n"
            "  • 'Prévision pour Amoxicilline'\n"
            "  • 'Quels sont les médicaments en rupture ?'\n\n"
            "Ou tapez 'aide' pour voir toutes les fonctionnalités."
        ),
        "timestamp": date.today().isoformat()
    }

@app.post("/chat")
def chat(request: ChatRequest):
    """Assistant IA intelligent pour la pharmacie"""
    msg = request.message.lower().strip()
    today = date.today()
    
    # Extraire les entités
    entities = extract_entities(msg)
    print(f"🔍 Entités extraites: {entities}")
    
    # Détecter l'intention
    intent = detect_intent(msg, entities)
    print(f"🎯 Intention détectée: {intent}")
    
    # Exécuter l'action
    if intent == "stock":
        result = handle_stock_query(entities)
    elif intent == "rupture":
        result = handle_rupture_query()
    elif intent == "prevision":
        result = handle_prediction_query(entities)
    elif intent == "ca":
        result = handle_revenue_query(entities)
    elif intent == "expiration":
        result = handle_expiration_query(entities)
    elif intent == "commande":
        result = handle_order_query(entities)
    elif intent == "vente":
        result = handle_sales_query(entities)
    elif intent == "aide":
        result = handle_help()
    else:
        result = handle_fallback(msg)
    
    result["timestamp"] = today.isoformat()
    return result

print("\n✅ API DENG PHARMA prête !")
print("📖 Documentation : http://127.0.0.1:8001/docs")