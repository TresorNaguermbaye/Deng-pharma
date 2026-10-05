# ai_service/api/main.py
"""
DENG PHARMA - Service IA v6.1
Compatible SQLite (dev) et PostgreSQL (prod)
Modèle v3.0 : XGBoost entraîné sur tchad_pharma_sales.csv (32 features)
"""

from dotenv import load_dotenv
load_dotenv()

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
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ==========================================
# FIX IPv6 — Force IPv4 (contourne DNS cassé)
# ==========================================
import socket

_original_getaddrinfo = socket.getaddrinfo

def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Force IPv4 uniquement pour éviter les timeouts IPv6."""
    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _ipv4_only_getaddrinfo


# ==========================================
# LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# BASE DE DONNÉES - DÉTECTION AUTO
# ==========================================
DATABASE_URL = os.getenv('DATABASE_URL')

IS_SQLITE = bool(DATABASE_URL and DATABASE_URL.startswith('sqlite'))
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith('postgres'))

if not DATABASE_URL:
    sqlite_path = Path(__file__).resolve().parent.parent.parent / 'backend' / 'db.sqlite3'
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    IS_SQLITE = True
    logger.warning(f"⚠️ DATABASE_URL non définie → SQLite: {sqlite_path}")
else:
    db_type = "SQLite" if IS_SQLITE else "PostgreSQL" if IS_POSTGRES else "Inconnu"
    logger.info(f"✅ Base: {db_type}")


def get_db_connection():
    """Connexion compatible SQLite + PostgreSQL"""
    try:
        if IS_SQLITE:
            import sqlite3
            db_path = DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
            return sqlite3.connect(db_path)
        else:
            import psycopg2
            result = urllib.parse.urlparse(DATABASE_URL)
            return psycopg2.connect(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port or 5432
            )
    except Exception as e:
        logger.error(f"❌ Erreur DB: {e}")
        return None


def _convert_postgres_to_sqlite(query: str) -> str:
    """Convertit la syntaxe PostgreSQL en SQLite"""
    query = re.sub(
        r"CURRENT_DATE\s*-\s*INTERVAL\s*'(\d+)\s+days?'",
        r"date('now', '-\1 days')",
        query
    )
    query = re.sub(
        r"CURRENT_DATE\s*\+\s*INTERVAL\s*'(\d+)\s+days?'",
        r"date('now', '+\1 days')",
        query
    )
    query = query.replace("CURRENT_DATE", "date('now')")
    query = query.replace("DATE(", "date(")
    query = query.replace("NOW()", "datetime('now')")
    query = query.replace(" ILIKE ", " LIKE ")
    return query


def execute_query(query: str, params: tuple = ()) -> List[tuple]:
    """Exécute une requête compatible SQLite + PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        if IS_SQLITE:
            query = query.replace('%s', '?')
            query = _convert_postgres_to_sqlite(query)

        cursor.execute(query, params)

        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows

        conn.commit()
        cursor.close()
        conn.close()
        return []
    except Exception as e:
        logger.error(f"❌ Erreur SQL: {e}")
        logger.error(f"   Query: {query[:200]}")
        try:
            conn.close()
        except:
            pass
        return []


# ==========================================
# FONCTIONS D'ACCÈS AUX DONNÉES
# ==========================================

def get_medicine_info(medicine_id: str) -> Optional[Dict]:
    clean_id = medicine_id.replace('-', '').strip() if medicine_id else ''

    query = """
        SELECT id, commercial_name, generic_name, dosage_form, strength,
               selling_price, purchase_price, min_stock, max_stock
        FROM medicines_medicine WHERE id = %s
    """
    rows = execute_query(query, (clean_id,))

    if not rows:
        rows = execute_query(query, (medicine_id,))

    if not rows:
        query_like = """
            SELECT id, commercial_name, generic_name, dosage_form, strength,
                   selling_price, purchase_price, min_stock, max_stock
            FROM medicines_medicine WHERE id LIKE %s
        """
        rows = execute_query(query_like, (f'%{clean_id}%',))

    if not rows:
        return None

    row = rows[0]
    return {
        "id": str(row[0]),
        "commercial_name": row[1],
        "generic_name": row[2] if row[2] else "",
        "dosage_form": row[3] if row[3] else "",
        "strength": row[4] if row[4] else "",
        "selling_price": float(row[5]) if row[5] else 0,
        "purchase_price": float(row[6]) if row[6] else 0,
        "min_stock": int(row[7]) if row[7] else 10,
        "max_stock": int(row[8]) if row[8] else 100
    }


def get_medicine_by_name(name: str) -> Optional[Dict]:
    query = """
        SELECT id, commercial_name, selling_price, min_stock, max_stock
        FROM medicines_medicine WHERE commercial_name LIKE %s LIMIT 1
    """
    rows = execute_query(query, (f'%{name}%',))
    if not rows:
        return None
    row = rows[0]
    return {
        "id": str(row[0]),
        "commercial_name": row[1],
        "selling_price": float(row[2]) if row[2] else 0,
        "min_stock": int(row[3]) if row[3] else 10,
        "max_stock": int(row[4]) if row[4] else 100
    }


