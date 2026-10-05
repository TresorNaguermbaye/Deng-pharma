"""
DENG PHARMA - Génération des graphiques professionnels
Version rapport PFE — Style académique publication-ready
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ==========================================
# CONFIGURATION GLOBALE
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "tchad_pharma_sales.csv")
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")
MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_tchad.pkl")
FEATURES_PATH = os.path.join(MODELS_DIR, "features.pkl")
PLOTS_DIR = os.path.join(BASE_DIR, "..", "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# ==========================================
# PALETTE DE COULEURS DENG PHARMA
# ==========================================
COLORS = {
    'primary':   '#0ABAB5',  # Cyan (marque)
    'secondary': '#0F1A2C',  # Bleu foncé (marque)
    'danger':    '#FF6B6B',  # Rouge corail
    'success':   '#10b981',  # Vert
    'warning':   '#f59e0b',  # Orange
    'info':      '#3b82f6',  # Bleu
    'gray':      '#6b7280',  # Gris
    'light':     '#f3f4f6',  # Gris clair
}

# ==========================================
# STYLE MATPLOTLIB PROFESSIONNEL
# ==========================================
plt.rcParams.update({
    'figure.figsize': (14, 7),
    'figure.dpi': 100,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
    'font.family': 'DejaVu Sans',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.titlepad': 15,
    'axes.labelsize': 12,
    'axes.labelweight': 'semibold',
    'axes.labelpad': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.edgecolor': '#d1d5db',
    'axes.linewidth': 0.8,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 11,
    'legend.frameon': True,
    'legend.framealpha': 0.95,
    'legend.edgecolor': '#e5e7eb',
    'grid.color': '#e5e7eb',
    'grid.linewidth': 0.6,
    'grid.alpha': 0.5,
})

print("=" * 70)
print("🎨 DENG PHARMA — Graphiques professionnels PFE")
print("=" * 70)
print(f"📁 Plots → {PLOTS_DIR}\n")

# ==========================================
# 1. CHARGEMENT DES DONNÉES
# ==========================================
print("📊 Chargement des données...")
df = pd.read_csv(CSV_PATH)
df.columns = [c.strip().lower() for c in df.columns]
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['date', 'sales'])

model = joblib.load(MODEL_PATH)
FEATURES = joblib.load(FEATURES_PATH)
TARGET = 'sales'

print(f"   ✅ {len(df)} lignes chargées")
print(f"   ✅ Modèle : {os.path.basename(MODEL_PATH)}")
print(f"   ✅ Features : {len(FEATURES)}\n")

# ==========================================
# 2. FEATURE ENGINEERING (identique à l'entraînement)
# ==========================================
print("🔧 Reconstruction des features...")

df['medicine_encoded'] = df['medicine_id'].astype('category').cat.codes
df['category_encoded'] = df['category'].astype('category').cat.codes

if 'day_of_month' not in df.columns:
    df['day_of_month'] = df['date'].dt.day
if 'week_of_year' not in df.columns:
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
if 'day_of_week' not in df.columns:
    df['day_of_week'] = df['date'].dt.weekday
if 'month' not in df.columns:
    df['month'] = df['date'].dt.month
if 'is_weekend' not in df.columns:
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
if 'season' not in df.columns:
    df['season'] = df['month'].apply(lambda m: 1 if m in [6, 7, 8, 9, 10] else 0)

all_series = []
for med_id, group in df.groupby('medicine_id'):
    group = group.set_index('date').sort_index()
    full_range = pd.date_range(group.index.min(), group.index.max(), freq='D')
    group = group.reindex(full_range)
    group['sales'] = group['sales'].fillna(0)
    group['medicine_id'] = med_id
    for col in ['medicine_encoded', 'category_encoded', 'price',
                'base_criticality', 'current_stock']:
        if col in group.columns:
            group[col] = group[col].ffill().bfill()
    all_series.append(group)

df = pd.concat(all_series).reset_index().rename(columns={'index': 'date'})

for lag in [2, 4, 5, 6, 21]:
    df[f'lag_{lag}'] = df.groupby('medicine_id')['sales'].shift(lag)

for w in [7, 30]:
    df[f'rolling_std_{w}'] = df.groupby('medicine_id')['sales'].transform(
        lambda x: x.rolling(w, min_periods=1).std().fillna(0))
    df[f'rolling_min_{w}'] = df.groupby('medicine_id')['sales'].transform(
        lambda x: x.rolling(w, min_periods=1).min())
    df[f'rolling_max_{w}'] = df.groupby('medicine_id')['sales'].transform(
        lambda x: x.rolling(w, min_periods=1).max())

df['trend_7'] = df['rolling_mean_7'] - df['rolling_mean_14']
df['trend_30'] = df['rolling_mean_7'] - df['rolling_mean_30']

df = df.dropna(subset=FEATURES).fillna(0)
print(f"   ✅ {len(df)} lignes exploitables\n")

# ==========================================
# 3. SPLIT TEMPOREL
# ==========================================
print("✂️ Split temporel 70/15/15...")
train_dfs, val_dfs, test_dfs = [], [], []

for med_id, group in df.groupby('medicine_id'):
    group = group.sort_values('date').reset_index(drop=True)
    n = len(group)
    if n < 20: continue
    train_end = int(n * 0.7)
    val_end = train_end + int(n * 0.15)
    train_dfs.append(group.iloc[:train_end])
    val_dfs.append(group.iloc[train_end:val_end])
    test_dfs.append(group.iloc[val_end:])

train = pd.concat(train_dfs, ignore_index=True).sort_values('date')
test = pd.concat(test_dfs, ignore_index=True).sort_values('date')
print(f"   ✅ Train : {len(train)} lignes")
print(f"   ✅ Test  : {len(test)} lignes\n")

# ==========================================
# 4. PRÉDICTIONS + MÉTRIQUES
# ==========================================
print("🤖 Prédictions...")
X_test = test[FEATURES]
y_test = test[TARGET].values
y_pred = np.maximum(model.predict(X_test), 0)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
mask = y_test > 0
mape = np.mean(np.abs((y_test[mask] - y_pred[mask]) / y_test[mask])) * 100

print(f"   MAE  : {mae:.2f}")
print(f"   RMSE : {rmse:.2f}")
print(f"   MAPE : {mape:.2f}%")
print(f"   R²   : {r2:.4f}\n")

# ==========================================
# FONCTION UTILITAIRE : ENCADRÉ MÉTRIQUES
# ==========================================
def add_metrics_box(ax, metrics_dict, loc='upper left'):
    """Ajoute un encadré avec les métriques sur le graphique."""
    text = "\n".join([f"{k} : {v}" for k, v in metrics_dict.items()])
    props = dict(
        boxstyle='round,pad=0.6',
        facecolor='white',
        edgecolor=COLORS['primary'],
        linewidth=1.5,
        alpha=0.95,
    )
    positions = {
        'upper left': (0.02, 0.97, 'top', 'left'),
        'upper right': (0.98, 0.97, 'top', 'right'),
        'lower left': (0.02, 0.03, 'bottom', 'left'),
        'lower right': (0.98, 0.03, 'bottom', 'right'),
    }
    x, y, va, ha = positions[loc]
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=10, verticalalignment=va, horizontalalignment=ha,
            bbox=props, fontfamily='monospace')


# ==========================================
# FIGURE 1 — Vue globale agrégée
# ==========================================
print("📈 Figure 1 — Vue globale...")
daily = pd.DataFrame({
    'date': test['date'].values,
    'reel': y_test,
    'predit': y_pred,
}).groupby('date').sum().reset_index()

fig, ax = plt.subplots(figsize=(15, 7))

# Zone d'écart (fill between)
ax.fill_between(daily['date'], daily['reel'], daily['predit'],
                color=COLORS['gray'], alpha=0.15, label='Écart réel/prédit')

# Courbes
ax.plot(daily['date'], daily['reel'],
        color=COLORS['primary'], linewidth=2.5,
        marker='o', markersize=3, label='Ventes réelles', zorder=3)
ax.plot(daily['date'], daily['predit'],
        color=COLORS['danger'], linewidth=2.5, linestyle='--',
        marker='s', markersize=3, label='Ventes prédites', zorder=2)

# Encadré métriques
add_metrics_box(ax, {
    'R²': f'{r2:.4f}',
    'MAE': f'{mae:.2f} unités',
    'RMSE': f'{rmse:.2f} unités',
    'MAPE': f'{mape:.2f}%',
}, loc='upper left')

# Titre et labels
ax.set_title('Figure 1 — Ventes totales : Réel vs Prédit (jeu de test)',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Ventes journalières (unités)', fontsize=12)
ax.legend(loc='upper right', fontsize=11, framealpha=0.95)
ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.6)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
plt.xticks(rotation=45, ha='right')

# Annotation période
ax.text(0.98, 0.02,
        f'Période de test : {daily["date"].min().strftime("%d/%m/%Y")} → {daily["date"].max().strftime("%d/%m/%Y")}\n'
        f'{len(test)} observations • 15 médicaments',
        transform=ax.transAxes, fontsize=9, style='italic',
        verticalalignment='bottom', horizontalalignment='right',
        color=COLORS['gray'])

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, '01_reel_vs_predit_global.png'), dpi=300)
plt.savefig(os.path.join(PLOTS_DIR, '01_reel_vs_predit_global.pdf'))
plt.close()
print("   ✅ 01_reel_vs_predit_global.png + .pdf")


# ==========================================
# FIGURE 2 — Zoom 60 jours (barres + ligne)
# ==========================================
print("📈 Figure 2 — Zoom 60 jours...")
zoom = daily.head(60).copy()

fig, ax = plt.subplots(figsize=(15, 7))

# Barres pour le réel
ax.bar(zoom['date'], zoom['reel'],
       color=COLORS['primary'], alpha=0.4,
       label='Ventes réelles', width=0.8, zorder=1)

# Ligne pour le prédit
ax.plot(zoom['date'], zoom['predit'],
        color=COLORS['danger'], linewidth=2.5,
        marker='o', markersize=5,
        label='Ventes prédites', zorder=3)

# Ligne horizontale = moyenne réelle
mean_reel = zoom['reel'].mean()
ax.axhline(mean_reel, color=COLORS['secondary'],
           linestyle=':', linewidth=1.5, alpha=0.7,
           label=f'Moyenne réelle ({mean_reel:.0f} u.)')

# Encadré statistiques
mae_zoom = np.mean(np.abs(zoom['reel'] - zoom['predit']))
add_metrics_box(ax, {
    'MAE (zoom)': f'{mae_zoom:.2f}',
    'Max réel': f'{zoom["reel"].max():.0f}',
    'Max prédit': f'{zoom["predit"].max():.0f}',
    'Min réel': f'{zoom["reel"].min():.0f}',
}, loc='upper right')

ax.set_title('Figure 2 — Zoom sur les 60 premiers jours du test',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Ventes journalières (unités)', fontsize=12)
ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
ax.grid(True, alpha=0.3, axis='y')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, '02_zoom_60_jours.png'), dpi=300)
plt.savefig(os.path.join(PLOTS_DIR, '02_zoom_60_jours.pdf'))
plt.close()
print("   ✅ 02_zoom_60_jours.png + .pdf")


# ==========================================
# FIGURE 3 — Scatter avec densité
# ==========================================
print("📈 Figure 3 — Scatter corrélation...")
fig, ax = plt.subplots(figsize=(10, 10))

# Scatter avec gradient
scatter = ax.scatter(y_test, y_pred,
                     c=np.abs(y_test - y_pred),  # couleur = erreur
                     cmap='RdYlGn_r', alpha=0.6, s=25,
                     edgecolors='white', linewidths=0.3)

# Droite idéale
max_val = max(y_test.max(), y_pred.max()) * 1.05
ax.plot([0, max_val], [0, max_val],
        color=COLORS['danger'], linewidth=2.5, linestyle='--',
        label='Prédiction parfaite (y=x)', zorder=2)

# Colorbar
cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Erreur absolue (unités)', fontsize=11, fontweight='semibold')

# Encadré métriques
add_metrics_box(ax, {
    'R²': f'{r2:.4f}',
    'MAE': f'{mae:.2f}',
    'RMSE': f'{rmse:.2f}',
    'MAPE': f'{mape:.2f}%',
}, loc='upper left')

ax.set_title('Figure 3 — Corrélation Réel / Prédit',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlabel('Valeurs réelles (unités)', fontsize=12)
ax.set_ylabel('Valeurs prédites (unités)', fontsize=12)
ax.legend(loc='lower right', fontsize=11)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, max_val)
ax.set_ylim(0, max_val)
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, '03_scatter.png'), dpi=300)
plt.savefig(os.path.join(PLOTS_DIR, '03_scatter.pdf'))
plt.close()
print("   ✅ 03_scatter.png + .pdf")


# ==========================================
# FIGURE 4 — Top 4 médicaments (2x2)
# ==========================================
print("📈 Figure 4 — Top 4 médicaments...")
top_meds = test.groupby('medicine_id')[TARGET].sum().nlargest(4).index.tolist()

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()

for i, med_id in enumerate(top_meds):
    sub = test[test['medicine_id'] == med_id].sort_values('date')
    X_sub = sub[FEATURES]
    y_sub = sub[TARGET].values
    y_sub_pred = np.maximum(model.predict(X_sub), 0)

    mae_sub = mean_absolute_error(y_sub, y_sub_pred)
    r2_sub = r2_score(y_sub, y_sub_pred)

    ax = axes[i]

    # Zone d'écart
    ax.fill_between(sub['date'].values, y_sub, y_sub_pred,
                    color=COLORS['gray'], alpha=0.15)

    # Courbes
    ax.plot(sub['date'].values, y_sub,
            color=COLORS['primary'], linewidth=1.8, label='Réel')
    ax.plot(sub['date'].values, y_sub_pred,
            color=COLORS['danger'], linewidth=1.8, linestyle='--',
            label='Prédit')

    # Titre avec métriques
    ax.set_title(f'{med_id}  |  MAE = {mae_sub:.2f}  |  R² = {r2_sub:.3f}',
                 fontsize=11, fontweight='bold', color=COLORS['secondary'])

    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Ventes (unités)', fontsize=10)
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45, labelsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

fig.suptitle('Figure 4 — Précision par médicament (Top 4 des ventes)',
             fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, '04_par_medicament.png'), dpi=300)
plt.savefig(os.path.join(PLOTS_DIR, '04_par_medicament.pdf'))
plt.close()
print("   ✅ 04_par_medicament.png + .pdf")


# ==========================================
# FIGURE 5 — Distribution des erreurs
# ==========================================
print("📈 Figure 5 — Distribution des erreurs...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Histogramme des erreurs %
error_pct = np.abs((y_test[mask] - y_pred[mask]) / y_test[mask]) * 100
error_pct = error_pct[error_pct < 100]  # filtrer les outliers extrêmes

n, bins, patches = ax1.hist(error_pct, bins=40,
                             color=COLORS['primary'], alpha=0.7,
                             edgecolor='white', linewidth=0.5)

# Colorer selon seuils
for patch, bin_left in zip(patches, bins[:-1]):
    if bin_left < 10:
        patch.set_facecolor(COLORS['success'])
    elif bin_left < 20:
        patch.set_facecolor(COLORS['warning'])
    else:
        patch.set_facecolor(COLORS['danger'])

ax1.axvline(mape, color=COLORS['secondary'], linestyle='--',
            linewidth=2, label=f'MAPE = {mape:.2f}%')
ax1.set_title('Distribution des erreurs relatives (%)',
              fontsize=13, fontweight='bold')
ax1.set_xlabel('Erreur (%)', fontsize=11)
ax1.set_ylabel('Fréquence', fontsize=11)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# Diagramme cumulé
sorted_err = np.sort(error_pct)
cumulative = np.arange(1, len(sorted_err) + 1) / len(sorted_err) * 100

ax2.plot(sorted_err, cumulative,
         color=COLORS['primary'], linewidth=2.5)
ax2.fill_between(sorted_err, 0, cumulative,
                 color=COLORS['primary'], alpha=0.15)

# Lignes de référence
for pct in [10, 20, 30]:
    y_at_pct = np.sum(error_pct <= pct) / len(error_pct) * 100
    ax2.axvline(pct, color=COLORS['gray'], linestyle=':', linewidth=1)
    ax2.text(pct + 0.5, y_at_pct,
             f'{pct}% → {y_at_pct:.0f}% des cas',
             fontsize=9, color=COLORS['gray'])

ax2.set_title('Distribution cumulée des erreurs',
              fontsize=13, fontweight='bold')
ax2.set_xlabel('Erreur (%)', fontsize=11)
ax2.set_ylabel('% des observations', fontsize=11)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 60)
ax2.set_ylim(0, 105)

fig.suptitle('Figure 5 — Analyse des erreurs du modèle',
             fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(PLOTS_DIR, '05_distribution_erreurs.png'), dpi=300)
plt.savefig(os.path.join(PLOTS_DIR, '05_distribution_erreurs.pdf'))
plt.close()
print("   ✅ 05_distribution_erreurs.png + .pdf")


# ==========================================
# FIGURE 6 — DASHBOARD RÉCAPITULATIF
# ==========================================
print("📈 Figure 6 — Dashboard récapitulatif...")
fig = plt.figure(figsize=(16, 10))
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# --- KPI 1 : R² ---
ax_kpi1 = fig.add_subplot(gs[0, 0])
ax_kpi1.axis('off')
ax_kpi1.add_patch(Rectangle((0.05, 0.1), 0.9, 0.8,
                             facecolor=COLORS['primary'], alpha=0.15,
                             edgecolor=COLORS['primary'], linewidth=2,
                             transform=ax_kpi1.transAxes))
ax_kpi1.text(0.5, 0.65, f'{r2:.3f}', fontsize=42, fontweight='bold',
             ha='center', va='center', color=COLORS['primary'],
             transform=ax_kpi1.transAxes)
ax_kpi1.text(0.5, 0.3, 'R² (coefficient de détermination)',
             fontsize=11, ha='center', va='center', color=COLORS['gray'],
             transform=ax_kpi1.transAxes)

# --- KPI 2 : MAE ---
ax_kpi2 = fig.add_subplot(gs[0, 1])
ax_kpi2.axis('off')
ax_kpi2.add_patch(Rectangle((0.05, 0.1), 0.9, 0.8,
                             facecolor=COLORS['info'], alpha=0.15,
                             edgecolor=COLORS['info'], linewidth=2,
                             transform=ax_kpi2.transAxes))
ax_kpi2.text(0.5, 0.65, f'{mae:.2f}', fontsize=42, fontweight='bold',
             ha='center', va='center', color=COLORS['info'],
             transform=ax_kpi2.transAxes)
ax_kpi2.text(0.5, 0.3, 'MAE (erreur absolue moyenne)',
             fontsize=11, ha='center', va='center', color=COLORS['gray'],
             transform=ax_kpi2.transAxes)

# --- KPI 3 : MAPE ---
ax_kpi3 = fig.add_subplot(gs[0, 2])
ax_kpi3.axis('off')
ax_kpi3.add_patch(Rectangle((0.05, 0.1), 0.9, 0.8,
                             facecolor=COLORS['warning'], alpha=0.15,
                             edgecolor=COLORS['warning'], linewidth=2,
                             transform=ax_kpi3.transAxes))
ax_kpi3.text(0.5, 0.65, f'{mape:.1f}%', fontsize=42, fontweight='bold',
             ha='center', va='center', color=COLORS['warning'],
             transform=ax_kpi3.transAxes)
ax_kpi3.text(0.5, 0.3, 'MAPE (erreur relative)',
             fontsize=11, ha='center', va='center', color=COLORS['gray'],
             transform=ax_kpi3.transAxes)

# --- Graphique 1 : Courbe global (2 colonnes) ---
ax_main = fig.add_subplot(gs[1, :])
ax_main.plot(daily['date'], daily['reel'],
             color=COLORS['primary'], linewidth=2, label='Réel')
ax_main.plot(daily['date'], daily['predit'],
             color=COLORS['danger'], linewidth=2, linestyle='--', label='Prédit')
ax_main.fill_between(daily['date'], daily['reel'], daily['predit'],
                     color=COLORS['gray'], alpha=0.15)
ax_main.set_title('Vue globale : Réel vs Prédit', fontsize=12, fontweight='bold')
ax_main.set_ylabel('Ventes (u.)', fontsize=10)
ax_main.legend(loc='upper left', fontsize=9)
ax_main.grid(True, alpha=0.3)
ax_main.tick_params(labelsize=9)

# --- Graphique 2 : Scatter ---
ax_scatter = fig.add_subplot(gs[2, 0])
ax_scatter.scatter(y_test, y_pred, alpha=0.4,
                    color=COLORS['primary'], s=10)
ax_scatter.plot([0, max_val], [0, max_val],
                color=COLORS['danger'], linestyle='--', linewidth=1.5)
ax_scatter.set_title(f'Corrélation (R²={r2:.3f})',
                     fontsize=11, fontweight='bold')
ax_scatter.set_xlabel('Réel', fontsize=9)
ax_scatter.set_ylabel('Prédit', fontsize=9)
ax_scatter.grid(True, alpha=0.3)
ax_scatter.tick_params(labelsize=9)

# --- Graphique 3 : Distribution erreurs ---
ax_hist = fig.add_subplot(gs[2, 1])
ax_hist.hist(error_pct, bins=30, color=COLORS['info'],
             alpha=0.7, edgecolor='white')
ax_hist.axvline(mape, color=COLORS['danger'],
                linestyle='--', linewidth=2,
                label=f'MAPE = {mape:.1f}%')
ax_hist.set_title('Distribution des erreurs',
                  fontsize=11, fontweight='bold')
ax_hist.set_xlabel('Erreur (%)', fontsize=9)
ax_hist.set_ylabel('Fréquence', fontsize=9)
ax_hist.legend(fontsize=8)
ax_hist.grid(True, alpha=0.3, axis='y')
ax_hist.tick_params(labelsize=9)

# --- Graphique 4 : Erreur par médicament ---
ax_bar = fig.add_subplot(gs[2, 2])
med_errors = test.copy()
med_errors['erreur_abs'] = np.abs(y_test - y_pred)
med_mae = med_errors.groupby('medicine_id')['erreur_abs'].mean().sort_values()

colors_bar = [COLORS['success'] if v < 10 else
              COLORS['warning'] if v < 20 else COLORS['danger']
              for v in med_mae.values]

ax_bar.barh(range(len(med_mae)), med_mae.values,
            color=colors_bar, alpha=0.8, edgecolor='white')
ax_bar.set_yticks(range(len(med_mae)))
ax_bar.set_yticklabels(med_mae.index, fontsize=8)
ax_bar.set_title('MAE par médicament', fontsize=11, fontweight='bold')
ax_bar.set_xlabel('MAE (unités)', fontsize=9)
ax_bar.grid(True, alpha=0.3, axis='x')
ax_bar.tick_params(labelsize=9)

fig.suptitle('DENG PHARMA — Dashboard Performance du modèle XGBoost',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(os.path.join(PLOTS_DIR, '06_dashboard_performance.png'),
            dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(PLOTS_DIR, '06_dashboard_performance.pdf'),
            bbox_inches='tight')
plt.close()
print("   ✅ 06_dashboard_performance.png + .pdf")


# ==========================================
# EXPORT CSV
# ==========================================
print("\n💾 Export CSV des prédictions...")
export_df = pd.DataFrame({
    'date': test['date'].dt.strftime('%Y-%m-%d').values,
    'medicine_id': test['medicine_id'].values,
    'reel': y_test,
    'predit': y_pred,
    'erreur_absolue': np.abs(y_test - y_pred),
    'erreur_pct': np.where(y_test > 0,
                            np.abs((y_test - y_pred) / y_test) * 100,
                            0),
})
csv_out = os.path.join(PLOTS_DIR, 'predictions_test.csv')
export_df.to_csv(csv_out, index=False)
print(f"   ✅ predictions_test.csv ({len(export_df)} lignes)")


# ==========================================
# RÉSUMÉ FINAL
# ==========================================
print("\n" + "=" * 70)
print("🎉 GÉNÉRATION TERMINÉE AVEC SUCCÈS !")
print("=" * 70)
print(f"\n📁 Dossier : {PLOTS_DIR}\n")
print("📊 Fichiers générés :")
print("   • 01_reel_vs_predit_global.png / .pdf   (vue globale)")
print("   • 02_zoom_60_jours.png / .pdf           (zoom détaillé)")
print("   • 03_scatter.png / .pdf                 (corrélation)")
print("   • 04_par_medicament.png / .pdf          (top 4 médicaments)")
print("   • 05_distribution_erreurs.png / .pdf    (analyse erreurs)")
print("   • 06_dashboard_performance.png / .pdf   (dashboard récap)")
print("   • predictions_test.csv                  (données brutes)")
print(f"\n📈 Métriques finales :")
print(f"   • R²   = {r2:.4f}")
print(f"   • MAE  = {mae:.2f} unités")
print(f"   • RMSE = {rmse:.2f} unités")
print(f"   • MAPE = {mape:.2f}%")
print("=" * 70)