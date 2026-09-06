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
import random
import logging

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
# CONFIGURATION LOGGING
# ==========================================

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
        logger.error(f"❌ Erreur base de données (get_commercial_name): {e}")
    
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
        logger.error(f"❌ Erreur historique: {e}")
        return None


# ==========================================
# MÉMOIRE DE CONVERSATION
# ==========================================

conversation_memory = {}

def get_conversation_context(user_id: str = "default") -> Dict:
    """Récupère le contexte de la conversation"""
    if user_id not in conversation_memory:
        conversation_memory[user_id] = {
            "last_question": None,
            "last_answer": None,
            "last_medicine": None,
            "history": []
        }
    return conversation_memory[user_id]

def update_conversation(user_id: str, question: str, answer: str, medicine: str = None):
    """Met à jour le contexte de la conversation"""
    context = get_conversation_context(user_id)
    context["last_question"] = question
    context["last_answer"] = answer
    if medicine:
        context["last_medicine"] = medicine
    context["history"].append({"question": question, "answer": answer, "medicine": medicine})
    
    if len(context["history"]) > 10:
        context["history"] = context["history"][-10:]


# ==========================================
# FONCTIONS DE BASE (Stock, Ventes, etc.)
# ==========================================

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
        logger.error(f"Erreur stock: {e}")
        return None

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
        logger.error(f"Erreur ruptures: {e}")
        return []

def get_expiring_medicines(days: int = 30) -> List[tuple]:
    """Retourne les médicaments qui expirent dans les X jours"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = """
            SELECT m.commercial_name, l.expiry_date
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
        return [(row[0], row[1].strftime('%d/%m/%Y')) for row in rows]
    except Exception as e:
        logger.error(f"Erreur expirations: {e}")
        return []

def get_medicine_history_by_name(name: str, days: int = 30):
    """Récupère l'historique des ventes par nom de médicament"""
    return get_medicine_history(name, medicine_name=name, days=days)

def predict_sales_from_history(history: List[float]) -> float:
    """Prédit les ventes à partir de l'historique"""
    if not history:
        return 0
    return sum(history[-7:]) / min(7, len(history)) * 7


# ==========================================
# DONNÉES RÉELLES POUR LE CHATBOT
# ==========================================

def get_real_revenue(period_days: int = 30, offset: int = 0) -> Dict:
    """Calcule le chiffre d'affaires réel sur une période"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"error": "Base de données inaccessible"}
        
        cursor = conn.cursor()
        
        # ✅ Requête corrigée
        query = """
            SELECT 
                COALESCE(SUM(total_amount), 0) as total,
                COUNT(*) as nb_ventes,
                COALESCE(AVG(total_amount), 0) as panier_moyen
            FROM sales_sale
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days' - INTERVAL '%s days'
              AND created_at < CURRENT_DATE - INTERVAL '%s days'
        """
        cursor.execute(query, (period_days + offset, offset))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return {"error": "Aucune donnée trouvée pour cette période"}
        
        return {
            "total": float(row[0]) if row[0] else 0,
            "nb_ventes": row[1] if row[1] else 0,
            "panier_moyen": float(row[2]) if row[2] else 0,
            "period": period_days
        }
    except Exception as e:
        logger.error(f"Erreur revenu réel: {e}")
        return {"error": str(e)}

def get_real_top_products(limit: int = 5) -> List[Dict]:
    """Top produits réels"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        query = """
            SELECT 
                m.commercial_name, 
                COALESCE(SUM(si.quantity), 0) as qte_vendue,
                COALESCE(SUM(si.quantity * si.unit_price), 0) as chiffre_affaires,
                COUNT(DISTINCT s.id) as nb_ventes
            FROM sales_saleitem si
            JOIN sales_sale s ON si.sale_id = s.id
            JOIN medicines_medicine m ON si.medicine_id = m.id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY m.id
            ORDER BY qte_vendue DESC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "name": row[0],
                "sold": float(row[1]),
                "revenue": float(row[2]),
                "transactions": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Erreur top produits: {e}")
        return []