def get_medicine_history(medicine_id: str, days: int = 90) -> List[float]:
    """Historique des ventes (série continue, compatible SQLite + PostgreSQL)."""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    if IS_SQLITE:
        query = """
            SELECT date(s.created_at), COALESCE(SUM(si.quantity), 0)
            FROM sales_saleitem si
            JOIN sales_sale s ON si.sale_id = s.id
            WHERE si.medicine_id = %s
              AND date(s.created_at) >= %s
            GROUP BY date(s.created_at)
            ORDER BY date(s.created_at) ASC
        """
    else:
        query = """
            SELECT DATE(s.created_at), COALESCE(SUM(si.quantity), 0)
            FROM sales_saleitem si
            JOIN sales_sale s ON si.sale_id = s.id
            WHERE si.medicine_id = %s
              AND s.created_at >= %s
            GROUP BY DATE(s.created_at)
            ORDER BY DATE(s.created_at) ASC
        """

    rows = execute_query(query, (medicine_id, start_date))

    if not rows:
        logger.warning(f"⚠️ Aucun historique pour {medicine_id}")
        return []

    try:
        start_str = str(rows[0][0])[:10]
        end_str = str(rows[-1][0])[:10]

        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()

        data_dict = {}
        for row in rows:
            date_str = str(row[0])[:10]
            try:
                d = datetime.strptime(date_str, '%Y-%m-%d').date()
                data_dict[d] = float(row[1])
            except Exception as e:
                logger.error(f"Erreur parsing date {date_str}: {e}")

        history = []
        current = start
        while current <= end:
            history.append(data_dict.get(current, 0.0))
            current += timedelta(days=1)

        logger.info(f"✅ Historique {medicine_id}: {len(history)} jours ({sum(history):.0f} unités)")
        return history

    except Exception as e:
        logger.error(f"❌ Erreur get_medicine_history: {e}")
        return [float(row[1]) for row in rows]


def get_medicine_history_by_name(name: str, days: int = 30) -> List[float]:
    med = get_medicine_by_name(name)
    if not med:
        return []
    return get_medicine_history(med["id"], days)


def get_current_stock(medicine_id: str) -> float:
    query = """
        SELECT COALESCE(SUM(quantity), 0)
        FROM inventory_stocklot
        WHERE medicine_id = %s
          AND expiry_date >= CURRENT_DATE
          AND quantity > 0
    """
    rows = execute_query(query, (medicine_id,))
    return float(rows[0][0]) if rows and rows[0][0] else 0


def get_real_daily_demand(medicine_id: str, days: int = 30) -> float:
    history = get_medicine_history(medicine_id, days)
    if not history or sum(history) == 0:
        return get_average_demand_all_medicines(days)
    return sum(history) / len(history)


def get_average_demand_all_medicines(days: int = 30) -> float:
    query = """
        SELECT COALESCE(AVG(daily_total), 0)
        FROM (
            SELECT DATE(s.created_at), SUM(si.quantity) as daily_total
            FROM sales_saleitem si
            JOIN sales_sale s ON si.sale_id = s.id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(s.created_at)
        ) subquery
    """
    rows = execute_query(query, (days,))
    return float(rows[0][0]) if rows and rows[0][0] else 1.0


def get_out_of_stock_medicines() -> List[str]:
    query = """
        SELECT m.commercial_name,
               COALESCE(SUM(CASE WHEN l.expiry_date >= CURRENT_DATE AND l.quantity > 0
                                 THEN l.quantity ELSE 0 END), 0) as total_stock
        FROM medicines_medicine m
        LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
        GROUP BY m.id, m.commercial_name
        HAVING total_stock <= 0
    """
    rows = execute_query(query)
    result = [row[0] for row in rows]

    logger.info(f"🔍 Ruptures détectées: {len(result)} médicaments")
    for med in result:
        logger.info(f"  • {med}")

    return result


def get_revenue_period(days: int, offset: int = 0) -> float:
    query = """
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales_sale
        WHERE created_at >= CURRENT_DATE - INTERVAL '%s days' - INTERVAL '%s days'
          AND created_at < CURRENT_DATE - INTERVAL '%s days'
    """
    rows = execute_query(query, (days + offset, offset, offset))
    return float(rows[0][0]) if rows and rows[0][0] else 0


def get_expiring_medicines(days: int = 30) -> List[tuple]:
    query = """
        SELECT m.commercial_name, l.expiry_date, l.quantity
        FROM inventory_stocklot l
        JOIN medicines_medicine m ON l.medicine_id = m.id
        WHERE l.quantity > 0
          AND l.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
        ORDER BY l.expiry_date ASC LIMIT 15
    """
    rows = execute_query(query, (days,))
    result = []
    for row in rows:
        date_str = row[1]
        if isinstance(date_str, str):
            try:
                date_str = datetime.fromisoformat(date_str).strftime('%d/%m/%Y')
            except:
                pass
        else:
            date_str = date_str.strftime('%d/%m/%Y')
        result.append((row[0], date_str, float(row[2])))
    return result


def get_top_stocks(limit: int = 5) -> List[tuple]:
    query = """
        SELECT m.commercial_name, COALESCE(SUM(l.quantity), 0) as total
        FROM medicines_medicine m
        LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
        WHERE l.expiry_date >= CURRENT_DATE
        GROUP BY m.id ORDER BY total DESC LIMIT %s
    """
    rows = execute_query(query, (limit,))
    return [(row[0], float(row[1])) for row in rows if row[1] > 0]


