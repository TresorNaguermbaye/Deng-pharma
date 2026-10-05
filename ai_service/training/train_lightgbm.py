# ai_service/training/train_lightgbm.py
"""
DENG PHARMA - Entraînement LightGBM (modèle secondaire)
Version 1.0 - Basé sur tchad_pharma_sales.csv
Objectif : comparer avec XGBoost
"""
import os
import json
import warnings
import pandas as pd
import numpy as np
from datetime import date
import lightgbm as lgb
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

# ==========================================
# MÊMES FEATURES QUE XGBOOST (pour comparaison équitable)
# ==========================================
FEATURES = [
    'day_of_week', 'day_of_month', 'month', 'week_of_year',
    'is_weekend', 'season',
    'lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_5',
    'lag_6', 'lag_7', 'lag_14', 'lag_21', 'lag_30',
    'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
    'rolling_std_7', 'rolling_std_30',
    'rolling_min_7', 'rolling_max_7',
    'rolling_min_30', 'rolling_max_30',
    'trend_7', 'trend_30',
    'price', 'base_criticality', 'current_stock',
    'medicine_encoded', 'category_encoded',
]
TARGET = 'sales'

# ==========================================
# CHARGEMENT (identique à XGBoost)
# ==========================================
def load_data_from_csv():
    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip().lower() for c in df.columns]
    
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'sales'])
    df['sales'] = df['sales'].astype(float)
    
    if 'price' not in df.columns:
        df['price'] = 2500.0
    if 'base_criticality' not in df.columns:
        df['base_criticality'] = 5
    if 'current_stock' not in df.columns:
        df['current_stock'] = 0
    if 'category' not in df.columns:
        df['category'] = 'unknown'
    
    print(f"📊 Données : {len(df)} lignes")
    return df

# ==========================================
# FEATURE ENGINEERING (identique)
# ==========================================
def feature_engineering(df):
    df['medicine_encoded'] = df['medicine_id'].astype('category').cat.codes
    df['category_encoded'] = df['category'].astype('category').cat.codes
    df['day_of_month'] = df['date'].dt.day
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    
    # Série continue
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
    
    for lag in [2, 4, 5, 6, 21]:
        df[f'lag_{lag}'] = df.groupby('medicine_id')['sales'].shift(lag)
    
    for window in [7, 30]:
        df[f'rolling_std_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).std().fillna(0))
        df[f'rolling_min_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).min())
        df[f'rolling_max_{window}'] = df.groupby('medicine_id')['sales'].transform(
            lambda x: x.rolling(window, min_periods=1).max())
    
    df['trend_7'] = df['rolling_mean_7'] - df['rolling_mean_14']
    df['trend_30'] = df['rolling_mean_7'] - df['rolling_mean_30']
    
    df = df.dropna(subset=FEATURES).fillna(0)
    return df

# ==========================================
# SPLIT (identique)
# ==========================================
def split_data(df, train_ratio=0.7, val_ratio=0.15):
    train_dfs, val_dfs, test_dfs = [], [], []
    for med_id, group in df.groupby('medicine_id'):
        group = group.sort_values('date').reset_index(drop=True)
        n = len(group)
        if n < 20:
            continue
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        train_dfs.append(group.iloc[:train_end])
        val_dfs.append(group.iloc[train_end:val_end])
        test_dfs.append(group.iloc[val_end:])
    
    train = pd.concat(train_dfs, ignore_index=True).sample(frac=1, random_state=42)
    val = pd.concat(val_dfs, ignore_index=True).sample(frac=1, random_state=42)
    test = pd.concat(test_dfs, ignore_index=True).sample(frac=1, random_state=42)
    
    print(f"  ✅ Train : {len(train)} | Val : {len(val)} | Test : {len(test)}")
    return train, val, test

# ==========================================
# OPTUNA LIGHTGBM
# ==========================================
def optimize_lightgbm(X_train, y_train, X_val, y_val, n_trials=30):
    print(f"\n🔧 Optimisation Optuna LightGBM ({n_trials} trials)...")
    
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 200, 1000),
            'max_depth': trial.suggest_int('max_depth', 4, 12),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 1),
        }
        model = lgb.LGBMRegressor(**params, random_state=42, n_jobs=-1, verbose=-1)
        model.fit(X_train, y_train)
        return mean_absolute_error(y_val, model.predict(X_val))
    
    study = optuna.create_study(
        direction='minimize',
        sampler=optuna.samplers.TPESampler(seed=42)  # Reproductibilité
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    
    print(f"\n✅ Meilleur MAE : {study.best_value:.4f}")
    return study.best_params

# ==========================================
# ENTRAÎNEMENT FINAL
# ==========================================
def train_final_lightgbm(X_train, y_train, X_val, y_val, params):
    print("\n🤖 Entraînement final LightGBM...")
    model = lgb.LGBMRegressor(
        **params,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric='mae',
        callbacks=[lgb.early_stopping(50, verbose=False)]
    )
    print(f"✅ Meilleure itération : {model.best_iteration_}")
    return model

# ==========================================
# ÉVALUATION
# ==========================================
def evaluate(model, X, y, name):
    y_pred = np.maximum(model.predict(X), 0)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    mask = y > 0
    mape = np.mean(np.abs((y[mask] - y_pred[mask]) / y[mask])) * 100 if mask.sum() else 0
    
    print(f"\n📊 {name} : MAE={mae:.2f} | RMSE={rmse:.2f} | MAPE={mape:.1f}% | R²={r2:.3f}")
    return {"mae": float(mae), "rmse": float(rmse), "mape": float(mape), "r2": float(r2)}

# ==========================================
# MAIN
# ==========================================
def train_lightgbm():
    print("=" * 70)
    print("🚀 ENTRAÎNEMENT LIGHTGBM - DENG PHARMA")
    print("=" * 70)
    
    df = load_data_from_csv()
    df = feature_engineering(df)
    train, val, test = split_data(df)
    
    X_train, y_train = train[FEATURES], train[TARGET]
    X_val, y_val = val[FEATURES], val[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]
    
    best_params = optimize_lightgbm(X_train, y_train, X_val, y_val, n_trials=30)
    model = train_final_lightgbm(X_train, y_train, X_val, y_val, best_params)
    
    print("\n" + "=" * 70)
    print("📊 ÉVALUATION LIGHTGBM")
    print("=" * 70)
    val_metrics = evaluate(model, X_val, y_val, "Validation")
    test_metrics = evaluate(model, X_test, y_test, "Test")
    
    # Sauvegarde
    joblib.dump(model, os.path.join(MODELS_DIR, 'lightgbm_tchad.pkl'))
    joblib.dump(FEATURES, os.path.join(MODELS_DIR, 'features_lightgbm.pkl'))
    
    metrics = {
        "test": test_metrics,
        "validation": val_metrics,
        "model_version": f"lgbm-v{date.today().strftime('%Y%m%d')}",
        "trained_at": date.today().isoformat(),
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
        "best_params": best_params,
    }
    with open(os.path.join(MODELS_DIR, 'metrics_lightgbm.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("\n" + "=" * 70)
    print("🎉 LIGHTGBM TERMINÉ !")
    print(f"   MAE  : {test_metrics['mae']:.2f}")
    print(f"   RMSE : {test_metrics['rmse']:.2f}")
    print(f"   MAPE : {test_metrics['mape']:.1f}%")
    print(f"   R²   : {test_metrics['r2']:.3f}")
    print("=" * 70)

if __name__ == "__main__":
    train_lightgbm()