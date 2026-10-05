# ai_service/training/compare_models.py
import json
import matplotlib.pyplot as plt
import numpy as np

# Charger les métriques
with open('../models/metrics.json', 'r') as f:
    xgb = json.load(f)
with open('../models/metrics_lightgbm.json', 'r') as f:
    lgbm = json.load(f)

models = ['XGBoost', 'LightGBM']
mae = [xgb['test']['mae'], lgbm['test']['mae']]
rmse = [xgb['test']['rmse'], lgbm['test']['rmse']]
mape = [xgb['test']['mape'], lgbm['test']['mape']]
r2 = [xgb['test']['r2'], lgbm['test']['r2']]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# MAE
axes[0, 0].bar(models, mae, color=['#3498db', '#e67e22'])
axes[0, 0].set_title('MAE (plus bas = mieux)', fontweight='bold')
for i, v in enumerate(mae):
    axes[0, 0].text(i, v + 0.2, f'{v:.2f}', ha='center', fontweight='bold')

# RMSE
axes[0, 1].bar(models, rmse, color=['#3498db', '#e67e22'])
axes[0, 1].set_title('RMSE (plus bas = mieux)', fontweight='bold')
for i, v in enumerate(rmse):
    axes[0, 1].text(i, v + 0.3, f'{v:.2f}', ha='center', fontweight='bold')

# MAPE
axes[1, 0].bar(models, mape, color=['#3498db', '#e67e22'])
axes[1, 0].set_title('MAPE % (plus bas = mieux)', fontweight='bold')
for i, v in enumerate(mape):
    axes[1, 0].text(i, v + 0.2, f'{v:.1f}%', ha='center', fontweight='bold')

# R²
axes[1, 1].bar(models, r2, color=['#3498db', '#e67e22'])
axes[1, 1].set_title('R² (plus haut = mieux)', fontweight='bold')
axes[1, 1].set_ylim(0, 1)
for i, v in enumerate(r2):
    axes[1, 1].text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold')

plt.suptitle('Comparaison XGBoost vs LightGBM', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('comparison_xgb_lgbm.png', dpi=300, bbox_inches='tight')
plt.show()
print("✅ comparison_xgb_lgbm.png généré")