def get_dashboard_summary() -> Dict:
    rows = execute_query("SELECT COUNT(*) FROM medicines_medicine")
    total_medicines = rows[0][0] if rows else 0

    rows = execute_query("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales_sale WHERE DATE(created_at) = CURRENT_DATE
    """)
    today_sales = float(rows[0][0]) if rows else 0

    rows = execute_query("""
        SELECT COUNT(DISTINCT m.id)
        FROM medicines_medicine m
        LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
        WHERE l.id IS NULL OR l.quantity <= 0
    """)
    out_of_stock = rows[0][0] if rows else 0

    rows = execute_query("""
        SELECT COUNT(DISTINCT m.id)
        FROM inventory_stocklot l
        JOIN medicines_medicine m ON l.medicine_id = m.id
        WHERE l.quantity > 0
          AND l.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
    """)
    expiring_soon = rows[0][0] if rows else 0

    return {
        "total_medicines": total_medicines,
        "today_sales": today_sales,
        "out_of_stock": out_of_stock,
        "expiring_soon": expiring_soon,
        "date": date.today().isoformat()
    }


# ==========================================
# EXTRACTION D'ENTITÉS
# ==========================================

def extract_entities(msg: str) -> Dict:
    msg_lower = msg.lower()
    entities = {"medicine_name": None, "medicine_id": None, "period": "7", "quantity": None}

    rows = execute_query("SELECT id, commercial_name FROM medicines_medicine")
    for med_id, med_name in rows:
        if not med_name:
            continue

        med_name_lower = med_name.lower()
        first_word = med_name_lower.split()[0]

        if med_name_lower in msg_lower or first_word in msg_lower:
            entities["medicine_name"] = med_name
            entities["medicine_id"] = str(med_id)
            logger.info(f"✅ Médicament détecté: {med_name}")
            break

    numbers = re.findall(r'\d+', msg)
    if numbers:
        entities["quantity"] = int(numbers[0])

    if "jour" in msg_lower:
        days = re.findall(r'(\d+)\s*jour', msg_lower)
        entities["period"] = days[0] if days else "7"
    elif "semaine" in msg_lower:
        weeks = re.findall(r'(\d+)\s*semaine', msg_lower)
        entities["period"] = str(int(weeks[0]) * 7) if weeks else "7"
    elif "mois" in msg_lower:
        months = re.findall(r'(\d+)\s*mois', msg_lower)
        entities["period"] = str(int(months[0]) * 30) if months else "30"

    return entities


def detect_intent(msg: str, entities: Dict) -> str:
    msg_lower = msg.lower()

    def contains_word(word: str) -> bool:
        return bool(re.search(r'\b' + re.escape(word) + r'\b', msg_lower))

    if any(contains_word(k) for k in ["expire", "expirent", "expiré", "périmé", "péremption", "périmés"]):
        return "expiration"

    if entities.get("medicine_name"):
        if any(contains_word(k) for k in ["stock", "quantité", "disponible", "reste"]):
            return "stock"
        if any(contains_word(k) for k in ["prévision", "prédiction", "prévoir", "estimer"]):
            return "prevision"
        if any(contains_word(k) for k in ["commander", "achat", "approvisionner"]):
            return "commande"

    if any(contains_word(k) for k in ["rupture", "épuisé", "manquant", "pénurie"]):
        return "rupture"

    if any(contains_word(k) for k in ["chiffre", "revenu", "recette", "gagné"]) or "chiffre d'affaire" in msg_lower:
        return "ca"

    if any(contains_word(k) for k in ["meilleur", "top", "populaire"]) or "plus vendu" in msg_lower:
        return "top"

    if any(contains_word(k) for k in ["dashboard", "résumé", "global", "état", "panorama"]):
        return "dashboard"

    if any(contains_word(k) for k in ["aide", "help", "fonctionnalité"]):
        return "aide"

    if any(contains_word(k) for k in ["bonjour", "salut", "hello", "coucou"]):
        return "salutation"

    return "fallback"


# ==========================================
# MÉMOIRE DE CONVERSATION
# ==========================================

class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.sessions: Dict[str, List[Dict]] = {}
        self.max_history = max_history

    def get_or_create_session(self, session_id: str) -> List[Dict]:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        history = self.get_or_create_session(session_id)
        history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if len(history) > self.max_history * 2:
            self.sessions[session_id] = history[-self.max_history * 2:]

    def get_context(self, session_id: str, last_n: int = 5) -> str:
        history = self.get_or_create_session(session_id)
        if not history:
            return ""
        recent = history[-last_n:]
        return "\n".join([f"{m['role']}: {m['content']}" for m in recent])


conversation_memory = ConversationMemory()

# ==========================================
# CONFIGURATION LLM (Groq)
# ==========================================
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"  # 1 000 req/jour — bon équilibre

# Fallback : si Groq absent, on essaie Mistral
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

if GROQ_API_KEY:
    logger.info(f"✅ Groq configuré (clé: {GROQ_API_KEY[:8]}..., modèle: {GROQ_MODEL})")
elif MISTRAL_API_KEY:
    logger.info(f"✅ Mistral configuré (fallback)")
else:
    logger.warning("⚠️ Aucune clé LLM → fallback uniquement")

SYSTEM_PROMPT = """Tu es l'assistant IA de DENG PHARMA, une pharmacie au Tchad.

RÔLE :
- Tu aides le personnel de la pharmacie (gestion de stock, ventes, ruptures, dates d'expiration, commandes).
- Tu peux aussi répondre à des questions générales sur la santé, les médicaments courants au Tchad, et la gestion d'une pharmacie.

RÈGLES :
1. 🇫🇷 Réponds TOUJOURS en français, ton professionnel et amical.
2. ✂️ Sois concis : 3 à 5 phrases maximum.
3. 💵 Utilise le format FCFA pour les prix (ex: 2 500 FCFA).
4. 📊 Si une question porte sur les données de DENG PHARMA (stock, ventes, CA), utilise UNIQUEMENT le contexte fourni. Si le contexte est vide, dis-le poliment.
5. 💡 Si une question est générale (bonnes pratiques, conseils, définitions), réponds avec tes connaissances.
6. Si tu ne sais vraiment pas, dis-le honnêtement et propose une alternative.
7. Utilise des emojis pertinents pour rendre la réponse plus claire et agréable (💊 🏥 📦 💰 ⚠️ ✅ 🚨 📈 📊 🌧️ ☀️).
8. 🎨 Utilise BEAUCOUP d'emojis pertinents pour illustrer chaque idée.

STYLE :
- Commence souvent par un emoji contextuel (ex: 💊 pour médicaments, 📊 pour données).
- Utilise des listes à puces avec emojis quand tu énumères des points.
- Termine par une phrase amicale.

🎨 RÈGLES D'EMOJIS (à respecter systématiquement) :
- 💊 Pour les médicaments
- 📦 🏪 Pour le stock / inventaire
- 💰 💵 📈 📉 Pour les ventes, prix, chiffre d'affaires
- 🚨 ⚠️ ❌ Pour les alertes, ruptures, problèmes
- ✅ ☑️ 🎉 Pour les confirmations, bonnes nouvelles
- 📅 🗓️ ⏰ Pour les dates, expirations, délais
- 🏥 🩺 👨‍⚕️ Pour la santé, le personnel
- 🌧️ ☀️ 🌡️ Pour la saisonnalité Tchad
- 📊 📋 🔍 Pour les analyses, résumés
- 🛒 🚚 📞 Pour les commandes, livraisons, contact
- 💡 🔔 ⭐ Pour les conseils, rappels, points clés
- 👋 😊 🙏 Pour les salutations et politesses


IMPORTANT : 🚫 Réponds directement en français, sans raisonnement interne visible.
Ne montre pas ton raisonnement dans la réponse finale.
"""

def _call_groq(prompt: str, context: str = "") -> Optional[str]:
    """Appel à l'API Groq via httpx (plus rapide que requests sur cette config)."""
    if not GROQ_API_KEY:
        return None

    t_start = time.time()
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": f"Contexte:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 500,
            "reasoning_effort": "low",
        }

        logger.info(f"🚀 [t={time.time()-t_start:.2f}s] Envoi requête Groq (httpx)...")

        with httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0)
        ) as client:
            response = client.post(GROQ_API_URL, json=payload, headers=headers)

        logger.info(f"✅ [t={time.time()-t_start:.2f}s] Réponse reçue, status={response.status_code}")

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"📝 [t={time.time()-t_start:.2f}s] content_len={len(content)}")
            return content.strip() if content else None

        elif response.status_code == 429:
            logger.warning("⏳ Rate limit Groq (429)")
            return None

        elif response.status_code == 401:
            logger.error("❌ Clé Groq invalide (401)")
            return None

        else:
            logger.error(f"❌ Erreur Groq {response.status_code}: {response.text[:200]}")
            return None

    except httpx.TimeoutException as e:
        logger.error(f"❌ Timeout Groq à t={time.time()-t_start:.2f}s : {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Exception Groq à t={time.time()-t_start:.2f}s : {e}")
        return None




