# ai_service/training/plot_radar_fr.py
"""
Radar chart des hyperparamètres XGBoost - VERSION FRANÇAISE
Avec traductions et annotations pédagogiques
"""
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. TRADUCTION DES HYPERPARAMÈTRES
# ==========================================
# Mapping anglais → français
traduction = {
    'n_estimators':      'Nombre d\'arbres',
    'max_depth':         'Profondeur max',
    'learning_rate':     'Taux d\'apprentissage',
    'subsample':         'Échantillonnage\nlignes',
    'colsample_bytree':  'Échantillonnage\ncolonnes',
    'min_child_weight':  'Poids min\npar feuille',
    'gamma':             'Gain min\npour split',
    'reg_alpha':         'Régularisation L1',
    'reg_lambda':        'Régularisation L2',
}

# ==========================================
# 2. HYPERPARAMÈTRES OPTIMAUX (trouvés par Optuna)
# ==========================================
params = {
    'n_estimators':      669,
    'max_depth':         12,
    'learning_rate':     0.0228,
    'subsample':         0.617,
    'colsample_bytree':  0.676,
    'min_child_weight':  4,
    'gamma':             0.762,
    'reg_alpha':         0.646,
    'reg_lambda':        0.140,
}

# ==========================================
# 3. PLAGES DE RECHERCHE OPTUNA
# ==========================================
ranges = {
    'n_estimators':      (200, 1000),
    'max_depth':         (4, 12),
    'learning_rate':     (0.01, 0.2),
    'subsample':         (0.6, 1.0),
    'colsample_bytree':  (0.6, 1.0),
    'min_child_weight':  (1, 10),
    'gamma':             (0, 1),
    'reg_alpha':         (0, 1),
    'reg_lambda':        (0, 1),
}

# ==========================================
# 4. NORMALISATION
# ==========================================
labels_en = list(params.keys())
labels_fr = [traduction[k] for k in labels_en]

values_norm = []
for name in labels_en:
    vmin, vmax = ranges[name]
    values_norm.append((params[name] - vmin) / (vmax - vmin))

values_norm += values_norm[:1]
angles = np.linspace(0, 2 * np.pi, len(labels_en), endpoint=False).tolist()
angles += angles[:1]

# ==========================================
# 5. GRAPHIQUE
# ==========================================
fig, ax = plt.subplots(figsize=(11, 11), subplot_kw=dict(polar=True))
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

# Polygone
ax.plot(angles, values_norm, 'o-', linewidth=2.5, color='#2E86DE',
        markersize=10, markerfacecolor='#2E86DE', markeredgecolor='white',
        markeredgewidth=2)
ax.fill(angles, values_norm, alpha=0.25, color='#2E86DE')

# Labels en français avec valeurs
labels_with_values = []
for name, trad in zip(labels_en, labels_fr):
    raw = params[name]
    if isinstance(raw, float) and raw < 1:
        labels_with_values.append(f"{trad}\n= {raw:.3f}")
    else:
        labels_with_values.append(f"{trad}\n= {raw}")

ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels_with_values, fontsize=11, fontweight='bold',
                   color='#1e293b')

# Axe radial
ax.set_ylim(0, 1)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'],
                   fontsize=9, color='#64748b')
ax.grid(color='#cbd5e1', linestyle='--', linewidth=0.8, alpha=0.7)

# Titre
plt.title('Profil des hyperparamètres XGBoost optimaux\n'
          '(Optimisation bayésienne Optuna — 30 essais)\n',
          fontsize=15, fontweight='bold', color='#0f172a', pad=35)

# Légende explicative
plt.figtext(0.5, -0.06,
    'Chaque sommet représente un hyperparamètre, normalisé entre 0 (valeur minimale)\n'
    'et 1 (valeur maximale) de sa plage de recherche.\n'
    'Plus le polygone s\'étend vers l\'extérieur, plus la valeur est élevée.',
    ha='center', fontsize=10, style='italic', color='#475569',
    bbox=dict(boxstyle='round,pad=0.6', facecolor='#f1f5f9',
              edgecolor='#cbd5e1', alpha=0.9))

plt.tight_layout()
plt.savefig('hyperparams_radar_fr.png', dpi=300, bbox_inches='tight',
            facecolor='white')
plt.show()
print("✅ Graphique sauvegardé : hyperparams_radar_fr.png")