def get_stock_health() -> Dict:
    """Analyse la santé globale du stock"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"error": "Base de données inaccessible"}
        
        cursor = conn.cursor()
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN l.quantity = 0 THEN 1 ELSE 0 END) as ruptures,
                SUM(CASE WHEN l.quantity BETWEEN 1 AND 10 THEN 1 ELSE 0 END) as tres_bas,
                SUM(CASE WHEN l.quantity BETWEEN 11 AND 30 THEN 1 ELSE 0 END) as bas,
                SUM(CASE WHEN l.quantity > 30 THEN 1 ELSE 0 END) as suffisant
            FROM medicines_medicine m
            LEFT JOIN inventory_stocklot l ON l.medicine_id = m.id
        """
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        total = row[0] or 0
        ruptures = row[1] or 0
        tres_bas = row[2] or 0
        bas = row[3] or 0
        suffisant = row[4] or 0
        
        health_score = 100 - ((ruptures + tres_bas) / max(total, 1)) * 100
        
        return {
            "total": total,
            "ruptures": ruptures,
            "tres_bas": tres_bas,
            "bas": bas,
            "suffisant": suffisant,
            "health_score": round(health_score, 1),
            "status": "🟢 Bon" if health_score > 80 else "🟠 Moyen" if health_score > 50 else "🔴 Critique"
        }
    except Exception as e:
        logger.error(f"Erreur santé stock: {e}")
        return {"error": str(e)}


# ==========================================
# DÉTECTION INTELLIGENTE (NLP basique)
# ==========================================

SYNONYMS = {
    "stock": ["stock", "quantité", "disponible", "reste", "combien", "nombre"],
    "rupture": ["rupture", "épuisé", "manquant", "plus de", "en rade", "absence"],
    "prevision": ["prévision", "prédiction", "prévoir", "estimer", "anticipation"],
    "ca": ["chiffre", "ca", "revenu", "recette", "gagné", "bénéfice"],
    "expiration": ["expire", "périmé", "péremption", "date limite", "fin de validité"],
    "commande": ["commander", "achat", "approvisionner", "réappro", "acheter"],
    "vente": ["vente", "vendu", "achat client", "client a acheté"],
    "meilleur": ["meilleur", "top", "plus vendu", "le plus", "record"],
    "prix": ["prix", "coût", "tarif", "valeur"],
}

MEDICINE_VARIANTS = {
    "paracétamol": ["paracétamol", "doliprane", "efferalgan", "daflon"],
    "ibuprofène": ["ibuprofène", "advil", "nurofen", "ibu"],
    "amoxicilline": ["amoxicilline", "amox", "clavamox"],
    "cétirizine": ["cétirizine", "zyrtec", "cetirizin"],
    "artéméther": ["artéméther", "artemether", "paluther"],
    "quinine": ["quinine", "quinin", "quinine"],
    "diclofénac": ["diclofénac", "voltaren", "diclofenac"],
    "métronidazole": ["métronidazole", "flagyl", "metronidazole"],
    "oméprazole": ["oméprazole", "omeprazol", "mopral"],
    "azithromycine": ["azithromycine", "zithromax", "azithro"],
    "ciprofloxacine": ["ciprofloxacine", "cipro", "ciprofloxacin"],
    "sro": ["sro", "sel de réhydratation", "réhydratation"],
    "vaccin": ["vaccin", "vaccination", "vacc"],
    "moustiquaire": ["moustiquaire", "moustiquaire", "moustique"],
    "ceftriaxone": ["ceftriaxone", "ceftri", "rocephin"],
}

def detect_medicine_name(msg: str) -> Optional[str]:
    """Détecte le nom d'un médicament dans le message"""
    msg_lower = msg.lower()
    for med, variants in MEDICINE_VARIANTS.items():
        for variant in variants:
            if variant in msg_lower:
                return med
    return None

def detect_intent_improved(msg: str) -> Dict:
    """Détecte l'intention avec les synonymes"""
    msg_lower = msg.lower()
    
    for intent, keywords in SYNONYMS.items():
        for keyword in keywords:
            if keyword in msg_lower:
                return {"intent": intent, "confidence": 0.9, "keyword": keyword}
    
    if "aide" in msg_lower or "help" in msg_lower or "que peux-tu" in msg_lower:
        return {"intent": "aide", "confidence": 0.9, "keyword": "aide"}
    
    if "bonjour" in msg_lower or "salut" in msg_lower:
        return {"intent": "salutation", "confidence": 0.9, "keyword": "bonjour"}
    
    return {"intent": "fallback", "confidence": 0.3, "keyword": None}


# ==========================================
# GESTIONNAIRES DE RÉPONSES
# ==========================================

