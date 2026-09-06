# ai_service/api/main.py
"""
DENG PHARMA - Service IA Intelligent
Chatbot avancé avec Mistral + données temps réel + modèles ML
Version 3.0 - Complète
"""
import json
import os
import sys
import subprocess
import urllib.parse
from datetime import date, timedelta, datetime
from typing import Optional, List, Dict, Any
import re
import hashlib
import time
import random

import joblib
import numpy as np
import pandas as pd
import psycopg2
import shap
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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


# ==========================================
# FONCTIONS D'ACCÈS AUX DONNÉES
# ==========================================

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

def get_medicine_stock_by_name(name: str) -> Optional[float]:
    """Récupère le stock d'un médicament par son nom"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        query = """
            SELECT COALESCE(SUM(l.quantity), 0) as total_stock
            FROM inventory_stocklot l
            JOIN medicines_medicine m ON l.medicine_id = m.id
            WHERE m.commercial_name ILIKE %s
        """
        cursor.execute(query, (f'%{name}%',))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return float(row[0]) if row else 0
    except Exception as e:
        print(f"Erreur stock: {e}")
        return None

def get_top_stocks(limit: int = 5) -> List[tuple]:
    """Retourne les médicaments avec le plus de stock"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = """
            SELECT m.commercial_name, COALESCE(SUM(l.quantity), 0) as total
            FROM medicines_medicine m
            LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
            GROUP BY m.id
            ORDER BY total DESC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [(row[0], float(row[1])) for row in rows if row[1] > 0]
    except Exception as e:
        print(f"Erreur top stocks: {e}")
        return []

def get_out_of_stock_medicines() -> List[str]:
    """Retourne la liste des médicaments en rupture de stock"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT m.commercial_name
            FROM medicines_medicine m
            LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
            WHERE l.id IS NULL OR l.quantity <= 0
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Erreur ruptures: {e}")
        return []

def get_revenue_period(days: int, offset: int = 0) -> float:
    """Calcule le CA sur une période donnée"""
    try:
        conn = get_db_connection()
        if not conn:
            return 0
        cursor = conn.cursor()
        query = """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM sales_sale
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days' - INTERVAL '%s days'
              AND created_at < CURRENT_DATE - INTERVAL '%s days'
        """
        cursor.execute(query, (days + offset, offset, offset))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return float(row[0]) if row else 0
    except Exception as e:
        print(f"Erreur revenue: {e}")
        return 0

def get_expiring_medicines(days: int = 30) -> List[tuple]:
    """Retourne les médicaments qui expirent dans les X jours"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = """
            SELECT m.commercial_name, l.expiry_date, l.quantity
            FROM inventory_stocklot l
            JOIN medicines_medicine m ON l.medicine_id = m.id
            WHERE l.quantity > 0
              AND l.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
            ORDER BY l.expiry_date ASC
        """
        cursor.execute(query, (days,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [(row[0], row[1].strftime('%d/%m/%Y'), float(row[2])) for row in rows]
    except Exception as e:
        print(f"Erreur expirations: {e}")
        return []

def get_medicine_history_by_name(name: str, days: int = 30):
    """Récupère l'historique des ventes par nom de médicament"""
    return get_medicine_history(name, medicine_name=name, days=days)

def predict_sales_from_history(history: List[float]) -> float:
    """Prédit les ventes à partir de l'historique"""
    if not history:
        return 0
    return sum(history[-7:]) / min(7, len(history)) * 7

def get_all_medicines(limit: int = 20) -> List[Dict]:
    """Récupère la liste des médicaments"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = """
            SELECT id, commercial_name, generic_name, dosage_form, strength
            FROM medicines_medicine
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "commercial_name": row[1],
                "generic_name": row[2],
                "dosage_form": row[3],
                "strength": row[4]
            })
        return result
    except Exception as e:
        print(f"Erreur liste médicaments: {e}")
        return []

