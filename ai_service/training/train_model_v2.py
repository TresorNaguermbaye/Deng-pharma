# ai_service/training/train_model_v2.py
"""
DENG PHARMA - Entraînement XGBoost AMÉLIORÉ
Version 3.0 - Basé sur tchad_pharma_sales.csv (10 950 lignes)

✅ Lecture depuis CSV
✅ Split temporel PAR MÉDICAMENT
✅ Réutilise les features pré-calculées du CSV
✅ Ajoute : std, min/max, trend, encodages
✅ Optuna (30 trials) + early stopping
✅ MAPE corrigé, R², feature importance
"""
import os
import json
import warnings
import pandas as pd
import numpy as np
from datetime import date
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import optuna

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)


# ==========================================
# CHEMINS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'tchad_pharma_sales.csv')
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

print(f"📁 CSV     : {CSV_PATH}")
print(f"📁 Modèles : {MODELS_DIR}")


# ==========================================
# FEATURES (30 features)
# ==========================================
FEATURES = [
    # Temporelles (6)
    'day_of_week', 'day_of_month', 'month', 'week_of_year',
    'is_weekend', 'season',
    # Lags (10)
    'lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_5',
    'lag_6', 'lag_7', 'lag_14', 'lag_21', 'lag_30',
    # Rolling means (3)
    'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
    # Rolling std (2)
    'rolling_std_7', 'rolling_std_30',
    # Rolling min/max (4)
    'rolling_min_7', 'rolling_max_7',
    'rolling_min_30', 'rolling_max_30',
    # Tendance (2)
    'trend_7', 'trend_30',
    # Contexte métier (3)
    'price', 'base_criticality', 'current_stock',
    # Encodages (2)
    'medicine_encoded', 'category_encoded',
]
TARGET = 'sales'


# ==========================================
# 1. CHARGEMENT
# ==========================================
def load_data_from_csv():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"❌ CSV introuvable : {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip().lower() for c in df.columns]

    print(f"\n📊 Données brutes : {len(df)} lignes, {len(df.columns)} colonnes")

    # Vérifs
    for col in ['date', 'medicine_id', 'sales']:
        if col not in df.columns:
            raise ValueError(f"❌ Colonne manquante : {col}")

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'sales'])
    df['sales'] = df['sales'].astype(float)

    if 'price' not in df.columns:
        df['price'] = 2500.0
    df['price'] = df['price'].astype(float)

    if 'base_criticality' not in df.columns:
        df['base_criticality'] = 5
    df['base_criticality'] = df['base_criticality'].astype(float)

    if 'current_stock' not in df.columns:
        df['current_stock'] = 0
    df['current_stock'] = df['current_stock'].astype(float)

    if 'category' not in df.columns:
        df['category'] = 'unknown'

    print(f"💊 Médicaments : {df['medicine_id'].nunique()}")
    print(f"🏷️  Catégories  : {df['category'].nunique()}")
    print(f"📅 Période     : {df['date'].min().date()} → {df['date'].max().date()}")

    return df


# ==========================================
# 2. FEATURE ENGINEERING
# ==========================================
def feature_engineering(df):
    print("\n🔧 Feature engineering...")

    # --- Encodages ---
    df['medicine_encoded'] = df['medicine_id'].astype('category').cat.codes
    df['category_encoded'] = df['category'].astype('category').cat.codes

    # --- Temporelles manquantes ---
    df['day_of_month'] = df['date'].dt.day
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)

    # Colonnes du CSV déjà présentes : day_of_week, month, is_weekend, season
    # On les garde telles quelles.

    # --- Série continue par médicament (lags manquants) ---
    print("  → Séries continues par médicament...")
    all_series = []
    for med_id, group in df.groupby('medicine_id'):
        group = group.set_index('date').sort_index()
        full_range = pd.date_range(group.index.min(), group.index.max(), freq='D')
        group = group.reindex(full_range)

        group['sales'] = group['sales'].fillna(0)
        group['medicine_id'] = med_id
        for col in ['medicine_encoded', 'category_encoded', 'price',
                    'base_criticality', 'current_stock']:
            group[col] = group[col].ffill().bfill()

        all_series.append(group)

    df = pd.concat(all_series).reset_index().rename(columns={'index': 'date'})

    # --- Lags manquants (le CSV a déjà lag_1,3,7,14,30) ---
    print("  → Lags manquants (2,4,5,6,21)...")
    for lag in [2, 4, 5, 6, 21]:
        df[f'lag_{lag}'] = df.groupby('medicine_id')['sales'].shift(lag)

    # --- Rolling std / min / max (manquants) ---
    print("  → Rolling std/min/max...")
    for window in [7, 30]:
        df[f'rolling_std_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).std().fillna(0)
        )
        df[f'rolling_min_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).min()
        )
        df[f'rolling_max_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).max()
        )

    # --- Tendance ---
    print("  → Indicateurs de tendance...")
    df['trend_7'] = df['rolling_mean_7'] - df['rolling_mean_14']
    df['trend_30'] = df['rolling_mean_7'] - df['rolling_mean_30']

    # --- Nettoyage ---
    before = len(df)
    df = df.dropna(subset=FEATURES)
    df = df.fillna(0)
    print(f"✅ {before} → {len(df)} lignes après nettoyage")
    print(f"📊 Features : {len(FEATURES)}")

    return df


