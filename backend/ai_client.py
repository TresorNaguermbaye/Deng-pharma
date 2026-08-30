# backend/ai_client.py
"""
Client HTTP pour le service IA DENG PHARMA
Permet au backend Django de communiquer avec le microservice FastAPI
"""
import os

import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DengPharmaAIClient:
    """
    Client pour interagir avec le service IA de DENG PHARMA
    """
    
    def __init__(self, base_url: str = None):
        # Utiliser la variable d'environnement ou la valeur par défaut
        self.base_url = base_url or os.getenv('AI_SERVICE_URL', 'http://127.0.0.1:8001')
        self.timeout = 10  # secondes
        logger.info(f"🤖 Service IA configuré à : {self.base_url}")
        
    def health_check(self) -> Dict:
        """Vérifie que le service IA est opérationnel"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Service IA inaccessible : {e}")
            return {"status": "error", "message": str(e)}
    
    def predict_sales(self, medicine_id: str, days_ahead: int = 7) -> Dict:
        """
        Prédit les ventes pour un médicament
        
        Args:
            medicine_id: Identifiant du médicament (ex: MED003)
            days_ahead: Nombre de jours à prédire
        
        Returns:
            Dict avec les prédictions
        """
        try:
            response = requests.post(
                f"{self.base_url}/predict",
                json={"medicine_id": medicine_id, "days_ahead": days_ahead},
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur prédiction : {e}")
            return {"error": str(e)}
    
    def analyze_stock(self, medicine_id: str, current_stock: float) -> Dict:
        """
        Analyse le risque de rupture ou surstock
        
        Args:
            medicine_id: Identifiant du médicament
            current_stock: Stock actuel en unités
        
        Returns:
            Dict avec l'analyse de stock
        """
        try:
            response = requests.post(
                f"{self.base_url}/analyze/stock",
                json={"medicine_id": medicine_id, "current_stock": current_stock},
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur analyse stock : {e}")
            return {"error": str(e)}
    
    def recommend_order(
        self, 
        medicine_id: str, 
        current_stock: float, 
        lead_time_days: int = 7,
        service_level: float = 0.95
    ) -> Dict:
        """
        Recommande la quantité à commander
        
        Args:
            medicine_id: Identifiant du médicament
            current_stock: Stock actuel
            lead_time_days: Délai de livraison en jours
            service_level: Niveau de service souhaité (0.95 = 95%)
        
        Returns:
            Dict avec la recommandation
        """
        try:
            response = requests.post(
                f"{self.base_url}/recommend/order",
                json={
                    "medicine_id": medicine_id,
                    "current_stock": current_stock,
                    "lead_time_days": lead_time_days,
                    "service_level": service_level
                },
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur recommandation : {e}")
            return {"error": str(e)}
    
    def get_seasonal_analysis(self) -> Dict:
        """Retourne l'analyse saisonnière pour le Tchad"""
        try:
            response = requests.get(
                f"{self.base_url}/seasonal-analysis",
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur analyse saisonnière : {e}")
            return {"error": str(e)}
    
    def get_criticality(self, medicine_id: str) -> Dict:
        """Retourne le score de criticité d'un médicament"""
        try:
            response = requests.get(
                f"{self.base_url}/criticality",
                params={"medicine_id": medicine_id},
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur criticité : {e}")
            return {"error": str(e)}


    def get_model_performance(self) -> Dict:
        """Récupère les métriques du modèle en production (MAE, RMSE, MAPE, version)."""
        try:
            response = requests.get(
                f"{self.base_url}/model-performance",
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur model performance : {e}")
            return {"error": str(e)}



    def get_shap_analysis(self, medicine_id: str) -> Dict:
        """Récupère l'analyse SHAP pour un médicament."""
        try:
            response = requests.get(
                f"{self.base_url}/shap-analysis",
                params={"medicine_id": medicine_id},
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur SHAP : {e}")
            return {"error": str(e)}



    def train_model(self) -> Dict:
        """Déclenche l'entraînement du modèle IA."""
        try:
            response = requests.post(
                f"{self.base_url}/train",
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur lors du lancement de l'entraînement : {e}")
            return {"error": str(e)}




    def chat(self, message: str) -> Dict:
        """Envoie un message au chatbot IA"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message},
                timeout=self.timeout
            )
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur chat : {e}")
            return {"reply": "Désolé, le service IA est momentanément indisponible."}


# Instance unique du client (pattern Singleton)
ai_client = DengPharmaAIClient()