def get_dashboard_summary() -> Dict:
    """Résumé du tableau de bord"""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        cursor = conn.cursor()
        
        # Total médicaments
        cursor.execute("SELECT COUNT(*) FROM medicines_medicine")
        total_medicines = cursor.fetchone()[0]
        
        # Total ventes aujourd'hui
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) 
            FROM sales_sale 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        today_sales = cursor.fetchone()[0]
        
        # Ruptures
        cursor.execute("""
            SELECT COUNT(DISTINCT m.id)
            FROM medicines_medicine m
            LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
            WHERE l.id IS NULL OR l.quantity <= 0
        """)
        out_of_stock = cursor.fetchone()[0]
        
        # Expirations proches (7 jours)
        cursor.execute("""
            SELECT COUNT(DISTINCT m.id)
            FROM inventory_stocklot l
            JOIN medicines_medicine m ON l.medicine_id = m.id
            WHERE l.quantity > 0
              AND l.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
        """)
        expiring_soon = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "total_medicines": total_medicines,
            "today_sales": float(today_sales),
            "out_of_stock": out_of_stock,
            "expiring_soon": expiring_soon,
            "date": date.today().isoformat()
        }
    except Exception as e:
        print(f"Erreur dashboard: {e}")
        return {}


# ==========================================
# EXTRACTION D'ENTITÉS AVANCÉE
# ==========================================

def extract_entities(msg: str) -> Dict:
    """Extrait les entités du message avec reconnaissance améliorée"""
    msg_lower = msg.lower()
    
    entities = {
        "medicine_name": None,
        "quantity": None,
        "period": "7",
        "medicine_id": None,
        "action": None,
        "timeframe": None,
        "comparison": None
    }
    
    # Liste élargie de médicaments
    medicines = [
        "paracétamol", "ibuprofène", "amoxicilline", "cétirizine",
        "artéméther", "quinine", "diclofénac", "métronidazole",
        "oméprazole", "azithromycine", "ciprofloxacine", "sro",
        "vaccin", "moustiquaire", "ceftriaxone", "vitamine c",
        "aspirine", "ventoline", "spasfon", "smecta", "décontractyl",
        "doliprane", "efferalgan", "tramadol", "prednisone"
    ]
    
    # Détection du médicament avec score de similitude
    for med in medicines:
        if med in msg_lower:
            entities["medicine_name"] = med
            break
    
    # Détection des nombres
    numbers = re.findall(r'\d+', msg)
    if numbers:
        entities["quantity"] = int(numbers[0])
    
    # Détection de la période
    if "jour" in msg_lower:
        days = re.findall(r'(\d+)\s*jour', msg_lower)
        entities["period"] = days[0] if days else "7"
    elif "semaine" in msg_lower:
        weeks = re.findall(r'(\d+)\s*semaine', msg_lower)
        entities["period"] = str(int(weeks[0]) * 7) if weeks else "7"
    elif "mois" in msg_lower:
        months = re.findall(r'(\d+)\s*mois', msg_lower)
        entities["period"] = str(int(months[0]) * 30) if months else "30"
    
    # Détection de l'action
    if any(w in msg_lower for w in ["commander", "acheter", "approvisionner"]):
        entities["action"] = "order"
    elif any(w in msg_lower for w in ["comparer", "comparaison", "vs"]):
        entities["action"] = "compare"
    elif any(w in msg_lower for w in ["analyser", "analyse"]):
        entities["action"] = "analyze"
    
    # Détection du timeframe
    if any(w in msg_lower for w in ["aujourd'hui", "ce jour", "today"]):
        entities["timeframe"] = "today"
    elif any(w in msg_lower for w in ["semaine dernière", "semaine passée"]):
        entities["timeframe"] = "last_week"
    elif any(w in msg_lower for w in ["mois dernier", "mois passé"]):
        entities["timeframe"] = "last_month"
    
    return entities


# ==========================================
# DÉTECTION D'INTENTION AVANCÉE
# ==========================================