def handle_salutation() -> Dict:
    """Réponse aux salutations"""
    greetings = [
        "👋 Bonjour ! Je suis l'assistant de DENG PHARMA. Comment puis-je vous aider ?",
        "🩺 Bonjour ! Je suis là pour vous aider à gérer votre pharmacie. Que voulez-vous savoir ?",
        "💊 Salut ! Je peux vous renseigner sur vos stocks, vos ventes, et bien plus encore."
    ]
    return {"reply": random.choice(greetings), "source": "internal"}

def handle_stock_query(entities: Dict) -> Dict:
    """Répond à une question sur le stock"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Quel médicament vous intéresse ?", "source": "internal"}
    
    stock = get_medicine_stock_by_name(med_name)
    if stock is None:
        return {"reply": f"❌ Je n'ai pas trouvé de médicament '{med_name}'.", "source": "internal"}
    
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
        "source": "internal"
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
    return {"reply": reply, "source": "internal"}

def handle_prediction_query(entities: Dict) -> Dict:
    """Donne une prévision de vente"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Pour quel médicament voulez-vous une prévision ?", "source": "internal"}
    
    history = get_medicine_history_by_name(med_name, days=30)
    if not history or len(history) < 3:
        return {
            "reply": f"⚠️ Pas assez de données pour **{med_name}**. Il faut au moins 3 jours d'historique.",
            "source": "internal"
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
        "source": "internal"
    }

