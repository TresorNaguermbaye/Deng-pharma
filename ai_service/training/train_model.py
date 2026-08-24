# ai_service/training/train_model.py
"""
Script d'entraînement du modèle XGBoost pour DENG PHARMA.
- Charge les données depuis le fichier CSV local tchad_pharma_sales.csv (sinon fallback base SQLite).
- Divise en train (70%), validation (15%), test (15%).
- Entraîne, évalue, sauvegarde le modèle + les métriques.
- Les métriques sont écrites dans models/metrics.json pour l'interface admin.
"""
import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import date, timedelta
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import joblib

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # racine ai_service/
DB_PATH = os.path.join(BASE_DIR, '..', 'backend', 'db.sqlite3')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# Nom du fichier CSV local (dans le même dossier que ce script)
CSV_FILENAME = 'tchad_pharma_sales.csv'
CSV_PATH = os.path.join(os.path.dirname(__file__), CSV_FILENAME)

FEATURES = [
    'day_of_week', 'month', 'is_weekend', 'season',
    'lag_1', 'lag_7', 'lag_30', 'rolling_mean_7', 'rolling_mean_30', 'price'
]

def load_data_from_csv():
    """Charge les données depuis le CSV local en détectant les colonnes."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Fichier CSV introuvable : {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Colonnes détectées dans le CSV : {list(df.columns)}")

    # Dictionnaire de correspondances possibles
    column_mapping = {
        'medicine_id': ['medicine_id', 'med_id', 'id_medicament', 'produit_id', 'medicament_id'],
        'price': ['price', 'prix', 'selling_price', 'prix_unitaire'],
        'date': ['date', 'jour', 'date_vente', 'date_sale'],
        'sales': ['sales', 'ventes', 'quantity', 'quantite', 'total_sales']
    }

    # Fonction pour trouver la première colonne correspondante
    def find_column(df, candidates):
        for c in df.columns:
            if c.lower() in candidates:
                return c
        return None

    # Renommer les colonnes
    rename_dict = {}
    for target, candidates in column_mapping.items():
        col = find_column(df, candidates)
        if col is None:
            raise ValueError(f"Colonne requise introuvable : {target}. Colonnes disponibles : {list(df.columns)}")
        rename_dict[col] = target

    df = df.rename(columns=rename_dict)

    # S'assurer que les colonnes nécessaires sont présentes
    required = ['medicine_id', 'price', 'date', 'sales']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Colonne manquante après mapping : {col}")

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['medicine_id', 'date']).reset_index(drop=True)
    return df

def load_data_from_db():
    """Fallback : charge depuis la base SQLite si le CSV n'est pas disponible."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            m.id AS medicine_id,
            m.commercial_name,
            m.selling_price AS price,
            DATE(s.created_at) AS date,
            SUM(si.quantity) AS sales
        FROM sales_saleitem si
        JOIN sales_sale s ON si.sale_id = s.id
        JOIN medicines_medicine m ON si.medicine_id = m.id
        GROUP BY m.id, date
        ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if df.empty:
        raise ValueError("Aucune donnée trouvée dans la base SQLite.")
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['medicine_id', 'date']).reset_index(drop=True)
    return df

def load_data():
    """Charge les données : priorité au CSV local, sinon base SQLite."""
    try:
        print(f"📂 Tentative de chargement depuis {CSV_FILENAME}...")
        df = load_data_from_csv()
        print(f"✅ Données chargées depuis le CSV ({len(df)} lignes).")
        return df
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("   Utilisation de la base SQLite...")
        return load_data_from_db()
    except Exception as e:
        print(f"Erreur lors du chargement du CSV : {e}")
        print("   Utilisation de la base SQLite...")
        return load_data_from_db()

def feature_engineering(df):
    """Calcule les features temporelles et les lags."""
    df['day_of_week'] = df['date'].dt.weekday
    df['month'] = df['date'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['season'] = df['month'].apply(lambda m: 1 if m in [6,7,8,9,10] else 0)

    # Lags et rolling means par médicament
    for lag in [1, 7, 30]:
        df[f'lag_{lag}'] = df.groupby('medicine_id')['sales'].shift(lag)
    for window in [7, 30]:
        df[f'rolling_mean_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
    return df

def split_data(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """
    Divise le dataframe en train/validation/test en respectant l'ordre temporel.
    Les données sont déjà triées par date (globalement). Pour préserver l'ordre
    temporel global, on divise en fonction de la date.
    """
    # S'assurer que les données sont triées par date globale
    df = df.sort_values('date').reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]

    return train, val, test

def train_model():
    """Charge, prépare, entraîne et sauvegarde le modèle + métriques."""
    print("🚀 Démarrage de l'entraînement...")

    # 1. Chargement des données
    df = load_data()
    print(f"📊 Données brutes : {len(df)} lignes")

    # 2. Feature engineering
    df = feature_engineering(df)
    df_clean = df.dropna()
    print(f"✅ Après nettoyage : {len(df_clean)} lignes")

    if len(df_clean) < 100:
        raise ValueError("Pas assez de données pour un entraînement fiable.")

    # 3. Division train/validation/test
    train, val, test = split_data(df_clean)
    print(f"📚 Entraînement : {len(train)} lignes, Validation : {len(val)} lignes, Test : {len(test)} lignes")

    X_train = train[FEATURES]
    y_train = train['sales']
    X_val = val[FEATURES]
    y_val = val['sales']
    X_test = test[FEATURES]
    y_test = test['sales']

    # 4. Entraînement XGBoost
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        random_state=42
    )
    model.fit(X_train, y_train)

    # 5. Évaluation sur les ensembles validation et test
    def evaluate(model, X, y, name):
        y_pred = model.predict(X)
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mape = np.mean(np.abs((y.values - y_pred) / np.maximum(y.values, 1))) * 100
        r2 = model.score(X, y)
        print(f"\n📊 PERFORMANCE - {name} :")
        print(f"   MAE  : {mae:.2f}")
        print(f"   RMSE : {rmse:.2f}")
        print(f"   MAPE : {mape:.1f}%")
        print(f"   R²   : {r2:.3f}")
        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "r2": float(r2)
        }

    val_metrics = evaluate(model, X_val, y_val, "Validation")
    test_metrics = evaluate(model, X_test, y_test, "Test")

    # 6. Sauvegarde du modèle et des features
    joblib.dump(model, os.path.join(MODELS_DIR, 'xgboost_tchad.pkl'))
    joblib.dump(FEATURES, os.path.join(MODELS_DIR, 'features.pkl'))

    # 7. Sauvegarde des métriques dans metrics.json
    metrics = {
        "test": test_metrics,
        "validation": val_metrics,
        "model_version": f"v{date.today().strftime('%Y%m%d')}",
        "trained_at": date.today().isoformat(),
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test)
    }

    metrics_path = os.path.join(MODELS_DIR, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n💾 Modèle et métriques sauvegardés dans {MODELS_DIR}")
    print(f"📈 Version du modèle : {metrics['model_version']}")

if __name__ == "__main__":
    train_model()