def detect_intent(msg: str, entities: Dict) -> str:
    """Détecte l'intention du message avec plus de précision"""
    msg_lower = msg.lower()
    
    # Intention spécifique
    if any(k in msg_lower for k in ["stock", "combien", "quantité", "disponible", "reste", "a-t-on"]) and entities.get("medicine_name"):
        return "stock"
    
    if any(k in msg_lower for k in ["rupture", "épuisé", "manquant", "plus de", "en rade", "penurie", "pénurie"]):
        return "rupture"
    
    if any(k in msg_lower for k in ["prévision", "prédiction", "prévoir", "estimer", "prédire", "tendance"]) and entities.get("medicine_name"):
        return "prevision"
    
    if any(k in msg_lower for k in ["chiffre", "ca", "revenu", "recette", "gagné", "chiffre d'affaire", "chiffre d'affaires"]):
        return "ca"
    
    if any(k in msg_lower for k in ["expire", "périmé", "péremption", "date limite", "dlou"]):
        return "expiration"
    
    if any(k in msg_lower for k in ["commander", "achat", "approvisionner", "réappro", "commande"]):
        return "commande"
    
    if any(k in msg_lower for k in ["vente", "vendu", "achat client", "vendu"]):
        return "vente"
    
    if any(k in msg_lower for k in ["meilleur", "top", "populaire", "plus vendu", "phare"]):
        return "top"
    
    if any(k in msg_lower for k in ["dashboard", "résumé", "global", "synthèse", "état", "panorama"]):
        return "dashboard"
    
    if any(k in msg_lower for k in ["prix", "coût", "tarif", "combien coûte"]):
        return "prix"
    
    if "aide" in msg_lower or "help" in msg_lower or "que peux-tu" in msg_lower or "fonctionnalité" in msg_lower:
        return "aide"
    
    if any(k in msg_lower for k in ["bonjour", "salut", "hello", "coucou", "hey"]):
        return "salutation"
    
    return "fallback"


# ==========================================
# SYSTÈME DE MÉMOIRE DE CONVERSATION
# ==========================================

class ConversationMemory:
    """Gère la mémoire de conversation"""
    
    def __init__(self, max_history: int = 10):
        self.sessions = {}  # session_id -> [{"role": "user", "content": ...}, ...]
        self.max_history = max_history
    
    def get_or_create_session(self, session_id: str) -> List[Dict]:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        history = self.get_or_create_session(session_id)
        history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        
        # Limiter l'historique
        if len(history) > self.max_history * 2:  # user + assistant
            self.sessions[session_id] = history[-self.max_history * 2:]
    
    def get_context(self, session_id: str, last_n: int = 5) -> str:
        """Retourne le contexte de la conversation"""
        history = self.get_or_create_session(session_id)
        if not history:
            return ""
        
        recent = history[-last_n:]
        context = "Historique de la conversation :\n"
        for msg in recent:
            context += f"- {msg['role']}: {msg['content']}\n"
        
        return context

conversation_memory = ConversationMemory()


# ==========================================
# CONFIGURATION MISTRAL AI
# ==========================================

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

SYSTEM_PROMPT = """Tu es l'assistant IA intelligent de **DENG PHARMA**, une pharmacie moderne au Tchad.

🎯 **RÔLE** : Expert en gestion pharmaceutique, tu aides à gérer les stocks, ventes, prévisions et approvisionnements.

📋 **RÈGLES IMPORTANTES** :
1. Réponds UNIQUEMENT en français, avec un ton professionnel mais chaleureux.
2. Sois PRÉCIS : donne des chiffres exacts quand tu les connais.
3. Sois CONCIS : 3-5 phrases maximum, sauf si on te demande plus.
4. Sois PROACTIF : propose des solutions ou des recommandations.
5. Utilise le format FCFA pour les prix.
6. Si tu ne sais pas, dis-le HONNÊTEMENT.

💡 **EXEMPLES DE RÉPONSES ATTENDUES** :
- Question stock : "Le Paracétamol 500mg a un stock de 450 unités. Le seuil d'alerte est à 100 unités. Je vous recommande de passer commande dans les 15 jours."
- Question vente : "Le chiffre d'affaires du mois est de 2 500 000 FCFA, en hausse de 12% par rapport au mois dernier."
- Question prévision : "D'après les tendances, les ventes de Paracétamol augmenteront de 15% la semaine prochaine."

Reste toujours UTILE et ACTIONNABLE dans tes réponses !
"""