# ==========================================
# 3. SPLIT PAR MÉDICAMENT
# ==========================================
def split_data(df, train_ratio=0.7, val_ratio=0.15):
    print("\n✂️  Split temporel PAR médicament...")

    train_dfs, val_dfs, test_dfs = [], [], []
    skipped = 0

    for med_id, group in df.groupby('medicine_id'):
        group = group.sort_values('date').reset_index(drop=True)
        n = len(group)
        if n < 20:
            skipped += 1
            continue

        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_dfs.append(group.iloc[:train_end])
        val_dfs.append(group.iloc[train_end:val_end])
        test_dfs.append(group.iloc[val_end:])

    train = pd.concat(train_dfs, ignore_index=True).sample(frac=1, random_state=42)
    val = pd.concat(val_dfs, ignore_index=True).sample(frac=1, random_state=42)
    test = pd.concat(test_dfs, ignore_index=True).sample(frac=1, random_state=42)

    print(f"  ✅ Train : {len(train)} lignes")
    print(f"  ✅ Val   : {len(val)} lignes")
    print(f"  ✅ Test  : {len(test)} lignes")
    if skipped:
        print(f"  ⚠️  {skipped} médicaments ignorés")

    return train, val, test


# ==========================================
# 4. OPTUNA
# ==========================================
def optimize_hyperparameters(X_train, y_train, X_val, y_val, n_trials=30):
    print(f"\n🔧 Optimisation Optuna ({n_trials} trials)...")

    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 200, 1000),
            'max_depth': trial.suggest_int('max_depth', 4, 12),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'gamma': trial.suggest_float('gamma', 0, 1),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 1),
        }
        model = XGBRegressor(**params, random_state=42, n_jobs=-1)z
        model.fit(X_train, y_train, verbose=False)
        return mean_absolute_error(y_val, model.predict(X_val))

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"\n✅ Meilleur MAE : {study.best_value:.4f}")
    for k, v in study.best_params.items():
        print(f"   • {k}: {v}")

    return study.best_params


# ==========================================
# 5. ENTRAÎNEMENT FINAL
# ==========================================
def train_final_model(X_train, y_train, X_val, y_val, params):
    print("\n🤖 Entraînement final...")
    model = XGBRegressor(**params, early_stopping_rounds=50,
                         random_state=42, n_jobs=-1)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    print(f"✅ {model.best_iteration} arbres")
    return model


# ==========================================
# 6. ÉVALUATION
# ==========================================
def evaluate(model, X, y, name):
    y_pred = np.maximum(model.predict(X), 0)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    mask = y > 0
    mape = np.mean(np.abs((y[mask] - y_pred[mask]) / y[mask])) * 100 if mask.sum() else 0

    print(f"\n📊 {name} :")
    print(f"   MAE  : {mae:.2f}")
    print(f"   RMSE : {rmse:.2f}")
    print(f"   MAPE : {mape:.1f}%")
    print(f"   R²   : {r2:.3f}")

    return {"mae": float(mae), "rmse": float(rmse),
            "mape": float(mape), "r2": float(r2)}


# ==========================================
# 7. FEATURE IMPORTANCE
# ==========================================
def show_feature_importance(model, features):
    print("\n📊 TOP 15 FEATURES :")
    imp = model.feature_importances_
    idx = np.argsort(imp)[::-1]
    for i in range(min(15, len(features))):
        print(f"   {i+1:2d}. {features[idx[i]]:25s} : {imp[idx[i]]:.4f}")


# ==========================================
# 8. MAIN
# ==========================================
def train_model():
    print("=" * 70)
    print("🚀 ENTRAÎNEMENT DENG PHARMA v3.0 (CSV)")
    print("=" * 70)

    df = load_data_from_csv()
    df = feature_engineering(df)

    if len(df) < 200:
        raise ValueError(f"❌ Pas assez de données ({len(df)})")

    train, val, test = split_data(df)

    X_train, y_train = train[FEATURES], train[TARGET]
    X_val, y_val = val[FEATURES], val[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]

    best_params = optimize_hyperparameters(X_train, y_train, X_val, y_val, n_trials=30)
    model = train_final_model(X_train, y_train, X_val, y_val, best_params)

    print("\n" + "=" * 70)
    print("📊 ÉVALUATION FINALE")
    print("=" * 70)
    val_metrics = evaluate(model, X_val, y_val, "Validation")
    test_metrics = evaluate(model, X_test, y_test, "Test")

    show_feature_importance(model, FEATURES)

    print("\n💾 Sauvegarde...")
    joblib.dump(model, os.path.join(MODELS_DIR, 'xgboost_tchad.pkl'))
    joblib.dump(FEATURES, os.path.join(MODELS_DIR, 'features.pkl'))

    metrics = {
        "test": test_metrics,
        "validation": val_metrics,
        "model_version": f"v{date.today().strftime('%Y%m%d')}-v3-csv",
        "trained_at": date.today().isoformat(),
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
        "n_features": len(FEATURES),
        "n_medicines": int(df['medicine_id'].nunique()),
        "date_range": [df['date'].min().isoformat(), df['date'].max().isoformat()],
        "best_params": best_params,
    }
    with open(os.path.join(MODELS_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 70)
    print("🎉 ENTRAÎNEMENT TERMINÉ !")
    print("=" * 70)
    print(f"   MAE  : 16.18 → {test_metrics['mae']:.2f}")
    print(f"   RMSE : 43.17 → {test_metrics['rmse']:.2f}")
    print(f"   MAPE : 23.95% → {test_metrics['mape']:.1f}%")
    print(f"   R²   : 0.792 → {test_metrics['r2']:.3f}")
    print(f"\n💾 {MODELS_DIR}/xgboost_tchad.pkl")
    print("=" * 70)


if __name__ == "__main__":
    train_model()