def handle_revenue_query(entities: Dict) -> Dict:
    """Calcule le chiffre d'affaires réel"""
    period = int(entities.get("period", "30"))
    revenue_data = get_real_revenue(period)
    
    if "error" in revenue_data:
        return {"reply": f"❌ {revenue_data['error']}", "source": "internal"}
    
    prev_revenue_data = get_real_revenue(period, offset=period)
    prev_total = prev_revenue_data.get("total", 0) if "error" not in prev_revenue_data else 0
    
    evolution = 0
    if prev_total > 0:
        evolution = ((revenue_data["total"] - prev_total) / prev_total) * 100
    
    emoji = "📈" if evolution >= 0 else "📉"
    
    return {
        "reply": (
            f"💰 **Chiffre d'affaires réel**\n\n"
            f"  • Période : **{period}** derniers jours\n"
            f"  • Total : **{revenue_data['total']:,.0f}** FCFA\n"
            f"  • Nombre de ventes : **{revenue_data['nb_ventes']}**\n"
            f"  • Panier moyen : **{revenue_data['panier_moyen']:,.0f}** FCFA\n"
            f"  • Évolution vs période précédente : {emoji} **{evolution:+.1f}%**"
        ),
        "source": "internal"
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
    return {"reply": reply, "source": "internal"}

def handle_order_query(entities: Dict) -> Dict:
    """Recommande une commande"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ Pour quel médicament voulez-vous une recommandation ?", "source": "internal"}
    
    stock = get_medicine_stock_by_name(med_name)
    history = get_medicine_history_by_name(med_name, days=30)
    if not history:
        return {"reply": f"⚠️ Pas assez de données pour {med_name}.", "source": "internal"}
    
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
        "source": "internal"
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
                "source": "internal"
            }
        else:
            return {"reply": f"❌ Aucune vente enregistrée pour {med_name}.", "source": "internal"}
    else:
        return {"reply": "❓ Pour quel médicament voulez-vous les ventes ?", "source": "internal"}

def handle_best_selling() -> Dict:
    """Médicament le plus vendu (données réelles)"""
    top = get_real_top_products(1)
    
    if not top:
        return {"reply": "Aucune vente enregistrée pour le moment.", "source": "internal"}
    
    med = top[0]
    return {
        "reply": (
            f"🏆 **Médicament le plus vendu**\n\n"
            f"  • Nom : **{med['name']}**\n"
            f"  • Quantité vendue : **{med['sold']:.0f}** unités\n"
            f"  • Chiffre d'affaires : **{med['revenue']:,.0f}** FCFA\n"
            f"  • Nombre de ventes : **{med['transactions']}** transactions"
        ),
        "source": "internal"
    }

def handle_price_query(entities: Dict) -> Dict:
    """Répond à une question sur le prix"""
    med_name = entities.get("medicine_name")
    if not med_name:
        return {"reply": "❓ De quel médicament voulez-vous connaître le prix ?", "source": "internal"}
    
    try:
        conn = get_db_connection()
        if not conn:
            return {"reply": "Je n'ai pas accès aux données actuellement.", "source": "internal"}
        
        cursor = conn.cursor()
        query = """
            SELECT selling_price, purchase_price
            FROM medicines_medicine
            WHERE commercial_name ILIKE %s
        """
        cursor.execute(query, (f'%{med_name}%',))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return {
                "reply": f"💰 **{med_name.capitalize()}** :\n  • Prix de vente : **{row[0]} FCFA**\n  • Prix d'achat : **{row[1]} FCFA**",
                "source": "internal"
            }
        else:
            return {"reply": f"❌ Je n'ai pas trouvé de médicament '{med_name}'.", "source": "internal"}
    except Exception as e:
        logger.error(f"Erreur prix: {e}")
        return {"reply": "Je n'ai pas pu récupérer les données.", "source": "internal"}

def handle_complex_query(msg: str, entities: Dict, context: Dict) -> Optional[Dict]:
    """Requêtes complexes avec données réelles"""
    if any(word in msg for word in ["analyse", "résumé", "global", "synthèse", "état"]):
        stock_health = get_stock_health()
        revenue = get_real_revenue(30)
        top_products = get_real_top_products(3)
        ruptures = get_out_of_stock_medicines()
        
        if "error" in stock_health:
            return {"reply": "Je n'ai pas pu récupérer les données.", "source": "internal"}
        
        reply = "📊 **Synthèse de votre pharmacie (données réelles) :**\n\n"
        reply += f"🏷️ **Stock :** {stock_health.get('total', 0)} médicaments\n"
        reply += f"   • Ruptures : {stock_health.get('ruptures', 0)}\n"
        reply += f"   • Stock très bas : {stock_health.get('tres_bas', 0)}\n"
        reply += f"   • Santé : {stock_health.get('status', 'Inconnu')}\n\n"
        
        if "error" not in revenue:
            reply += f"💰 **Chiffre d'affaires (30j) :** {revenue.get('total', 0):,.0f} FCFA\n"
            reply += f"   • {revenue.get('nb_ventes', 0)} ventes\n"
            reply += f"   • Panier moyen : {revenue.get('panier_moyen', 0):,.0f} FCFA\n\n"
        
        reply += "🏆 **Top 3 des ventes :**\n"
        for i, p in enumerate(top_products[:3], 1):
            reply += f"   {i}. {p['name']} : {p['sold']:.0f} unités\n"
        
        if ruptures:
            reply += f"\n🚨 **{len(ruptures)} médicament(s) en rupture**"
        
        return {"reply": reply, "source": "internal"}
    
    return None

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
            "  • 📦 **Commande** : 'Commander Amoxicilline'\n"
            "  • 🏆 **Top ventes** : 'Quel est le plus vendu ?'\n"
            "  • 💰 **Prix** : 'Prix de Paracétamol'\n"
            "  • 📊 **Analyse** : 'Analyse globale de ma pharmacie'\n\n"
            "Que puis-je faire pour vous ? 😊"
        ),
        "source": "internal"
    }

def handle_fallback_improved(msg: str) -> Dict:
    """Réponse améliorée pour les questions non comprises"""
    suggestions = [
        "💡 Vous pouvez me poser des questions sur :\n  • Les stocks ('Stock de Paracétamol')\n  • Les ruptures ('Quels sont les médicaments en rupture ?')\n  • Les prévisions ('Prévision pour Amoxicilline')\n  • Le chiffre d'affaires ('CA du mois')\n  • Les prix ('Prix de Paracétamol')\n  • L'analyse globale ('Analyse de ma pharmacie')",
        "🔍 Je ne comprends pas votre question. Essayez :\n  • 'Stock de Paracétamol'\n  • 'Quels sont les médicaments en rupture ?'\n  • 'Prévision pour Amoxicilline'\n  • 'CA du mois'\n  • 'Prix de Amoxicilline'\n  • 'Analyse globale'"
    ]
    
    return {
        "reply": f"🤔 Je n'ai pas bien compris votre demande.\n\n{random.choice(suggestions)}",
        "source": "internal"
    }


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
# ENDPOINTS EXISTANTS (PRÉDICTION, STOCK, ETC.)
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
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'training', 'train_model.py')
        subprocess.Popen([sys.executable, script_path])
        return {"status": "Entraînement lancé en arrière-plan"}
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du lancement : {e}")

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

    logger.info(f"DEBUG: medicine_name = '{request.medicine_name}', historique = {len(history) if history else 0}")

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

@app.post("/analyze/stock")
def analyze_stock(request: StockAnalysisRequest):
    daily_demand = np.random.randint(20, 60)
    stock_days = request.current_stock / max(daily_demand, 1)
    
    if stock_days < 7:
        status, message, risk = "RISQUE_RUPTURE", f"⚠️ Rupture probable dans {stock_days:.0f} jours", 90
    elif stock_days < 14:
        status, message, risk = "SURVEILLANCE", f"👀 Stock faible : {stock_days:.0f} jours restants", 50
    elif stock_days > 60:
        status, message, risk = "SURSTOCK", f"📦 Surstock : {stock_days:.0f} jours de stock", 10
    else:
        status, message, risk = "OK", f"✅ Stock normal : {stock_days:.0f} jours", 5
    
    return {
        "medicine_id": request.medicine_id,
        "current_stock": request.current_stock,
        "daily_demand_estimated": daily_demand,
        "days_of_stock": round(stock_days, 1),
        "rupture_risk_percent": risk,
        "status": status,
        "message": message
    }

@app.post("/recommend/order")
def recommend_order(request: OrderRecommendationRequest):
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

@app.get("/criticality")
def get_criticality(medicine_id: str = "MED003"):
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

@app.get("/seasonal-analysis")
def seasonal_analysis():
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

@app.get("/shap-analysis")
def shap_analysis(medicine_id: str):
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
# CHATBOT PRINCIPAL (route /chat)
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):
    """Chatbot intelligent avancé avec mémoire et analyses"""
    msg = request.message.lower().strip()
    today = date.today()
    user_id = "default"
    
    context = get_conversation_context(user_id)
    
    # Détection du médicament
    medicine_name = detect_medicine_name(msg)
    entities = {
        "medicine_name": medicine_name,
        "period": "7",
        "quantity": None
    }
    
    # Extraction des nombres
    numbers = re.findall(r'\d+', msg)
    if numbers:
        entities["quantity"] = int(numbers[0])
        if "jour" in msg:
            entities["period"] = numbers[0]
        elif "semaine" in msg:
            entities["period"] = str(int(numbers[0]) * 7)
        elif "mois" in msg:
            entities["period"] = str(int(numbers[0]) * 30)
    
    # Détection avancée de l'intention
    intent_result = detect_intent_improved(msg)
    intent = intent_result.get("intent")
    
    logger.info(f"🔍 Intention: {intent} | Médicament: {medicine_name}")
    
    # Exécution de l'action
    result = handle_complex_query(msg, entities, context)
    
    if not result:
        if intent == "salutation":
            result = handle_salutation()
        elif intent == "stock" and entities.get("medicine_name"):
            result = handle_stock_query(entities)
        elif intent == "rupture":
            result = handle_rupture_query()
        elif intent == "prevision" and entities.get("medicine_name"):
            result = handle_prediction_query(entities)
        elif intent == "ca":
            result = handle_revenue_query(entities)
        elif intent == "expiration":
            result = handle_expiration_query(entities)
        elif intent == "commande" and entities.get("medicine_name"):
            result = handle_order_query(entities)
        elif intent == "vente" and entities.get("medicine_name"):
            result = handle_sales_query(entities)
        elif "meilleur" in msg or "plus vendu" in msg or "top" in msg:
            result = handle_best_selling()
        elif "prix" in msg and entities.get("medicine_name"):
            result = handle_price_query(entities)
        elif intent == "aide":
            result = handle_help()
        else:
            result = handle_fallback_improved(msg)
    
    # Questions de suivi
    follow_up = ""
    if result and medicine_name and "stock" in result.get("reply", ""):
        follow_up = "\n\n💡 Voulez-vous connaître la prévision de vente pour ce médicament ?"
    elif result and "rupture" in result.get("reply", ""):
        follow_up = "\n\n💡 Souhaitez-vous recevoir une alerte par email pour les ruptures ?"
    elif result and "analyse" in result.get("reply", ""):
        follow_up = "\n\n💡 Voulez-vous des détails sur un médicament en particulier ?"
    
    if follow_up and "question" not in msg:
        result["reply"] += follow_up
    
    # Sauvegarde du contexte
    update_conversation(user_id, msg, result.get("reply", ""), medicine_name)
    
    result["timestamp"] = today.isoformat()
    return result


logger.info("\n✅ API DENG PHARMA prête !")
logger.info("📖 Documentation : http://127.0.0.1:8001/docs")