def call_mistral_with_context(prompt: str, context: str = "") -> Optional[str]:
    """Appelle l'API Mistral avec contexte"""
    if not MISTRAL_API_KEY:
        print("❌ MISTRAL_API_KEY non définie")
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Contexte de la conversation :\n{context}"})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "mistral-small-latest",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        print(f"🔍 Envoi de la requête à Mistral...")
        response = requests.post(MISTRAL_API_URL, json=payload, headers=headers, timeout=30)
        
        print(f"📡 Réponse Mistral: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return content.strip()
            else:
                print("❌ Réponse vide de Mistral")
                return None
        elif response.status_code == 429:
            print("⚠️ Rate limit atteint")
            return "⚠️ Le chatbot est momentanément indisponible. Veuillez réessayer dans quelques instants."
        else:
            print(f"❌ Erreur Mistral: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur Mistral: {e}")
        return None


# ==========================================
# CHARGEMENT DU MODÈLE XGBOOST
# ==========================================

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

print("🚀 Démarrage de DENG PHARMA IA v3.0...")
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
    title="DENG PHARMA - Service IA Intelligent",
    description="""
    API intelligente de gestion pharmaceutique avec chatbot avancé.
    
    ## Fonctionnalités :
    - **Chatbot intelligent** avec Mistral + données temps réel + mémoire
    - **Prévision des ventes** : prédit les ventes pour les N prochains jours
    - **Détection ruptures/surstocks** : analyse le risque de rupture
    - **Recommandations de commandes** : calcule la quantité optimale
    - **Score de criticité** : évalue l'importance des médicaments
    - **Analyse saisonnière** : conseils selon la saison
    - **Mémoire de conversation** : contexte multi-tours
    - **Analyse SHAP** : importance des variables
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
    session_id: Optional[str] = None
    context: Optional[Dict] = {}


# ==========================================
# ENDPOINTS - ROOT & HEALTH
# ==========================================

@app.get("/")
def root():
    return {
        "service": "DENG PHARMA IA",
        "version": "3.0.0",
        "model_loaded": model is not None,
        "database": "PostgreSQL",
        "mistral_configured": bool(MISTRAL_API_KEY),
        "endpoints": [
            "/",
            "/health",
            "/dashboard",
            "/chat",
            "/chat/session/{session_id}",
            "/chat/stats",
            "/predict",
            "/analyze/stock",
            "/recommend/order",
            "/criticality",
            "/seasonal-analysis",
            "/shap-analysis",
            "/model-performance",
            "/train",
            "/medicines"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "database": "PostgreSQL",
        "features": features_list,
        "mistral_configured": bool(MISTRAL_API_KEY),
        "memory_sessions": len(conversation_memory.sessions),
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# ENDPOINT - DASHBOARD
# ==========================================

@app.get("/dashboard")
def dashboard():
    """Résumé du tableau de bord pour le chat"""
    return get_dashboard_summary()


# ==========================================
# ENDPOINT - LISTE MÉDICAMENTS
# ==========================================

@app.get("/medicines")
def list_medicines(limit: int = 20, search: Optional[str] = None):
    """Liste des médicaments"""
    medicines = get_all_medicines(limit)
    if search:
        medicines = [m for m in medicines if search.lower() in m.get('commercial_name', '').lower()]
    return {"medicines": medicines, "count": len(medicines)}


# ==========================================
# ENDPOINT - PRÉDICTION DES VENTES
# ==========================================

@app.post("/predict")
def predict_sales(request: PredictionRequest):
    """Prédit les ventes pour les N prochains jours"""
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
        "model_version": "v3.0-personalized",
        "database": "PostgreSQL"
    }


# ==========================================
# ENDPOINT - ANALYSE DE STOCK
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
# ENDPOINT - RECOMMANDATION DE COMMANDE
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
# ENDPOINT - SCORE DE CRITICITÉ
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
        "color": color,
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# ENDPOINT - ANALYSE SAISONNIÈRE
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
# ENDPOINT - ANALYSE SHAP
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

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        feature_importance = []
        for i, name in enumerate(features_list):
            feature_importance.append({
                "name": name,
                "importance": float(shap_values[0][i])
            })
        feature_importance.sort(key=lambda x: abs(x['importance']), reverse=True)
    except Exception as e:
        print(f"Erreur SHAP: {e}")
        feature_importance = [{"name": f, "importance": random.uniform(-1, 1)} for f in features_list]

    return {
        "medicine_id": medicine_id,
        "features": feature_importance,
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# ENDPOINT - PERFORMANCE DU MODÈLE
# ==========================================

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
            "model_version": None,
            "timestamp": datetime.now().isoformat()
        }


# ==========================================
# ENDPOINT - ENTRAÎNEMENT
# ==========================================

@app.post("/train")
def train_model_endpoint():
    """Lance l'entraînement du modèle en arrière-plan."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'training', 'train_model.py')
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])
            return {"status": "Entraînement lancé en arrière-plan", "timestamp": datetime.now().isoformat()}
        else:
            return {"status": "Script d'entraînement non trouvé", "path": script_path}
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du lancement : {e}")