def _call_mistral(prompt: str, context: str = "") -> Optional[str]:
    """Fallback Mistral via httpx."""
    if not MISTRAL_API_KEY:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": f"Contexte:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "mistral-small-latest",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 400,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(MISTRAL_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content else None
        logger.warning(f"⚠️ Mistral {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"❌ Exception Mistral: {e}")
        return None



def call_mistral(prompt: str, context: str = "") -> Optional[str]:
    """
    Point d'entrée unique : essaie Groq, puis Mistral.
    Le nom 'call_mistral' est conservé pour compatibilité avec le reste du code.
    """
    reply = _call_groq(prompt, context)
    if reply:
        return reply

    logger.info("↩️ Bascule sur Mistral (fallback)")
    return _call_mistral(prompt, context)

# ==========================================
# CHARGEMENT DU MODÈLE (CORRIGÉ v6.1)
# ==========================================

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'
MODEL_PATH = MODELS_DIR / 'xgboost_tchad.pkl'
FEATURES_PATH = MODELS_DIR / 'features.pkl'

model = None
features_list = None

logger.info(f"📁 MODELS_DIR   = {MODELS_DIR}")
logger.info(f"📁 MODEL_PATH   = {MODEL_PATH} (exists={MODEL_PATH.exists()})")
logger.info(f"📁 FEATURES_PATH= {FEATURES_PATH} (exists={FEATURES_PATH.exists()})")

try:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Modèle introuvable: {MODEL_PATH}")
    model = joblib.load(str(MODEL_PATH))
    logger.info(f"✅ Modèle chargé: {MODEL_PATH.name}")
except Exception as e:
    logger.error(f"❌ Modèle NON chargé: {e}")
    model = None

try:
    if FEATURES_PATH.is_file():
        features_list = joblib.load(str(FEATURES_PATH))
        logger.info(f"✅ {len(features_list)} features chargées: {features_list}")
    else:
        raise FileNotFoundError(f"features.pkl introuvable: {FEATURES_PATH}")
except Exception as e:
    logger.error(f"❌ Features NON chargées: {e}")
    features_list = None


# ==========================================
# ENCODAGES STABLES (identiques à l'entraînement)
# ==========================================

MEDICINE_ENCODING = {
    "MED001": 0, "MED002": 1, "MED003": 2, "MED004": 3, "MED005": 4,
    "MED006": 5, "MED007": 6, "MED008": 7, "MED009": 8, "MED010": 9,
    "MED011": 10, "MED012": 11, "MED013": 12, "MED014": 13, "MED015": 14,
}

CATEGORY_ENCODING = {
    "Antalgique": 0, "Antibiotique": 1, "Antipaludéen": 2,
    "Réhydratation": 3, "Anti-inflammatoire": 4, "Antihistaminique": 5,
    "Antiseptique": 6, "Vitamine": 7, "Antiparasitaire": 8,
    "unknown": 9,
}


# ==========================================
# HELPERS POUR CONSTRUIRE LES 32 FEATURES
# ==========================================

def _build_full_features(
    history: List[float],
    target_date: date,
    medicine_id: str,
    category: str,
    price: float,
    base_criticality: float,
    current_stock: float,
) -> Dict[str, float]:
    """Construit les 32 features pour une date cible, à partir de l'historique."""
    sales = list(history) if history else [0.0]
    n = len(sales)

    def lag(k: int) -> float:
        if n >= k:
            return float(sales[-k])
        return float(sales[-1]) if n > 0 else 0.0

    def window(w: int) -> List[float]:
        return sales[-w:] if n >= w else sales

    def rmean(w: int) -> float:
        win = window(w)
        return float(np.mean(win)) if win else 0.0

    def rstd(w: int) -> float:
        win = window(w)
        return float(np.std(win)) if len(win) > 1 else 0.0

    def rmin(w: int) -> float:
        win = window(w)
        return float(np.min(win)) if win else 0.0

    def rmax(w: int) -> float:
        win = window(w)
        return float(np.max(win)) if win else 0.0

    month = target_date.month
    dow = target_date.weekday()
    week = target_date.isocalendar().week

    rm7 = rmean(7)
    rm14 = rmean(14)
    rm30 = rmean(30)

    med_enc = MEDICINE_ENCODING.get(medicine_id, 0)
    cat_enc = CATEGORY_ENCODING.get(category, 9)

    return {
        "day_of_week": dow,
        "day_of_month": target_date.day,
        "month": month,
        "week_of_year": week,
        "is_weekend": 1 if dow >= 5 else 0,
        "season": 1 if month in (6, 7, 8, 9, 10) else 0,
        "lag_1": lag(1), "lag_2": lag(2), "lag_3": lag(3),
        "lag_4": lag(4), "lag_5": lag(5), "lag_6": lag(6),
        "lag_7": lag(7), "lag_14": lag(14), "lag_21": lag(21),
        "lag_30": lag(30),
        "rolling_mean_7": rm7,
        "rolling_mean_14": rm14,
        "rolling_mean_30": rm30,
        "rolling_std_7": rstd(7),
        "rolling_std_30": rstd(30),
        "rolling_min_7": rmin(7),
        "rolling_max_7": rmax(7),
        "rolling_min_30": rmin(30),
        "rolling_max_30": rmax(30),
        "trend_7": rm7 - rm14,
        "trend_30": rm7 - rm30,
        "price": float(price),
        "base_criticality": float(base_criticality),
        "current_stock": float(current_stock),
        "medicine_encoded": med_enc,
        "category_encoded": cat_enc,
    }


def _get_medicine_meta(medicine_id: str) -> Dict[str, Any]:
    """Récupère prix + criticité + catégorie depuis la DB (fallbacks neutres)."""
    med = get_medicine_info(medicine_id)
    return {
        "price": med["selling_price"] if med and med.get("selling_price") else 2500.0,
        "base_criticality": 5.0,
        "category": "unknown",
    }


# ==========================================
# APPLICATION FASTAPI
# ==========================================

app = FastAPI(title="DENG PHARMA - Service IA v6.1", version="6.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    medicine_id: str
    days_ahead: int = 7


class StockAnalysisRequest(BaseModel):
    medicine_id: str
    current_stock: Optional[float] = None


class OrderRecommendationRequest(BaseModel):
    medicine_id: str
    current_stock: Optional[float] = None
    lead_time_days: int = 7
    service_level: float = 0.95


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


# ==========================================
# SUPPORT HEAD (Render healthchecks)
# ==========================================

@app.head("/health")
async def health_head():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.head("/")
async def root_head():
    return {"status": "ok", "version": "6.1.0"}


# ==========================================
# ENDPOINTS DE BASE
# ==========================================

@app.get("/")
def root():
    return {
        "service": "DENG PHARMA IA",
        "version": "6.1.0",
        "base": "SQLite" if IS_SQLITE else "PostgreSQL",
        "model_loaded": model is not None,
        "features_count": len(features_list) if features_list else 0,
    }


@app.get("/health")
def health():
    db_ok = get_db_connection() is not None
    return {
        "status": "healthy" if db_ok else "degraded",
        "model_loaded": model is not None,
        "database": "connected" if db_ok else "disconnected",
        "database_type": "SQLite" if IS_SQLITE else "PostgreSQL",
        "groq_configured": bool(GROQ_API_KEY),
        "mistral_configured": bool(MISTRAL_API_KEY),
        "llm_provider": "groq" if GROQ_API_KEY else ("mistral" if MISTRAL_API_KEY else "none"),
        "features_count": len(features_list) if features_list else 0,
        "features": features_list,
    }


# ==========================================
# /predict — VERSION CORRIGÉE v3.0 (32 features)
# ==========================================

@app.post("/predict")
def predict_sales(request: PredictionRequest):
    """
    Prédiction des ventes à J+N avec les 32 features attendues par le modèle v3.0.
    """
    if model is None:
        raise HTTPException(503, "Modèle non disponible")

    if features_list is None:
        raise HTTPException(503, "features.pkl non chargé")

    medicine = get_medicine_info(request.medicine_id)
    if not medicine:
        raise HTTPException(404, f"Médicament non trouvé: {request.medicine_id}")

    history = get_medicine_history(request.medicine_id, days=90)
    if not history or len(history) < 7:
        raise HTTPException(
            400,
            f"Pas assez d'historique pour {request.medicine_id} "
            f"({len(history) if history else 0} jours, minimum 7)"
        )

    meta = _get_medicine_meta(request.medicine_id)
    current_stock = get_current_stock(request.medicine_id)

    today = date.today()
    predictions = []
    working_history = list(history)

    for i in range(request.days_ahead):
        pred_date = today + timedelta(days=i + 1)

        features = _build_full_features(
            history=working_history,
            target_date=pred_date,
            medicine_id=request.medicine_id,
            category=meta["category"],
            price=meta["price"],
            base_criticality=meta["base_criticality"],
            current_stock=current_stock,
        )

        try:
            X = pd.DataFrame([features])[features_list]
        except KeyError as e:
            logger.error(f"❌ Features manquantes: {e}")
            logger.error(f"   Attendues: {features_list}")
            logger.error(f"   Fournies : {list(features.keys())}")
            raise HTTPException(500, f"Features manquantes: {e}")

        pred = max(0.0, float(model.predict(X)[0]))

        predictions.append({
            "date": pred_date.isoformat(),
            "predicted_sales": round(pred, 1),
            "lower_bound": round(pred * 0.7, 1),
            "upper_bound": round(pred * 1.3, 1),
        })

        working_history.append(pred)
        if len(working_history) > 200:
            working_history = working_history[-200:]

    return {
        "medicine_id": request.medicine_id,
        "medicine_name": medicine["commercial_name"],
        "current_stock": current_stock,
        "history_days": len(history),
        "features_used": len(features_list),
        "predictions": predictions,
    }


# ==========================================
# ANALYSE STOCK
# ==========================================

@app.post("/analyze/stock")
def analyze_stock(request: StockAnalysisRequest):
    stock = request.current_stock if request.current_stock is not None else get_current_stock(request.medicine_id)
    daily_demand = get_real_daily_demand(request.medicine_id, days=30)
    if daily_demand <= 0:
        daily_demand = 1.0
    stock_days = stock / daily_demand
    medicine = get_medicine_info(request.medicine_id)

    if stock <= 0:
        status, message, risk = "RUPTURE", "🚨 Rupture totale", 100
    elif stock_days < 7:
        status, message, risk = "RISQUE_RUPTURE", f"⚠️ Rupture dans {stock_days:.1f} jours", 90
    elif stock_days < 14:
        status, message, risk = "SURVEILLANCE", f"👀 Stock faible: {stock_days:.1f} jours", 50
    elif stock_days > 60:
        status, message, risk = "SURSTOCK", f"📦 Surstock: {stock_days:.1f} jours", 10
    else:
        status, message, risk = "OK", f"✅ Stock normal: {stock_days:.1f} jours", 5

    return {
        "medicine_id": request.medicine_id,
        "medicine_name": medicine["commercial_name"] if medicine else "Inconnu",
        "current_stock": round(stock, 1),
        "daily_demand_real": round(daily_demand, 2),
        "days_of_stock": round(stock_days, 1),
        "status": status,
        "message": message,
        "rupture_risk_percent": risk,
    }


@app.post("/recommend/order")
def recommend_order(request: OrderRecommendationRequest):
    daily_demand = get_real_daily_demand(request.medicine_id, days=30)
    if daily_demand <= 0:
        daily_demand = 1.0
    current_stock = request.current_stock if request.current_stock is not None else get_current_stock(request.medicine_id)
    history = get_medicine_history(request.medicine_id, days=90)
    demand_std = float(np.std(history)) if history and len(history) > 1 else daily_demand * 0.3
    z_score = 1.65 if request.service_level == 0.95 else 1.28
    safety_stock = z_score * demand_std * np.sqrt(request.lead_time_days)
    reorder_point = daily_demand * request.lead_time_days + safety_stock
    order_quantity = max(0, reorder_point - current_stock)
    medicine = get_medicine_info(request.medicine_id)
    max_stock = medicine["max_stock"] if medicine else 100
    order_quantity = min(order_quantity, max(0, max_stock - current_stock))

    return {
        "medicine_id": request.medicine_id,
        "medicine_name": medicine["commercial_name"] if medicine else "Inconnu",
        "current_stock": round(current_stock, 1),
        "recommended_order": round(order_quantity),
        "reorder_point": round(reorder_point),
        "safety_stock": round(safety_stock),
        "daily_demand_real": round(daily_demand, 2),
        "message": f"📦 Commander {round(order_quantity)} unités" if order_quantity > 0 else "✅ Stock suffisant",
    }


@app.get("/criticality")
def get_criticality(medicine_id: str):
    medicine = get_medicine_info(medicine_id)
    if not medicine:
        raise HTTPException(404, "Médicament non trouvé")

    history = get_medicine_history(medicine_id, days=90)
    total_sold = sum(history) if history else 0
    avg_daily = total_sold / len(history) if history else 0
    current_stock = get_current_stock(medicine_id)
    days_of_stock = current_stock / avg_daily if avg_daily > 0 else 999

    score = 0
    if total_sold > 500: score += 40
    elif total_sold > 200: score += 30
    elif total_sold > 100: score += 20
    elif total_sold > 50: score += 10
    if days_of_stock < 3: score += 40
    elif days_of_stock < 7: score += 30
    elif days_of_stock < 14: score += 20
    elif days_of_stock < 30: score += 10
    if current_stock < medicine["min_stock"]: score += 20

    if score >= 85: level, color = "CRITIQUE", "red"
    elif score >= 70: level, color = "ÉLEVÉ", "orange"
    elif score >= 50: level, color = "MOYEN", "yellow"
    else: level, color = "FAIBLE", "green"

    return {
        "medicine_id": medicine_id,
        "medicine_name": medicine["commercial_name"],
        "criticality_score": min(score, 100),
        "level": level,
        "color": color,
        "total_sold_90d": int(total_sold),
        "avg_daily_sales": round(avg_daily, 2),
        "current_stock": round(current_stock, 1),
        "days_of_stock": round(days_of_stock, 1) if days_of_stock < 999 else "infini",
    }


@app.get("/seasonal-analysis")
def seasonal_analysis():
    today = date.today()
    is_rainy = today.month in [6, 7, 8, 9, 10]
    rows = execute_query("""
        SELECT m.commercial_name, SUM(si.quantity) as total_sold
        FROM sales_saleitem si
        JOIN sales_sale s ON si.sale_id = s.id
        JOIN medicines_medicine m ON si.medicine_id = m.id
        WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY m.commercial_name ORDER BY total_sold DESC LIMIT 5
    """)
    top_medicines = [{"name": row[0], "sold": int(row[1])} for row in rows]

    return {
        "date": today.isoformat(),
        "season": "Saison des pluies 🌧️" if is_rainy else "Saison sèche ☀️",
        "top_selling_medicines": top_medicines,
        "alerts": [
            "🦟 Pic de paludisme : renforcer antipaludéens" if is_rainy else "🏥 Saison méningite : prévoir vaccins"
        ],
    }


@app.get("/model-performance")
def model_performance():
    try:
        metrics_path = MODELS_DIR / 'metrics.json'
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Métriques non disponibles"}


@app.get("/medicines")
def list_medicines(limit: int = 20):
    rows = execute_query("""
        SELECT id, commercial_name
        FROM medicines_medicine LIMIT %s
    """, (limit,))
    return {
        "medicines": [
            {"id": str(r[0]), "commercial_name": r[1]}
            for r in rows
        ],
        "count": len(rows),
    }


# ==========================================
# /shap-analysis — CORRIGÉ v3.0 (32 features)
# ==========================================

@app.get("/shap-analysis")
def shap_analysis(medicine_id: str):
    """Importance SHAP des 32 features pour un médicament."""
    if model is None:
        raise HTTPException(503, "Modèle non disponible")
    if features_list is None:
        raise HTTPException(503, "features.pkl non chargé")

    clean_id = medicine_id.replace('-', '').strip() if medicine_id else ''

    history = get_medicine_history(clean_id, days=90)
    if not history or len(history) < 7:
        return {
            "medicine_id": medicine_id,
            "error": "Pas assez d'historique (minimum 7 jours)",
            "features": [],
        }

    medicine = get_medicine_info(clean_id)
    meta = _get_medicine_meta(clean_id)
    current_stock = get_current_stock(clean_id)

    last_date = date.today()
    features = _build_full_features(
        history=history,
        target_date=last_date,
        medicine_id=clean_id,
        category=meta["category"],
        price=meta["price"],
        base_criticality=meta["base_criticality"],
        current_stock=current_stock,
    )

    try:
        X = pd.DataFrame([features])[features_list]
    except KeyError as e:
        logger.error(f"❌ SHAP features manquantes: {e}")
        raise HTTPException(500, f"Features manquantes: {e}")

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            sv = shap_values[0][0]
        else:
            sv = shap_values[0]

        feature_importance = [
            {"name": name, "importance": float(sv[i])}
            for i, name in enumerate(features_list)
        ]
        feature_importance.sort(key=lambda x: abs(x['importance']), reverse=True)

        base_val = 0.0
        if hasattr(explainer, 'expected_value'):
            ev = explainer.expected_value
            base_val = float(ev[0]) if hasattr(ev, '__len__') else float(ev)

        return {
            "medicine_id": medicine_id,
            "medicine_name": medicine["commercial_name"] if medicine else "Inconnu",
            "features": feature_importance,
            "base_value": base_val,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.exception("❌ Erreur SHAP")
        return {
            "medicine_id": medicine_id,
            "error": f"Erreur SHAP: {e}",
            "features": [],
        }

# ==========================================
# /chat
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):
    session_id = request.session_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    msg = request.message.strip()
    source = "local" 

    logger.info(f"📩 [{session_id}] {msg}")

    context = conversation_memory.get_context(session_id)
    entities = extract_entities(msg)
    intent = detect_intent(msg, entities)

    logger.info(f"🎯 Intention: {intent}, Entités: {entities}")

    reply = None

    # STOCK
    if intent == "stock" and entities.get("medicine_id"):
        stock = get_current_stock(entities["medicine_id"])
        if stock == 0:
            reply = f"🚨 **{entities['medicine_name']}** est en **RUPTURE DE STOCK** !"
        elif stock < 50:
            reply = f"⚠️ **{entities['medicine_name']}** : seulement **{stock:.0f} unités** en stock. Stock faible."
        else:
            reply = f"✅ **{entities['medicine_name']}** : **{stock:.0f} unités** en stock."

    # RUPTURE
    elif intent == "rupture":
        out = get_out_of_stock_medicines()
        if out:
            reply = f"🚨 **{len(out)} médicaments en rupture :**\n" + "\n".join([f"• {m}" for m in out[:10]])
        else:
            reply = "✅ Aucun médicament en rupture."

    # EXPIRATION
    elif intent == "expiration":
        days = int(entities.get("period", 30))
        expiring = get_expiring_medicines(days)
        if expiring:
            reply = f"⚠️ **{len(expiring)} médicaments expirent dans {days} jours :**\n"
            for med, date_str, qty in expiring[:10]:
                reply += f"• {med} : {qty:.0f} unités (expire le {date_str})\n"
        else:
            reply = f"✅ Aucun médicament n'expire dans les {days} jours."

    # CA
    elif intent == "ca":
        period = int(entities.get("period", 7))
        revenue = get_revenue_period(period)
        prev_revenue = get_revenue_period(period, offset=period)
        evol = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        emoji = "📈" if evol >= 0 else "📉"
        reply = f"💰 **Chiffre d'affaires** ({period} jours) : **{revenue:,.0f} FCFA**\n"
        reply += f"Évolution : {emoji} {evol:+.1f}%"

    # PRÉVISION
    elif intent == "prevision" and entities.get("medicine_id"):
        history = get_medicine_history(entities["medicine_id"], days=30)
        if history:
            pred = sum(history[-7:]) / min(7, len(history)) * 7
            avg = sum(history) / len(history)
            trend = "📈 hausse" if pred > avg else "📉 baisse"
            reply = f"📈 **Prévision {entities['medicine_name']}** :\n"
            reply += f"• Ventes prévues (7j) : **{pred:.0f} unités**\n"
            reply += f"• Moyenne : {avg:.0f}/jour\n"
            reply += f"• Tendance : {trend}"
        else:
            reply = f"⚠️ Pas assez d'historique pour {entities['medicine_name']}."

    # COMMANDE
    elif intent == "commande" and entities.get("medicine_id"):
        stock = get_current_stock(entities["medicine_id"])
        history = get_medicine_history(entities["medicine_id"], days=30)
        if history:
            avg_daily = sum(history) / len(history)
            recommended = max(0, (avg_daily * 14) - stock)
            reply = f"📦 **Commande {entities['medicine_name']}** :\n"
            reply += f"• Stock actuel : {stock:.0f}\n"
            reply += f"• Vente moyenne : {avg_daily:.0f}/jour\n"
            reply += f"• **Quantité recommandée : {recommended:.0f} unités**"
        else:
            reply = f"⚠️ Pas assez de données."

    # TOP
    elif intent == "top":
        top = get_top_stocks(5)
        if top:
            reply = "🏆 **Top 5 stocks :**\n" + "\n".join(
                [f"{i}. {med} : {qty:.0f} unités" for i, (med, qty) in enumerate(top, 1)]
            )
        else:
            reply = "❌ Aucun stock disponible."

    # DASHBOARD
    elif intent == "dashboard":
        data = get_dashboard_summary()
        reply = f"📊 **Résumé DENG PHARMA**\n"
        reply += f"• Médicaments : **{data.get('total_medicines', 0)}**\n"
        reply += f"• Ventes aujourd'hui : **{data.get('today_sales', 0):,.0f} FCFA**\n"
        reply += f"• Ruptures : **{data.get('out_of_stock', 0)}**"

    # AIDE
    elif intent == "aide":
        reply = """🤖 **Aide - Assistant DENG PHARMA**

📦 **Stock** : "Stock de Paracétamol"
🚨 **Ruptures** : "Médicaments en rupture ?"
📈 **Prévisions** : "Prévision Amoxicilline"
💰 **CA** : "Chiffre d'affaires du mois"
⚠️ **Expirations** : "Médicaments qui expirent ?"
📦 **Commande** : "Commander Paracétamol"
🏆 **Top** : "Meilleurs produits"
📊 **Dashboard** : "Résumé"

Posez votre question !"""

    # SALUTATION
    elif intent == "salutation":
        reply = "Bonjour ! 👋 Je suis l'assistant DENG PHARMA. Comment puis-je vous aider ?"

        # FALLBACK → Mistral ou message par défaut
    if reply is None:
        mistral_reply = call_mistral(msg, context)
        if mistral_reply:
            reply = mistral_reply
            source = "llm"
        else:
            reply = "🤔 Je n'ai pas compris. Tapez 'aide' pour voir les fonctionnalités."
            source = "fallback"

    conversation_memory.add_message(session_id, "user", msg)
    conversation_memory.add_message(session_id, "assistant", reply)

    logger.info(f"✅ Réponse générée (intent={intent}, source={source})")

    return {
        "reply": reply,
        "session_id": session_id,
        "intent": intent,
        "source": source,
        "timestamp": datetime.now().isoformat(),
    }


logger.info("✅ Service IA v6.1 démarré")