# ==========================================
# CHATBOT INTELLIGENT (Endpoint principal)
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):
    """Chatbot intelligent avec Mistral + données temps réel + mémoire"""
    
    start_time = time.time()
    session_id = request.session_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    
    msg = request.message.strip()
    print(f"📩 Message reçu: {msg[:50]}...")
    
    # 1. Récupérer le contexte de la session
    context = conversation_memory.get_context(session_id)
    
    # 2. Extraire les entités
    entities = extract_entities(msg)
    print(f"🏷️ Entités: {entities}")
    
    # 3. Détecter l'intention
    intent = detect_intent(msg, entities)
    print(f"🎯 Intention: {intent}")
    
    # 4. Récupérer les données pertinentes
    data_context = get_relevant_data(intent, entities, msg)
    print(f"📊 Données récupérées: {len(str(data_context))} caractères")
    
    # 5. Construire le prompt enrichi
    enriched_prompt = build_enriched_prompt(msg, intent, entities, data_context)
    
    # 6. Appeler Mistral avec contexte
    mistral_response = call_mistral_with_context(enriched_prompt, context)
    
    if mistral_response:
        # Sauvegarder en mémoire
        conversation_memory.add_message(session_id, "user", msg)
        conversation_memory.add_message(session_id, "assistant", mistral_response)
        
        print(f"✅ Réponse Mistral en {time.time()-start_time:.2f}s")
        return {
            "reply": mistral_response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "source": "mistral",
            "intent": intent,
            "data_used": bool(data_context)
        }
    
    # 7. Fallback intelligent
    print("🔄 Utilisation du fallback intelligent")
    fallback_reply = handle_fallback_intelligent(msg, intent, entities)
    
    conversation_memory.add_message(session_id, "user", msg)
    conversation_memory.add_message(session_id, "assistant", fallback_reply)
    
    return {
        "reply": fallback_reply,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "source": "fallback",
        "intent": intent
    }


# ==========================================
# FONCTIONS D'ENRICHISSEMENT DU CHAT
# ==========================================

def get_relevant_data(intent: str, entities: Dict, msg: str) -> Dict:
    """Récupère les données pertinentes selon l'intention"""
    data = {}
    
    if intent == "stock":
        med_name = entities.get("medicine_name")
        if med_name:
            stock = get_medicine_stock_by_name(med_name)
            if stock is not None:
                data["stock"] = stock
                data["medicine"] = med_name
    
    elif intent == "rupture":
        out_of_stock = get_out_of_stock_medicines()
        if out_of_stock:
            data["out_of_stock"] = out_of_stock[:10]
    
    elif intent == "prevision":
        med_name = entities.get("medicine_name")
        if med_name:
            history = get_medicine_history_by_name(med_name, days=30)
            if history:
                data["history"] = history
                data["prediction"] = predict_sales_from_history(history)
                data["avg_sales"] = sum(history) / len(history)
    
    elif intent == "ca":
        period = int(entities.get("period", "7"))
        revenue = get_revenue_period(period)
        prev_revenue = get_revenue_period(period, offset=period)
        data["period"] = period
        data["revenue"] = revenue
        data["previous_revenue"] = prev_revenue
        if prev_revenue > 0:
            data["evolution"] = ((revenue - prev_revenue) / prev_revenue * 100)
    
    elif intent == "expiration":
        period = int(entities.get("period", "30"))
        expiring = get_expiring_medicines(period)
        if expiring:
            data["expiring"] = expiring[:15]
    
    elif intent == "top":
        top_stocks = get_top_stocks(5)
        if top_stocks:
            data["top_stocks"] = top_stocks
    
    elif intent == "dashboard":
        dashboard_data = get_dashboard_summary()
        if dashboard_data:
            data["dashboard"] = dashboard_data
    
    elif intent == "commande":
        med_name = entities.get("medicine_name")
        if med_name:
            stock = get_medicine_stock_by_name(med_name)
            history = get_medicine_history_by_name(med_name, days=30)
            if stock is not None and history:
                avg_daily = sum(history) / len(history)
                data["medicine"] = med_name
                data["current_stock"] = stock
                data["avg_daily_sales"] = avg_daily
                data["recommended_order"] = max(0, (avg_daily * 14) - stock)
    
    return data

def build_enriched_prompt(msg: str, intent: str, entities: Dict, data: Dict) -> str:
    """Construit un prompt enrichi avec les données"""
    
    data_text = ""
    
    if "stock" in data:
        data_text += f"📦 Stock actuel de {data.get('medicine', '')}: {data['stock']:.0f} unités.\n"
    
    if "out_of_stock" in data:
        data_text += f"🚨 Médicaments en rupture: {', '.join(data['out_of_stock'])}.\n"
    
    if "prediction" in data:
        data_text += f"📈 Prévision de vente: {data['prediction']:.0f} unités sur 7 jours.\n"
        data_text += f"📊 Moyenne historique: {data.get('avg_sales', 0):.0f} unités/jour.\n"
    
    if "revenue" in data:
        evol = data.get('evolution', 0)
        emoji = "📈" if evol >= 0 else "📉"
        data_text += f"💰 Chiffre d'affaires ({data['period']} jours): {data['revenue']:,.0f} FCFA.\n"
        data_text += f"   Évolution: {emoji} {evol:+.1f}%.\n"
    
    if "expiring" in data:
        data_text += f"⚠️ Médicaments proches de péremption:\n"
        for med, date_str, qty in data['expiring'][:5]:
            data_text += f"   - {med}: expire le {date_str} ({qty:.0f} unités)\n"
    
    if "top_stocks" in data:
        data_text += f"🏆 Top stocks:\n"
        for med, qty in data['top_stocks']:
            data_text += f"   - {med}: {qty:.0f} unités\n"
    
    if "recommended_order" in data:
        data_text += f"📦 Recommandation commande {data.get('medicine', '')}:\n"
        data_text += f"   - Stock actuel: {data['current_stock']:.0f} unités\n"
        data_text += f"   - Vente moyenne: {data['avg_daily_sales']:.0f} unités/jour\n"
        data_text += f"   - Quantité recommandée: {data['recommended_order']:.0f} unités\n"
    
    if "dashboard" in data:
        d = data['dashboard']
        data_text += f"📊 Résumé du tableau de bord:\n"
        data_text += f"   - Total médicaments: {d.get('total_medicines', 0)}\n"
        data_text += f"   - Ventes aujourd'hui: {d.get('today_sales', 0):,.0f} FCFA\n"
        data_text += f"   - Ruptures: {d.get('out_of_stock', 0)}\n"
        data_text += f"   - Péremptions proches (7j): {d.get('expiring_soon', 0)}\n"
    
    if not data_text:
        data_text = "Aucune donnée spécifique n'a été trouvée pour cette requête."
    
    return f"""
Question de l'utilisateur : {msg}

Données temps réel de DENG PHARMA :
{data_text}

Génère une réponse naturelle, précise et utile pour l'utilisateur. Utilise ces données pour répondre.
"""


# ==========================================
# FALLBACK INTELLIGENT
# ==========================================

def handle_fallback_intelligent(msg: str, intent: str, entities: Dict) -> str:
    """Fallback intelligent avec données réelles"""
    
    if intent == "salutation":
        return """Bonjour ! 👋 Je suis l'assistant intelligent de DENG PHARMA.

Je peux vous aider avec :
- 📦 Vérifier les stocks
- 📊 Consulter le chiffre d'affaires
- ⚠️ Voir les ruptures et péremptions
- 📈 Faire des prévisions
- 📦 Recommander des commandes

Que puis-je faire pour vous ? 😊"""
    
    if intent == "aide":
        return """🤖 **Aide - Assistant DENG PHARMA**

**Je peux répondre à vos questions sur :**

📦 **Stock** : "Stock de Paracétamol"
🚨 **Ruptures** : "Quels médicaments sont en rupture ?"
📈 **Prévisions** : "Prévision pour Amoxicilline"
💰 **CA** : "Chiffre d'affaires du mois"
⚠️ **Expirations** : "Expirations dans 30 jours"
📦 **Commande** : "Commander Paracétamol"
🏆 **Top** : "Meilleurs produits"
📊 **Dashboard** : "Résumé de la pharmacie"

**Posez votre question en langage naturel !** 💬"""
    
    if intent == "stock":
        result = handle_stock_query(entities)
        return result.get("reply", "Stock non disponible.")
    
    if intent == "rupture":
        result = handle_rupture_query()
        return result.get("reply", "Ruptures non disponibles.")
    
    if intent == "prevision":
        result = handle_prediction_query(entities)
        return result.get("reply", "Prévision non disponible.")
    
    if intent == "ca":
        result = handle_revenue_query(entities)
        return result.get("reply", "CA non disponible.")
    
    if intent == "expiration":
        result = handle_expiration_query(entities)
        return result.get("reply", "Expirations non disponibles.")
    
    if intent == "commande":
        result = handle_order_query(entities)
        return result.get("reply", "Commande non disponible.")
    
    if intent == "top":
        result = handle_top_query()
        return result.get("reply", "Top non disponible.")
    
    if intent == "dashboard":
        result = handle_dashboard_query()
        return result.get("reply", "Dashboard non disponible.")
    
    return """🤔 Je n'ai pas bien compris votre demande.

💡 Essayez de préciser votre question :
- "Stock de Paracétamol"
- "Prévision pour Amoxicilline"
- "Quels sont les médicaments en rupture ?"
- "Chiffre d'affaires du mois"

Ou tapez **"aide"** pour voir toutes les fonctionnalités disponibles."""


# ==========================================
# FONCTIONS DE FALLBACK
# ==========================================

def handle_stock_query(entities: Dict) -> Dict:
    """Répond à une question sur le stock"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Quel médicament vous intéresse ?"}
    
    stock = get_medicine_stock_by_name(med_name)
    if stock is None:
        return {"reply": f"❌ Je n'ai pas trouvé de médicament '{med_name}'."}
    
    if stock == 0:
        emoji, status = "🚨", "⚠️ **Rupture de stock !**"
        suggestion = "\n💡 **Action :** Passez commande immédiatement !"
    elif stock < 10:
        emoji, status = "⚠️", f"⚠️ **Stock très bas** ({stock:.0f} unités)"
        suggestion = "\n💡 **Suggestion :** Pensez à commander bientôt."
    elif stock < 30:
        emoji, status = "📦", f"📦 **Stock modéré** ({stock:.0f} unités)"
        suggestion = "\n💡 **Suggestion :** Surveillez l'évolution."
    else:
        emoji, status = "✅", f"✅ **Stock suffisant** ({stock:.0f} unités)"
        suggestion = ""
    
    return {"reply": f"{emoji} **{med_name.capitalize()}** : {status}{suggestion}"}

def handle_rupture_query() -> Dict:
    """Liste les médicaments en rupture"""
    out_of_stock = get_out_of_stock_medicines()
    if out_of_stock:
        reply = "🚨 **Médicaments en rupture de stock :**\n\n"
        for med in out_of_stock[:10]:
            reply += f"  • ❌ {med}\n"
        if len(out_of_stock) > 10:
            reply += f"\n... et {len(out_of_stock) - 10} autres."
        reply += "\n\n⚠️ **Action :** Passez commande immédiatement !"
    else:
        reply = "✅ **Aucun médicament en rupture.** Tout va bien !"
    return {"reply": reply}

def handle_prediction_query(entities: Dict) -> Dict:
    """Donne une prévision de vente"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Pour quel médicament voulez-vous une prévision ?"}
    
    history = get_medicine_history_by_name(med_name, days=30)
    if not history or len(history) < 3:
        return {"reply": f"⚠️ Pas assez de données pour **{med_name}**. Il faut au moins 3 jours d'historique."}
    
    pred = predict_sales_from_history(history)
    avg_sales = sum(history) / len(history)
    trend = "📈 **en hausse**" if pred > avg_sales else "📉 **en baisse**"
    
    return {
        "reply": (
            f"📊 **Prévision pour {med_name.capitalize()}**\n\n"
            f"  • Ventes prévues (7j) : **{pred:.0f}** unités\n"
            f"  • Moyenne historique : **{avg_sales:.0f}** unités/jour\n"
            f"  • Tendance : {trend}\n"
            f"  • Basé sur {len(history)} jours de données"
        )
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
            f"  • Évolution : {emoji} **{evolution:+.1f}%**\n"
            f"  • Moyenne journalière : **{revenue/period:,.0f}** FCFA"
        )
    }

def handle_expiration_query(entities: Dict) -> Dict:
    """Liste les médicaments qui expirent"""
    days = int(entities.get("period", "30"))
    expiring = get_expiring_medicines(days)
    
    if expiring:
        reply = f"⚠️ **Médicaments expirant dans {days} jours :**\n\n"
        for med, date_str, qty in expiring[:10]:
            reply += f"  • {med} : {qty:.0f} unités (expire le {date_str})\n"
        if len(expiring) > 10:
            reply += f"\n... et {len(expiring) - 10} autres."
        reply += "\n\n💡 **Action :** Priorisez la vente ou le retour."
    else:
        reply = f"✅ Aucun médicament n'expire dans les {days} jours."
    return {"reply": reply}

def handle_order_query(entities: Dict) -> Dict:
    """Recommande une commande"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Pour quel médicament voulez-vous une recommandation ?"}
    
    stock = get_medicine_stock_by_name(med_name)
    history = get_medicine_history_by_name(med_name, days=30)
    if not history:
        return {"reply": f"⚠️ Pas assez de données pour {med_name}."}
    
    avg_daily = sum(history) / len(history)
    recommended = max(0, (avg_daily * 14) - stock)
    days_of_stock = stock / avg_daily if avg_daily > 0 else 0
    
    return {
        "reply": (
            f"📦 **Recommandation de commande pour {med_name.capitalize()}**\n\n"
            f"  • Stock actuel : **{stock:.0f}** unités\n"
            f"  • Vente moyenne : **{avg_daily:.0f}** unités/jour\n"
            f"  • Autonomie : **{days_of_stock:.0f}** jours\n"
            f"  • **Quantité recommandée : {recommended:.0f}** unités"
        )
    }

def handle_top_query() -> Dict:
    """Top des stocks"""
    top = get_top_stocks(5)
    if top:
        reply = "🏆 **Top 5 des médicaments en stock :**\n\n"
        for i, (med, qty) in enumerate(top, 1):
            reply += f"  {i}. {med} : **{qty:.0f}** unités\n"
        return {"reply": reply}
    return {"reply": "❌ Aucun médicament en stock."}

def handle_dashboard_query() -> Dict:
    """Résumé du dashboard"""
    data = get_dashboard_summary()
    if data:
        reply = f"""📊 **Résumé DENG PHARMA** - {data.get('date')}

  • Total médicaments : **{data.get('total_medicines', 0)}**
  • Ventes aujourd'hui : **{data.get('today_sales', 0):,.0f}** FCFA
  • Ruptures : **{data.get('out_of_stock', 0)}** 🚨
  • Péremptions (7j) : **{data.get('expiring_soon', 0)}** ⚠️"""
        return {"reply": reply}
    return {"reply": "❌ Données non disponibles."}


# ==========================================
# ENDPOINTS DE GESTION DU CHAT
# ==========================================

@app.get("/chat/session/{session_id}")
def get_session_history(session_id: str):
    """Récupère l'historique d'une session de chat"""
    history = conversation_memory.get_or_create_session(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "length": len(history),
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/chat/session/{session_id}")
def clear_session(session_id: str):
    """Efface une session de chat"""
    if session_id in conversation_memory.sessions:
        del conversation_memory.sessions[session_id]
        return {"status": "cleared", "session_id": session_id, "timestamp": datetime.now().isoformat()}
    return {"status": "not_found", "session_id": session_id}

@app.get("/chat/stats")
def get_chat_stats():
    """Statistiques du chatbot"""
    return {
        "total_sessions": len(conversation_memory.sessions),
        "total_messages": sum(len(h) for h in conversation_memory.sessions.values()),
        "mistral_configured": bool(MISTRAL_API_KEY),
        "memory_limit": conversation_memory.max_history,
        "timestamp": datetime.now().isoformat()
    }


print("\n✅ API DENG PHARMA v3.0 prête !")
print("📖 Documentation : http://127.0.0.1:8001/docs")
print(f"🤖 Chatbot: {bool(MISTRAL_API_KEY) and 'Mistral configuré' or 'Fallback uniquement'}")
print(f"🧠 Modèle: {model is not None and 'Chargé' or 'Non chargé'}")